"""
Desktop Pet for Windows — v3 "Playtime"
---------------------------------------
New in this version:
- PER-STATE ANIMATIONS: put idle.gif, walk.gif, jump.gif next to the
  script and he'll use the right animation for each action.
  Any that are missing fall back to pet.png / pet.gif automatically.
- BALL PLAY: every few minutes a ball appears. He chases it and
  kicks it around the screen for a while. (You can also press 'b'
  while the pet is focused... or just wait.)
- He flips to face the direction he's walking.
- Still: wanders, idle-bobs, and jumps every JUMP_INTERVAL.

Requires: pip install pillow

Right-click the pet to quit. Left-click + drag to move him.
"""

import tkinter as tk
import random
import sys

try:
    from PIL import Image, ImageTk, ImageSequence
except ImportError:
    print("Please run:  pip install pillow")
    sys.exit(1)

# ---------------- Settings ----------------
PET_IMAGE = "pet.png"        # fallback image if state files are missing
STATE_FILES = {              # optional per-state animations
    "idle": "idle.gif",
    "walk": "walk.gif",
    "jump": "jump.gif",
}
PET_SCALE = 0.25
JUMP_INTERVAL_MS = 5 * 60 * 1000   # solo jump every 5 minutes
PLAY_INTERVAL_MS = 3 * 60 * 1000   # ball play session every 3 minutes
PLAY_DURATION_MS = 20 * 1000       # each play session lasts ~20 seconds
WANDER_INTERVAL_MS = 4000
WANDER_CHANCE = 0.5
MOVE_STEP = 4
CHASE_STEP = 6                     # he runs faster when chasing the ball
JUMP_HEIGHT = 60
BOB_PIXELS = 3
BOB_SPEED_MS = 400
GIF_FRAME_MS = 100
BALL_SIZE = 36
BALL_COLOR = "#e74c3c"
BALL_COLOR2 = "#f1c40f"
TRANSPARENT_COLOR = "#ff00fe"


def load_animation(path, scale):
    """Load an image/GIF into (right_frames, left_frames) lists."""
    right, left = [], []
    img = Image.open(path)
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert("RGBA")
        size = (max(1, int(frame.width * scale)),
                max(1, int(frame.height * scale)))
        frame = frame.resize(size, Image.LANCZOS)
        bg = Image.new("RGBA", frame.size, TRANSPARENT_COLOR)
        bg.alpha_composite(frame)
        flat = bg.convert("RGB")
        right.append(ImageTk.PhotoImage(flat))
        left.append(ImageTk.PhotoImage(flat.transpose(Image.FLIP_LEFT_RIGHT)))
    return right, left


class Ball:
    """A bouncing ball in its own borderless window."""

    GRAVITY = 1.2
    BOUNCE = 0.75       # energy kept after hitting the ground
    FRICTION = 0.995

    def __init__(self, master, screen_w, ground_y):
        self.screen_w = screen_w
        self.ground_y = ground_y + 20  # ball rolls a bit below pet's feet
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.config(bg=TRANSPARENT_COLOR)
        try:
            self.win.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass
        c = tk.Canvas(self.win, width=BALL_SIZE, height=BALL_SIZE,
                      bg=TRANSPARENT_COLOR, highlightthickness=0)
        c.pack()
        c.create_oval(1, 1, BALL_SIZE - 1, BALL_SIZE - 1,
                      fill=BALL_COLOR, outline="")
        c.create_arc(1, 1, BALL_SIZE - 1, BALL_SIZE - 1, start=0,
                     extent=180, fill=BALL_COLOR2, outline="")
        self.x = random.randint(100, screen_w - 100)
        self.y = self.ground_y - 300
        self.vx = random.choice([-6, 6])
        self.vy = 0
        self.alive = True
        self._tick()

    def _tick(self):
        if not self.alive:
            return
        self.vy += self.GRAVITY
        self.vx *= self.FRICTION
        self.x += self.vx
        self.y += self.vy
        if self.y >= self.ground_y:
            self.y = self.ground_y
            self.vy = -abs(self.vy) * self.BOUNCE
            if abs(self.vy) < 2:
                self.vy = 0
        if self.x <= 0 or self.x >= self.screen_w - BALL_SIZE:
            self.vx = -self.vx
            self.x = max(0, min(self.screen_w - BALL_SIZE, self.x))
        self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.win.after(20, self._tick)

    def kick(self, direction):
        self.vx = direction * random.uniform(8, 14)
        self.vy = -random.uniform(10, 16)

    def destroy(self):
        self.alive = False
        self.win.destroy()


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

        # Load animations: each state -> (right_frames, left_frames)
        self.anims = {}
        fallback = None
        try:
            fallback = load_animation(PET_IMAGE, PET_SCALE)
        except Exception:
            pass
        for state, fname in STATE_FILES.items():
            try:
                self.anims[state] = load_animation(fname, PET_SCALE)
            except Exception:
                if fallback:
                    self.anims[state] = fallback
        if not self.anims:
            print(f"Couldn't load '{PET_IMAGE}' or any state GIFs.")
            sys.exit(1)

        self.state = "idle"
        self.facing = 1          # 1 = right, -1 = left
        self.frame_index = 0

        first = self.anims["idle"][0][0]
        self.label = tk.Label(self.root, image=first,
                              bg=TRANSPARENT_COLOR, bd=0)
        self.label.pack()

        self.root.update_idletasks()
        self.w = first.width()
        self.h = first.height()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.x = self.screen_w // 2
        self.ground_y = self.screen_h - self.h - 60
        self.y = self.ground_y
        self._place()

        self.label.bind("<Button-3>", lambda e: self.root.destroy())
        self.label.bind("<Button-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._on_drag)
        self.root.bind("<KeyPress-b>", lambda e: self._start_play())

        self.moving = False
        self.bob_up = True
        self.ball = None
        self.playing = False

        self.root.after(GIF_FRAME_MS, self._animate)
        self.root.after(BOB_SPEED_MS, self._idle_bob)
        self.root.after(WANDER_INTERVAL_MS, self._maybe_wander)
        self.root.after(JUMP_INTERVAL_MS, self._jump)
        self.root.after(PLAY_INTERVAL_MS, self._start_play)

    # ---------- helpers ----------
    def _place(self):
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _set_state(self, state):
        if state in self.anims and state != self.state:
            self.state = state
            self.frame_index = 0

    def _start_drag(self, event):
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event):
        self.x = self.root.winfo_x() + event.x - self._drag_dx
        self.y = self.root.winfo_y() + event.y - self._drag_dy
        self.ground_y = self.y
        self._place()

    # ---------- animation loop ----------
    def _animate(self):
        frames = self.anims.get(self.state, next(iter(self.anims.values())))
        side = frames[0] if self.facing == 1 else frames[1]
        self.frame_index = (self.frame_index + 1) % len(side)
        self.label.config(image=side[self.frame_index])
        self.root.after(GIF_FRAME_MS, self._animate)

    def _idle_bob(self):
        if not self.moving and not self.playing:
            self.y = self.ground_y - (BOB_PIXELS if self.bob_up else 0)
            self.bob_up = not self.bob_up
            self._place()
        self.root.after(BOB_SPEED_MS, self._idle_bob)

    # ---------- wandering ----------
    def _maybe_wander(self):
        if not self.moving and not self.playing and random.random() < WANDER_CHANCE:
            distance = random.randint(80, 300)
            direction = random.choice([-1, 1])
            target = max(0, min(self.screen_w - self.w,
                                self.x + direction * distance))
            self._walk_to(target)
        self.root.after(WANDER_INTERVAL_MS, self._maybe_wander)

    def _walk_to(self, target_x, then=None, speed=MOVE_STEP):
        self.moving = True
        self._set_state("walk")

        def step():
            if abs(self.x - target_x) <= speed:
                self.x = target_x
                self.y = self.ground_y
                self._place()
                self.moving = False
                self._set_state("idle")
                if then:
                    then()
                return
            self.facing = 1 if target_x > self.x else -1
            self.x += speed * self.facing
            self.y = self.ground_y - (4 if (self.x // 12) % 2 == 0 else 0)
            self._place()
            self.root.after(20, step)

        step()

    # ---------- jumping ----------
    def _jump(self):
        if not self.moving and not self.playing:
            self._do_jump_animation()
        self.root.after(JUMP_INTERVAL_MS, self._jump)

    def _do_jump_animation(self, then=None):
        self.moving = True
        self._set_state("jump")
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
                self._set_state("idle")
                if then:
                    then()
                return
            self.y = (self.ground_y - JUMP_HEIGHT) + JUMP_HEIGHT * (i / frames_up) ** 2
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    # ---------- ball play ----------
    def _start_play(self, *_):
        if self.playing:
            return
        self.playing = True
        self.moving = False
        self.ball = Ball(self.root, self.screen_w, self.ground_y + self.h - BALL_SIZE)
        self.root.after(PLAY_DURATION_MS, self._end_play)
        self._chase()
        # schedule the next session
        self.root.after(PLAY_INTERVAL_MS, self._start_play)

    def _chase(self):
        if not self.playing or not self.ball or not self.ball.alive:
            return
        ball_cx = self.ball.x + BALL_SIZE / 2
        pet_cx = self.x + self.w / 2
        gap = ball_cx - pet_cx
        self._set_state("walk")
        if abs(gap) > self.w * 0.4:
            self.facing = 1 if gap > 0 else -1
            self.x += CHASE_STEP * self.facing
            self.x = max(0, min(self.screen_w - self.w, self.x))
            self.y = self.ground_y - (4 if (self.x // 12) % 2 == 0 else 0)
            self._place()
        else:
            # close enough — KICK! (only if ball is near the ground)
            if self.ball.y > self.ground_y - 60:
                self.ball.kick(1 if self.facing == 1 else -1)
                # happy little hop after a kick
                if not self.moving:
                    self._mini_hop()
        self.root.after(25, self._chase)

    def _mini_hop(self):
        self.moving = True

        def up(i=0):
            if i >= 6:
                down()
                return
            self.y -= 4
            self._place()
            self.root.after(15, lambda: up(i + 1))

        def down(i=0):
            if i >= 6:
                self.y = self.ground_y
                self._place()
                self.moving = False
                return
            self.y += 4
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    def _end_play(self):
        self.playing = False
        self._set_state("idle")
        if self.ball:
            self.ball.destroy()
            self.ball = None

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    DesktopPet().run()