"""
===============================================================================
  DESKTOP PET FOR WINDOWS  —  v7  ("Documented Edition")
===============================================================================
  An animated Doraemon that lives on your desktop: he sits there, wanders,
  jumps, teleports through the Anywhere Door, plays with a bouncing ball, and
  chases your mouse cursor — all chosen at random by an "activity director".

-------------------------------------------------------------------------------
  CONTROLS
-------------------------------------------------------------------------------
  LEFT-CLICK + DRAG ...... pick him up and move him anywhere
  RIGHT-CLICK ............ close / quit the pet
  KEY  c ................. make him chase your mouse cursor now
  KEY  p ................. make him play with the ball now
  KEY  t ................. make him teleport (Anywhere Door) now
  KEY  j ................. make him jump now

  NOTE: the keyboard keys only work while the pet window has focus, so
        LEFT-CLICK on Doraemon first, then press the key.

-------------------------------------------------------------------------------
  SETUP
-------------------------------------------------------------------------------
  1.  Install Pillow (one time):      pip install pillow
  2.  Put these image files in the SAME folder as this script:
          entrance.gif  - the Anywhere Door animation (teleport & play)
          idle.gif      - standing around / sleeping
          walk.gif      - walking / chasing the ball / chasing the cursor
          jump.gif      - jumping
      Any missing file simply falls back to "pet.png", so you can add them
      one at a time. Only "idle" (or pet.png) is strictly required.
  3.  Run it:                         python desktop_pet.py

-------------------------------------------------------------------------------
  GITHUB / VERSION CONTROL REMINDER
-------------------------------------------------------------------------------
  After editing this file, save the change to your repo to keep a history.
  Run these from inside your Desktop-Pet folder:
      git add desktop_pet.py
      git commit -m "Describe what you changed here"
      git push
  (One-time setup, if you haven't already:
      git init
      git remote add origin <your-repo-url>
      git push -u origin main )
===============================================================================
"""

import tkinter as tk   # built-in GUI toolkit — gives us windows, labels, timers
import random          # for picking random activities, positions, directions
import sys             # used to exit cleanly if images can't be loaded

# Pillow (PIL) handles image loading, resizing and transparency. It is the one
# external library we need; everything else is part of standard Python.
try:
    from PIL import Image, ImageTk, ImageSequence
except ImportError:
    print("Please run:  pip install pillow")
    sys.exit(1)


# =============================================================================
#  SETTINGS  —  tweak these numbers to change how the pet behaves
# =============================================================================

PET_IMAGE = "pet.png"          # fallback image used if a state GIF is missing

# Maps each "state" (what he's doing) to its animation file.
STATE_FILES = {
    "entrance": "entrance.gif",
    "idle": "idle.gif",
    "walk": "walk.gif",
    "jump": "jump.gif",
}

PET_SCALE = 0.25               # 0.25 = quarter size. Raise for a bigger pet.

# The "director" wakes up this often (in milliseconds) and, if the pet is
# free, picks one random thing for him to do. 12 * 1000 ms = 12 seconds.
ACTIVITY_INTERVAL_MS = 12 * 1000

# Relative chance of each activity being chosen. Bigger number = more often.
# (These are weights, not percentages — they don't need to add up to 100.)
ACTIVITY_WEIGHTS = {
    "wander":       4,
    "teleport":     2,
    "jump":         2,
    "play":         1,
    "chase_cursor": 2,
}

ENTRANCE_LOOPS = 1                    # times the door animation plays per use
PLAY_DURATION_MS = 20 * 1000          # how long a ball-play session lasts
CURSOR_CHASE_DURATION_MS = 8 * 1000   # how long he follows the mouse
CURSOR_CHASE_STEP = 7                 # how fast he follows the mouse (px/frame)
MOVE_STEP = 4                         # walking speed (pixels per frame)
CHASE_STEP = 6                        # running speed while chasing the ball
JUMP_HEIGHT = 60                      # how high a jump goes (pixels)
BOB_PIXELS = 3                        # size of the idle "breathing" bob
BOB_SPEED_MS = 400                    # rhythm of the idle bob
GIF_FRAME_MS = 100                    # delay between animation frames
GROUND_MARGIN = 60                    # gap kept above the taskbar (the "floor")

# The bouncing ball's appearance.
BALL_SIZE = 36
BALL_COLOR = "#e74c3c"                # main (red) colour
BALL_COLOR2 = "#f1c40f"               # top stripe (yellow) colour

# Windows trick: any pixel of this exact colour is rendered fully see-through.
# We use a near-magenta that won't clash with Doraemon's blue/red/white.
TRANSPARENT_COLOR = "#ff00fe"


def load_animation(path, scale):
    """Load an image or GIF and return two lists of frames:
    (frames_facing_right, frames_facing_left).

    Each frame is resized by `scale`, has its transparency flattened onto the
    magenta key colour (so Windows can punch it out cleanly), and the "left"
    version is just a horizontal mirror so the pet can face either way.
    """
    right, left = [], []
    img = Image.open(path)
    # ImageSequence.Iterator walks every frame of a GIF (or the single frame
    # of a PNG), so this works for both static images and animations.
    for frame in ImageSequence.Iterator(img):
        frame = frame.convert("RGBA")                 # ensure an alpha channel
        size = (max(1, int(frame.width * scale)),
                max(1, int(frame.height * scale)))
        frame = frame.resize(size, Image.LANCZOS)     # smooth, high-quality resize
        # Paste the frame over a solid magenta background. Transparent areas
        # become magenta, which Windows then renders as see-through.
        bg = Image.new("RGBA", frame.size, TRANSPARENT_COLOR)
        bg.alpha_composite(frame)
        flat = bg.convert("RGB")
        right.append(ImageTk.PhotoImage(flat))
        left.append(ImageTk.PhotoImage(flat.transpose(Image.FLIP_LEFT_RIGHT)))
    return right, left


# =============================================================================
#  BALL  —  a separate little window holding a ball that bounces with gravity
# =============================================================================
class Ball:
    GRAVITY = 1.2        # downward pull added to vertical speed each frame
    BOUNCE = 0.75        # fraction of speed kept after hitting the ground
    FRICTION = 0.995     # slight horizontal slowdown each frame

    def __init__(self, master, screen_w, ground_y):
        self.screen_w = screen_w
        self.ground_y = ground_y + 20    # the floor the ball rests/bounces on

        # The ball lives in its own borderless, always-on-top window.
        self.win = tk.Toplevel(master)
        self.win.overrideredirect(True)       # no title bar / border
        self.win.attributes("-topmost", True) # stay above other windows
        self.win.config(bg=TRANSPARENT_COLOR)
        try:
            self.win.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass  # the transparency trick is Windows-only

        # Draw the ball on a canvas: a red circle with a yellow top half.
        c = tk.Canvas(self.win, width=BALL_SIZE, height=BALL_SIZE,
                      bg=TRANSPARENT_COLOR, highlightthickness=0)
        c.pack()
        c.create_oval(1, 1, BALL_SIZE - 1, BALL_SIZE - 1,
                      fill=BALL_COLOR, outline="")
        c.create_arc(1, 1, BALL_SIZE - 1, BALL_SIZE - 1, start=0,
                     extent=180, fill=BALL_COLOR2, outline="")

        # Starting position and velocity.
        self.x = random.randint(100, screen_w - 100)
        self.y = self.ground_y - 300          # start up high so it drops in
        self.vx = random.choice([-6, 6])      # initial sideways speed
        self.vy = 0                           # initial vertical speed
        self.alive = True
        self._tick()                          # begin the physics loop

    def _tick(self):
        """Advance the ball's physics by one frame, then schedule the next."""
        if not self.alive:
            return
        # Apply gravity and friction.
        self.vy += self.GRAVITY
        self.vx *= self.FRICTION
        self.x += self.vx
        self.y += self.vy
        # Bounce off the floor.
        if self.y >= self.ground_y:
            self.y = self.ground_y
            self.vy = -abs(self.vy) * self.BOUNCE
            if abs(self.vy) < 2:      # stop tiny jitter once it slows down
                self.vy = 0
        # Bounce off the left/right screen edges.
        if self.x <= 0 or self.x >= self.screen_w - BALL_SIZE:
            self.vx = -self.vx
            self.x = max(0, min(self.screen_w - BALL_SIZE, self.x))
        # Move the window to the new position and loop again in 20 ms.
        self.win.geometry(f"+{int(self.x)}+{int(self.y)}")
        self.win.after(20, self._tick)

    def kick(self, direction):
        """Send the ball flying when Doraemon reaches it. direction: 1 or -1."""
        self.vx = direction * random.uniform(8, 14)
        self.vy = -random.uniform(10, 16)     # negative = upward

    def destroy(self):
        """Remove the ball window at the end of a play session."""
        self.alive = False
        self.win.destroy()


# =============================================================================
#  DESKTOP PET  —  the main character and his behaviour
# =============================================================================
class DesktopPet:
    def __init__(self):
        # ---- create the transparent, always-on-top, borderless window ----
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg=TRANSPARENT_COLOR)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass

        # ---- load every animation we can find ----
        # self.anims["walk"] = (right_frames, left_frames), and so on.
        self.anims = {}
        fallback = None
        try:
            fallback = load_animation(PET_IMAGE, PET_SCALE)   # pet.png
        except Exception:
            pass
        for state, fname in STATE_FILES.items():
            try:
                self.anims[state] = load_animation(fname, PET_SCALE)
            except Exception:
                # If a state GIF is missing, reuse pet.png — except for the
                # entrance, which is skipped entirely if absent.
                if fallback and state != "entrance":
                    self.anims[state] = fallback
        if "idle" not in self.anims:
            print(f"Couldn't load '{PET_IMAGE}' or any state GIFs.")
            sys.exit(1)

        # ---- current visual state ----
        self.state = "idle"        # which animation is playing
        self.facing = 1            # 1 = facing right, -1 = facing left
        self.frame_index = 0       # which frame of the animation we're on

        # Put the first frame on a label widget (the thing that shows the image).
        first = self.anims["idle"][0][0]
        self.label = tk.Label(self.root, image=first,
                              bg=TRANSPARENT_COLOR, bd=0)
        self.label.pack()

        # ---- figure out screen size and where the "floor" is ----
        self.root.update_idletasks()
        self.w = first.width()
        self.h = first.height()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()

        # real_ground_y is the TRUE floor (just above the taskbar) and never
        # changes. ground_y is his CURRENT standing level, which can float up
        # high after a teleport. Ball-play always returns to real_ground_y so
        # the ball's gravity has a proper floor to land on.
        self.real_ground_y = self.screen_h - self.h - GROUND_MARGIN
        self.ground_y = self.real_ground_y
        self.x = self.screen_w // 2          # start in the middle, horizontally
        self.y = self.ground_y
        self._place()

        # ---- mouse and keyboard controls (see CONTROLS at top of file) ----
        self.label.bind("<Button-3>", lambda e: self.root.destroy())  # right-click quits
        self.label.bind("<Button-1>", self._start_drag)               # begin drag
        self.label.bind("<B1-Motion>", self._on_drag)                 # dragging
        self.root.bind("<KeyPress-p>", lambda e: self._activity_play())
        self.root.bind("<KeyPress-t>", lambda e: self._activity_teleport())
        self.root.bind("<KeyPress-j>", lambda e: self._activity_jump())
        self.root.bind("<KeyPress-c>", lambda e: self._activity_chase_cursor())

        # ---- status flags: only one "big" activity runs at a time ----
        self.moving = False          # walking or jumping
        self.bob_up = True           # toggles the idle breathing bob
        self.ball = None             # the Ball object during play (else None)
        self.playing = False         # currently in a ball session?
        self.entering = False        # currently mid Anywhere-Door animation?
        self.chasing_cursor = False  # currently following the mouse?

        # ---- start the two always-running loops ----
        self.root.after(GIF_FRAME_MS, self._animate)   # advance the animation
        self.root.after(BOB_SPEED_MS, self._idle_bob)  # gentle idle breathing

        # First arrival plays where he starts (no teleport); when it finishes,
        # the director takes over and runs his random life.
        if "entrance" in self.anims:
            self._play_entrance(on_finish=self._start_director,
                                 teleport=False, wander_after=False)
        else:
            self._start_director()

    # =========================================================================
    #  DIRECTOR  —  every ACTIVITY_INTERVAL, pick one random thing to do
    # =========================================================================
    def _start_director(self):
        self.root.after(ACTIVITY_INTERVAL_MS, self._next_activity)

    def _busy(self):
        """True if he's mid-activity, so the director and idle-bob leave him be."""
        return (self.moving or self.playing or self.entering
                or self.chasing_cursor)

    def _next_activity(self):
        # Only start something new if he's currently free.
        if not self._busy():
            # Weighted random pick from ACTIVITY_WEIGHTS.
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
        # Schedule the next decision regardless of whether we acted this time.
        self.root.after(ACTIVITY_INTERVAL_MS, self._next_activity)

    # ---- the individual activities the director can choose ----
    def _activity_wander(self):
        """Stroll a short random distance at his current height."""
        distance = random.randint(80, 300)
        direction = random.choice([-1, 1])
        target = max(0, min(self.screen_w - self.w,
                            self.x + direction * distance))
        self._walk_to(target)

    def _activity_jump(self):
        """Hop straight up and back down."""
        self._do_jump_animation()

    def _activity_teleport(self):
        """Step through the Anywhere Door to a random spot AND random height."""
        if "entrance" in self.anims:
            self._play_entrance(teleport=True, wander_after=True)
        else:
            self._activity_wander()   # no door art? just wander instead

    def _activity_play(self):
        """Ball play needs real gravity, so door DOWN to the floor first,
        then start the bouncing-ball session."""
        if "entrance" in self.anims:
            self._play_entrance(on_finish=self._begin_ball,
                                 teleport=True, wander_after=False,
                                 target_y=self.real_ground_y)
        else:
            # No door animation: just snap to the floor and play.
            self.ground_y = self.real_ground_y
            self.y = self.ground_y
            self._place()
            self._begin_ball()

    # =========================================================================
    #  CHASE THE MOUSE CURSOR
    # =========================================================================
    def _activity_chase_cursor(self):
        """Follow the mouse pointer around for CURSOR_CHASE_DURATION_MS."""
        if self._busy():
            return
        self.chasing_cursor = True
        self._set_state("walk")
        # Schedule the end of the chase, then start the per-frame follow loop.
        self.root.after(CURSOR_CHASE_DURATION_MS, self._end_cursor_chase)
        self._chase_cursor_step()

    def _chase_cursor_step(self):
        """One frame of cursor-following: nudge toward the pointer, then loop."""
        if not self.chasing_cursor:
            return
        # winfo_pointerx/y give the mouse position in absolute screen coords.
        cx = self.root.winfo_pointerx()
        cy = self.root.winfo_pointery()
        # Aim so his centre sits just under the pointer.
        target_x = cx - self.w / 2
        target_y = cy - self.h / 2
        # Keep him on-screen.
        target_x = max(0, min(self.screen_w - self.w, target_x))
        target_y = max(0, min(self.screen_h - self.h, target_y))

        # Move a fixed step toward the target (don't teleport onto it).
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
        """Stop following the mouse and return to idle."""
        self.chasing_cursor = False
        self._set_state("idle")

    # =========================================================================
    #  ENTRANCE / TELEPORT  (the Anywhere Door)
    # =========================================================================
    def _play_entrance(self, on_finish=None, teleport=True,
                       wander_after=True, target_x=None, target_y=None):
        """Play the door animation. Optionally teleport him first, and
        optionally take a few wandering steps afterwards.

        on_finish    - a function to call once the entrance (and any
                       wander-off) is complete.
        teleport     - if True, jump to a new position before the animation.
        wander_after - if True, stroll a few steps after arriving.
        target_x/y   - specific landing spot; random if left as None.
        """
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
        # The door animation finishes after all its frames have played.
        n_frames = len(self.anims["entrance"][0])
        duration = n_frames * GIF_FRAME_MS * ENTRANCE_LOOPS
        self.root.after(duration,
                        lambda: self._finish_entrance(on_finish,
                                                      teleport and wander_after))

    def _finish_entrance(self, on_finish=None, wander_after=False):
        """Called when the door animation ends."""
        self.entering = False
        self.moving = False
        self._set_state("idle")
        if wander_after:
            # Stroll a little so it reads as "stepped through, wandered off".
            steps = random.randint(60, 160)
            direction = self.facing
            target = self.x + direction * steps
            if target < 0 or target > self.screen_w - self.w:
                target = self.x - direction * steps   # turn back if off-screen
            target = max(0, min(self.screen_w - self.w, target))
            self._walk_to(target, then=on_finish)
        elif on_finish:
            on_finish()

    # =========================================================================
    #  SMALL HELPERS
    # =========================================================================
    def _place(self):
        """Move the pet window to its current (x, y) position."""
        self.root.geometry(f"+{int(self.x)}+{int(self.y)}")

    def _set_state(self, state):
        """Switch which animation is playing (and restart it from frame 0)."""
        if state in self.anims and state != self.state:
            self.state = state
            self.frame_index = 0

    def _start_drag(self, event):
        """Remember where inside the pet you grabbed him."""
        self._drag_dx = event.x
        self._drag_dy = event.y

    def _on_drag(self, event):
        """Move the pet to follow the mouse while the left button is held."""
        self.x = self.root.winfo_x() + event.x - self._drag_dx
        self.y = self.root.winfo_y() + event.y - self._drag_dy
        self.ground_y = self.y
        self.real_ground_y = self.y   # wherever you drop him becomes the floor
        self._place()

    # =========================================================================
    #  ANIMATION LOOP  (always running)
    # =========================================================================
    def _animate(self):
        """Show the next frame of the current animation, then loop."""
        frames = self.anims.get(self.state, self.anims["idle"])
        side = frames[0] if self.facing == 1 else frames[1]   # right or left set
        self.frame_index = (self.frame_index + 1) % len(side)
        self.label.config(image=side[self.frame_index])
        self.root.after(GIF_FRAME_MS, self._animate)

    def _idle_bob(self):
        """Gently bob up and down while idle so he never looks frozen."""
        if not self._busy():
            self.y = self.ground_y - (BOB_PIXELS if self.bob_up else 0)
            self.bob_up = not self.bob_up
            self._place()
        self.root.after(BOB_SPEED_MS, self._idle_bob)

    # =========================================================================
    #  WALKING
    # =========================================================================
    def _walk_to(self, target_x, then=None, speed=MOVE_STEP):
        """Walk step-by-step to target_x, then optionally call `then`."""
        self.moving = True
        self._set_state("walk")

        def step():
            # Close enough? Snap to target, go idle, and run the callback.
            if abs(self.x - target_x) <= speed:
                self.x = target_x
                self.y = self.ground_y
                self._place()
                self.moving = False
                self._set_state("idle")
                if then:
                    then()
                return
            # Otherwise take one step toward the target.
            self.facing = 1 if target_x > self.x else -1
            self.x += speed * self.facing
            # Tiny up/down wobble gives a cartoonish waddle.
            self.y = self.ground_y - (4 if (self.x // 12) % 2 == 0 else 0)
            self._place()
            self.root.after(20, step)

        step()

    # =========================================================================
    #  JUMPING  (rises with ease-out, falls with ease-in for a natural arc)
    # =========================================================================
    def _do_jump_animation(self, then=None):
        self.moving = True
        self._set_state("jump")
        frames_up = 15
        base = self.ground_y       # remember the level he jumps from

        def up(i=0):
            if i >= frames_up:
                down()
                return
            # Ease-out: fast at first, slowing near the top.
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
            # Ease-in: slow at first, speeding up as he falls.
            self.y = (base - JUMP_HEIGHT) + JUMP_HEIGHT * (i / frames_up) ** 2
            self._place()
            self.root.after(15, lambda: down(i + 1))

        up()

    # =========================================================================
    #  BALL PLAY  (chase the ball and kick it around on the real floor)
    # =========================================================================
    def _begin_ball(self):
        """Drop a ball and start chasing it. Always runs on the real floor."""
        self.playing = True
        self.moving = False
        self.ground_y = self.real_ground_y    # make sure he's on the floor
        self.y = self.ground_y
        self._place()
        self.ball = Ball(self.root, self.screen_w,
                         self.real_ground_y + self.h - BALL_SIZE)
        self.root.after(PLAY_DURATION_MS, self._end_play)   # end after a while
        self._chase()

    def _chase(self):
        """One frame of ball-chasing: run toward the ball and kick it if close."""
        if not self.playing or not self.ball or not self.ball.alive:
            return
        ball_cx = self.ball.x + BALL_SIZE / 2     # ball centre
        pet_cx = self.x + self.w / 2              # pet centre
        gap = ball_cx - pet_cx
        self._set_state("walk")
        if abs(gap) > self.w * 0.4:
            # Still far away: run toward the ball.
            self.facing = 1 if gap > 0 else -1
            self.x += CHASE_STEP * self.facing
            self.x = max(0, min(self.screen_w - self.w, self.x))
            self.y = self.ground_y - (4 if (self.x // 12) % 2 == 0 else 0)
            self._place()
        else:
            # Close enough: kick it (only if it's near the ground) and hop.
            if self.ball.y > self.ground_y - 60:
                self.ball.kick(1 if self.facing == 1 else -1)
                if not self.moving:
                    self._mini_hop()
        self.root.after(25, self._chase)

    def _mini_hop(self):
        """A small happy hop after kicking the ball."""
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
        """End the play session and remove the ball."""
        self.playing = False
        self._set_state("idle")
        if self.ball:
            self.ball.destroy()
            self.ball = None

    # =========================================================================
    #  START
    # =========================================================================
    def run(self):
        """Hand control to tkinter's event loop (keeps the window alive)."""
        self.root.mainloop()


# Only run the pet if this file is executed directly (not imported elsewhere).
if __name__ == "__main__":
    DesktopPet().run()