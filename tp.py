import pygame, random, math, os

pygame.init()

# ================= AUDIO FIX =================
os.environ["SDL_AUDIODRIVER"] = "directsound"

audio_enabled = True
try:
    pygame.mixer.init()
    eat_sound = pygame.mixer.Sound(buffer=b'\x00'*2000)
    die_sound = pygame.mixer.Sound(buffer=b'\x00'*4000)
except:
    print("⚠️ Audio no disponible")
    audio_enabled = False

def play_eat():
    if audio_enabled:
        try: eat_sound.play()
        except: pass

def play_die():
    if audio_enabled:
        try: die_sound.play()
        except: pass

# ================= CONFIG =================
WIDTH, HEIGHT = 900, 600
WORLD = 3000
FPS = 60
SPEED = 2.8
TURN_SPEED = 0.08

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

COLORS = [(0,255,136),(0,200,255),(255,45,120),(255,230,0)]

def dist(a,b): return math.hypot(a[0]-b[0], a[1]-b[1])

def angle_diff(a,b):
    d=b-a
    while d>math.pi: d-=2*math.pi
    while d<-math.pi: d+=2*math.pi
    return d

# ================= PARTICLES =================
particles = []
def spawn_particles(x,y,color):
    for _ in range(20):
        a=random.random()*math.pi*2
        sp=random.random()*4
        particles.append([x,y,math.cos(a)*sp,math.sin(a)*sp,1,color])

# ================= SNAKE =================
class Snake:
    def __init__(self,id,isAI,x,y):
        self.id=id
        self.isAI=isAI
        self.color=COLORS[id]
        self.angle=0
        self.target=0
        self.segments=[(x,y)]
        self.alive=True
        self.score=0

    def head(self): return self.segments[0]

    def update(self,keys):
        if not self.alive: return

        if self.isAI: self.ai()
        else: self.control(keys)

        da=angle_diff(self.angle,self.target)
        self.angle+=max(-TURN_SPEED,min(TURN_SPEED,da))

        x,y=self.head()
        nx=x+math.cos(self.angle)*SPEED
        ny=y+math.sin(self.angle)*SPEED
        self.segments.insert(0,(nx,ny))

        while len(self.segments)>40+self.score*3:
            self.segments.pop()

    def control(self,keys):
        controls=[
            (pygame.K_w,pygame.K_s,pygame.K_a,pygame.K_d),
            (pygame.K_UP,pygame.K_DOWN,pygame.K_LEFT,pygame.K_RIGHT)
        ]
        k=controls[self.id]

        if keys[k[0]]: self.target=-math.pi/2
        elif keys[k[1]]: self.target=math.pi/2
        elif keys[k[2]]: self.target=math.pi
        elif keys[k[3]]: self.target=0

    def ai(self):
        hx,hy=self.head()

        # evitar enemigos
        for s in snakes:
            if s!=self and s.alive:
                if dist(self.head(), s.head()) < 120:
                    self.target = math.atan2(hy-s.head()[1], hx-s.head()[0])
                    return

        # ir a comida
        if food:
            f=min(food,key=lambda x:dist(self.head(),x))
            self.target=math.atan2(f[1]-hy,f[0]-hx)

    def draw(self,surf,camx,camy):
        for i,(x,y) in enumerate(self.segments):
            sx=x-camx+surf.get_width()//2
            sy=y-camy+surf.get_height()//2

            r=8 if i==0 else 5

            # glow
            glow = pygame.Surface((r*4,r*4), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*self.color,80),(r*2,r*2),r*2)
            surf.blit(glow,(sx-r*2,sy-r*2))

            pygame.draw.circle(surf,self.color,(int(sx),int(sy)),r)

# ================= FOOD =================
food=[]
def spawn_food(n=150):
    for _ in range(n):
        food.append((random.randint(0,WORLD),random.randint(0,WORLD)))

# ================= MINIMAP =================
def draw_minimap(surf,camx,camy):
    size=120
    mini=pygame.Surface((size,size))
    mini.fill((20,20,20))

    scale=size/WORLD

    for f in food:
        pygame.draw.circle(mini,(255,100,100),(int(f[0]*scale),int(f[1]*scale)),1)

    for s in snakes:
        if not s.alive: continue
        pygame.draw.circle(mini,s.color,(int(s.head()[0]*scale),int(s.head()[1]*scale)),3)

    surf.blit(mini,(surf.get_width()-130,10))

# ================= INIT =================
snakes=[]
food=[]

def init():
    global snakes,food
    snakes=[Snake(0,False,500,500),Snake(1,True,2500,2500)]
    food=[]
    spawn_food()

init()

# ================= LOOP =================
running=True
while running:
    clock.tick(FPS)
    keys=pygame.key.get_pressed()

    for e in pygame.event.get():
        if e.type==pygame.QUIT:
            running=False

    screen.fill((5,10,14))

    for s in snakes:
        s.update(keys)

    # COMER
    for f in food[:]:
        for s in snakes:
            if s.alive and dist(s.head(),f)<10:
                s.score+=1
                food.remove(f)
                spawn_particles(f[0],f[1],(255,100,100))
                play_eat()

    # COLISION
    for s in snakes:
        if not s.alive: continue
        for o in snakes:
            for seg in o.segments[10:]:
                if dist(s.head(),seg)<8:
                    s.alive=False
                    spawn_particles(*s.head(),s.color)
                    play_die()

    # PARTICULAS
    for p in particles[:]:
        p[0]+=p[2]
        p[1]+=p[3]
        p[4]-=0.03
        if p[4]<=0: particles.remove(p)
        else:
            pygame.draw.circle(screen,p[5],(int(p[0]),int(p[1])),3)

    camx,camy=snakes[0].head()

    for f in food:
        sx=f[0]-camx+WIDTH//2
        sy=f[1]-camy+HEIGHT//2
        pygame.draw.circle(screen,(255,100,100),(int(sx),int(sy)),4)

    for s in snakes:
        s.draw(screen,camx,camy)

    draw_minimap(screen,camx,camy)

    pygame.display.flip()

pygame.quit()