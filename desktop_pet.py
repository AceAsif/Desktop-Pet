"""
Desktop Pet for Windows — v2
----------------------------
New in this version:
- PET_SCALE setting to shrink (or enlarge) your image
- Idle "breathing" bob animation so the pet always feels alive
- Smooth resizing via Pillow (pip install pillow)
- Still supports animated GIFs (each frame gets resized too)

HOW TO USE:
1. pip install pillow
2. Put your image next to this script as "pet.png" or "pet.gif"
3. python desktop_pet.py
Right-click the pet to quit. Left-click + drag to move it.
"""

import tkinter as tk
import random
import sys

try:
    from PIL import Image, ImageTk, ImageSequence
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------------- Settings ----------------
PET_IMAGE = "pet.png"            # your character image (png or gif)
PET_SCALE = 0.25                 # 0.25 = quarter size. Try 0.15-0.4
JUMP_INTERVAL_MS = 5 * 60 * 1000 # jump every 5 minutes
WANDER_INTERVAL_MS = 4000
WANDER_CHANCE = 0.5
MOVE_STEP = 4
JUMP_HEIGHT = 60
BOB_PIXELS = 3                   # how much the idle "breathing" bob moves
BOB_SPEED_MS = 400               # bob rhythm
TRANSPARENT_COLOR = "#ff00fe"    # near-magenta key color (see note in chat)


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg=TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass

        self.frames = self._load_frames()
        if not self.frames:
            print(f"Could not load '{PET_IMAGE}'.")
            sys.exit(1)

        self.frame_index = 0
        self.label = tk.Label(self.root, image=self.frames[0],
                              bg=TRANSPARENT_COLOR, bd=0)
        self.label.pack()

        self.root.update_idletasks()
        self.w = self.frames[0].width()
        self.h = self.frames[0].height()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = self.screen_w // 2
        self.ground_y = self.screen_h - self.h - 60
        self.y = self.ground_y
        self._place()

        self.label.bind("<Button-3>", lambda e: self.root.destroy())
        self.label.bind("<Button-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._on_drag)

        self.moving = False
        self.bob_up = True

        if len(self.frames) > 1:
            self.root.after(100, self._animate_gif)
        else:
            self.root.after(BOB_SPEED_MS, self._idle_bob)
        self.root.after(WANDER_INTERVAL_MS, self._maybe_wander)
        self.root.after(JUMP_INTERVAL_MS, self._jump)

    # ---------- image loading ----------
    def _load_frames(self):
        frames = []
        if HAS_PIL:
            try:
                img = Image.open(PET_IMAGE)
                for frame in ImageSequence.Iterator(img):
                    frame = frame.convert("RGBA")
                    new_size = (max(1, int(frame.width * PET_SCALE)),
                                max(1, int(frame.height * PET_SCALE)))
                    frame = frame.resize(new_size, Image.LANCZOS)
                    # flatten true transparency onto the key color so
                    # Windows' transparentcolor trick gives clean edges
                    bg = Image.new("RGBA", frame.size, TRANSPARENT_COLOR)
                    bg.alpha_composite(frame)
                    frames.append(ImageTk.PhotoImage(bg.convert("RGB")))
            except Exception as e:
                print("Pillow load failed:", e)
        else:
            # Fallback: tk-only, integer shrink (e.g. scale 0.25 -> subsample 4)
            try:
                factor = max(1, round(1 / PET_SCALE))
                img = tk.PhotoImage(file=PET_IMAGE).subsample(factor, factor)
                frames.append(img)
            except tk.TclError:
                pass
        return frames

    # ---------- helpers ----------
    def _place(self):
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _start_drag(self, event):
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event):
        self.x = self.root.winfo_x() + event.x - self._drag_dx
        self.y = self.root.winfo_y() + event.y - self._drag_dy
        self.ground_y = self.y
        self._place()

    # ---------- animations ----------
    def _animate_gif(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.label.config(image=self.frames[self.frame_index])
        self.root.after(100, self._animate_gif)

    def _idle_bob(self):
        """Gentle up/down 'breathing' so a static PNG feels alive."""
        if not self.moving:
            self.y = self.ground_y - (BOB_PIXELS if self.bob_up else 0)
            self.bob_up = not self.bob_up
            self._place()
        self.root.after(BOB_SPEED_MS, self._idle_bob)

    # ---------- wandering ----------
    def _maybe_wander(self):
        if not self.moving and random.random() < WANDER_CHANCE:
            distance = random.randint(80, 300)
            direction = random.choice([-1, 1])
            target = max(0, min(self.screen_w - self.w,
                                self.x + direction * distance))
            self._walk_to(target)
        self.root.after(WANDER_INTERVAL_MS, self._maybe_wander)

    def _walk_to(self, target_x):
        self.moving = True

        def step():
            if abs(self.x - target_x) <= MOVE_STEP:
                self.x = target_x
                self.y = self.ground_y
                self._place()
                self.moving = False
                return
            self.x += MOVE_STEP if target_x > self.x else -MOVE_STEP
            # little hop while walking for a cartoonish waddle
            self.y = self.ground_y - (4 if (self.x // 12) % 2 == 0 else 0)
            self._place()
            self.root.after(20, step)

        step()

    # ---------- jumping every 5 minutes ----------
    def _jump(self):
        if not self.moving:
            self._do_jump_animation()
        self.root.after(JUMP_INTERVAL_MS, self._jump)

    def _do_jump_animation(self):
        self.moving = True
        frames_up = 15

        def up(i=0):
            if i >= frames_up:
                down()
                return
            self.y = self.ground_y - JUMP_HEIGHT * (1 - ((frames_up - i) / frames_up) ** 2)
            self._place()
            self.root.after(15, lambda: up(i + 1))

        def down(i=0):
            if i >= frames_up:
                self.y = self.ground_y
                self._place()
                self.moving = False
                return
            self.y = (self.ground_y - JUMP_HEIGHT) + JUMP_HEIGHT * (i / frames_up) ** 2
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()