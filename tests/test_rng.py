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
