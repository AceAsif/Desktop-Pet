# 🐱 Doraemon Desktop Pet

A small animated Doraemon that lives on your Windows desktop. He sits there, wanders around, jumps, steps through the Anywhere Door to teleport across your screen, plays with a bouncing ball, and chases your mouse cursor — all on his own, chosen at random.

Built in Python with `tkinter` and `Pillow`. No game engine, no heavy frameworks.

> **Note on artwork:** Doraemon is a copyrighted character owned by Fujiko F. Fujio / Shogakukan / TV Asahi. The character GIFs are **not** included in this repository. This project is a personal, non-commercial hobby project — please supply your own image files (see [Adding Your Character](#-adding-your-character)).

---

## ✨ Features

- **Always-on-top, transparent window** — he sits on top of your desktop with no border or background box.
- **Activity director** — every few seconds he randomly picks one thing to do, so his behaviour never feels scripted.
- **Anywhere Door teleport** — he disappears and reappears somewhere new (sometimes floating up high), then wanders off.
- **Ball play with real physics** — a ball drops with gravity, bounces, and he chases and kicks it around on the floor.
- **Cursor chasing** — he follows your mouse pointer around the screen.
- **Per-state animations** — separate GIFs for idle, walking, jumping, and the door entrance.
- **Direction flipping** — he faces whichever way he's moving.
- **Draggable** — pick him up and drop him anywhere.

---

## 🎮 Controls

| Action | What it does |
| --- | --- |
| **Left-click + drag** | Pick him up and move him |
| **Right-click** | Close / quit the pet |
| **Key `c`** | Chase the mouse cursor now |
| **Key `p`** | Play with the ball now |
| **Key `t`** | Teleport (Anywhere Door) now |
| **Key `j`** | Jump now |

> The keyboard keys only work while the pet window has focus — **left-click Doraemon first**, then press the key.

---

## 📦 Requirements

- Windows (the transparent-window trick is Windows-only)
- [Python 3](https://www.python.org/) (tick **"Add Python to PATH"** during install)
- [Pillow](https://pypi.org/project/Pillow/) — the only external library

Install Pillow with:

```bash
pip install pillow
```

---

## 🚀 Setup & Running

1. **Clone the repo** (or download it as a ZIP):

   ```bash
   git clone <your-repo-url>
   cd Desktop-Pet
   ```

2. **Install the dependency:**

   ```bash
   pip install pillow
   ```

3. **Add your character images** to the same folder (see below).

4. **Run it:**

   ```bash
   python desktop_pet.py
   ```

### Run it without a console window

Rename `desktop_pet.py` to `desktop_pet.pyw` and double-click it — it runs silently, no command prompt. Right-click the file and **Send to → Desktop (create shortcut)** for a one-click launcher.

### Launch automatically at startup

Press `Win + R`, type `shell:startup`, press Enter, and drop a shortcut to the `.pyw` file into the folder that opens. Doraemon will greet you every time Windows boots.

---

## 🖼️ Adding Your Character

The script looks for these files in its own folder. All are optional except a fallback `pet.png` (or `idle.gif`):

| File | When it plays |
| --- | --- |
| `idle.gif` | Standing around / sleeping |
| `walk.gif` | Walking, chasing the ball, chasing the cursor |
| `jump.gif` | Jumping |
| `entrance.gif` | The Anywhere Door (teleport & start of play) |
| `pet.png` | Fallback used for any of the above that's missing |

**Tips for good-looking sprites:**

- Use GIFs or PNGs with **transparent backgrounds**. If a background needs removing, a flood-fill from the edges works well (so the white *inside* the character is kept).
- Keep all states a **similar height** so he doesn't change size when switching actions.
- Cartoon art with flat colours scales nicely; you can upscale small GIFs to keep them crisp at your chosen display size.

---

## ⚙️ Customization

All the knobs live in the **SETTINGS** section at the top of the script:

| Setting | Effect |
| --- | --- |
| `PET_SCALE` | Display size (e.g. `0.25` = quarter size; raise for bigger) |
| `ACTIVITY_INTERVAL_MS` | How often he picks a new activity |
| `ACTIVITY_WEIGHTS` | Relative chance of each activity (bigger = more often) |
| `PLAY_DURATION_MS` | How long a ball-play session lasts |
| `CURSOR_CHASE_DURATION_MS` | How long he follows your mouse |
| `JUMP_HEIGHT` | How high he jumps |
| `GROUND_MARGIN` | Gap kept above the taskbar (his "floor") |

For example, to make him play with the ball more often, raise `"play"` in `ACTIVITY_WEIGHTS`.

---

## 🛠️ Building a Standalone `.exe` (optional)

To share the pet with someone who doesn't have Python, bundle it with [PyInstaller](https://pyinstaller.org/):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name Doraemon desktop_pet.py
```

The executable appears in a new `dist/` folder. Keep your image files next to `Doraemon.exe` so it can find them.

---

## 📁 Project Structure

```
Desktop-Pet/
├── desktop_pet.py     # the main script
├── pet.png            # fallback image (your own art)
├── idle.gif           # your own art
├── walk.gif           # your own art
├── jump.gif           # your own art
├── entrance.gif       # your own art
└── README.md
```

---

## 📜 License

This code is released under the MIT License — feel free to use and modify it.

The MIT License covers **the code only**. It does **not** cover any Doraemon artwork, which remains the property of its respective copyright holders. Do not redistribute character images with this project.

---

## 🙌 Acknowledgements

- Built with [Python](https://www.python.org/), [tkinter](https://docs.python.org/3/library/tkinter.html), and [Pillow](https://python-pillow.org/).
- Inspired by classic desktop mascots like Shimeji.
