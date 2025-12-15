import asyncio
import logging
import threading
import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# ADK / GenAI imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# local modules
from Master_Agent.agent import master_pharma_agent
from Backend.src.auth import router as auth_router
from Backend.src.db import init_db, AsyncSessionLocal  # new
from Backend.src import models                  # new
from Backend.src.auth import SECRET_KEY, ALGORITHM  # new
from jose import jwt, JWTError                     # new

# Load .env early
load_dotenv()

# ------------------------------------------------------------------
# Config / Logging
# ------------------------------------------------------------------
APP_NAME = "repurpoai_master"
USER_ID = "web_user"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("backend.app")

# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------
app = FastAPI(title="RepurpoAI Master Agent")

# Register routers (auth/messages/downloads)
app.include_router(auth_router, prefix="/api", tags=["auth", "messages", "downloads"])

# CORS - update origins as needed
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Startup / Shutdown
# ------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Starting up application; initializing DB...")
    try:
        await init_db()
    except Exception as e:
        logger.exception("Failed to initialize DB on startup: %s", e)
        # Fail fast — raise to prevent app from starting in a bad state
        raise

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down application")


# ------------------------------------------------------------------
# Helpers: serialize ADK events & start runner thread
# ------------------------------------------------------------------
def serialize_event(event) -> Dict[str, Any]:
    """Convert an ADK event to a JSON-serializable dict (best-effort)."""
    out: Dict[str, Any] = {"is_final": False, "type": event.__class__.__name__}

    try:
        out["is_final"] = event.is_final_response()
    except Exception:
        out["is_final"] = False

    # Extract text parts
    texts = []
    content = getattr(event, "content", None)
    if content and getattr(content, "parts", None):
        for p in content.parts:
            try:
                if hasattr(p, "text") and p.text:
                    texts.append(p.text)
            except Exception:
                # safe fallback
                continue

    if texts:
        out["text"] = "\n".join(texts)

    # Tool call/response (if present)
    if hasattr(event, "tool_call"):
        try:
            out["tool_call"] = str(event.tool_call)
        except Exception:
            out["tool_call"] = repr(event.tool_call)[:1000]
    if hasattr(event, "tool_response"):
        try:
            out["tool_response"] = event.tool_response
        except Exception:
            out["tool_response"] = repr(event.tool_response)[:1000]

    # Fallback raw repr when nothing extracted
    if "text" not in out and "tool_response" not in out:
        out["raw"] = repr(event)[:2000]

    return out


def start_runner_in_thread(
    runner: Runner,
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue,
    session_id: str,
    content: types.Content,
) -> threading.Thread:
    """
    Start a background thread that runs runner.run(...) and pushes serialized events
    into the provided asyncio.Queue.
    """
    def _run():
        try:
            for event in runner.run(user_id=USER_ID, session_id=session_id, new_message=content):
                # Push into asyncio queue from thread
                asyncio.run_coroutine_threadsafe(queue.put(serialize_event(event)), loop)
                # Stop on final
                try:
                    if event.is_final_response():
                        break
                except Exception:
                    # continue trying to consume events
                    pass
        except Exception as e:
            logger.exception("Runner thread error: %s", e)
            asyncio.run_coroutine_threadsafe(queue.put({"error": str(e)}), loop)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put({"_done": True}), loop)

    thr = threading.Thread(target=_run, daemon=True)
    thr.start()
    return thr


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# ------------------------------------------------------------------
# WebSocket: Master agent streaming
# Protocol (client -> server messages):
#  - {"type":"user_message", "content": "<text>"}
#  - {"type":"human_reply", "content": "<text>"}   (sends feedback to runner)
#  - {"type":"interrupt"}                          (cancel the runner)
#
# Server -> client messages:
#  - {"type":"event", "payload": { ... serialized event ... }}
#  - {"type":"error", "message":"..."}
#  - {"type":"done"}
# ------------------------------------------------------------------
@app.websocket("/ws/master")
async def ws_master(ws: WebSocket):
    await ws.accept()

    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    session_service = InMemorySessionService()

    # Authenticate websocket user from Authorization header (optional)
    user_email = None
    user_id = None
    try:
        auth_hdr = ws.headers.get("authorization") or ws.headers.get("Authorization")
        if auth_hdr and auth_hdr.lower().startswith("bearer "):
            token = auth_hdr.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_email = payload.get("sub")
            except JWTError:
                user_email = None
    except Exception:
        user_email = None

    # Resolve user_id from DB if email present
    if user_email:
        try:
            async with AsyncSessionLocal() as db:
                q = select(models.User).where(models.User.email == user_email)
                res = await db.execute(q)
                user = res.scalar_one_or_none()
                if user:
                    user_id = user.id
        except Exception:
            user_id = None

    # Create ADK session (async API)
    try:
        await session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=session_id)
    except Exception as e:
        logger.exception("Failed to create ADK session: %s", e)
        await ws.send_json({"type": "error", "message": f"session init failed: {e}"})
        await ws.close()
        return

    # build Runner for Master Agent
    runner = Runner(agent=master_pharma_agent, app_name=APP_NAME, session_service=session_service)
    loop = asyncio.get_running_loop()

    # track currently running thread(s)
    active_thread: Optional[threading.Thread] = None

    try:
        while True:
            # Wait for client message
            try:
                msg = await ws.receive_json()
            except WebSocketDisconnect:
                logger.info("WebSocket client disconnected")
                break
            except Exception as e:
                logger.exception("Invalid websocket message: %s", e)
                await ws.send_json({"type": "error", "message": "invalid message"})
                continue

            mtype = msg.get("type")
            if mtype == "user_message":
                text = msg.get("content", "")
                # allow client to pass an existing conversation_id to reuse
                client_conv_id = msg.get("conversation_id")  # expected as UUID string

                conversation_id: Optional[str] = None

                # If the client provided a conversation_id, try to reuse it
                if client_conv_id:
                    conversation_id = client_conv_id

                # If no conversation_id provided, create one (once)
                if not conversation_id and user_id:
                    try:
                        async with AsyncSessionLocal() as db:
                            conv = models.Conversation(user_id=user_id, title=(text[:120] if text else None), meta=None)
                            db.add(conv)
                            await db.commit()
                            await db.refresh(conv)
                            # conv.id is a UUID object (SQLAlchemy UUID as_uuid=True)
                            conversation_id = str(conv.id)
                            # notify client of created conversation id so they can reuse it
                            try:
                                await ws.send_json({"type": "conversation_created", "conversation_id": conversation_id})
                            except Exception:
                                # non-fatal - client might not be listening for this
                                pass
                    except Exception:
                        logger.exception("Failed to persist conversation row")

                # Also create a user Message row for history using conversation_id if available
                if user_id:
                    try:
                        async with AsyncSessionLocal() as db:
                            # If we do not have a conversation_id (no user or creation failed),
                            # insert a message with conversation_id NULL (if schema allows) or skip.
                            if conversation_id:
                                db_msg = models.Message(
                                    user_id=user_id,
                                    conversation_id=conversation_id,
                                    role="user",
                                    content=text,
                                    meta=None,
                                )
                            else:
                                # fallback when no conversation is available: create a message without conversation_id
                                db_msg = models.Message(
                                    user_id=user_id,
                                    role="user",
                                    content=text,
                                    meta=None,
                                )
                            db.add(db_msg)
                            await db.commit()
                    except Exception:
                        logger.exception("Failed to persist user message")

                content = types.Content(role="user", parts=[types.Part(text=text)])
                # start runner thread
                active_thread = start_runner_in_thread(runner, loop, queue, session_id, content)

                # stream events until done
                while True:
                    ev = await queue.get()
                    # runtime errors from thread
                    if isinstance(ev, dict) and ev.get("error"):
                        await ws.send_json({"type": "error", "message": ev["error"]})
                        break
                    # done sentinel
                    if isinstance(ev, dict) and ev.get("_done"):
                        await ws.send_json({"type": "done"})
                        break
                    # normal event
                    await ws.send_json({"type": "event", "payload": ev})

                    # If this event is a final response with text, persist it as a bot message
                    try:
                        if isinstance(ev, dict) and ev.get("is_final") and ev.get("text"):
                            bot_text = ev.get("text")
                            # update Conversation.response with bot_text (if we created one)
                            if conversation_id and user_id:
                                try:
                                    # create assistant message tied to same conversation_id
                                    async with AsyncSessionLocal() as db:
                                        db_msg = models.Message(
                                            user_id=user_id,
                                            conversation_id=conversation_id,
                                            role="assistant",
                                            content=bot_text,
                                            meta=None,
                                        )
                                        db.add(db_msg)
                                        await db.commit()
                                except Exception:
                                    logger.exception("Failed to persist bot response")
                            else:
                                # fallback: persist assistant message without conversation_id if necessary
                                if user_id:
                                    try:
                                        async with AsyncSessionLocal() as db:
                                            db_msg = models.Message(
                                                user_id=user_id,
                                                role="assistant",
                                                content=bot_text,
                                                meta=None,
                                            )
                                            db.add(db_msg)
                                            await db.commit()
                                    except Exception:
                                        logger.exception("Failed to persist fallback bot response")
                    except Exception:
                        # ignore persistence errors and continue streaming
                        logger.exception("Error while handling final event persistence")

            elif mtype == "human_reply":
                # feed human reply to the runner if supported
                content_text = msg.get("content", "")
                if hasattr(runner, "send_user_input"):
                    try:
                        runner.send_user_input(content_text)
                    except Exception as e:
                        logger.exception("Failed to send human_reply: %s", e)
                        await ws.send_json({"type": "error", "message": str(e)})
                else:
                    await ws.send_json({"type": "error", "message": "runner does not support human_reply"})

            elif mtype == "interrupt":
                # cancel the runner if supported
                if hasattr(runner, "cancel"):
                    try:
                        runner.cancel()
                        await ws.send_json({"type": "info", "message": "runner cancelled"})
                    except Exception as e:
                        logger.exception("Failed to cancel runner: %s", e)
                        await ws.send_json({"type": "error", "message": str(e)})
                else:
                    await ws.send_json({"type": "error", "message": "runner cancel not supported"})

            elif mtype == "store_pair":
                # client sends {"type":"store_pair","query":"...", "content":"..."}
                qtext = msg.get("query")
                ctext = msg.get("content")
                if user_id and qtext is not None:
                    try:
                        async with AsyncSessionLocal() as db:
                            conv = models.Conversation(user_id=user_id, query=qtext, response=ctext, meta=None)
                            db.add(conv)
                            await db.commit()
                    except Exception:
                        logger.exception("Failed to store_pair to conversations")
                await ws.send_json({"type": "info", "message": "stored_pair"})

            else:
                await ws.send_json({"type": "error", "message": f"unknown message type: {mtype}"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as e:
        logger.exception("Unexpected error in websocket handler: %s", e)
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        # attempt to close runner (some Runner.close() implementations are async, some sync)
        try:
            close_result = runner.close()
            if asyncio.iscoroutine(close_result):
                await close_result
        except TypeError:
            # close returned None or is sync; ignore
            pass
        except Exception:
            logger.exception("Error closing runner")
        # ensure queue drained / thread stops
        await ws.close()
