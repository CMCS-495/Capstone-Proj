import os
import uuid
import tempfile
import shutil
import atexit

TEMP_ROOT = os.path.join(tempfile.gettempdir(), f"capstone_{uuid.uuid4().hex}")
VOICE_DIR = os.path.join(TEMP_ROOT, 'voice')
MAP_DIR = os.path.join(TEMP_ROOT, 'map')

os.makedirs(VOICE_DIR, exist_ok=True)
os.makedirs(MAP_DIR, exist_ok=True)

def _cleanup() -> None:
    shutil.rmtree(TEMP_ROOT, ignore_errors=True)

atexit.register(_cleanup)
