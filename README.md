# Phyrexian Engine

Generate Magic: the Gathering–style cards procedurally using ad‑libs and a local LLM.  
This repo packages the app so that *non‑technical* folks can run it with a few clicks.

## What you get

- A desktop app with simple fields for set name, code, card count, and checkboxes for themes.
- Procedural rules text based on “content packs” (templates) for each color and card type.
- Optional AI‑assisted **name**, **art prompt**, and **flavor text** via a local model (Ollama).
- Export to **JSON**, **CSV**, and **Magic Set Editor (.mse-set)**.

---

## Quick start (10 minutes)

### 1) Install Python
- Windows/macOS: [python.org/downloads](https://www.python.org/downloads/)  
  Choose Python 3.10 or newer. During install on Windows, tick **“Add Python to PATH.”**

### 2) Install Ollama (optional, for names/art/flavor)
- Download from: https://ollama.com/download
- After installing, open a terminal and run:
  ```
  ollama pull llama3
  ollama serve
  ```
  Keep that window open while using the app.  
  If you skip Ollama, the app still generates cards, just with placeholder name/art/flavor.

### 3) Get the app files
- Click the green **Code** button on GitHub, choose **Download ZIP** and unzip.
- Or, if you have Git installed:
  ```
  git clone https://github.com/your-account/phyrexian-engine.git
  cd phyrexian-engine
  ```

### 4) Install the one dependency
Open a terminal in the project folder and run:
```
python -m pip install -r requirements.txt
```

### 5) Start the app
- Windows:
  ```
  start.bat
  ```
- macOS/Linux:
  ```
  ./start.sh
  ```
  If you get a permission error on macOS/Linux, run:
  ```
  chmod +x start.sh
  ./start.sh
  ```

### 6) Generate a set
1. Type a **Set Name** and **Code** (3 letters).
2. Choose how many cards you want.
3. Pick one or more **Packages** (themes) from the list.
4. Press **Generate**.
5. Use **Export JSON/CSV/MSE** to save your set.

---

## How it works (brief)

The app plans a set skeleton (rarities, mana curve, types), then builds each card by:
- picking a color identity and mana value,
- selecting one or more **effect templates** from the chosen packages,
- filling tokens like `{TOKEN_SUBTYPE}` or `{TRIGGER_INTRO}` with strings,
- sizing P/T and adding evergreen keywords for creatures.

If Ollama is running, the app asks a local model to propose a **name**, **art prompt**, and **flavor text**.  
Finally, exporters write your set to JSON, CSV, or Magic Set Editor.

---

## Troubleshooting

- **Windows: “‘python’ is not recognized.”**  
  Reinstall Python and check “Add Python to PATH,” or try `py -m pip ...` and `py -m phyrexian_engine`.

- **macOS: “cannot import tkinter.”**  
  Install Python from python.org (not Homebrew), or install the `python-tk` package on Linux.

- **App opens but naming/flavor is blank.**  
  Ollama likely isn’t running. Start it with `ollama serve`, or just ignore this if you don’t need names/flavor.

- **Exports look weird in MSE.**  
  Make sure you open the generated `.mse-set` file with a recent Magic Set Editor and the `m15` style installed.

---

## Developer notes

- Entry point: `python -m phyrexian_engine`
- Package folders:
  - `generation/` for planning, card assembly, and template handling
  - `llm/` for the Ollama client
  - `exporters/` for JSON/CSV/MSE
  - `packages/` for content packs (you can add new ones here)

### Requirements
See `requirements.txt`. Tkinter ships with Python, but on some Linux distros you may need:
```
sudo apt-get install python3-tk
```

### License
See `LICENSE`. 

---

## Thanks
Have fun. May your rares be spicy and your commons sensible.
