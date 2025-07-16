import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Game_Modules import llm_client

def test_generate_description(monkeypatch):
    def mock_pipeline(prompt, max_new_tokens, do_sample, temperature, top_p, num_return_sequences, return_full_text):
        return [{'generated_text': 'A short sentence.'}]
    monkeypatch.setattr(llm_client, '_get_llm_pipeline', lambda device=None: mock_pipeline)
    llm_client._LLM = None
    desc = llm_client.generate_description('gear', {'name':'Sword','stats':{}})
    assert desc == 'A short sentence.'
