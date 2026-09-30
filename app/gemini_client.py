from functools import lru_cache

from google import genai

from .config import settings


@lru_cache(maxsize=1)
def get_gemini_client():
    """
    Creates the Gemini client only when it is first needed.

    This lazy initialization allows the application homepage,
    database and tests to work without calling Gemini.
    """

    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Create a .env file and add your Gemini API key."
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )