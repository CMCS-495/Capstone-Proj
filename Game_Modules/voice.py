import os
import uuid

import subprocess
from typing import Dict

try:
    from gtts import gTTS
except ImportError as exc:  # pragma: no cover - gtts is optional
    gTTS = None
    _import_error = exc

from voicebox.voiceboxes import SimpleVoicebox
from voicebox.sinks.wavefile import WaveFile

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

VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Flask', 'static', 'voice')
os.makedirs(VOICE_DIR, exist_ok=True)

VOICE_OPTIONS: Dict[str, str] = {
    'default': 'Default',
    'glados': 'GLaDOS',
}

def available_voices() -> Dict[str, str]:
    """Return mapping of selectable voice identifiers to display names."""
    return VOICE_OPTIONS

def _ensure_gtts():

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

def _glados_voice(text: str, out_mp3: str) -> None:
    """Generate audio using the built-in GLaDOS character."""
    from voicebox.examples import glados

    wav_path = out_mp3 + '.wav'
    vb = SimpleVoicebox(
        tts=glados.build_glados_tts(),
        effects=glados.build_glados_effects(),
        sink=WaveFile(wav_path),
    )
    vb.say(text)
    try:
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav_path, out_mp3], check=True)
    except FileNotFoundError:
        raise RuntimeError(
            "ffmpeg is required for audio processing but was not found. "
            "Please install ffmpeg and ensure it is available in your system's PATH."
        )
    os.remove(wav_path)


def generate_voice(text: str, voice: str = 'default') -> str:
    """Generate speech audio for the given text using the selected voice."""
    _ensure_gtts()

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(VOICE_DIR, filename)

    if voice.lower() == next(key for key in VOICE_OPTIONS if key.lower() == 'glados'):
        _glados_voice(text, path)
    else:
        tts = gTTS(text=text)
        tts.save(path)

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(VOICE_DIR, filename)

    tts = gTTS(text=text, lang=lang)
    tts.save(path)

    return filename
