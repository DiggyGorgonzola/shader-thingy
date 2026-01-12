import math, pygame, numpy,random,os
pygame.init()
class Screen():
    def __init__(self,resolution=(800,480), max_fps=300, name="Screen"):
        self.resolution = resolution
        self.screen = pygame.display.set_mode((self.resolution[0], self.resolution[1]))
        self.clock = pygame.time.Clock()
        self.pixels = numpy.zeros((self.resolution[0], self.resolution[1], 3), dtype=numpy.uint8)
        self.age = 0
        self.ts = self.resolution[0]*self.resolution[1]-1
        self.rx = resolution[0]
        self.ry = resolution[1]
        self.bg_image = None
        self.max_fps = max_fps
        self.name = name
        pygame.display.set_caption(self.name)
    def clock_step(self, step):
        self.age += step
        self.clock.tick(step)

    def set_bg_image(self, img):
        self.bg_image = pygame.transform.scale(pygame.image.load(img), self.resolution)
    def set_bg(self, r,g,b):
        self.pixels[:, :, 0] = r
        self.pixels[:, :, 1] = g
        self.pixels[:, :, 2] = b
    def colorize(self):
        r = int((math.sin(self.age / 1000) * 127) + 128)
        g = int((math.sin(self.age / 1000 + 2*math.pi/3) * 127) + 128)
        b = int((math.sin(self.age / 1000 + 4*math.pi/3) * 127) + 128)

        self.pixels[:, :, 0] = r
        self.pixels[:, :, 1] = g
        self.pixels[:, :, 2] = b

    def draw_pixel(self,x,y, r,g,b):
        self.pixels[x, y, 0] = r
        self.pixels[x, y, 1] = g
        self.pixels[x, y, 2] = b
    def brightest_pixel(self, p1, p2):
        return True if sum(self.pixels[p1[0], p1[1]]) > sum(self.pixels[p2[0], p2[1]]) else False
    def swap_pixels(self, criterion=brightest_pixel, p1=(0,0), p2=(0,1)):
        if criterion(self, p1, p2):
            c1 = self.pixels[p1[0], p1[1]]
            c2 = self.pixels[p2[0], p2[1]]
            self.pixels[p1[0], p1[1]] = c2
            self.pixels[p2[0], p2[1]] = c1
    def affect_pixel(self, x,y, r,g,b, func=(lambda x,y:x+y)):
        def clamp(val):
            return max(0, min(255, val))
        
        self.pixels[y, x, 0] = clamp(func(int(self.pixels[y, x, 0]), r))
        self.pixels[y, x, 1] = clamp(func(int(self.pixels[y, x, 1]), g))
        self.pixels[y, x, 2] = clamp(func(int(self.pixels[y, x, 2]), b))
    def affect_screen(self, r,g,b, func=(lambda x,y:x+y)):
        def clamp(val):
            return max(0, min(255, val))
        
        self.pixels = self.pixels.astype(numpy.int32)

        self.pixels[:, :, 0] = func(self.pixels[:, :, 0], r)
        self.pixels[:, :, 1] = func(self.pixels[:, :, 1], g)
        self.pixels[:, :, 2] = func(self.pixels[:, :, 2], b)

        self.pixels = self.pixels.astype(numpy.uint8)
    def draw_line(self,p1, p2, r,g,b):
        distance = math.ceil(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2))
        L=[(p1[0]*(1-i/distance) + p2[0]*i/distance,p1[1]*(1-i/distance) + p2[1]*i/distance) for i in range(distance)]
        for i in range(distance):
            self.pixels[int(L[i][0]), int(L[i][1]),0] = r
            self.pixels[int(L[i][0]), int(L[i][1]),1] = g
            self.pixels[int(L[i][0]), int(L[i][1]),1] = g
    def run(self, function=lambda: None, *fargs, **fkargs):
        while all([event.type != pygame.QUIT for event in pygame.event.get()]):
            if self.bg_image:
                self.screen.blit(self.bg_image, (0,0))
                self.pixels = pygame.surfarray.array3d(self.bg_image).copy()
                self.bg_image = None
            function(*fargs, **fkargs)
            pygame.surfarray.blit_array(self.screen, self.pixels)
            pygame.display.flip()
            self.clock_step(self.max_fps)
s = Screen(resolution=(230,230),max_fps=1)
def guh():
    s.draw_line((random.randrange(0, s.rx),random.randrange(0, s.ry)),(random.randrange(0, s.rx),random.randrange(0, s.ry)),255,0,0)
s.run(guh)
