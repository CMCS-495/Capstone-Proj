# Capstone-Proj

A text based dungeon crawler using Qwen for dynamic descriptions for rooms, items and npc dialog

Dependencies

```
pip install flask networkx matplotlib pillow pytest voicebox-tts gtts "transformers[torch]" .[torch]

You will also need ffmpeg installed and available on your PATH for applying the
GLaDOS voice effects.

Audio narration now saves MP3 files in a temporary directory under your system
``TEMP`` folder. Map images are stored in the same location. The folder name is
generated with a random GUID and is removed automatically when the game exits.
Ensure your browser allows autoplay of audio so narration can play correctly.
