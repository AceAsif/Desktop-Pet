"""
Desktop Pet for Windows — v6 "Catch That Cursor"
------------------------------------------------
A director wakes up every ACTIVITY_INTERVAL and, if Doraemon is idle,
picks ONE random thing to do:

  wander        - stroll a short distance at his current level
  jump          - hop in place
  teleport      - step through the Anywhere Door to a random spot AND a
                  random height, then wander off
  play          - door DOWN to the real floor, then chase & kick the ball
  chase_cursor  - follow your mouse pointer around the screen for a bit

State files (all optional, fall back to pet.png):
  entrance.gif - the Anywhere Door animation (used for teleport & play)
  idle.gif     - standing around / sleeping
  walk.gif     - walking, chasing the ball, chasing the cursor
  jump.gif     - jumping

Requires: pip install pillow
Right-click the pet to quit. Left-click + drag to move him.
"""

# -----------------------------------------------------------------------------
# GITHUB / VERSION CONTROL REMINDER
# After editing this file, save the change to your repo so you keep a history.
# Run these from inside your Desktop-Pet folder:
#     git add desktop_pet.py
#     git commit -m "Add mouse-cursor chasing activity"
#     git push
# (One-time setup, if you haven't already:
#     git init
#     git remote add origin <your-repo-url>
#     git push -u origin main )
# -----------------------------------------------------------------------------

import tkinter as tk
import random
import sys

try:
    from PIL import Image, ImageTk, ImageSequence
except ImportError:
    print("Please run:  pip install pillow")
    sys.exit(1)

# ---------------- Settings ----------------
PET_IMAGE = "pet.png"
STATE_FILES = {
    "entrance": "entrance.gif",
    "idle": "idle.gif",
    "walk": "walk.gif",
    "jump": "jump.gif",
}
PET_SCALE = 0.25

# How often the director considers doing something new (ms).
ACTIVITY_INTERVAL_MS = 12 * 1000
# Relative chance of each activity. Bigger = more often.
ACTIVITY_WEIGHTS = {
    "wander":       4,
    "teleport":     2,
    "jump":         2,
    "play":         1,
    "chase_cursor": 2,
}

ENTRANCE_LOOPS = 1
PLAY_DURATION_MS = 20 * 1000
CURSOR_CHASE_DURATION_MS = 8 * 1000   # how long he follows the mouse
CURSOR_CHASE_STEP = 7                 # how fast he follows it (px/frame)
MOVE_STEP = 4
CHASE_STEP = 6
JUMP_HEIGHT = 60
BOB_PIXELS = 3
BOB_SPEED_MS = 400
GIF_FRAME_MS = 100
GROUND_MARGIN = 60        # how far above the taskbar the real floor sits
BALL_SIZE = 36
BALL_COLOR = "#e74c3c"
BALL_COLOR2 = "#f1c40f"
TRANSPARENT_COLOR = "#ff00fe"


def load_animation(path, scale):
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
    GRAVITY = 1.2
    BOUNCE = 0.75
    FRICTION = 0.995

    def __init__(self, master, screen_w, ground_y):
        self.screen_w = screen_w
        self.ground_y = ground_y + 20
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

        # ---- load animations ----
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
                if fallback and state != "entrance":
                    self.anims[state] = fallback
        if "idle" not in self.anims:
            print(f"Couldn't load '{PET_IMAGE}' or any state GIFs.")
            sys.exit(1)

        self.state = "idle"
        self.facing = 1
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

        # real_ground_y = true floor; ground_y = his CURRENT walking level
        # (may float high after a teleport). Play always returns to
        # real_ground_y so the ball's gravity has somewhere to land.
        self.real_ground_y = self.screen_h - self.h - GROUND_MARGIN
        self.ground_y = self.real_ground_y
        self.x = self.screen_w // 2
        self.y = self.ground_y
        self._place()

        self.label.bind("<Button-3>", lambda e: self.root.destroy())
        self.label.bind("<Button-1>", self._start_drag)
        self.label.bind("<B1-Motion>", self._on_drag)
        # handy test keys (click the pet first so it has focus):
        #   p = play, t = teleport, j = jump, c = chase cursor
        self.root.bind("<KeyPress-p>", lambda e: self._activity_play())
        self.root.bind("<KeyPress-t>", lambda e: self._activity_teleport())
        self.root.bind("<KeyPress-j>", lambda e: self._activity_jump())
        self.root.bind("<KeyPress-c>", lambda e: self._activity_chase_cursor())

        self.moving = False
        self.bob_up = True
        self.ball = None
        self.playing = False
        self.entering = False
        self.chasing_cursor = False

        self.root.after(GIF_FRAME_MS, self._animate)
        self.root.after(BOB_SPEED_MS, self._idle_bob)

        # First arrival happens where he starts (no teleport), then the
        # director takes over and runs his random life.
        if "entrance" in self.anims:
            self._play_entrance(on_finish=self._start_director,
                                 teleport=False, wander_after=False)
        else:
            self._start_director()

    # ================= director =================
    def _start_director(self):
        self.root.after(ACTIVITY_INTERVAL_MS, self._next_activity)

    def _busy(self):
        return (self.moving or self.playing or self.entering
                or self.chasing_cursor)

    def _next_activity(self):
        if not self._busy():
            choices = list(ACTIVITY_WEIGHTS.keys())
            weights = list(ACTIVITY_WEIGHTS.values())
            pick = random.choices(choices, weights=weights, k=1)[0]
            if pick == "wander":
                self._activity_wander()
            elif pick == "teleport":
                self._activity_teleport()
            elif pick == "jump":
                self._activity_jump()
            elif pick == "play":
                self._activity_play()
            elif pick == "chase_cursor":
                self._activity_chase_cursor()
        self.root.after(ACTIVITY_INTERVAL_MS, self._next_activity)

    # ---- individual activities ----
    def _activity_wander(self):
        distance = random.randint(80, 300)
        direction = random.choice([-1, 1])
        target = max(0, min(self.screen_w - self.w,
                            self.x + direction * distance))
        self._walk_to(target)

    def _activity_jump(self):
        self._do_jump_animation()

    def _activity_teleport(self):
        if "entrance" in self.anims:
            self._play_entrance(teleport=True, wander_after=True)
        else:
            self._activity_wander()

    def _activity_play(self):
        # He needs real gravity for the ball, so door DOWN to the real
        # floor first (no random height here), then start playing.
        if "entrance" in self.anims:
            self._play_entrance(on_finish=self._begin_ball,
                                 teleport=True, wander_after=False,
                                 target_y=self.real_ground_y)
        else:
            self.ground_y = self.real_ground_y
            self.y = self.ground_y
            self._place()
            self._begin_ball()

    # ================= chase the mouse cursor =================
    def _activity_chase_cursor(self):
        if self._busy():
            return
        self.chasing_cursor = True
        self._set_state("walk")
        self.root.after(CURSOR_CHASE_DURATION_MS, self._end_cursor_chase)
        self._chase_cursor_step()

    def _chase_cursor_step(self):
        if not self.chasing_cursor:
            return
        # global pointer position on screen
        cx = self.root.winfo_pointerx()
        cy = self.root.winfo_pointery()
        # aim so his centre sits just under the pointer
        target_x = cx - self.w / 2
        target_y = cy - self.h / 2
        target_x = max(0, min(self.screen_w - self.w, target_x))
        target_y = max(0, min(self.screen_h - self.h, target_y))

        dx = target_x - self.x
        dy = target_y - self.ground_y
        if abs(dx) > CURSOR_CHASE_STEP:
            self.facing = 1 if dx > 0 else -1
            self.x += CURSOR_CHASE_STEP * self.facing
        if abs(dy) > CURSOR_CHASE_STEP:
            self.ground_y += CURSOR_CHASE_STEP * (1 if dy > 0 else -1)
        self.y = self.ground_y
        self._place()
        self.root.after(20, self._chase_cursor_step)

    def _end_cursor_chase(self):
        self.chasing_cursor = False
        self._set_state("idle")

    # ================= entrance / teleport =================
    def _play_entrance(self, on_finish=None, teleport=True,
                       wander_after=True, target_x=None, target_y=None):
        if self.playing or self.entering:
            return
        self.entering = True
        self.moving = True
        if teleport:
            self.x = (target_x if target_x is not None
                      else random.randint(0, max(0, self.screen_w - self.w)))
            new_ground = (target_y if target_y is not None
                          else random.randint(0, max(0, self.screen_h - self.h - GROUND_MARGIN)))
            self.ground_y = new_ground
            self.y = new_ground
            self.facing = random.choice([-1, 1])
            self._place()
        self._set_state("entrance")
        n_frames = len(self.anims["entrance"][0])
        duration = n_frames * GIF_FRAME_MS * ENTRANCE_LOOPS
        self.root.after(duration,
                        lambda: self._finish_entrance(on_finish,
                                                      teleport and wander_after))

    def _finish_entrance(self, on_finish=None, wander_after=False):
        self.entering = False
        self.moving = False
        self._set_state("idle")
        if wander_after:
            steps = random.randint(60, 160)
            direction = self.facing
            target = self.x + direction * steps
            if target < 0 or target > self.screen_w - self.w:
                target = self.x - direction * steps
            target = max(0, min(self.screen_w - self.w, target))
            self._walk_to(target, then=on_finish)
        elif on_finish:
            on_finish()

    # ================= helpers =================
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
        self.real_ground_y = self.y   # dropping him sets a new real floor
        self._place()

    # ================= animation loop =================
    def _animate(self):
        frames = self.anims.get(self.state, self.anims["idle"])
        side = frames[0] if self.facing == 1 else frames[1]
        self.frame_index = (self.frame_index + 1) % len(side)
        self.label.config(image=side[self.frame_index])
        self.root.after(GIF_FRAME_MS, self._animate)

    def _idle_bob(self):
        if not self._busy():
            self.y = self.ground_y - (BOB_PIXELS if self.bob_up else 0)
            self.bob_up = not self.bob_up
            self._place()
        self.root.after(BOB_SPEED_MS, self._idle_bob)

    # ================= walking =================
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

    # ================= jumping =================
    def _do_jump_animation(self, then=None):
        self.moving = True
        self._set_state("jump")
        frames_up = 15
        base = self.ground_y

        def up(i=0):
            if i >= frames_up:
                down()
                return
            self.y = base - JUMP_HEIGHT * (1 - ((frames_up - i) / frames_up) ** 2)
            self._place()
            self.root.after(15, lambda: up(i + 1))

        def down(i=0):
            if i >= frames_up:
                self.y = base
                self._place()
                self.moving = False
                self._set_state("idle")
                if then:
                    then()
                return
            self.y = (base - JUMP_HEIGHT) + JUMP_HEIGHT * (i / frames_up) ** 2
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    # ================= ball play =================
    def _begin_ball(self):
        self.playing = True
        self.moving = False
        self.ground_y = self.real_ground_y      # play happens on the floor
        self.y = self.ground_y
        self._place()
        self.ball = Ball(self.root, self.screen_w,
                         self.real_ground_y + self.h - BALL_SIZE)
        self.root.after(PLAY_DURATION_MS, self._end_play)
        self._chase()

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
            if self.ball.y > self.ground_y - 60:
                self.ball.kick(1 if self.facing == 1 else -1)
                if not self.moving:
                    self._mini_hop()
        self.root.after(25, self._chase)

    def _mini_hop(self):
        self.moving = True
        base = self.ground_y

        def up(i=0):
            if i >= 6:
                down()
                return
            self.y = base - (i + 1) * 4
            self._place()
            self.root.after(15, lambda: up(i + 1))

        def down(i=0):
            if i >= 6:
                self.y = base
                self._place()
                self.moving = False
                return
            self.y = base - (6 - i) * 4
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