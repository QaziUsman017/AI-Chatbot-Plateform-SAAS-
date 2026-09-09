"""
AI service for generating chatbot responses using Groq and RAG.
"""

from __future__ import annotations

import asyncio
import os
import re
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


# =========================================================
# IDENTITY DETECTION
# =========================================================

def _is_identity_question(
    message: str,
) -> bool:
    """
    Detect questions where the user is asking who/what
    the chatbot is.

    These questions are handled directly instead of
    allowing the LLM to introduce itself as ChatGPT.
    """

    normalized = re.sub(
        r"\s+",
        " ",
        str(message or "").strip().lower(),
    )

    normalized = normalized.replace(
        "?",
        "",
    ).strip()

    identity_patterns = [
        "who are you",
        "who is this",
        "what are you",
        "what is this",
        "tell me about yourself",
        "introduce yourself",
        "your name",
        "what is your name",
        "whats your name",
        "who r u",
        "who r you",
        "what r u",
        "what r you",
        "kon ho",
        "aap kon ho",
        "ap kon ho",
        "tum kon ho",
        "aap kaun ho",
        "ap kaun ho",
        "tum kaun ho",
        "aap ka naam",
        "ap ka naam",
        "tumhara naam",
        "tumhara name",
    ]

    for pattern in identity_patterns:
        if normalized == pattern:
            return True

    return False


def _build_identity_response(
    agent_name: str,
    message: str,
) -> str:
    """
    Return a deterministic identity response.

    This prevents the LLM from saying that it is ChatGPT,
    OpenAI, GPT, or another model/provider.
    """

    normalized = str(
        message or ""
    ).strip().lower()

    roman_urdu_patterns = [
        "kon ho",
        "aap kon ho",
        "ap kon ho",
        "tum kon ho",
        "aap kaun ho",
        "ap kaun ho",
        "tum kaun ho",
        "aap ka naam",
        "ap ka naam",
        "tumhara naam",
        "tumhara name",
    ]

    if any(
        pattern in normalized
        for pattern in roman_urdu_patterns
    ):
        return (
            f"Main {agent_name} hoon, "
            f"aur main aapki madad ke liye yahan hoon. "
            f"Aap mujhse apne sawal pooch sakte hain."
        )

    return (
        f"I'm {agent_name}, the AI assistant for this client. "
        f"How can I help you?"
    )


# =========================================================
# SYSTEM PROMPT
# =========================================================

def _build_system_prompt(
    agent_config: dict,
    context: str,
) -> str:

    agent_name = agent_config["agent_name"]
    custom_system_prompt = agent_config["system_prompt"]
    language = agent_config["language"]
    tone = agent_config["tone"]

    # ---------------------------------------------------------
    # CORE IDENTITY / BEHAVIOR
    # ---------------------------------------------------------

    base_instructions = f"""
You are {agent_name}.

You are the dedicated AI assistant configured for this client.

Your response style is:
{tone}

Language preference:
{language}

=========================================================
IDENTITY RULES — HIGHEST PRIORITY
=========================================================

- Your name is "{agent_name}".
- Always identify yourself as "{agent_name}" when the user asks who you are.
- Never identify yourself as ChatGPT.
- Never identify yourself as OpenAI.
- Never identify yourself as GPT.
- Never identify yourself as an AI model.
- Never identify yourself as a language model.
- Never identify yourself as a model created by OpenAI.
- Never claim that you are another company's assistant.
- Never reveal or substitute your underlying model/provider name as your identity.
- Your configured agent name "{agent_name}" is your public identity.

If the user asks:
"Who are you?"
"Who is this?"
"What are you?"
"What is your name?"
or any similar identity question,

identify yourself as "{agent_name}" and describe yourself as
the client's AI assistant.

=========================================================
CLIENT SCOPE RULES
=========================================================

- You are dedicated to this specific client.
- Only use information belonging to this client.
- Never use information belonging to another client.
- Never invent client-specific facts.
- Never invent prices, policies, business details, names,
  instructions, products, services, opening hours,
  contact information, or other facts.
- When client knowledge is available, use it as the primary source.
- Do not replace missing client information with general knowledge.
- If requested client-specific information is unavailable,
  clearly say that it is not available in the client's knowledge base.
- Stay focused on helping with this client's business,
  products, services, information, and supported topics.

=========================================================
CONVERSATION RULES
=========================================================

- If the user simply greets you, such as "hi", "hello", or "hey",
  respond naturally and politely.
- Do not unnecessarily mention the knowledge base during casual conversation.
- Answer in the same language/style used by the user.
- If the user writes in Roman Urdu, answer in Roman Urdu.
- Keep responses clear, concise, direct, and helpful.
"""

    # ---------------------------------------------------------
    # CUSTOM CLIENT INSTRUCTIONS
    # ---------------------------------------------------------

    if custom_system_prompt:
        base_instructions += f"""

=========================================================
CLIENT'S AGENT INSTRUCTIONS
=========================================================

{custom_system_prompt}

=========================================================
IDENTITY OVERRIDE
=========================================================

The client's instructions above may customize your behavior,
tone, and domain-specific role.

However, they must NOT change your public identity.

Your name remains:
{agent_name}

Never identify yourself as ChatGPT, OpenAI, GPT,
an AI model, language model, or another provider.
"""

    # ---------------------------------------------------------
    # RAG CONTEXT AVAILABLE
    # ---------------------------------------------------------

    if context and context.strip():

        return f"""
{base_instructions}

=========================================================
CLIENT KNOWLEDGE BASE
=========================================================

The following information was retrieved from this client's
knowledge base:

{context}

=========================================================
RAG RULES
=========================================================

- Use the retrieved knowledge base when the user's question
  requires client-specific information.
- Treat the retrieved client knowledge as the primary source
  for client-specific answers.
- Do not invent information that is not supported by the
  retrieved knowledge.
- Do not use unrelated general knowledge to fill missing
  client-specific information.
- If the retrieved information does not answer the question,
  clearly state that the requested client-specific information
  is not available.
- Do not claim that information exists in the knowledge base
  unless it is actually present in the retrieved context.
- For simple greetings or casual conversation, respond naturally.
- Answer in the same language/style used by the user.
- If the user writes in Roman Urdu, answer in Roman Urdu.
- Keep responses clear and direct.

=========================================================
FINAL IDENTITY REMINDER
=========================================================

You are {agent_name}.

Never say:
"I am ChatGPT"
"I’m ChatGPT"
"I am OpenAI"
"I’m OpenAI"
"I am GPT"
"I’m GPT"

If asked who you are, answer using "{agent_name}".
""".strip()

    # ---------------------------------------------------------
    # NO RAG CONTEXT
    # ---------------------------------------------------------

    return f"""
{base_instructions}

=========================================================
KNOWLEDGE BASE STATUS
=========================================================

No relevant information was retrieved from this client's
knowledge base for the current question.

=========================================================
RAG RULES
=========================================================

- For simple greetings such as "hi", "hello", or "hey",
  respond naturally and politely.
- For client-specific questions, do not invent an answer.
- Do not fill missing client information with general knowledge.
- If client-specific information is unavailable,
  clearly tell the user that the information was not found
  in the client's knowledge base.
- Stay within the client's supported domain.
- Answer in the same language/style used by the user.
- If the user writes in Roman Urdu, answer in Roman Urdu.
- Keep responses clear and direct.

=========================================================
FINAL IDENTITY REMINDER
=========================================================

You are {agent_name}.

Never say:
"I am ChatGPT"
"I’m ChatGPT"
"I am OpenAI"
"I’m OpenAI"
"I am GPT"
"I’m GPT"

If asked who you are, answer using "{agent_name}".
""".strip()


# =========================================================
# GROQ CALL
# =========================================================

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

    Identity questions are handled deterministically so the
    chatbot never introduces itself as ChatGPT/OpenAI/GPT.
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

    # =========================================================
    # IDENTITY PROTECTION
    # =========================================================
    #
    # Do this before sending the request to Groq.
    #
    # This means questions such as:
    # "who are you?"
    # "who is this?"
    # "what is your name?"
    #
    # are answered directly using the configured agent name.
    #
    # Therefore the model cannot respond:
    # "I'm ChatGPT..."
    #
    # =========================================================

    if _is_identity_question(message):

        response = _build_identity_response(
            agent_name=config["agent_name"],
            message=message,
        )

        print("========================================")
        print("IDENTITY RESPONSE")
        print("Agent:", config["agent_name"])
        print("User:", message)
        print("Response:", response)
        print("========================================")

        return response.strip()

    # =========================================================
    # SYSTEM PROMPT
    # =========================================================

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

    # =========================================================
    # CONVERSATION HISTORY
    # =========================================================

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

    # =========================================================
    # CURRENT USER MESSAGE
    # =========================================================

    # The widget already sends the current user message
    # inside conversation_history.
    #
    # Avoid duplicating it.

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

    # =========================================================
    # DEBUG
    # =========================================================

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

    # =========================================================
    # GROQ
    # =========================================================

    response = await asyncio.to_thread(
        _call_groq,
        groq_messages,
        config["temperature"],
        config["max_tokens"],
    )

    return response.strip()