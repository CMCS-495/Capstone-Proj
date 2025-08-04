# Capstone-Proj

A text-based Dungeon Crawler using Qwen for dynamic descriptions for rooms, items and npc dialog

**🚀 How to Play**
Explore rooms across 3 Regions (🌲 Forest, 🏚️ Cabin, 🌊 River Cave)
Fight enemies and earn gear.
Equip gear items to boost stats.
Your progress is tracked per room.
Rooms that have a 💀 skull symbol next to their name mean you've already defeated the enemy there.
Once all rooms are cleared, the game is won.

**Room Names**
--🌲 Forest: Twisted Oak Clearing, Skeletal Birch Path, Whispering Shadow Grove, Firefly Moss Glade, Vine-Overgrown Stone Circle--
--🏚️ Cabin: Creaking Cabin Porch, Broken Rocking Chair Room, Rusty Cobweb Kitchen, Decaying Barrel Cellar, Tattered Curtains Attic--
--🌊 River Cave: Misty Pool Waterfall, Slippery River Ledge, Wet Stone Cave Entrance, Calm River Alcove, River Cave Echo Chamber--

**⚔️ Gear Types**
You can find and equip:
--Weapons: Rusty Sword, Iron Dagger, Magic Staff--
--Armor: Leather Armor, Iron Armor, Robes of Light--
--Boots: Traveler’s Boots, Heavy Boots, Silent Slippers--
--Helmets: Iron Helmet, Hood of Insight, Bone Crown--
--Rings: Ring of Strength, Ring of Defense, Ring of Swiftness--
--Shields: Wooden Shield, Iron Buckler, Dragon Scale Shield--
--Potions: Health Potion, Big Potion, Mountain Dew--


Dependencies

```
pip install flask networkx matplotlib pillow pytest voicebox-tts gtts "transformers[torch]" .[torch]

You will also need ffmpeg installed and available on your PATH for applying the
GLaDOS voice effects.

Audio narration now saves MP3 files in a temporary directory under your system
``TEMP`` folder. Map images are stored in the same location. The folder name is
generated with a random GUID and is removed automatically when the game exits.
Ensure your browser allows autoplay of audio so narration can play correctly.
