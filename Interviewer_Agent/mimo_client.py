"""MIMO API helper (OpenAI-compatible)."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_API_KEY = os.environ.get("MIMO_API_KEY")
if not _API_KEY:
    raise RuntimeError("MIMO_API_KEY is not set. Add it to your .env file.")

client = OpenAI(
    api_key=_API_KEY,
    base_url="https://api.xiaomimimo.com/v1",
)


def call_mimo(system_prompt: str, user_content: str, use_web_search: bool = False) -> str:
    """Call the MIMO chat completion API, optionally with web search enabled."""
    kwargs = {
        "model": "mimo-v2.5",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_completion_tokens": 4096,
        "temperature": 1.0,
        "top_p": 0.95,
        "stream": False,
        "stop": None,
        "frequency_penalty": 0,
        "presence_penalty": 0,
    }
    if use_web_search:
        kwargs["tools"] = [
            {
                "type": "web_search",
                "max_keyword": 3,
                "force_search": True,
                "limit": 1,
            }
        ]
        kwargs["tool_choice"] = "auto"

    completion = client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content
