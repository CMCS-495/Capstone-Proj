import os
import sys
import types
import pytest

# Provide a dummy 'transformers' module so flask_app can be imported without
# requiring heavy dependencies.
dummy = types.ModuleType('transformers')
dummy.pipeline = lambda *a, **k: (lambda *a, **k: [{'generated_text': ''}])
sys.modules.setdefault('transformers', dummy)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Flask.flask_app import app


def test_xp_awarded_on_enemy_defeat():
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['encounter'] = {'name': 'Test Enemy', 'encounter_rate': 50}
            sess['xp'] = 0
        resp = client.get('/artifact')
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess.get('xp') == 2  # int(100 / 50)
            assert 'encounter' not in sess
