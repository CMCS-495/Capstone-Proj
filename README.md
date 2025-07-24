# Capstone-Proj

A text based dungeon crawler using Qwen for dynamic descriptions for rooms, items and npc dialog

Dependencies


pip install flask networkx matplotlib pillow pytest voicebox-tts gtts "transformers[torch]" .[torch]

You will also need ffmpeg installed for applying voice effects.

Audio narration saves MP3 files in ``Flask/static/voice``. The voice can be
changed in the game settings. Available options are "Default" and the

pip install flask networkx matplotlib pillow pytest gtts "transformers[torch]" .[torch]

Audio narration now uses ``gtts`` directly and saves MP3 files in
``Flask/static/voice``. Ensure your browser allows autoplay of audio.