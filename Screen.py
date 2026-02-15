import math, pygame, numpy,random,os,time
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
        self.age += 1
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
            self.pixels[int(L[i][0]), int(L[i][1]),2] = b
    def draw_segment(self, p1, p2, r, g, b, thickness, outline=False, outline_thickness=0):

        x1, y1 = p1
        x2, y2 = p2

        dx = x2 - x1
        dy = y2 - y1
        length_sq = dx*dx + dy*dy

        if length_sq == 0:
            return

        min_x = max(0, int(min(x1, x2) - thickness - outline_thickness))
        max_x = min(self.rx, int(max(x1, x2) + thickness + outline_thickness))
        min_y = max(0, int(min(y1, y2) - thickness - outline_thickness))
        max_y = min(self.ry, int(max(y1, y2) + thickness + outline_thickness))

        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                t = ((x - x1)*dx + (y - y1)*dy) / length_sq
                t = max(0, min(1, t))
                proj_x = x1 + t*dx
                proj_y = y1 + t*dy
                dist_sq = (x - proj_x)**2 + (y - proj_y)**2

                if dist_sq <= thickness*thickness:
                    self.pixels[y, x, 0] = r
                    self.pixels[y, x, 1] = g
                    self.pixels[y, x, 2] = b
                if outline is not False:
                    if dist_sq - thickness**2 <= outline_thickness**2 and dist_sq > thickness*thickness:
                        self.pixels[y, x, 0] = outline[0]
                        self.pixels[y, x, 1] = outline[1]
                        self.pixels[y, x, 2] = outline[2]
    def draw_circle(self,radius, center, color, thickness, fill=None):
        x1, y1 = center
        r,g,b = color
        outer_sq = radius * radius
        inner_sq = (radius - thickness) * (radius - thickness)
        min_x = max(0, int(x1 - radius))
        max_x = min(self.rx, int(x1 + radius))
        min_y = max(0, int(y1 - radius))
        max_y = min(self.ry, int(y1 + radius))
        for y in range(min_y, max_y):
            for x in range(min_x,max_x):
                dx = x - x1
                dy = y - y1
                dist_sq = dx*dx + dy*dy
                if dist_sq <= outer_sq:
                    self.pixels[y, x, 0] = fill[0]
                    self.pixels[y, x, 1] = fill[1]
                    self.pixels[y, x, 2] = fill[2]
                if inner_sq <= dist_sq <= outer_sq:
                    self.pixels[y, x, 0] = r
                    self.pixels[y, x, 1] = g
                    self.pixels[y, x, 2] = b

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
    def random_pixel(self):
        return (random.randrange(0,self.rx),random.randrange(0,self.ry))
    def interpolate(self, p1, p2, t_start, t_end, i_mode=lambda x:x*2):
        a,b = p1
        c,d = p2

        clamp = lambda time:0 if time == t_start else 0 if (time - t_start) / (t_end - t_start) < 0 else 1 if (time - t_start) / (t_end - t_start) > 1 else (time - t_start) / (t_end - t_start)
        g = i_mode(clamp(self.age))
        return (a*(1-g)+c*g,b*(1-g)+d*g)


s = Screen(resolution=(800,600),max_fps=60)
x = 0
def guh():
    s.set_bg(0, 0, 0)
    x=s.interpolate((0,0), (400,400), 0, 100, i_mode=lambda x:x**2)
    y=s.interpolate((200,500), (23,80), 0, 500, i_mode=lambda x:(math.sin(x*math.pi*10)+1)/2)
    s.draw_circle(20,y,(100,0,0),5, fill=(255,0,0))
s.run(guh)
