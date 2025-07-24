import os
import uuid
import subprocess
import shutil
from typing import Dict

from . import temp_utils

try:
    from gtts import gTTS
except ImportError as exc:  # pragma: no cover - gtts is optional
    gTTS = None
    _import_error = exc

from voicebox.voiceboxes import SimpleVoicebox
from voicebox.sinks.wavefile import WaveFile
from voicebox.tts.tts import WavFileTTS

VOICE_DIR = temp_utils.VOICE_DIR

VOICE_OPTIONS: Dict[str, str] = {
    'default': 'Default',
    'glados': 'GLaDOS',
}

def available_voices() -> Dict[str, str]:
    """Return mapping of selectable voice identifiers to display names."""
    return VOICE_OPTIONS


class _GTTSWavTTS(WavFileTTS):
    """Minimal TTS engine that outputs a WAV file using gTTS and ffmpeg."""

    def __init__(self) -> None:
        super().__init__(None, "gtts_")

    def generate_speech_audio_file(self, text: str, audio_file_path: str) -> None:
        tmp_mp3 = f"{audio_file_path}.mp3"
        gTTS(text=text, lang='en').save(tmp_mp3)
        _run_ffmpeg(['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp_mp3, audio_file_path])
        os.remove(tmp_mp3)

def _ensure_gtts():
    if gTTS is None:  # pragma: no cover - raised only when dependency missing
        raise RuntimeError(
            "gtts package is required for speech output; install it with 'pip install gtts'"
        ) from _import_error


def _run_ffmpeg(cmd: list[str]) -> None:
    """Run ffmpeg with better error reporting."""
    if shutil.which('ffmpeg') is None:
        raise RuntimeError(
            "ffmpeg executable not found. Please install ffmpeg and ensure it is available in your PATH."
        )
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError as exc:  # pragma: no cover - should not happen if which succeeded
        raise RuntimeError(
            "ffmpeg executable not found. Please install ffmpeg and ensure it is available in your PATH."
        ) from exc


def _glados_voice(text: str, out_mp3: str) -> None:
    """Generate audio using the built-in GLaDOS character."""
    from voicebox.examples import glados

    wav_path = f'{out_mp3}.wav'
    vb = SimpleVoicebox(
        tts=_GTTSWavTTS(),
        effects=glados.build_glados_effects(),
        sink=WaveFile(wav_path),
    )
    vb.say(text)
    _run_ffmpeg([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', wav_path, out_mp3
    ])
    os.remove(wav_path)


def generate_voice(text: str, voice: str = 'default') -> str:
    """Generate speech audio for the given text using the selected voice."""
    _ensure_gtts()

    filename = f"{uuid.uuid4().hex}.mp3"
    path = os.path.join(VOICE_DIR, filename)

    if voice.lower() == 'glados':
        _glados_voice(text, path)
    else:
        tts = gTTS(text=text)
        tts.save(path)

    return filename
