import os
import uuid
from voicebox.voiceboxes import SimpleVoicebox
from voicebox.sinks.wavefile import WaveFile

try:  # voicebox's gTTS engine depends on the gtts package
    from voicebox.tts.gtts import gTTS as VoiceboxGTTS
except ImportError as exc:
    VoiceboxGTTS = None
    _import_error = exc

VOICE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Flask', 'static', 'voice')

os.makedirs(VOICE_DIR, exist_ok=True)

def generate_voice(text: str, lang: str = 'en') -> str:
    """Generate speech audio for the given text.

    Returns the relative filename of the generated WAV file under
    ``static/voice``.
    """
    if VoiceboxGTTS is None:
        raise RuntimeError(
            "gtts package is required for speech output; install it with 'pip install gtts'"
        ) from _import_error

    filename = f"{uuid.uuid4().hex}.wav"
    path = os.path.join(VOICE_DIR, filename)
    tts_engine = VoiceboxGTTS(lang=lang)
    vb = SimpleVoicebox(tts=tts_engine, sink=WaveFile(path))
    vb.say(text)
    return filename
