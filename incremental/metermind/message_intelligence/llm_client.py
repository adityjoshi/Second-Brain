import hashlib
import json
import os
import time
from pathlib import Path

from config import constants

API_KEY_ENVIRONMENT_NAME = "GEMINI_API_KEY"
MODEL_NAME_ENVIRONMENT_NAME = "GEMINI_MODEL"
QUOTED_ANSWER_CHARACTERS = 120


class LanguageModelError(Exception):
    pass


class ModelNotConfigured(LanguageModelError):
    pass


def _read_environment_file():
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv(usecwd=True))


# Read once on import too, so anything reading os.environ sees the same model name ask_model does.
_read_environment_file()


def _configured_model_name():
    _read_environment_file()
    chosen = os.environ.get(MODEL_NAME_ENVIRONMENT_NAME, "").strip()
    return chosen or constants.DEFAULT_LANGUAGE_MODEL


def load_settings():
    _read_environment_file()
    api_key = os.environ.get(API_KEY_ENVIRONMENT_NAME, "").strip()
    if not api_key:
        raise ModelNotConfigured(
            f"{API_KEY_ENVIRONMENT_NAME} is not set; put "
            f"{API_KEY_ENVIRONMENT_NAME}=<your key> in the .env file at the project root"
        )
    return {"api_key": api_key, "model_name": _configured_model_name()}


def cache_key(model_name, prompt):
    joined = json.dumps([str(model_name), str(prompt)], ensure_ascii=False)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def read_cache(cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    path = Path(cache_path)
    if not path.is_file():
        return {}
    try:
        cache = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LanguageModelError(f"the cache at {path} cannot be read: {error}") from error
    if not isinstance(cache, dict):
        raise LanguageModelError(f"the cache at {path} does not hold a dictionary")
    return cache


def write_cache(cache, cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def open_model_client(api_key):
    from google import genai

    return genai.Client(api_key=api_key)


def ask_model(prompt, cache_path=constants.LANGUAGE_MODEL_CACHE_PATH):
    model_name = _configured_model_name()
    key = cache_key(model_name, prompt)
    cache = read_cache(cache_path)
    if key in cache:
        return cache[key]

    settings = load_settings()
    try:
        # Held in a name for the whole call; a client used inline can be collected mid-call.
        client = open_model_client(settings["api_key"])
        response = client.models.generate_content(
            model=settings["model_name"], contents=prompt
        )
        answer = response.text
    except LanguageModelError:
        raise
    except Exception as error:
        raise LanguageModelError(
            f"the model {settings['model_name']} could not be asked: {error}"
        ) from error
    if answer is None or not str(answer).strip():
        raise LanguageModelError(f"the model {settings['model_name']} answered with nothing")

    cache[key] = str(answer)
    write_cache(cache, cache_path)
    return cache[key]


def ask_model_with_retry(prompt, cache_path=constants.LANGUAGE_MODEL_CACHE_PATH,
                         attempts=constants.MODEL_RETRY_ATTEMPTS,
                         pause_seconds=constants.MODEL_RETRY_SECONDS, waits=None):
    if attempts < 1:
        attempts = 1
    for attempt in range(attempts):
        try:
            return ask_model(prompt, cache_path)
        except ModelNotConfigured:
            raise
        except LanguageModelError:
            if attempt + 1 >= attempts:
                raise
            wait = pause_seconds * (2 ** attempt)
            if waits is not None:
                waits.append(wait)
            else:
                time.sleep(wait)


def read_answer(said, wanted_keys):
    text = str(said)
    opening = text.find("{")
    closing = text.rfind("}")
    if opening < 0 or closing <= opening:
        raise LanguageModelError(
            f"the answer carries no JSON object: {text[:QUOTED_ANSWER_CHARACTERS]!r}"
        )
    try:
        answer = json.loads(text[opening : closing + 1])
    except ValueError as error:
        raise LanguageModelError(f"the answer is not readable as JSON: {error}") from error
    if not isinstance(answer, dict):
        raise LanguageModelError("the answer is not a JSON object")
    missing = [key for key in wanted_keys if key not in answer]
    if missing:
        raise LanguageModelError(f"the answer is missing {', '.join(missing)}")
    return answer


if __name__ == "__main__":
    print(f"cache holds: {len(read_cache())} answers")
