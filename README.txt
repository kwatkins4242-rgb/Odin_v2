ODIN Wake Word Files (.ppn)
===========================

This folder holds Porcupine wake word model files (.ppn).

HOW TO GET YOUR .ppn FILES
---------------------------
1. Go to: https://console.picovoice.ai/
2. Create free account (free tier = 3 custom wake words)
3. Click "Wake Word" → "Train a new wake word"
4. Type trigger phrase (e.g. "hey odin", "yo odin")
5. Select platform: Linux / Windows / Raspberry Pi
6. Download .ppn → drop it in this folder

RECOMMENDED TRIGGERS
---------------------
  hey-odin.ppn        → "hey odin"
  yo-odin.ppn         → "yo odin"
  odin-you-there.ppn  → "odin you there"
  odin-listen.ppn     → "odin listen"
  okay-odin.ppn       → "okay odin"

GET YOUR ACCESS KEY
-------------------
Set PORCUPINE_ACCESS_KEY=your_key in .env
Get it: https://console.picovoice.ai/ → AccessKey tab
