import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import io
import sys
from unittest.mock import patch
from Game_Modules import rng

def test_rng_main_outputs_number():
    with patch('random.randint', return_value=7):
        buf = io.StringIO()
        _stdout = sys.stdout
        sys.stdout = buf
        try:
            sys.argv = ['rng.py', '1', '10']
            rng.main()
        finally:
            sys.stdout = _stdout
        assert buf.getvalue().strip() == '7'
