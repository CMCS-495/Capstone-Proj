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
from voicebox.tts.tts import WavFileTTS

VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Flask', 'static', 'voice')
os.makedirs(VOICE_DIR, exist_ok=True)

VOICE_OPTIONS: Dict[str, str] = {
    'default': 'Default',
    'glados': 'GLaDOS',
}

def available_voices() -> Dict[str, str]:
    """Return mapping of selectable voice identifiers to display names."""
    return VOICE_OPTIONS


class _GTTSWavTTS(WavFileTTS):
    """Minimal TTS engine that outputs a WAV file using gTTS and ffmpeg."""

    def generate_speech_audio_file(self, text: str, audio_file_path: str) -> None:
        tmp_mp3 = f"{audio_file_path}.mp3"
        gTTS(text=text, lang='en').save(tmp_mp3)
        subprocess.run(
            ['ffmpeg', '-y', '-loglevel', 'error', '-i', tmp_mp3, audio_file_path],
            check=True,
        )
        os.remove(tmp_mp3)

def _ensure_gtts():
    if gTTS is None:  # pragma: no cover - raised only when dependency missing
        raise RuntimeError(
            "gtts package is required for speech output; install it with 'pip install gtts'"
        ) from _import_error


def _glados_voice(text: str, out_mp3: str) -> None:
    """Generate audio using the built-in GLaDOS character."""
    from voicebox.examples import glados

    wav_path = out_mp3 + '.wav'
    vb = SimpleVoicebox(
        tts=_GTTSWavTTS(),
        effects=glados.build_glados_effects(),
        sink=WaveFile(wav_path),
    )
    vb.say(text)
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', wav_path, out_mp3
    ], check=True)
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