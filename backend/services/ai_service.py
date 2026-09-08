"""
AI service for generating chatbot responses using Groq and RAG.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-20b",
).strip()


# =========================================================
# GROQ CLIENT
# =========================================================

groq_client: Groq | None = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY
    )


# =========================================================
# HELPERS
# =========================================================

def _safe_int(
    value: Any,
    default: int,
    minimum: int = 1,
) -> int:
    try:
        result = int(value)
        return max(result, minimum)
    except (TypeError, ValueError):
        return default


def _safe_float(
    value: Any,
    default: float,
    minimum: float = 0.0,
    maximum: float = 2.0,
) -> float:
    try:
        result = float(value)
        return min(
            max(result, minimum),
            maximum,
        )
    except (TypeError, ValueError):
        return default


def _build_agent_config(
    agent_config: dict | None,
) -> dict:

    config = agent_config or {}

    agent_name = str(
        config.get(
            "agent_name",
            "AI Assistant",
        )
        or "AI Assistant"
    ).strip()

    if not agent_name:
        agent_name = "AI Assistant"

    system_prompt = str(
        config.get(
            "system_prompt",
            "",
        )
        or ""
    ).strip()

    language = str(
        config.get(
            "language",
            "same_as_user",
        )
        or "same_as_user"
    ).strip()

    tone = str(
        config.get(
            "tone",
            "professional",
        )
        or "professional"
    ).strip()

    max_tokens = _safe_int(
        config.get(
            "max_tokens",
            300,
        ),
        default=300,
        minimum=1,
    )

    temperature = _safe_float(
        config.get(
            "temperature",
            0.1,
        ),
        default=0.1,
        minimum=0.0,
        maximum=2.0,
    )

    return {
        "agent_name": agent_name,
        "system_prompt": system_prompt,
        "language": language,
        "tone": tone,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }


def _clean_history(
    conversation_history: list[dict[str, str]] | None,
) -> list[dict[str, str]]:

    if not conversation_history:
        return []

    cleaned: list[dict[str, str]] = []

    for item in conversation_history:

        if not isinstance(item, dict):
            continue

        role = str(
            item.get("role", "")
        ).strip()

        content = str(
            item.get("content", "")
        ).strip()

        if role not in {
            "user",
            "assistant",
            "system",
        }:
            continue

        if not content:
            continue

        cleaned.append(
            {
                "role": role,
                "content": content,
            }
        )

    return cleaned


def _build_system_prompt(
    agent_config: dict,
    context: str,
) -> str:

    agent_name = agent_config["agent_name"]
    custom_system_prompt = agent_config["system_prompt"]
    language = agent_config["language"]
    tone = agent_config["tone"]

    base_instructions = f"""
You are {agent_name}.

Your response style is {tone}.

Language preference:
{language}

IMPORTANT:
- You are the AI assistant for this specific client.
- Never use information belonging to another client.
- Never invent client-specific facts.
- Never invent prices, policies, business details, names, instructions, or other facts.
- When client knowledge is available, use it as the primary source.
- If the requested client-specific information is not available, say so clearly.
- If the user simply greets you, such as "hi", "hello", or "hey", respond naturally and politely.
"""

    if custom_system_prompt:
        base_instructions += f"""

CLIENT'S AGENT INSTRUCTIONS:
{custom_system_prompt}
"""

    if context and context.strip():

        return f"""
{base_instructions}

The following information was retrieved from this client's
knowledge base:

KNOWLEDGE BASE:
{context}

RAG RULES:
- Use the knowledge base when the user's question requires client-specific information.
- Prefer retrieved client information over general knowledge.
- Do not invent information that is not supported by the knowledge base.
- If the user's question is a simple greeting or casual conversation,
  respond naturally instead of unnecessarily mentioning the knowledge base.
- Answer in the same language/style used by the user.
- If the user writes in Roman Urdu, answer in Roman Urdu.
- Keep responses clear and direct.
""".strip()

    return f"""
{base_instructions}

No relevant information was found in this client's knowledge base.

RAG RULES:
- For simple greetings such as "hi", "hello", or "hey",
  respond naturally and politely.
- For client-specific questions, do not invent an answer.
- If client-specific information is not available,
  clearly tell the user that the information was not found
  in the client's knowledge base.
- Answer in the same language/style used by the user.
- If the user writes in Roman Urdu, answer in Roman Urdu.
- Keep responses clear and direct.
""".strip()


def _call_groq(
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> str:

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    if groq_client is None:
        raise RuntimeError(
            "Groq client could not be initialized."
        )

    print("========================================")
    print("GROQ REQUEST")
    print("Model:", GROQ_MODEL)
    print("Temperature:", temperature)
    print("Max tokens:", max_tokens)
    print("Messages:", len(messages))
    print("========================================")

    try:

        completion = (
            groq_client
            .chat
            .completions
            .create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        )

    except Exception as error:

        print("========================================")
        print("GROQ API ERROR")
        print(type(error).__name__)
        print(str(error))
        print("========================================")

        raise RuntimeError(
            f"Groq API error: {error}"
        ) from error

    if not completion.choices:
        raise RuntimeError(
            "Groq returned no choices."
        )

    message = completion.choices[0].message

    content = getattr(
        message,
        "content",
        None,
    )

    if content is None:
        content = ""

    content = str(content).strip()

    print("========================================")
    print("GROQ RESPONSE")
    print(repr(content))
    print("========================================")

    if not content:
        raise RuntimeError(
            "Groq returned an empty response."
        )

    return content


# =========================================================
# MAIN GENERATION FUNCTION
# =========================================================

async def generate_response(
    message: str,
    conversation_history: list[dict[str, str]] | None = None,
    context: str = "",
    agent_config: dict | None = None,
) -> str:
    """
    Generate an AI response using Groq and optional RAG context.

    This function is async-friendly while using the synchronous
    Groq Python client through asyncio.to_thread().
    """

    message = str(
        message or ""
    ).strip()

    if not message:
        raise ValueError(
            "Message cannot be empty."
        )

    config = _build_agent_config(
        agent_config
    )

    history = _clean_history(
        conversation_history
    )

    system_prompt = _build_system_prompt(
        agent_config=config,
        context=context,
    )

    groq_messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": system_prompt,
        }
    ]

    # ---------------------------------------------------------
    # Conversation history
    # ---------------------------------------------------------

    for item in history:

        # Do not send duplicate system messages.
        if item["role"] == "system":
            continue

        groq_messages.append(
            {
                "role": item["role"],
                "content": item["content"],
            }
        )

    # ---------------------------------------------------------
    # Current user message
    # ---------------------------------------------------------

    # The widget already sends the current user message
    # inside conversation_history. Avoid duplicating it.
    if not (
        history
        and history[-1]["role"] == "user"
        and history[-1]["content"] == message
    ):
        groq_messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

    # ---------------------------------------------------------
    # Debug
    # ---------------------------------------------------------

    print("========================================")
    print("AGENT CONFIGURATION")
    print("Agent:", config["agent_name"])
    print("Language:", config["language"])
    print("Tone:", config["tone"])
    print("Temperature:", config["temperature"])
    print("Max Tokens:", config["max_tokens"])
    print("Model:", GROQ_MODEL)
    print("Context available:", bool(context.strip()))
    print("History messages:", len(history))
    print("========================================")

    # ---------------------------------------------------------
    # Groq is synchronous, so run it in a worker thread.
    # ---------------------------------------------------------

    response = await asyncio.to_thread(
        _call_groq,
        groq_messages,
        config["temperature"],
        config["max_tokens"],
    )

    return response.strip()