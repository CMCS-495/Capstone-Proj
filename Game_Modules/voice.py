import os
import uuid

try:
    from gtts import gTTS
    from gtts.lang import tts_langs
except ImportError as exc:  # pragma: no cover - gtts is an optional dependency
    gTTS = None

    def tts_langs() -> dict:
        """Return minimal language mapping when gtts is missing."""
        return {"en": "English"}

    _import_error = exc


VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Flask', 'static', 'voice')

os.makedirs(VOICE_DIR, exist_ok=True)

def generate_voice(text: str, lang: str = "en") -> str:
    """Generate speech audio for the given text.

    The audio is saved under ``static/voice`` and the relative filename is
    returned. ``gtts`` is used directly to avoid external decoding
    dependencies such as ``ffmpeg``.
    """

    if gTTS is None:  # pragma: no cover - raised only when dependency missing
        raise RuntimeError(
            "gtts package is required for speech output; install it with 'pip install gtts'"
        ) from _import_error

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(VOICE_DIR, filename)

    tts = gTTS(text=text, lang=lang)
    tts.save(path)

    return filename
