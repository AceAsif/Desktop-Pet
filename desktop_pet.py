"""
Desktop Pet for Windows
-----------------------
A small always-on-top character that sits on your desktop, wanders
around occasionally, and does a jump every 5 minutes.

HOW TO USE:
1. Install Python 3 (python.org) if you don't have it.
2. Put your character image in the same folder as this script and
   name it "pet.png" (a PNG with a transparent background works best),
   or change PET_IMAGE below. An animated GIF also works ("pet.gif").
3. Run:  python desktop_pet.py
4. Right-click the pet to close it. Left-click and drag to move it.

Tested with the standard library only — no extra packages required
for PNG/GIF. (For best PNG transparency, see the TRANSPARENT_COLOR
note below.)
"""

import tkinter as tk
import random
import sys

# ---------------- Settings ----------------
PET_IMAGE = "pet.png"        # your character image (png or gif)
JUMP_INTERVAL_MS = 5 * 60 * 1000   # jump every 5 minutes
WANDER_INTERVAL_MS = 4000    # consider wandering every 4 seconds
WANDER_CHANCE = 0.5          # 50% chance to wander each interval
MOVE_STEP = 4                # pixels per animation frame while walking
JUMP_HEIGHT = 60             # pixels
TRANSPARENT_COLOR = "#ff00ff"  # magenta; any pixel of this color becomes see-through


class DesktopPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)          # no title bar / border
        self.root.attributes("-topmost", True)    # always on top
        # Windows-only trick: make one color fully transparent
        self.root.config(bg=TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass  # non-Windows platforms

        # Load image (supports GIF animation frames if present)
        self.frames = []
        try:
            if PET_IMAGE.lower().endswith(".gif"):
                i = 0
                while True:
                    try:
                        frame = tk.PhotoImage(file=PET_IMAGE,
                                              format=f"gif -index {i}")
                        self.frames.append(frame)
                        i += 1
                    except tk.TclError:
                        break
            else:
                self.frames = [tk.PhotoImage(file=PET_IMAGE)]
        except tk.TclError:
            print(f"Could not load '{PET_IMAGE}'. Put your image next to "
                  f"this script or update PET_IMAGE at the top.")
            sys.exit(1)

        self.frame_index = 0
        self.label = tk.Label(self.root, image=self.frames[0],
                              bg=TRANSPARENT_COLOR, bd=0)
        self.label.pack()

        # Position: bottom-ish of the screen
        self.root.update_idletasks()
        self.w = self.frames[0].width()
        self.h = self.frames[0].height()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = self.screen_w // 2
        self.ground_y = self.screen_h - self.h - 60  # sit above the taskbar
        self.y = self.ground_y
        self._place()

        # Interactions
        self.label.bind("<Button-3>", lambda e: self.root.destroy())  # right-click quits
        self.label.bind("<Button-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._on_drag)

        self.moving = False

        # Timers
        if len(self.frames) > 1:
            self.root.after(100, self._animate_gif)
        self.root.after(WANDER_INTERVAL_MS, self._maybe_wander)
        self.root.after(JUMP_INTERVAL_MS, self._jump)

    # ---------- helpers ----------
    def _place(self):
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _start_drag(self, event):
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event):
        self.x = self.root.winfo_x() + event.x - self._drag_dx
        self.y = self.root.winfo_y() + event.y - self._drag_dy
        self.ground_y = self.y  # new resting height where you drop it
        self._place()

    def _animate_gif(self):
        self.frame_index = (self.frame_index + 1) % len(self.frames)
        self.label.config(image=self.frames[self.frame_index])
        self.root.after(100, self._animate_gif)

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
                self._place()
                self.moving = False
                return
            self.x += MOVE_STEP if target_x > self.x else -MOVE_STEP
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
            # ease-out rise
            self.y = self.ground_y - JUMP_HEIGHT * (1 - ((frames_up - i) / frames_up) ** 2)
            self._place()
            self.root.after(15, lambda: up(i + 1))

        def down(i=0):
            if i >= frames_up:
                self.y = self.ground_y
                self._place()
                self.moving = False
                return
            # ease-in fall
            self.y = (self.ground_y - JUMP_HEIGHT) + JUMP_HEIGHT * (i / frames_up) ** 2
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()