"""
Subway Runner - An endless runner game inspired by Subway Surfers
Requirements: pip install pygame
Controls:
  LEFT/RIGHT Arrow or A/D - Change lanes
  UP Arrow or W or SPACE  - Jump
  DOWN Arrow or S         - Slide/Duck
  P                       - Pause
  ESC                     - Quit
"""

import pygame
import random
import sys
import math

# ─── Init ────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 480, 700
FPS = 60

# Colors
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
GRAY       = (80, 80, 80)
DARK_GRAY  = (40, 40, 40)
LIGHT_GRAY = (160, 160, 160)
YELLOW     = (255, 220, 0)
RED        = (220, 50, 50)
ORANGE     = (255, 140, 0)
BLUE       = (50, 150, 255)
CYAN       = (0, 220, 255)
GREEN      = (50, 200, 80)
PURPLE     = (180, 60, 220)
GOLD       = (255, 215, 0)
SKIN       = (255, 200, 150)
BROWN      = (120, 70, 30)
DARK_BLUE  = (10, 20, 60)
PINK       = (255, 100, 180)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Subway Runner")
clock = pygame.time.Clock()

# ─── Fonts ───────────────────────────────────────────────────────────────────
font_big   = pygame.font.SysFont("Arial", 56, bold=True)
font_med   = pygame.font.SysFont("Arial", 32, bold=True)
font_small = pygame.font.SysFont("Arial", 22)
font_tiny  = pygame.font.SysFont("Arial", 16)

# ─── Lane setup ──────────────────────────────────────────────────────────────
LANES = [WIDTH // 4, WIDTH // 2, 3 * WIDTH // 4]   # x centers of 3 lanes
LANE_COUNT = 3
GROUND_Y = HEIGHT - 110

# ─── Particle system ─────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color, vel_x=0, vel_y=0, life=30, size=4):
        self.x = x
        self.y = y
        self.color = color
        self.vel_x = vel_x + random.uniform(-1.5, 1.5)
        self.vel_y = vel_y + random.uniform(-3, -0.5)
        self.life = life
        self.max_life = life
        self.size = size

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_y += 0.15
        self.life -= 1

    def draw(self, surf):
        alpha = int(255 * (self.life / self.max_life))
        s = max(1, int(self.size * (self.life / self.max_life)))
        col = (*self.color[:3], alpha)
        tmp = pygame.Surface((s*2, s*2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, col, (s, s), s)
        surf.blit(tmp, (int(self.x)-s, int(self.y)-s))

particles = []

def spawn_particles(x, y, color, count=8, size=5):
    for _ in range(count):
        particles.append(Particle(x, y, color, size=size))

# ─── Player ──────────────────────────────────────────────────────────────────
class Player:
    WIDTH  = 36
    HEIGHT = 56
    JUMP_VEL = -16
    GRAVITY  = 0.7

    def __init__(self):
        self.lane = 1            # 0=left, 1=center, 2=right
        self.x = LANES[self.lane]
        self.y = GROUND_Y
        self.vel_y = 0
        self.on_ground = True
        self.sliding = False
        self.slide_timer = 0
        self.target_x = self.x
        self.invincible = 0      # frames of invincibility after hit
        self.anim_frame = 0
        self.anim_timer = 0
        self.double_jump = True  # allow one double jump per air-time

    @property
    def rect(self):
        if self.sliding:
            return pygame.Rect(self.x - self.WIDTH//2,
                               self.y - self.HEIGHT//3,
                               self.WIDTH, self.HEIGHT//3)
        return pygame.Rect(self.x - self.WIDTH//2,
                           self.y - self.HEIGHT,
                           self.WIDTH, self.HEIGHT)

    def move_lane(self, direction):
        new_lane = self.lane + direction
        if 0 <= new_lane < LANE_COUNT:
            self.lane = new_lane
            self.target_x = LANES[self.lane]

    def jump(self):
        if self.on_ground:
            self.vel_y = self.JUMP_VEL
            self.on_ground = False
            self.sliding = False
            self.slide_timer = 0
            self.double_jump = True
            spawn_particles(self.x, self.y, CYAN, 6)
        elif self.double_jump:
            self.vel_y = self.JUMP_VEL * 0.85
            self.double_jump = False
            spawn_particles(self.x, self.y - self.HEIGHT//2, YELLOW, 10)

    def slide(self):
        if self.on_ground and not self.sliding:
            self.sliding = True
            self.slide_timer = 35

    def update(self):
        # Horizontal slide to target
        self.x += (self.target_x - self.x) * 0.22

        # Gravity
        if not self.on_ground:
            self.vel_y += self.GRAVITY
            self.y += self.vel_y
            if self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vel_y = 0
                self.on_ground = True
                spawn_particles(self.x, self.y, LIGHT_GRAY, 5, size=3)

        # Slide timer
        if self.sliding:
            self.slide_timer -= 1
            if self.slide_timer <= 0:
                self.sliding = False

        if self.invincible > 0:
            self.invincible -= 1

        # Animation
        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 4

    def draw(self, surf):
        if self.invincible > 0 and self.invincible % 6 < 3:
            return   # blink during invincibility

        x, y = int(self.x), int(self.y)
        if self.sliding:
            # Sliding pose
            pygame.draw.ellipse(surf, BLUE, (x-18, y-20, 36, 20))   # body
            pygame.draw.circle(surf, SKIN, (x+14, y-22), 8)          # head
            pygame.draw.rect(surf, BROWN, (x-16, y-8, 32, 6))        # board/legs
        else:
            # Run animation: slight bob
            bob = int(math.sin(self.anim_frame * math.pi / 2) * 2)
            leg_swing = int(math.sin(self.anim_frame * math.pi / 2) * 8)

            # Shadow
            pygame.draw.ellipse(surf, (30,30,30), (x-14, y-4, 28, 8))

            # Legs
            pygame.draw.line(surf, BLUE, (x-6, y-14), (x-6+leg_swing, y), 6)
            pygame.draw.line(surf, BLUE, (x+6, y-14), (x+6-leg_swing, y), 6)
            # Shoes
            pygame.draw.circle(surf, RED, (x-6+leg_swing, y), 5)
            pygame.draw.circle(surf, RED, (x+6-leg_swing, y), 5)
            # Body
            pygame.draw.rect(surf, BLUE, (x-12, y-42+bob, 24, 28), border_radius=4)
            # Arms
            arm = int(math.cos(self.anim_frame * math.pi / 2) * 10)
            pygame.draw.line(surf, SKIN, (x-12, y-36+bob), (x-20, y-28+bob+arm), 5)
            pygame.draw.line(surf, SKIN, (x+12, y-36+bob), (x+20, y-28+bob-arm), 5)
            # Head
            pygame.draw.circle(surf, SKIN, (x, y-48+bob), 12)
            # Hair
            pygame.draw.arc(surf, BROWN, (x-12, y-62+bob, 24, 18), 0, math.pi, 5)
            # Eyes
            pygame.draw.circle(surf, BLACK, (x-4, y-50+bob), 2)
            pygame.draw.circle(surf, BLACK, (x+4, y-50+bob), 2)
            # Backpack
            pygame.draw.rect(surf, ORANGE, (x+10, y-40+bob, 10, 18), border_radius=3)


# ─── Obstacles ───────────────────────────────────────────────────────────────
class Obstacle:
    def __init__(self, speed):
        self.lane = random.randint(0, LANE_COUNT-1)
        self.x = LANES[self.lane]
        self.y = -50
        self.speed = speed
        kind_roll = random.random()
        if kind_roll < 0.35:
            self.kind = "barrier"     # low - need to jump
            self.w, self.h = 48, 28
            self.color = RED
        elif kind_roll < 0.6:
            self.kind = "train"       # tall - need to slide or change lane
            self.w, self.h = 44, 90
            self.color = GRAY
        elif kind_roll < 0.80:
            self.kind = "pole"        # mid-height - jump or lane change
            self.w, self.h = 16, 60
            self.color = YELLOW
        else:
            self.kind = "gap"         # floating barrel - jump over
            self.w, self.h = 36, 36
            self.color = BROWN
            self.y = -(GROUND_Y - 80 - random.randint(20, 100))

    @property
    def rect(self):
        gy = GROUND_Y - self.h if self.kind != "gap" else GROUND_Y - 80 - 40
        return pygame.Rect(self.x - self.w//2,
                           int(self.y + gy if self.y < 0 else self.y - self.h),
                           self.w, self.h)

    def update(self):
        self.y += self.speed

    def is_off_screen(self):
        return self.y > HEIGHT + 100

    def draw(self, surf):
        r = self.rect
        if self.kind == "barrier":
            pygame.draw.rect(surf, self.color, r, border_radius=4)
            pygame.draw.rect(surf, WHITE, r, 2, border_radius=4)
            # stripes
            for i in range(0, r.width, 10):
                pygame.draw.line(surf, WHITE, (r.x+i, r.y), (r.x+i+6, r.bottom), 2)
        elif self.kind == "train":
            pygame.draw.rect(surf, DARK_GRAY, r, border_radius=6)
            pygame.draw.rect(surf, self.color, r, 3, border_radius=6)
            # windows
            for wy in range(r.y+6, r.bottom-14, 20):
                pygame.draw.rect(surf, CYAN, (r.x+6, wy, r.width-12, 12), border_radius=3)
            pygame.draw.rect(surf, YELLOW, (r.x+4, r.bottom-12, r.width-8, 6), border_radius=2)
        elif self.kind == "pole":
            pygame.draw.rect(surf, self.color, r, border_radius=4)
            pygame.draw.circle(surf, ORANGE, (r.centerx, r.y+8), 10)
        elif self.kind == "gap":
            pygame.draw.rect(surf, self.color, r, border_radius=6)
            pygame.draw.rect(surf, ORANGE, r, 3, border_radius=6)
            # bands
            pygame.draw.line(surf, ORANGE, (r.x, r.centery), (r.right, r.centery), 3)


# ─── Coins ───────────────────────────────────────────────────────────────────
class Coin:
    RADIUS = 10

    def __init__(self, speed):
        self.lane = random.randint(0, LANE_COUNT-1)
        self.x = LANES[self.lane]
        heights = [0, -40, -80, -120]
        self.y_offset = random.choice(heights)   # above ground
        self.y = -20
        self.speed = speed
        self.collected = False
        self.anim = random.randint(0, 30)
        self.special = random.random() < 0.08  # gold star coin

    @property
    def rect(self):
        gy = GROUND_Y + self.y_offset - self.RADIUS
        return pygame.Rect(self.x - self.RADIUS,
                           int(self.y + gy),
                           self.RADIUS*2, self.RADIUS*2)

    def update(self):
        self.y += self.speed
        self.anim += 1

    def is_off_screen(self):
        return self.y > HEIGHT + 50

    def draw(self, surf):
        if self.collected:
            return
        r = self.rect
        cx, cy = r.centerx, r.centery
        pulse = abs(math.sin(self.anim * 0.1)) * 3
        if self.special:
            # Star shape
            color = GOLD
            outer_r = int(self.RADIUS + pulse)
            pts = []
            for i in range(10):
                angle = math.pi/2 + i * 2*math.pi/10
                rad = outer_r if i % 2 == 0 else outer_r // 2
                pts.append((cx + int(math.cos(angle)*rad),
                             cy - int(math.sin(angle)*rad)))
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.polygon(surf, WHITE, pts, 1)
        else:
            color = GOLD
            pygame.draw.circle(surf, color, (cx, cy), int(self.RADIUS + pulse))
            pygame.draw.circle(surf, YELLOW, (cx, cy), int(self.RADIUS + pulse - 3))
            pygame.draw.circle(surf, WHITE, (cx-2, cy-2), 3)


# ─── Powerup ─────────────────────────────────────────────────────────────────
class Powerup:
    def __init__(self, speed):
        self.lane = random.randint(0, LANE_COUNT-1)
        self.x = LANES[self.lane]
        self.y = -20
        self.speed = speed
        self.kind = random.choice(["magnet", "shield", "boost"])
        self.colors = {"magnet": PURPLE, "shield": CYAN, "boost": ORANGE}
        self.anim = 0
        self.collected = False

    @property
    def rect(self):
        gy = GROUND_Y - 60
        return pygame.Rect(self.x - 16,
                           int(self.y + gy),
                           32, 32)

    def update(self):
        self.y += self.speed
        self.anim += 1

    def is_off_screen(self):
        return self.y > HEIGHT + 50

    def draw(self, surf):
        if self.collected:
            return
        r = self.rect
        cx, cy = r.centerx, r.centery
        pulse = abs(math.sin(self.anim * 0.08)) * 4
        col = self.colors[self.kind]
        # glow
        glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*col, 40), (30, 30), int(20 + pulse))
        surf.blit(glow_surf, (cx-30, cy-30))
        # icon
        pygame.draw.rect(surf, col, (cx-14, cy-14, 28, 28), border_radius=8)
        pygame.draw.rect(surf, WHITE, (cx-14, cy-14, 28, 28), 2, border_radius=8)
        label = font_tiny.render(self.kind[0].upper(), True, WHITE)
        surf.blit(label, label.get_rect(center=(cx, cy)))


# ─── Background ──────────────────────────────────────────────────────────────
class Background:
    def __init__(self):
        self.scroll = 0
        self.build_speed = 1
        self.buildings = [(random.randint(0, WIDTH//2 - 60),
                           random.randint(80, 200),
                           random.randint(30, 70),
                           random.randint(60, 160),
                           random.choice([DARK_BLUE, (20,30,70), (30,20,60)]))
                          for _ in range(8)]
        self.rail_scroll = 0

    def update(self, speed):
        self.scroll = (self.scroll + speed * 0.4) % HEIGHT
        self.rail_scroll = (self.rail_scroll + speed) % 60

    def draw(self, surf):
        # Sky gradient
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(10 + 20 * ratio)
            g = int(10 + 15 * ratio)
            b = int(40 + 30 * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))

        # Stars
        random.seed(42)
        for _ in range(60):
            sx = random.randint(0, WIDTH)
            sy = random.randint(0, HEIGHT//2)
            brightness = random.randint(150, 255)
            pygame.draw.circle(surf, (brightness,)*3, (sx, sy), 1)
        random.seed()

        # Buildings (left side)
        for bx, by, bw, bh, col in self.buildings:
            pygame.draw.rect(surf, col, (bx, by, bw, bh))
            for wy in range(by+8, by+bh-10, 16):
                for wx in range(bx+6, bx+bw-10, 14):
                    wc = random.choice([(YELLOW[0], YELLOW[1], 0, 180), (100,100,120,60)])
                    w_surf = pygame.Surface((8, 10), pygame.SRCALPHA)
                    w_surf.fill((*YELLOW[:2], 0, 120) if random.random() < 0.4 else (60,60,80,180))
                    surf.blit(w_surf, (wx, wy))

        # Buildings (right side, mirrored)
        for bx, by, bw, bh, col in self.buildings:
            rbx = WIDTH - bx - bw
            pygame.draw.rect(surf, col, (rbx, by, bw, bh))

        # Ground - track
        ground_rect = pygame.Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y)
        pygame.draw.rect(surf, (50, 40, 30), ground_rect)
        pygame.draw.rect(surf, (70, 60, 40), (0, GROUND_Y, WIDTH, 6))

        # Rail lines
        rail_cols = [WIDTH//4 - 1, WIDTH//2 - 1, 3*WIDTH//4 - 1]
        for rx in [WIDTH//4 - 20, WIDTH//2 - 20, 3*WIDTH//4 - 20,
                   WIDTH//4 + 20, WIDTH//2 + 20, 3*WIDTH//4 + 20]:
            pygame.draw.line(surf, LIGHT_GRAY, (rx, GROUND_Y), (rx, HEIGHT), 2)

        # Sleepers (horizontal ties) scrolling
        for ty in range(int(GROUND_Y + self.rail_scroll % 60), HEIGHT, 60):
            pygame.draw.rect(surf, BROWN, (30, ty, WIDTH-60, 8))

        # Lane dividers
        for lx in [WIDTH//4 + WIDTH//8, WIDTH//2 + WIDTH//8]:
            pygame.draw.line(surf, DARK_GRAY, (lx, GROUND_Y), (lx, HEIGHT), 2)


# ─── HUD ─────────────────────────────────────────────────────────────────────
def draw_hud(surf, score, coins, lives, powerup_active, powerup_timer, hi_score):
    # Top bar
    pygame.draw.rect(surf, (0, 0, 0, 160), (0, 0, WIDTH, 56))
    pygame.draw.line(surf, YELLOW, (0, 56), (WIDTH, 56), 2)

    score_txt = font_med.render(f"{int(score)}", True, WHITE)
    surf.blit(score_txt, (10, 8))
    lbl = font_tiny.render("SCORE", True, LIGHT_GRAY)
    surf.blit(lbl, (12, 44))

    hi_txt = font_small.render(f"BEST {int(hi_score)}", True, GOLD)
    surf.blit(hi_txt, hi_txt.get_rect(centerx=WIDTH//2, y=8))

    # Coins
    pygame.draw.circle(surf, GOLD, (WIDTH - 90, 24), 10)
    coin_txt = font_small.render(f"x{coins}", True, GOLD)
    surf.blit(coin_txt, (WIDTH - 74, 10))

    # Lives (hearts)
    for i in range(3):
        col = RED if i < lives else DARK_GRAY
        hx = WIDTH - 30 - i*26
        pygame.draw.circle(surf, col, (hx-4, 44), 6)
        pygame.draw.circle(surf, col, (hx+4, 44), 6)
        pts = [(hx-10, 44), (hx, 54), (hx+10, 44)]
        pygame.draw.polygon(surf, col, pts)

    # Powerup bar
    if powerup_active and powerup_timer > 0:
        colors_map = {"magnet": PURPLE, "shield": CYAN, "boost": ORANGE}
        max_t = 300
        bar_w = int((powerup_timer / max_t) * (WIDTH - 20))
        pygame.draw.rect(surf, DARK_GRAY, (10, 60, WIDTH-20, 8), border_radius=4)
        pygame.draw.rect(surf, colors_map.get(powerup_active, WHITE),
                         (10, 60, bar_w, 8), border_radius=4)
        p_lbl = font_tiny.render(powerup_active.upper(), True, WHITE)
        surf.blit(p_lbl, (10, 70))


# ─── Screens ─────────────────────────────────────────────────────────────────
def draw_start_screen(surf, hi_score):
    surf.fill(DARK_BLUE)
    # Title glow
    glow = font_big.render("SUBWAY", True, CYAN)
    for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
        surf.blit(glow, glow.get_rect(centerx=WIDTH//2+dx, y=120+dy))
    title1 = font_big.render("SUBWAY", True, YELLOW)
    title2 = font_big.render("RUNNER", True, WHITE)
    surf.blit(title1, title1.get_rect(centerx=WIDTH//2, y=120))
    surf.blit(title2, title2.get_rect(centerx=WIDTH//2, y=180))

    # Instructions
    instructions = [
        ("← →  /  A D", "Change Lane"),
        ("↑  /  W  /  SPACE", "Jump (x2 = Double Jump)"),
        ("↓  /  S", "Slide"),
        ("P", "Pause"),
    ]
    y = 290
    for key, action in instructions:
        k_txt = font_small.render(key, True, CYAN)
        a_txt = font_small.render(action, True, LIGHT_GRAY)
        surf.blit(k_txt, k_txt.get_rect(right=WIDTH//2-10, y=y))
        surf.blit(a_txt, (WIDTH//2+10, y))
        y += 34

    if hi_score > 0:
        hs = font_med.render(f"BEST: {int(hi_score)}", True, GOLD)
        surf.blit(hs, hs.get_rect(centerx=WIDTH//2, y=y+10))
        y += 40

    blink_txt = font_med.render("PRESS  SPACE  TO  START", True,
                                WHITE if (pygame.time.get_ticks()//500)%2 else YELLOW)
    surf.blit(blink_txt, blink_txt.get_rect(centerx=WIDTH//2, y=y+20))


def draw_game_over(surf, score, hi_score, coins):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surf.blit(overlay, (0, 0))

    go = font_big.render("GAME  OVER", True, RED)
    surf.blit(go, go.get_rect(centerx=WIDTH//2, y=180))

    sc = font_med.render(f"Score: {int(score)}", True, WHITE)
    surf.blit(sc, sc.get_rect(centerx=WIDTH//2, y=270))

    cn = font_med.render(f"Coins: {coins}", True, GOLD)
    surf.blit(cn, cn.get_rect(centerx=WIDTH//2, y=310))

    if score >= hi_score:
        new_best = font_med.render("NEW BEST!", True, YELLOW)
        surf.blit(new_best, new_best.get_rect(centerx=WIDTH//2, y=355))

    hs = font_small.render(f"Best: {int(hi_score)}", True, LIGHT_GRAY)
    surf.blit(hs, hs.get_rect(centerx=WIDTH//2, y=400))

    blink = font_med.render("SPACE = Restart   ESC = Quit", True,
                            WHITE if (pygame.time.get_ticks()//600)%2 else CYAN)
    surf.blit(blink, blink.get_rect(centerx=WIDTH//2, y=460))


def draw_pause(surf):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surf.blit(overlay, (0, 0))
    p = font_big.render("PAUSED", True, CYAN)
    surf.blit(p, p.get_rect(centerx=WIDTH//2, centery=HEIGHT//2-40))
    r = font_small.render("Press P to Resume", True, WHITE)
    surf.blit(r, r.get_rect(centerx=WIDTH//2, centery=HEIGHT//2+30))


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    hi_score = 0

    while True:   # outer loop: return to start screen
        # ── Start screen loop
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        goto_game = True
                        break
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
            else:
                draw_start_screen(screen, hi_score)
                pygame.display.flip()
                clock.tick(FPS)
                continue
            break

        # ── Game setup
        bg = Background()
        player = Player()
        obstacles = []
        coins_list = []
        powerups = []
        score = 0.0
        coins_collected = 0
        lives = 3
        speed = 6.0
        spawn_timer = 0
        coin_timer = 0
        powerup_timer_spawn = 0
        paused = False
        game_over = False
        powerup_active = None
        powerup_timer = 0
        magnet_range = 150
        last_lane_key = 0    # cooldown for lane switching

        running = True
        while running:
            dt = clock.tick(FPS)

            # ── Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        paused = not paused
                    elif not paused and not game_over:
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            player.move_lane(-1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            player.move_lane(1)
                        elif event.key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
                            player.jump()
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            player.slide()
                    elif game_over:
                        if event.key == pygame.K_SPACE:
                            running = False  # restart
                        elif event.key == pygame.K_ESCAPE:
                            pygame.quit(); sys.exit()

            if paused or game_over:
                if paused:
                    draw_pause(screen)
                elif game_over:
                    draw_game_over(screen, score, hi_score, coins_collected)
                pygame.display.flip()
                continue

            # ── Speed ramp
            speed = 6.0 + (score / 500) * 2.0
            speed = min(speed, 18.0)
            if powerup_active == "boost":
                speed = min(speed * 1.5, 24.0)

            # ── Spawn obstacles
            spawn_timer += 1
            interval = max(55, 95 - int(score / 300))
            if spawn_timer >= interval:
                spawn_timer = 0
                obstacles.append(Obstacle(speed))

            # ── Spawn coins
            coin_timer += 1
            if coin_timer >= 25:
                coin_timer = 0
                for _ in range(random.randint(1, 3)):
                    coins_list.append(Coin(speed))

            # ── Spawn powerups
            powerup_timer_spawn += 1
            if powerup_timer_spawn >= 360:
                powerup_timer_spawn = 0
                powerups.append(Powerup(speed))

            # ── Update
            bg.update(speed)
            player.update()

            for obs in obstacles[:]:
                obs.speed = speed
                obs.update()
                if obs.is_off_screen():
                    obstacles.remove(obs)

            for c in coins_list[:]:
                c.speed = speed
                c.update()
                if c.is_off_screen():
                    coins_list.remove(c)

            for pu in powerups[:]:
                pu.speed = speed
                pu.update()
                if pu.is_off_screen():
                    powerups.remove(pu)

            # ── Magnet
            if powerup_active == "magnet":
                for c in coins_list:
                    if not c.collected:
                        cr = c.rect
                        pr = player.rect
                        dx = pr.centerx - cr.centerx
                        dy = pr.centery - cr.centery
                        dist = math.hypot(dx, dy)
                        if dist < magnet_range and dist > 1:
                            c.x += dx / dist * 5
                            c.y += dy / dist * 5 - speed

            # ── Collisions: coins
            for c in coins_list[:]:
                if not c.collected and player.rect.colliderect(c.rect):
                    c.collected = True
                    coins_collected += c.rect.width // 10  # 2 for normal, more for star
                    val = 5 if c.special else 1
                    coins_collected += val - 1
                    score += 10 * val
                    spawn_particles(c.rect.centerx, c.rect.centery, GOLD, 6)

            # ── Collisions: powerups
            for pu in powerups[:]:
                if not pu.collected and player.rect.colliderect(pu.rect):
                    pu.collected = True
                    powerup_active = pu.kind
                    powerup_timer = 300
                    spawn_particles(pu.rect.centerx, pu.rect.centery,
                                    pu.colors[pu.kind], 12, size=6)

            # ── Powerup countdown
            if powerup_timer > 0:
                powerup_timer -= 1
                if powerup_timer == 0:
                    powerup_active = None

            # ── Collisions: obstacles
            for obs in obstacles[:]:
                if player.invincible == 0 and player.rect.colliderect(obs.rect):
                    if powerup_active == "shield":
                        powerup_active = None
                        powerup_timer = 0
                        player.invincible = 90
                        spawn_particles(player.x, player.y - 30, CYAN, 15, size=7)
                        obstacles.remove(obs)
                    else:
                        lives -= 1
                        player.invincible = 90
                        spawn_particles(player.x, player.y - 30, RED, 12, size=7)
                        if lives <= 0:
                            game_over = True
                            hi_score = max(hi_score, score)

            # ── Score
            score += speed * 0.05

            # ── Update particles
            for p in particles[:]:
                p.update()
                if p.life <= 0:
                    particles.remove(p)

            # ── Draw
            bg.draw(screen)

            for obs in obstacles:
                obs.draw(screen)
            for c in coins_list:
                if not c.collected:
                    c.draw(screen)
            for pu in powerups:
                if not pu.collected:
                    pu.draw(screen)

            player.draw(screen)

            for p in particles:
                p.draw(screen)

            draw_hud(screen, score, coins_collected, lives,
                     powerup_active, powerup_timer, hi_score)

            pygame.display.flip()

        # back to start screen after game ends


if __name__ == "__main__":
    main()
