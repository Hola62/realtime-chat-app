import os
from functools import wraps

import jwt
from flask import request
from flask_socketio import emit


def token_required(f):
    """Decorator to require JWT token for Socket.IO events."""

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if hasattr(request, "args") and "token" in request.args:
            token = request.args.get("token")

        if not token:
            emit("ai_error", {"message": "Authentication token is missing"})
            return None

        try:
            secret_key = os.getenv("JWT_SECRET_KEY", "change-me")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")

            if not user_id:
                emit("ai_error", {"message": "Invalid token payload"})
                return None

            return f(user_id, *args, **kwargs)
        except jwt.ExpiredSignatureError:
            emit("ai_error", {"message": "Token has expired"})
            return None
        except jwt.InvalidTokenError:
            emit("ai_error", {"message": "Invalid token"})
            return None

    return decorated


def _get_openai_client():
    """Create an OpenAI client from environment variables."""
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError(
            "OpenAI SDK is not installed. Add 'openai' to requirements.txt and install dependencies."
        ) from e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment.")

    return OpenAI(api_key=api_key)


def register_ai_events(socketio):
    """Register AI-related Socket.IO events for chat assistant."""

    @socketio.on("ai_request")
    @token_required
    def handle_ai_request(user_id, data):
        """Handle a request to the AI assistant.

        Expected payload:
        {
          "mode": "dm" | "mention",
          "input": "text",
          "room_id": "private_-1_123" | 42
        }
        """
        mode = (data or {}).get("mode", "dm")
        user_input = (data or {}).get("input", "").strip()
        room_id = (data or {}).get("room_id")

        if not user_input:
            emit("ai_error", {"message": "input is required"})
            return

        # Prepare model and prompt
        model = os.getenv("AI_MODEL", "gpt-4o-mini")
        system_prompt = os.getenv(
            "AI_SYSTEM_PROMPT",
            "You are an AI assistant embedded in a realtime chat app. Be concise, helpful, and safe.",
        )

        try:
            client = _get_openai_client()

            # For MVP, use non-streaming to simplify UI integration
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.4,
                max_tokens=512,
            )

            ai_text = (
                completion.choices[0].message.content
                if completion and completion.choices
                else ""
            )

            # Build a bot message compatible with existing UI
            # Optional avatar for LEXA from environment or default path under /uploads
            ai_avatar = os.getenv("AI_AVATAR_URL")  # e.g., /uploads/avatars/lexa.png

            bot_message = {
                "id": None,
                "room_id": room_id,
                "user_id": -1,
                "content": ai_text,
                "timestamp": None,
                "deleted": False,
                "user": {
                    "first_name": "LEXA",
                    "last_name": "",
                    "email": "",
                    "avatar_url": ai_avatar if ai_avatar else None,
                },
            }

            # Send response depending on mode
            if mode == "dm" and room_id:
                # Emit as a private message in the user's AI room
                emit("private_message", bot_message, to=str(room_id), include_self=True)
            elif mode == "mention" and room_id:
                # Broadcast to regular room as if bot posted there
                emit("new_message", bot_message, to=str(room_id), include_self=True)
            else:
                emit("ai_error", {"message": "Invalid mode or room_id"})

        except Exception as e:
            # Emit error for UI toast
            err_msg = str(e)
            emit("ai_error", {"message": f"AI request failed: {err_msg}"})

            # Additionally, send a helpful in-chat message if possible
            try:
                if mode == "dm" and room_id:
                    # Choose a friendly hint based on common failure modes
                    lower = err_msg.lower()
                    if (
                        "insufficient_quota" in lower
                        or "rate" in lower
                        and "429" in lower
                    ):
                        hint = (
                            "LEXA can't reply right now: the OpenAI API key has insufficient quota. "
                            "Please check your OpenAI billing/plan or use a different API key."
                        )
                    elif (
                        "openai_api_key is not set" in lower
                        or "api key" in lower
                        and "not set" in lower
                    ):
                        hint = "LEXA isn't configured yet. Set OPENAI_API_KEY in the server .env and restart the backend."
                    else:
                        hint = "LEXA hit a temporary error reaching the AI service. Please try again in a moment."

                    ai_avatar = os.getenv("AI_AVATAR_URL")
                    bot_message = {
                        "id": None,
                        "room_id": room_id,
                        "user_id": -1,
                        "content": hint,
                        "timestamp": None,
                        "deleted": False,
                        "user": {
                            "first_name": "LEXA",
                            "last_name": "",
                            "email": "",
                            "avatar_url": ai_avatar if ai_avatar else None,
                        },
                    }
                    emit(
                        "private_message",
                        bot_message,
                        to=str(room_id),
                        include_self=True,
                    )
            except Exception:
                # Don't let helper message cause additional failures
                pass
