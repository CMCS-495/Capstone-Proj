import os
import sys

# ensure root of project is on sys.path so Game_Modules and Flask packages import
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
