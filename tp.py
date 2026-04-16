"""
Slither de los papus

Controles:
  Jugador 1 : MOUSE (mover el cursor para dirigir) | Click izquierdo = TURBO
  Jugador 2 : W A S D | Doble W = TURBO
  Jugador 3 : Flechas | Doble ↑ = TURBO
  Jugador 4 : T F G H | Doble T = TURBO
  ESC / P   : Pausar
"""

import pygame, math, random, sys, json, os
from datetime import datetime

pygame.init()
try:    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except: pass

SW, SH = 1280, 720
screen = pygame.display.set_mode((SW, SH), pygame.RESIZABLE)
pygame.display.set_caption("Slither de los papus")
clock = pygame.time.Clock()
FPS   = 60

WORLD            = 3000
FOOD_COUNT       = 220
SPEED            = 2.8
SPEED_TURBO      = 5.2
TURN_SPEED       = 0.065
INITIAL_SEGMENTS = 12
RADIUS_BASE      = 9
RADIUS_MAX       = 22

# ── Turbo sistema ─────────────────────────────────────────────────────────────
TURBO_DURATION_SEC       = 3.0    # cuánto dura el turbo activo
TURBO_COOLDOWN_SEC       = 10.0   # cooldown tras usarlo
TURBO_DOUBLE_WINDOW      = 300    # ms para doble pulsación teclado
FOOD_COOLDOWN_REDUCE_SEC = 1.0    # segundos que reduce el cooldown al comer

SCORES_FILE = "resultados.json"

BG         = (5,  10, 14)
BORDER_COL = (255, 45, 120)
TEXT_COL   = (200, 255, 220)
DIVIDER    = (0, 255, 136)

# ── Paleta de colores disponibles ────────────────────────────────────────────
AVAILABLE_COLORS = [
    ("Verde",       (0, 255, 136),    (0, 160, 80)),
    ("Rosa",        (255, 105, 180),  (180, 50, 110)),
    ("Violeta",     (180, 80, 255),   (110, 30, 180)),
    ("Marrón",      (160, 100, 40),   (100, 60, 20)),
    ("Amarillo",    (255, 220, 0),    (180, 150, 0)),
    ("Azul",        (30, 80, 220),    (15, 40, 140)),
    ("Celeste",     (0, 200, 255),    (0, 130, 180)),
    ("Naranja",     (255, 140, 0),    (180, 90, 0)),
    ("Rojo",        (220, 30, 30),    (140, 10, 10)),
    ("Negro",       (60, 60, 60),     (30, 30, 30)),
    ("Militar",     (80, 110, 50),    (50, 70, 30)),
    ("🇫🇷 Francia",  (0, 85, 164),    (237, 41, 57)),
    ("🇦🇷 Argentina",(116, 185, 232),  (255, 255, 255)),
    ("🇵🇹 Portugal", (0, 102, 0),     (255, 0, 0)),
    ("🇧🇷 Brasil",   (0, 156, 59),    (255, 223, 0)),
    ("🇪🇸 España",   (170, 21, 27),   (241, 191, 0)),
    ("🇬🇧 Inglaterra",(255, 255, 255), (200, 16, 46)),
]

DEFAULT_COLOR_INDICES = [0, 6, 8, 4]

FOOD_COLORS = [
    (255,45,120),(0,255,136),(0,200,255),(255,220,0),(255,120,0),(180,80,255),
]

CONTROLS = [
    {"up":pygame.K_w,   "down":pygame.K_s,    "left":pygame.K_a,    "right":pygame.K_d    },
    {"up":pygame.K_UP,  "down":pygame.K_DOWN, "left":pygame.K_LEFT, "right":pygame.K_RIGHT},
    {"up":pygame.K_t,   "down":pygame.K_g,    "left":pygame.K_f,    "right":pygame.K_h    },
]
TURBO_KEYS = [pygame.K_w, pygame.K_UP, pygame.K_t]
CONTROLS_LABELS = ["MOUSE", "W A S D", "↑ ↓ ← →", "T F G H"]

try:
    FONT_BIG = pygame.font.SysFont("couriernew", 72, bold=True)
    FONT_MED = pygame.font.SysFont("couriernew", 36, bold=True)
    FONT_SM  = pygame.font.SysFont("couriernew", 22)
    FONT_XS  = pygame.font.SysFont("couriernew", 16)
except:
    FONT_BIG = FONT_MED = FONT_SM = FONT_XS = pygame.font.SysFont(None, 36)

# ── Audio ─────────────────────────────────────────────────────────────────────
def gen_tone(freq, duration_ms, vol=0.3, wave="sine"):
    sr = 44100; n = int(sr * duration_ms / 1000); buf = bytearray(n * 2)
    for i in range(n):
        t = i / sr
        v = math.sin(2*math.pi*freq*t) if wave=="sine" \
            else (1.0 if math.sin(2*math.pi*freq*t)>0 else -1.0)
        fade   = min(1.0,(n-i)/max(1,sr*0.05))
        sample = max(-32768,min(32767,int(v*vol*fade*32767)))
        buf[i*2]=sample&0xFF; buf[i*2+1]=(sample>>8)&0xFF
    return pygame.mixer.Sound(bytes(buf))

SFX_EAT=SFX_DIE=SFX_START=None; SOUND_OK=False
try:
    SFX_EAT=gen_tone(660,80,0.20,"sine"); SFX_DIE=gen_tone(180,400,0.30,"square")
    SFX_START=gen_tone(440,150,0.18,"sine"); SOUND_OK=True
except: pass

def play(sfx):
    if SOUND_OK and sfx:
        try: sfx.play()
        except: pass

# ── Guardar resultados ────────────────────────────────────────────────────────
def save_results(snakes):
    data = []
    if os.path.exists(SCORES_FILE):
        try:
            with open(SCORES_FILE,"r") as f: data = json.load(f)
        except: data = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session = {
        "fecha": now,
        "resultados": sorted([
            {"jugador": sn.color["name"],
             "tipo": "IA" if sn.is_ai else "Humano",
             "score": sn.score,
             "longitud": sn.length // 4,
             "vivo": sn.alive}
            for sn in snakes
        ], key=lambda x: x["score"], reverse=True)
    }
    data.append(session)
    with open(SCORES_FILE,"w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
#  SERPIENTE
# ══════════════════════════════════════════════════════════════════════════════
class Snake:
    def __init__(self, idx, is_ai, x, y, angle, custom_name=None, color_entry=None):
        self.idx          = idx
        self.is_ai        = is_ai
        self.alive        = True
        self.score        = 0
        self.angle        = angle
        self.target_angle = angle
        self.ai_timer     = 0
        self.ai_wander_angle = angle
        self.ai_wander_timer = 0
        self.ai_stuck_timer  = 0
        self.ai_last_pos     = [x, y]

        # ── Sistema de turbo ──────────────────────────────────────────────────
        self.turbo               = False
        self._turbo_timer        = 0.0   # segundos restantes de turbo activo
        self._turbo_cooldown     = 0.0   # segundos restantes de cooldown
        # Doble-pulsación teclado
        self._last_turbo_key_time = 0
        # Mouse: click izquierdo
        self._mouse_turbo_held    = False

        if color_entry:
            cname, chead, cbody = color_entry
        else:
            i = idx % len(AVAILABLE_COLORS)
            cname, chead, cbody = AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[i]]

        self.color = {
            "head": chead,
            "body": cbody,
            "name": custom_name if custom_name else f"Jugador {idx+1}"
        }

        seg_gap = RADIUS_BASE * 2.2
        self.segments = [
            [x - math.cos(angle)*i*seg_gap,
             y - math.sin(angle)*i*seg_gap]
            for i in range(INITIAL_SEGMENTS)
        ]

        self.use_mouse = (idx == 0 and not is_ai)

    @property
    def head(self):
        if not self.segments:
            return [0.0, 0.0]
        return self.segments[0]

    @property
    def length(self): return len(self.segments)

    @property
    def radius(self):
        return min(RADIUS_MAX, RADIUS_BASE + self.score * 0.22)

    def current_speed(self):
        return SPEED_TURBO if self.turbo else SPEED

    # ── Estado del turbo ──────────────────────────────────────────────────────
    @property
    def turbo_ready(self):
        return self._turbo_cooldown <= 0 and not self.turbo

    @property
    def turbo_cooldown_pct(self):
        return min(1.0, self._turbo_cooldown / TURBO_COOLDOWN_SEC)

    @property
    def turbo_remaining_pct(self):
        return min(1.0, self._turbo_timer / TURBO_DURATION_SEC)

    def _activate_turbo(self):
        if not self.turbo_ready:
            return
        self.turbo        = True
        self._turbo_timer = TURBO_DURATION_SEC

    # ── Activación por teclado (doble pulsación) ──────────────────────────────
    def try_activate_turbo_key(self, now_ms):
        dt = now_ms - self._last_turbo_key_time
        if dt < TURBO_DOUBLE_WINDOW:
            self._activate_turbo()
        self._last_turbo_key_time = now_ms

    # ── Turbo mouse: click izquierdo ──────────────────────────────────────────
    def press_turbo_mouse(self):
        self._activate_turbo()

    # ── Reducir cooldown al comer ─────────────────────────────────────────────
    def on_eat(self):
        self._turbo_cooldown = max(0.0, self._turbo_cooldown - FOOD_COOLDOWN_REDUCE_SEC)

    # ─────────────────────────────────────────────────────────────────────────
    def update(self, keys, snakes, food_list, cam_x, cam_y, viewport):
        if not self.alive: return

        dt = 1.0 / FPS  # delta time en segundos

        # ── Actualizar timer de turbo activo ──────────────────────────────────
        if self.turbo:
            self._turbo_timer -= dt
            if self._turbo_timer <= 0:
                self.turbo           = False
                self._turbo_timer    = 0.0
                self._turbo_cooldown = TURBO_COOLDOWN_SEC  # empieza cooldown

        # ── Actualizar cooldown ───────────────────────────────────────────────
        if not self.turbo and self._turbo_cooldown > 0:
            self._turbo_cooldown = max(0.0, self._turbo_cooldown - dt)

        if self.is_ai:
            self._ai_decide(snakes, food_list)
            # IA activa turbo automáticamente si puede (raramente)
            if self.turbo_ready and random.random() < 0.005:
                self._activate_turbo()
        elif self.use_mouse:
            self._mouse_control(cam_x, cam_y, viewport)
        else:
            ctrl_idx = self.idx - 1
            if 0 <= ctrl_idx < len(CONTROLS):
                self._human_control(keys, ctrl_idx)

        da = self.target_angle - self.angle
        while da >  math.pi: da -= 2*math.pi
        while da < -math.pi: da += 2*math.pi
        self.angle += math.copysign(min(abs(da), TURN_SPEED), da)

        spd = self.current_speed()
        nx = self.head[0] + math.cos(self.angle) * spd
        ny = self.head[1] + math.sin(self.angle) * spd
        self.segments.insert(0, [nx, ny])

        # Recortar siempre al largo objetivo — turbo o no.
        # El turbo solo cambia la velocidad, nunca la longitud.
        target_len = INITIAL_SEGMENTS + self.score * 4
        while len(self.segments) > target_len:
            self.segments.pop()

    def _mouse_control(self, cam_x, cam_y, viewport):
        mx, my = pygame.mouse.get_pos()
        if viewport:
            vw, vh = viewport.width, viewport.height
            rel_x = mx - viewport.x
            rel_y = my - viewport.y
            world_mx = cam_x + (rel_x - vw / 2)
            world_my = cam_y + (rel_y - vh / 2)
        else:
            sw, sh = screen.get_size()
            world_mx = cam_x + (mx - sw / 2)
            world_my = cam_y + (my - sh / 2)

        hx, hy = self.head
        dx = world_mx - hx
        dy = world_my - hy
        if abs(dx) > 2 or abs(dy) > 2:
            self.target_angle = math.atan2(dy, dx)

    def _human_control(self, keys, ctrl_idx):
        ctrl  = CONTROLS[ctrl_idx]
        up    = keys[ctrl["up"]];   down = keys[ctrl["down"]]
        left  = keys[ctrl["left"]]; right= keys[ctrl["right"]]
        if   up   and right: self.target_angle = -math.pi/4
        elif up   and left:  self.target_angle = -3*math.pi/4
        elif down and right: self.target_angle =  math.pi/4
        elif down and left:  self.target_angle =  3*math.pi/4
        elif up:             self.target_angle = -math.pi/2
        elif down:           self.target_angle =  math.pi/2
        elif left:           self.target_angle =  math.pi
        elif right:          self.target_angle =  0.0

    def _ai_decide(self, snakes, food_list):
        hx, hy = self.head
        margin = 200

        near_border = False
        if   hx < margin:         self.target_angle = 0.0;           near_border = True
        elif hx > WORLD-margin:   self.target_angle = math.pi;       near_border = True
        elif hy < margin:         self.target_angle = math.pi/2;     near_border = True
        elif hy > WORLD-margin:   self.target_angle = -math.pi/2;    near_border = True
        if near_border:
            self.ai_stuck_timer = 0
            return

        danger_angle = None
        min_danger   = float("inf")
        for s in snakes:
            if s is self or not s.alive: continue
            for seg in [s.head] + s.segments[1:min(15, len(s.segments))]:
                d = math.hypot(hx-seg[0], hy-seg[1])
                if d < 180 and d < min_danger:
                    min_danger   = d
                    danger_angle = math.atan2(hy-seg[1], hx-seg[0])
        if danger_angle is not None:
            self.target_angle    = danger_angle
            self.ai_stuck_timer  = 0
            self.ai_wander_timer = 0
            return

        self.ai_stuck_timer += 1
        if self.ai_stuck_timer >= 90:
            dx = hx - self.ai_last_pos[0]
            dy = hy - self.ai_last_pos[1]
            if math.hypot(dx, dy) < SPEED * 15:
                self.ai_wander_angle = self.angle + random.choice([-1,1]) * random.uniform(math.pi/2, math.pi*0.8)
                self.ai_wander_timer = random.randint(40, 80)
            self.ai_last_pos   = [hx, hy]
            self.ai_stuck_timer = 0

        if self.ai_wander_timer > 0:
            self.target_angle    = self.ai_wander_angle
            self.ai_wander_timer -= 1
            return

        self.ai_timer -= 1
        if self.ai_timer <= 0:
            best, best_d = None, float("inf")
            for f in food_list:
                d = math.hypot(hx-f["x"], hy-f["y"])
                if d < best_d: best_d, best = d, f
            if best:
                self.target_angle = math.atan2(best["y"]-hy, best["x"]-hx)
            self.ai_timer = random.randint(6, 14)

    def draw(self, surf, cam_x, cam_y):
        if not self.alive or not self.segments: return
        sw, sh = surf.get_size()
        head_c = self.color["head"]
        body_c = self.color["body"]
        if self.turbo:
            t_flash = (pygame.time.get_ticks() // 80) % 2
            head_c = (255, 255, 100) if t_flash else self.color["head"]
        r_head = max(5, int(self.radius))
        n      = len(self.segments)
        for i in range(n-1, -1, -1):
            seg = self.segments[i]
            sx  = int(seg[0]-cam_x+sw/2)
            sy  = int(seg[1]-cam_y+sh/2)
            if sx<-20 or sx>sw+20 or sy<-20 or sy>sh+20: continue
            t = i / max(n-1,1)
            r = max(3, int(r_head*(0.55+0.45*(1-t))))
            pygame.draw.circle(surf, head_c if i==0 else body_c, (sx,sy), r)
            if i==0:
                for eo in (-0.45, 0.45):
                    ea = self.angle+eo
                    ex = int(sx+math.cos(ea)*r_head*0.55)
                    ey = int(sy+math.sin(ea)*r_head*0.55)
                    pygame.draw.circle(surf,(0,0,0),      (ex,ey),max(2,int(r_head*0.28)))
                    pygame.draw.circle(surf,(255,255,255),(ex,ey),max(1,int(r_head*0.14)))
        if self.segments:
            sx = int(self.segments[0][0]-cam_x+sw/2)
            sy = int(self.segments[0][1]-cam_y+sh/2)
            label = self.color["name"]
            if self.turbo:
                label += " ⚡"
            elif self._turbo_cooldown > 0:
                label += f" [{self._turbo_cooldown:.1f}s]"
            name_surf = FONT_XS.render(label, True, head_c)
            surf.blit(name_surf, (sx - name_surf.get_width()//2, sy - r_head - 18))


# ══════════════════════════════════════════════════════════════════════════════
#  PARTÍCULAS
# ══════════════════════════════════════════════════════════════════════════════
class Particle:
    def __init__(self,x,y,color):
        a=random.uniform(0,2*math.pi); sp=random.uniform(1.5,4.0)
        self.x=x; self.y=y; self.vx=math.cos(a)*sp; self.vy=math.sin(a)*sp
        self.life=1.0; self.color=color; self.r=random.uniform(2,5)
    def update(self):
        self.x+=self.vx; self.y+=self.vy
        self.vx*=0.92;   self.vy*=0.92; self.life-=0.025
    def draw(self,surf,cam_x,cam_y):
        if self.life<=0: return
        sw,sh=surf.get_size()
        sx=int(self.x-cam_x+sw/2); sy=int(self.y-cam_y+sh/2)
        r=max(1,int(self.r*self.life))
        s=pygame.Surface((r*2,r*2),pygame.SRCALPHA)
        pygame.draw.circle(s,(*self.color,int(self.life*255)),(r,r),r)
        surf.blit(s,(sx-r,sy-r))


# ── Helpers ───────────────────────────────────────────────────────────────────
def spawn_food(n=1):
    return [{"x":random.uniform(60,WORLD-60),"y":random.uniform(60,WORLD-60),
             "r":random.uniform(5,9),"color":random.choice(FOOD_COLORS),
             "pulse":random.uniform(0,math.pi*2),"value":1} for _ in range(n)]

def dist(ax,ay,bx,by): return math.hypot(ax-bx,ay-by)
def spawn_particles(x,y,color,n=14): return [Particle(x,y,color) for _ in range(n)]
def draw_text_centered(surf,text,font,color,cx,cy):
    s=font.render(text,True,color); surf.blit(s,(cx-s.get_width()//2,cy-s.get_height()//2))
def draw_text(surf,text,font,color,x,y):
    surf.blit(font.render(text,True,color),(x,y))


# ── Viewports ──────────────────────────────────────────────────────────────────
def get_viewports(num_players, sw, sh):
    if num_players==1:
        return [pygame.Rect(0,0,sw,sh)]
    elif num_players==2:
        hw=sw//2
        return [pygame.Rect(0,0,hw,sh), pygame.Rect(hw,0,sw-hw,sh)]
    elif num_players==3:
        hw=sw//2; hh=sh//2
        return [
            pygame.Rect(0,   0,  hw,    hh),
            pygame.Rect(hw,  0,  sw-hw, hh),
            pygame.Rect(sw//4, hh, sw//2, sh-hh),
        ]
    else:
        hw=sw//2; hh=sh//2
        return [
            pygame.Rect(0, 0,  hw,    hh),
            pygame.Rect(hw,0,  sw-hw, hh),
            pygame.Rect(0, hh, hw,    sh-hh),
            pygame.Rect(hw,hh, sw-hw, sh-hh),
        ]

def get_divider_lines(num_players, sw, sh):
    if num_players == 1:
        return []
    elif num_players == 2:
        return [((sw//2,0),(sw//2,sh))]
    elif num_players == 3:
        hh = sh//2
        return [
            ((sw//2, 0),       (sw//2, hh)),
            ((sw//4, hh),      (3*sw//4, hh)),
            ((sw//4, hh),      (sw//4,  sh)),
            ((3*sw//4, hh),    (3*sw//4, sh)),
        ]
    else:
        hw=sw//2; hh=sh//2
        return [
            ((hw,0),(hw,sh)),
            ((0,hh),(sw,hh)),
        ]


# ── Barra de turbo ────────────────────────────────────────────────────────────
def draw_turbo_bar(surf, sn, x, y, w=180, h=10):
    pygame.draw.rect(surf, (0,15,8), (x, y, w, h), border_radius=4)

    if sn.turbo:
        pct = sn.turbo_remaining_pct
        fill_w = int(w * pct)
        if fill_w > 0:
            pygame.draw.rect(surf, (255, 220, 0), (x, y, fill_w, h), border_radius=4)
        label = FONT_XS.render(f"TURBO {sn._turbo_timer:.1f}s", True, (255, 220, 0))
        surf.blit(label, (x, y - 14))
    elif sn._turbo_cooldown > 0:
        pct = 1.0 - sn.turbo_cooldown_pct
        fill_w = int(w * pct)
        col = (200, 60, 60) if pct < 0.5 else (230, 130, 0)
        if fill_w > 0:
            pygame.draw.rect(surf, col, (x, y, fill_w, h), border_radius=4)
        label = FONT_XS.render(f"CD {sn._turbo_cooldown:.1f}s", True, col)
        surf.blit(label, (x, y - 14))
    else:
        pygame.draw.rect(surf, (0, 200, 80), (x, y, w, h), border_radius=4)
        label = FONT_XS.render("TURBO LISTO!", True, (0, 220, 80))
        surf.blit(label, (x, y - 14))

    pygame.draw.rect(surf, (0, 80, 40), (x, y, w, h), 1, border_radius=4)


# ── Render de un viewport ─────────────────────────────────────────────────────
def render_viewport(surf, vp, cam_x, cam_y, snakes, food_list, particles, owner):
    vw,vh=vp.width,vp.height
    sub=pygame.Surface((vw,vh)); sub.fill(BG)

    ox=int((-cam_x+vw/2)%40); oy=int((-cam_y+vh/2)%40)
    for x in range(ox,vw,40): pygame.draw.line(sub,(0,22,11),(x,0),(x,vh))
    for y in range(oy,vh,40): pygame.draw.line(sub,(0,22,11),(0,y),(vw,y))

    bx=int(-cam_x+vw/2); by=int(-cam_y+vh/2)
    pygame.draw.rect(sub,BORDER_COL,(bx,by,WORLD,WORLD),4)

    for f in food_list:
        sx=int(f["x"]-cam_x+vw/2); sy=int(f["y"]-cam_y+vh/2)
        if -20<sx<vw+20 and -20<sy<vh+20:
            r=max(2,int(f["r"]+math.sin(f.get("pulse",0))*1.5))
            pygame.draw.circle(sub,f["color"],(sx,sy),r)

    for sn in snakes: sn.draw(sub,cam_x,cam_y)
    for p  in particles: p.draw(sub,cam_x,cam_y)

    col   = owner.color["head"] if owner.alive else (80,80,80)
    label = owner.color["name"]+(" [MUERTO]" if not owner.alive else "")
    if owner.alive and owner.turbo:
        label += " ⚡TURBO"
    pygame.draw.rect(sub,(2,5,7),(4,4,220,70),border_radius=6)
    pygame.draw.rect(sub,col,   (4,4,220,70),1,border_radius=6)
    draw_text(sub,label,                    FONT_XS,col,12,10)
    draw_text(sub,"Score: "+str(owner.score),FONT_SM,col,12,28)

    if owner.alive:
        draw_turbo_bar(sub, owner, 12, 64, w=180, h=8)

    draw_minimap_in(sub,snakes,food_list,vw,vh)

    if owner.use_mouse and owner.alive:
        mx, my = pygame.mouse.get_pos()
        rel_x = mx - vp.x
        rel_y = my - vp.y
        if 0 <= rel_x < vw and 0 <= rel_y < vh:
            c = (255, 255, 100) if owner.turbo else owner.color["head"]
            pygame.draw.circle(sub, c, (rel_x, rel_y), 6, 2)
            pygame.draw.line(sub, c, (rel_x-10, rel_y), (rel_x+10, rel_y), 1)
            pygame.draw.line(sub, c, (rel_x, rel_y-10), (rel_x, rel_y+10), 1)

    surf.blit(sub,(vp.x,vp.y))


def draw_minimap_in(surf,snakes,food_list,vw,vh):
    mw=mh=min(110,vw//4,vh//4)
    if mw<40: return
    mx=vw-mw-8; my=vh-mh-8; scale=mw/WORLD
    s=pygame.Surface((mw,mh),pygame.SRCALPHA)
    s.fill((2,5,7,170)); pygame.draw.rect(s,(0,200,80,80),(0,0,mw,mh),1)
    for f in food_list:
        fx,fy=int(f["x"]*scale),int(f["y"]*scale)
        if 0<=fx<mw and 0<=fy<mh:
            pygame.draw.rect(s,f["color"],(fx-1,fy-1,2,2))
    for sn in snakes:
        if not sn.alive or not sn.segments: continue
        hx=int(sn.head[0]*scale); hy=int(sn.head[1]*scale)
        if 0<=hx<mw and 0<=hy<mh:
            pygame.draw.circle(s,(255,255,255),(hx,hy),4)
            pygame.draw.circle(s,sn.color["head"],(hx,hy),3)
    surf.blit(s,(mx,my))


def draw_live_scoreboard(surf, snakes):
    sw, sh = surf.get_size()
    sorted_s = sorted(snakes, key=lambda s: s.score, reverse=True)
    n     = len(sorted_s)
    row_h = 26
    pad   = 10
    w     = 220
    h     = pad*2 + 20 + n*row_h
    x     = sw - w - 10
    y     = 10

    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((2, 5, 7, 190))
    pygame.draw.rect(panel, (0, 180, 80, 120), (0, 0, w, h), 1, border_radius=6)

    title = FONT_XS.render("PUNTAJES", True, (0, 200, 80))
    panel.blit(title, (w//2 - title.get_width()//2, pad - 2))

    for i, sn in enumerate(sorted_s):
        ry   = pad + 20 + i * row_h
        col  = sn.color["head"] if sn.alive else (80, 80, 80)
        mark = " ✖" if not sn.alive else (" ⚡" if sn.turbo else "")
        pygame.draw.rect(panel, (*col, 30), (4, ry, w-8, row_h-2), border_radius=3)
        name_s  = FONT_XS.render(sn.color["name"] + mark, True, col)
        score_s = FONT_XS.render(str(sn.score), True, col)
        panel.blit(name_s,  (8,        ry + 5))
        panel.blit(score_s, (w - score_s.get_width() - 8, ry + 5))

    surf.blit(panel, (x, y))


def kill_snake(sn, food_list, particles):
    if not sn.alive: return
    sn.alive = False
    sn.turbo = False
    play(SFX_DIE)
    hx = sn.segments[0][0] if sn.segments else 0
    hy = sn.segments[0][1] if sn.segments else 0
    for i in range(0, len(sn.segments), 4):
        seg = sn.segments[i]
        food_list.append({"x": seg[0], "y": seg[1],
                          "r": random.uniform(6, 10), "color": sn.color["head"],
                          "pulse": 0, "value": 2})
    sn.segments = []
    particles += spawn_particles(hx, hy, sn.color["head"], 20)


# ══════════════════════════════════════════════════════════════════════════════
#  JUEGO
# ══════════════════════════════════════════════════════════════════════════════
def run_game(num_humans, use_ai, player_names, player_colors):
    starts=[
        (400,       400,        0.0    ),
        (WORLD-400, WORLD-400,  math.pi),
        (WORLD-400, 400,        math.pi),
        (400,       WORLD-400,  0.0    ),
    ]
    snakes=[]; idx=0
    for i in range(num_humans):
        x,y,a=starts[idx]
        name = player_names[i] if i < len(player_names) else None
        col  = player_colors[i] if i < len(player_colors) else None
        snakes.append(Snake(idx, False, x, y, a, name, col))
        idx+=1
    if use_ai:
        while idx<4:
            x,y,a=starts[idx]
            ai_col = AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[idx % len(DEFAULT_COLOR_INDICES)]]
            snakes.append(Snake(idx, True, x, y, a, "BOT "+str(idx+1), ai_col))
            idx+=1

    food_list=spawn_food(FOOD_COUNT); particles=[]
    humans=[sn for sn in snakes if not sn.is_ai]
    cams=[[sn.head[0], sn.head[1]] for sn in humans]
    paused=False; play(SFX_START)

    pygame.mouse.set_visible(False)

    human_cam_index = {sn: i for i, sn in enumerate(humans)}

    GRACE_FRAMES = 90
    frame = 0

    while True:
        sw,sh=screen.get_size(); keys=pygame.key.get_pressed()
        now_ms = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                pygame.mouse.set_visible(True)
                return "quit"
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE,pygame.K_p):
                    paused=not paused
                for sn in humans:
                    if sn.use_mouse: continue
                    ctrl_idx = sn.idx - 1
                    if 0 <= ctrl_idx < len(TURBO_KEYS):
                        if event.key == TURBO_KEYS[ctrl_idx]:
                            sn.try_activate_turbo_key(now_ms)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for sn in humans:
                        if sn.use_mouse and sn.alive:
                            sn.press_turbo_mouse()

        if paused:
            screen.fill(BG)
            draw_text_centered(screen,"PAUSA",FONT_BIG,(255,220,0),sw//2,sh//2)
            pygame.display.flip(); clock.tick(FPS); continue

        vps=get_viewports(num_humans,sw,sh)

        for sn in snakes:
            if sn.is_ai:
                cam_x = sn.segments[0][0] if sn.segments else 0
                cam_y = sn.segments[0][1] if sn.segments else 0
                vp = None
            else:
                ci = human_cam_index[sn]
                cam_x, cam_y = cams[ci]
                vp = vps[ci] if ci < len(vps) else None
            sn.update(keys, snakes, food_list, cam_x, cam_y, vp)

        for sn in snakes:
            if not sn.alive or not sn.segments: continue
            hx,hy=sn.head; i=len(food_list)-1
            while i>=0:
                f=food_list[i]
                if dist(hx,hy,f["x"],f["y"])<sn.radius+f["r"]:
                    sn.score+=f["value"]
                    sn.on_eat()
                    particles+=spawn_particles(f["x"],f["y"],f["color"],5)
                    food_list.pop(i); play(SFX_EAT)
                    if len(food_list)<FOOD_COUNT: food_list+=spawn_food(1)
                i-=1

        for sn in snakes:
            if not sn.alive or not sn.segments: continue
            hx,hy=sn.head
            if hx<0 or hx>WORLD or hy<0 or hy>WORLD:
                kill_snake(sn,food_list,particles); continue

            if frame < GRACE_FRAMES:
                continue

            for other in snakes:
                if not other.alive or not other.segments: continue
                if other is sn:
                    skip = max(20, int(sn.radius * 2.5))
                else:
                    skip = 0

                hit = False
                for seg in other.segments[skip:]:
                    if dist(hx,hy,seg[0],seg[1]) < sn.radius + other.radius * 0.75:
                        kill_snake(sn,food_list,particles)
                        if other is not sn and other.alive:
                            other.score += max(1, sn.length//8)
                        hit = True; break
                if hit or not sn.alive: break

        frame += 1

        for f in food_list: f["pulse"]=f.get("pulse",0)+0.07
        for p in particles: p.update()
        particles=[p for p in particles if p.life>0]

        for sn in humans:
            ci = human_cam_index[sn]
            if sn.alive and sn.segments:
                tx, ty = sn.head
            else:
                tx, ty = cams[ci]
            cams[ci][0]+=(tx-cams[ci][0])*0.08
            cams[ci][1]+=(ty-cams[ci][1])*0.08

        screen.fill((0,0,0))
        for sn in humans:
            ci = human_cam_index[sn]
            vp = vps[ci] if ci < len(vps) else None
            if vp:
                render_viewport(screen, vp, cams[ci][0], cams[ci][1],
                                snakes, food_list, particles, sn)

        for (p1,p2) in get_divider_lines(num_humans,sw,sh):
            pygame.draw.line(screen,DIVIDER,p1,p2,2)

        draw_live_scoreboard(screen, snakes)
        pygame.display.flip(); clock.tick(FPS)

        alive_h  =[sn for sn in snakes if not sn.is_ai and sn.alive]
        alive_all=[sn for sn in snakes if sn.alive]
        if len(alive_h)==0 or len(alive_all)<=1:
            pygame.time.wait(800)
            pygame.mouse.set_visible(True)
            return snakes

    pygame.mouse.set_visible(True)
    return snakes


# ══════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def menu_screen():
    num_humans=1; use_ai=True
    while True:
        sw,sh=screen.get_size(); screen.fill(BG)
        for x in range(0,sw,40): pygame.draw.line(screen,(0,22,11),(x,0),(x,sh))
        for y in range(0,sh,40): pygame.draw.line(screen,(0,22,11),(0,y),(sw,y))
        draw_text_centered(screen,"SLITHER DE LOS PAPUS",FONT_BIG,(0,255,136),sw//2,sh//4)
        draw_text_centered(screen,"JUGADORES HUMANOS",FONT_SM,(0,200,100),sw//2,sh//2-80)
        btn_rects=[]; bx0=sw//2-(4*70+3*10)//2
        for i in range(1,5):
            r=pygame.Rect(bx0+(i-1)*80,sh//2-50,70,50); btn_rects.append(r)
            col=(0,255,136) if i==num_humans else (0,60,30)
            pygame.draw.rect(screen,col,r,border_radius=8)
            pygame.draw.rect(screen,(0,180,70),r,2,border_radius=8)
            draw_text_centered(screen,str(i),FONT_MED,
                               (2,5,2) if i==num_humans else (0,160,60),r.centerx,r.centery)
        ai_rect=pygame.Rect(sw//2-120,sh//2+20,240,44)
        ai_color=(0,255,136) if use_ai else (60,60,60)
        pygame.draw.rect(screen,(0,30,15),ai_rect,border_radius=8)
        pygame.draw.rect(screen,ai_color,ai_rect,2,border_radius=8)
        draw_text_centered(screen,"BOTS IA: "+("ON" if use_ai else "OFF"),
                           FONT_SM,ai_color,sw//2,sh//2+42)

        ctrl_info = [
            ("J1", "MOUSE  [click=TURBO]",  AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[0]][1]),
            ("J2", "W A S D  [doble W]",    AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[1]][1]),
            ("J3", "↑ ↓ ← →  [doble ↑]",   AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[2]][1]),
            ("J4", "T F G H  [doble T]",    AVAILABLE_COLORS[DEFAULT_COLOR_INDICES[3]][1]),
        ]
        draw_text_centered(screen,
            "TURBO: 3s de velocidad extra  |  10s cooldown  |  comer reduce el cooldown",
            FONT_XS, (0,150,80), sw//2, sh//2+78)

        cy0=sh//2+100; cx0_c=sw//2-(4*190+3*12)//2
        for i,(jid,ks,col) in enumerate(ctrl_info):
            rx=cx0_c+i*202
            pygame.draw.rect(screen,(0,15,8),(rx,cy0,190,52),border_radius=6)
            pygame.draw.rect(screen,(*col,120),(rx,cy0,190,52),1,border_radius=6)
            draw_text(screen,jid,FONT_XS,col,rx+10,cy0+6)
            draw_text(screen,ks, FONT_XS,TEXT_COL,rx+10,cy0+26)

        start_rect=pygame.Rect(sw//2-120,sh-110,240,56)
        pygame.draw.rect(screen,(0,200,80),start_rect,border_radius=10)
        draw_text_centered(screen,"INICIAR JUEGO",FONT_MED,(2,5,2),sw//2,sh-82)
        draw_text_centered(screen,"ESC / P para pausar",FONT_XS,(0,100,50),sw//2,sh-40)
        pygame.display.flip(); clock.tick(FPS)
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return None
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                for i,r in enumerate(btn_rects):
                    if r.collidepoint(event.pos): num_humans=i+1
                if ai_rect.collidepoint(event.pos):    use_ai=not use_ai
                if start_rect.collidepoint(event.pos): return num_humans,use_ai
            if event.type==pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN,pygame.K_SPACE): return num_humans,use_ai
                if event.key==pygame.K_ESCAPE: return None


# ══════════════════════════════════════════════════════════════════════════════
#  SELECTOR DE COLOR
# ══════════════════════════════════════════════════════════════════════════════
def draw_color_picker(surf, x, y, current_idx, player_idx, selected_by_others):
    cols_per_row = 9
    btn_size = 28
    gap = 6
    rects = []

    for ci, (cname, chead, cbody) in enumerate(AVAILABLE_COLORS):
        col_in_row = ci % cols_per_row
        row        = ci // cols_per_row
        bx = x + col_in_row * (btn_size + gap)
        by = y + row        * (btn_size + gap)
        rect = pygame.Rect(bx, by, btn_size, btn_size)
        rects.append(rect)

        pygame.draw.rect(surf, (0,15,8), rect, border_radius=5)
        pygame.draw.circle(surf, chead,  (bx + btn_size//2, by + btn_size//3), btn_size//2 - 2)
        pygame.draw.circle(surf, cbody,  (bx + btn_size//2, by + 2*btn_size//3), btn_size//2 - 2)

        if ci == current_idx:
            pygame.draw.rect(surf, AVAILABLE_COLORS[ci][1], rect, 3, border_radius=5)
        elif ci in selected_by_others:
            pygame.draw.line(surf, (60,0,0), (bx+4,by+4), (bx+btn_size-4, by+btn_size-4), 2)
            pygame.draw.line(surf, (60,0,0), (bx+btn_size-4,by+4), (bx+4, by+btn_size-4), 2)
            dark = pygame.Surface((btn_size, btn_size), pygame.SRCALPHA)
            dark.fill((0,0,0,140))
            surf.blit(dark, (bx, by))
        else:
            pygame.draw.rect(surf, (0,50,25), rect, 1, border_radius=5)

    return rects


# ══════════════════════════════════════════════════════════════════════════════
#  PANTALLA DE NICKNAMES + COLOR
# ══════════════════════════════════════════════════════════════════════════════
def nickname_screen(num_humans):
    names        = [""] * num_humans
    active_idx   = 0
    errors       = [""] * num_humans
    cursor_timer = 0
    color_indices = list(DEFAULT_COLOR_INDICES[:num_humans])
    used = set()
    for i in range(num_humans):
        if color_indices[i] in used:
            for ci in range(len(AVAILABLE_COLORS)):
                if ci not in used:
                    color_indices[i] = ci
                    break
        used.add(color_indices[i])

    defaults = [f"Jugador{i+1}" for i in range(num_humans)]

    def is_valid_char(c):
        return c.isalnum()

    def validate(name):
        if len(name) < 3:  return "Mínimo 3 caracteres"
        if len(name) > 15: return "Máximo 15 caracteres"
        return ""

    use_grid = (num_humans >= 3)

    while True:
        sw, sh = screen.get_size()
        screen.fill(BG)
        for x in range(0, sw, 40): pygame.draw.line(screen, (0,22,11), (x,0), (x,sh))
        for y in range(0, sh, 40): pygame.draw.line(screen, (0,22,11), (0,y), (sw,y))

        draw_text_centered(screen, "NOMBRE Y COLOR", FONT_BIG, (0,255,136), sw//2, 48)
        draw_text_centered(screen, "Solo letras y números  |  3 a 15 caracteres",
                           FONT_XS, (0,150,80), sw//2, 92)

        cursor_timer += 1
        show_cursor = (cursor_timer // 30) % 2 == 0

        selected_by_others_map = {}
        for i in range(num_humans):
            for j in range(num_humans):
                if j != i:
                    selected_by_others_map.setdefault(i, set()).add(color_indices[j])

        field_rects     = []
        all_color_rects = []

        if use_grid:
            top_margin = 110
            bot_margin = 80
            available_h = sh - top_margin - bot_margin
            cell_w = sw // 2 - 20
            cell_h = available_h // 2

            for i in range(num_humans):
                col_grid = i % 2
                row_grid = i // 2
                cx = 10 + col_grid * (sw // 2)
                cy = top_margin + row_grid * cell_h

                col    = AVAILABLE_COLORS[color_indices[i]][1]
                active = (i == active_idx)

                ctrl_label = CONTROLS_LABELS[i]
                label = f"J{i+1}  [{ctrl_label}]"
                draw_text(screen, label, FONT_XS, col, cx + 8, cy + 6)

                box = pygame.Rect(cx + 8, cy + 24, min(260, cell_w - 80), 32)
                field_rects.append(box)
                bg_col  = (0, 40, 20) if active else (0, 15, 8)
                brd_col = col         if active else (0, 60, 30)
                pygame.draw.rect(screen, bg_col,  box, border_radius=6)
                pygame.draw.rect(screen, brd_col, box, 2, border_radius=6)

                cursor_str = "|" if (active and show_cursor) else ""
                text_surf  = FONT_SM.render((names[i] or "") + cursor_str,
                                            True, col if active else (0,160,70))
                screen.blit(text_surf, (box.x + 8, box.y + 5))
                if not names[i] and not active:
                    ph = FONT_SM.render(defaults[i], True, (0, 60, 30))
                    screen.blit(ph, (box.x + 8, box.y + 5))
                if errors[i]:
                    err_surf = FONT_XS.render(errors[i], True, (255, 80, 80))
                    screen.blit(err_surf, (box.x, box.y + 34))

                cname_txt, chead, cbody = AVAILABLE_COLORS[color_indices[i]]
                px_start = cx + 8
                py_center = cy + 70
                for si in range(6):
                    px = px_start + si * 12
                    r  = max(3, 8 - si)
                    pygame.draw.circle(screen, chead if si==0 else cbody, (px, py_center), r)
                cname_surf = FONT_XS.render(cname_txt, True, chead)
                screen.blit(cname_surf, (px_start + 78, cy + 63))

                picker_y = cy + 82
                picker_label = FONT_XS.render("Color:", True, (0,160,70))
                screen.blit(picker_label, (cx + 8, picker_y))
                crects = draw_color_picker(screen, cx + 56, picker_y,
                                           color_indices[i], i,
                                           selected_by_others_map.get(i, set()))
                all_color_rects.append(crects)

                if active:
                    pygame.draw.rect(screen, (*col, 60), (cx+2, cy+2, sw//2-4, cell_h-4), 1, border_radius=4)

            mid_x = sw // 2
            mid_y = top_margin + cell_h
            pygame.draw.line(screen, (0,60,30), (mid_x, top_margin), (mid_x, sh - bot_margin), 1)
            if num_humans >= 3:
                pygame.draw.line(screen, (0,60,30), (0, mid_y), (sw, mid_y), 1)

        else:
            FIELD_H   = 42
            PICKER_H  = 68
            SECTION_H = FIELD_H + PICKER_H + 50

            for i in range(num_humans):
                col    = AVAILABLE_COLORS[color_indices[i]][1]
                fy     = 110 + i * SECTION_H
                fx     = sw//2 - 320
                active = (i == active_idx)

                ctrl_label = CONTROLS_LABELS[i]
                label = f"Jugador {i+1}  [{ctrl_label}]"
                draw_text(screen, label, FONT_XS, col, fx, fy)

                box = pygame.Rect(fx, fy + 18, 340, 36)
                field_rects.append(box)
                bg_col  = (0, 40, 20) if active else (0, 15, 8)
                brd_col = col         if active else (0, 60, 30)
                pygame.draw.rect(screen, bg_col,  box, border_radius=6)
                pygame.draw.rect(screen, brd_col, box, 2, border_radius=6)

                cursor_str = "|" if (active and show_cursor) else ""
                text_surf  = FONT_SM.render((names[i] or "") + cursor_str,
                                            True, col if active else (0,160,70))
                screen.blit(text_surf, (box.x + 10, box.y + 7))
                if not names[i] and not active:
                    ph = FONT_SM.render(defaults[i], True, (0, 60, 30))
                    screen.blit(ph, (box.x + 10, box.y + 7))
                if errors[i]:
                    err_surf = FONT_XS.render(errors[i], True, (255, 80, 80))
                    screen.blit(err_surf, (box.x, box.y + 38))

                cname_txt, chead, cbody = AVAILABLE_COLORS[color_indices[i]]
                px_start = fx + 350
                py_center = fy + 36
                for si in range(8):
                    px = px_start + si * 14
                    r  = max(3, 9 - si)
                    pygame.draw.circle(screen, chead if si==0 else cbody, (px, py_center), r)
                cname_surf = FONT_XS.render(cname_txt, True, chead)
                screen.blit(cname_surf, (px_start, py_center + 12))

                picker_y = fy + 60
                picker_label = FONT_XS.render("Color:", True, (0,160,70))
                screen.blit(picker_label, (fx, picker_y - 2))
                crects = draw_color_picker(screen, fx + 50, picker_y,
                                           color_indices[i], i,
                                           selected_by_others_map.get(i, set()))
                all_color_rects.append(crects)

            for i in range(1, num_humans):
                sep_y = 110 + i * SECTION_H - 8
                pygame.draw.line(screen, (0,60,30), (sw//2-340, sep_y), (sw//2+340, sep_y), 1)

        cont_rect = pygame.Rect(sw//2 - 140, sh - 68, 280, 50)
        pygame.draw.rect(screen, (0,200,80), cont_rect, border_radius=10)
        draw_text_centered(screen, "CONTINUAR", FONT_MED, (2,5,2), sw//2, sh - 43)
        draw_text_centered(screen, "TAB para cambiar  |  ESC para volver",
                           FONT_XS, (0,100,50), sw//2, sh - 12)

        pygame.display.flip()
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_field = False
                for i, box in enumerate(field_rects):
                    if box.collidepoint(event.pos):
                        active_idx = i
                        clicked_field = True

                if not clicked_field:
                    for i, crects in enumerate(all_color_rects):
                        for ci, crect in enumerate(crects):
                            if crect.collidepoint(event.pos):
                                others = selected_by_others_map.get(i, set())
                                if ci not in others:
                                    color_indices[i] = ci
                                active_idx = i
                                break

                if cont_rect.collidepoint(event.pos):
                    all_ok = True
                    for i in range(num_humans):
                        n = names[i].strip() if names[i].strip() else defaults[i]
                        err = validate(n)
                        errors[i] = err
                        if err: all_ok = False
                        else:   names[i] = n
                    if all_ok:
                        chosen_colors = [AVAILABLE_COLORS[color_indices[i]] for i in range(num_humans)]
                        return names, chosen_colors

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None, None
                elif event.key == pygame.K_TAB:
                    active_idx = (active_idx + 1) % num_humans
                elif event.key == pygame.K_RETURN:
                    n = names[active_idx].strip() if names[active_idx].strip() else defaults[active_idx]
                    err = validate(n)
                    errors[active_idx] = err
                    if not err:
                        names[active_idx] = n
                        if active_idx < num_humans - 1:
                            active_idx += 1
                        else:
                            all_ok = True
                            for i in range(num_humans):
                                nm = names[i].strip() if names[i].strip() else defaults[i]
                                e  = validate(nm)
                                errors[i] = e
                                if e: all_ok = False
                                else: names[i] = nm
                            if all_ok:
                                chosen_colors = [AVAILABLE_COLORS[color_indices[i]] for i in range(num_humans)]
                                return names, chosen_colors
                elif event.key == pygame.K_BACKSPACE:
                    if names[active_idx]:
                        names[active_idx] = names[active_idx][:-1]
                    errors[active_idx] = ""
                else:
                    ch = event.unicode
                    if ch and is_valid_char(ch) and len(names[active_idx]) < 15:
                        names[active_idx] += ch
                        errors[active_idx] = ""


# ══════════════════════════════════════════════════════════════════════════════
#  RESULTADOS
# ══════════════════════════════════════════════════════════════════════════════
def gameover_screen(snakes):
    sorted_s=sorted(snakes,key=lambda s:s.score,reverse=True)
    while True:
        sw,sh=screen.get_size(); screen.fill(BG)
        for x in range(0,sw,40): pygame.draw.line(screen,(0,20,10),(x,0),(x,sh))
        for y in range(0,sh,40): pygame.draw.line(screen,(0,20,10),(0,y),(sw,y))
        draw_text_centered(screen,"FIN DEL JUEGO",FONT_BIG,(255,45,120),sw//2,100)
        col_x=[sw//2-340,sw//2-180,sw//2+80,sw//2+220]; ry0=200
        for i,h in enumerate(["#","JUGADOR","SCORE","LONGITUD"]):
            draw_text(screen,h,FONT_XS,(0,180,80),col_x[i],ry0)
        pygame.draw.line(screen,(0,100,40),(sw//2-360,ry0+24),(sw//2+320,ry0+24),1)
        for rank,sn in enumerate(sorted_s):
            ry=ry0+40+rank*44; col=sn.color["head"]
            mark=" [X]" if not sn.alive else ""
            draw_text(screen,str(rank+1),           FONT_SM,col,col_x[0],ry)
            draw_text(screen,sn.color["name"]+mark, FONT_SM,col,col_x[1],ry)
            draw_text(screen,str(sn.score),         FONT_SM,col,col_x[2],ry)
            draw_text(screen,str(sn.length//4),     FONT_SM,col,col_x[3],ry)
        replay_rect=pygame.Rect(sw//2-250,sh-130,220,54)
        quit_rect  =pygame.Rect(sw//2+30, sh-130,220,54)
        pygame.draw.rect(screen,(255,45,120),replay_rect,border_radius=10)
        pygame.draw.rect(screen,(40,10,20), quit_rect,  border_radius=10)
        pygame.draw.rect(screen,(255,45,120),quit_rect,2,border_radius=10)
        draw_text_centered(screen,"JUGAR DE NUEVO",FONT_SM,(10,0,5),   replay_rect.centerx,replay_rect.centery)
        draw_text_centered(screen,"SALIR",         FONT_SM,(255,80,120),quit_rect.centerx,  quit_rect.centery)
        pygame.display.flip(); clock.tick(FPS)
        for event in pygame.event.get():
            if event.type==pygame.QUIT: return False
            if event.type==pygame.MOUSEBUTTONDOWN and event.button==1:
                if replay_rect.collidepoint(event.pos): return True
                if quit_rect.collidepoint(event.pos):   return False
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_RETURN: return True
                if event.key==pygame.K_ESCAPE: return False


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    while True:
        result = menu_screen()
        if result is None:
            break
        num_humans, use_ai = result

        player_names, player_colors = nickname_screen(num_humans)
        if player_names is None:
            continue

        game_result = run_game(num_humans, use_ai, player_names, player_colors)
        if game_result == "quit":
            break
        save_results(game_result)
        if not gameover_screen(game_result):
            break

    pygame.quit()
    sys.exit()

if __name__=="__main__":
    main()