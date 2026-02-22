import math, pygame, numpy,random,os,time
from screeninfo import get_monitors
pygame.init()
class Screen():
    def __init__(self,resolution, max_fps=300, name="Screen", show_fps=True, bg_col=(0,0,0), clear_on_flip=False):
        self.resolution = resolution if isinstance(resolution, tuple) else (get_monitors()[0].width, get_monitors()[0].height-65) if resolution.upper().replace(" ", "") == "MAX" else (800, 480)
        self.screen = pygame.display.set_mode((self.resolution[0], self.resolution[1]))
        self.clock = pygame.time.Clock()
        self.pixels = numpy.zeros((self.resolution[0], self.resolution[1], 3), dtype=numpy.uint8)
        self.age = 0
        self.ts = self.resolution[0]*self.resolution[1]-1
        self.rx = self.resolution[0]
        self.ry = self.resolution[1]
        self.bg_image = None
        self.bg_col = bg_col
        self.max_fps = max_fps
        self.name = name
        self.elements = []
        self.show_fps = show_fps
        self.Arial = pygame.font.SysFont('Arial', 15)
        self.clear_on_flip = clear_on_flip
        pygame.display.set_caption(self.name)
    def random_pixel(self):
        return (random.randrange(self.rx),random.randrange(self.ry))
    def bresenham_line(p1, p2, d=1):
        x1,y1 = p1
        x2,y2 = p2
        dx,dy = abs(x2-x1), abs(y2-y1)
        xs    = d if x1 < x2 else -d
        ys    = d if y1 < y2 else -d
        x     = x1
        y     = y1

        yield (x,y)

        if dx > dy: # Line is more horizontal (slope <= 1)
            p = 2 * dy - dx
            for _ in range(math.floor(dx)):
                if p >= 0:
                    y += ys/d
                    p -= 2 * dx
                x += xs/d
                p += 2 * dy
                yield (x, y)
        else: # Line is more vertical (slope > 1)
            p = 2 * dx - dy
            for _ in range(math.floor(dy)):
                if p >= 0:
                    x += xs/d
                    p -= 2 * dy
                y += ys/d
                p += 2 * dx
                yield (x, y)
    def normalize(x):
        x = numpy.asarray(x)
        m = numpy.linalg.norm(x)
        if m == 0:
            return numpy.zeros_like(x)
        return x / m

    def vec_subtract(a, b):
        return numpy.asarray(a) - numpy.asarray(b)

    def vec_add(a, b):
        return numpy.asarray(a) + numpy.asarray(b)

    def vec_scale(a, s):
        return numpy.asarray(a) * s

    def cross(a, b):
        return numpy.cross(a, b)

    def dot(a, b):
        return numpy.dot(a, b)
    class color():
        r,red = (255,0,0),(255,0,0)
        o,orange = (255,165,0),(255,165,0)
        y,yellow = (255,255, 0),(255,255, 0)
        g,green = (0,255,0),(0,255,0)
        b,blue = (0,0,255),(0,0,255)
        p,purple = (165,0,255),(165,0,255)
        w,white = (255,255,255),(255,255,255)
        grey,gray = (165,165,165),(165,165,165)
        black = (0,0,0)
        rainbow = [r,o,y,g,b,p]
        def get_rainbow(i):
            return (255*(math.sin(2*math.pi*i+math.pi*2/3)+1)/2,
                    255*(math.sin(2*math.pi*i+math.pi*4/3)+1)/2,
                    255*(math.sin(2*math.pi*i+math.pi*2)+1)/2,
                    )
    class Pixel():
        def draw(screen,pos,color):
            x,y = pos
            x,y=int(x),int(y)
            r,g,b = color
            if 0 <= x < screen.rx and 0 <= y < screen.ry:
                screen.pixels[x, y, 0] = r
                screen.pixels[x, y, 1] = g
                screen.pixels[x, y, 2] = b
        def color_at(screen, pos):
            x,y=pos
            return (screen.pixels[x,y,0],screen.pixels[x,y,1],screen.pixels[x,y,2])
    class triangle():
        def __init__(self, screen, age, p1, p2, p3, color):
            self.age = age
            self.screen = screen
            self.points = [p1, p2, p3]
            self.color = color
        def draw(self):
            if self.screen.age not in self.age:
                return

            (x1, y1), (x2, y2), (x3, y3) = self.points
            r, g, b = self.color

            # Bounding box
            xmin = max(int(min(x1, x2, x3)), 0)
            xmax = min(int(max(x1, x2, x3)), self.screen.rx - 1)
            ymin = max(int(min(y1, y2, y3)), 0)
            ymax = min(int(max(y1, y2, y3)), self.screen.ry - 1)

            if xmin > xmax or ymin > ymax:
                return

            # Create grid of pixel coordinates
            xs = numpy.arange(xmin, xmax + 1)
            ys = numpy.arange(ymin, ymax + 1)
            X,Y = numpy.meshgrid(xs, ys)

            # Edge functions (vectorized)
            w0 = (x2 - x1)*(Y - y1) - (y2 - y1)*(X - x1)
            w1 = (x3 - x2)*(Y - y2) - (y3 - y2)*(X - x2)
            w2 = (x1 - x3)*(Y - y3) - (y1 - y3)*(X - x3)

            # Triangle orientation
            area = (x2 - x1)*(y3 - y1) - (y2 - y1)*(x3 - x1)

            if area >= 0:
                mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            else:
                mask = (w0 <= 0) & (w1 <= 0) & (w2 <= 0)

            region = self.screen.pixels[ymin:ymax+1, xmin:xmax+1]

            region[mask, 0] = r
            region[mask, 1] = g
            region[mask, 2] = b

    class reset():
        def __init__(self, screen, age):
            age = age if isinstance(age, list) else [age]
            if screen.age in age:
                for x in range(screen.rx):
                    for y in range(screen.ry):
                        Screen.Pixel.draw(s, (x,y),screen.bg_col)
    class circle():
        def __init__(self, screen, age, radius, center, color=(255,255,255), aliasing=False):
            self.screen = screen
            self.radius, self.center = radius, center
            self.color = color
            self.age = age if isinstance(age, list) else [age]
            self.aliasing = aliasing
        def draw(self):
            if self.screen.age in self.age:
                x1, y1 = self.center
                outer_sq = self.radius ** 2

                min_x = max(0, int(x1 - self.radius))
                max_x = min(self.screen.rx, int(x1 + self.radius))
                min_y = max(0, int(y1 - self.radius))
                max_y = min(self.screen.ry, int(y1 + self.radius))
                for y in range(min_y, max_y):
                    for x in range(min_x,max_x):
                        dx = x - x1
                        dy = y - y1
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= outer_sq:
                            if not self.aliasing:
                                Screen.Pixel.draw(self.screen, (x,y),self.color)
                            elif dist_sq <= outer_sq:
                                alpha = (self.radius - math.sqrt(dist_sq)) / 3
                                alpha = 0 if alpha < 0 else 1 if alpha > 1 else alpha
                                blended = self._blend_pixel(self.screen, (x,y), alpha)
                                Screen.Pixel.draw(self.screen, (x,y), blended)
        def _blend_pixel(self, screen, pos, alpha):
            bg = self.screen.Pixel.color_at(screen, pos)

            r = int(self.color[0] * alpha + bg[0] * (1 - alpha))
            g = int(self.color[1] * alpha + bg[1] * (1 - alpha))
            b = int(self.color[2] * alpha + bg[2] * (1 - alpha))
            return (r,g,b)
    class line():
        def __init__(self,screen, age, p1,p2, color, thickness=0):
            self.screen = screen
            self.age = age if isinstance(age, list) else [age]
            self.p1, self.p2 = p1, p2
            self.color = color
            self.thickness = thickness
            screen.elements.append(self)
        def draw(self):
            if self.screen.age not in self.age:
                return

            # Direction from p1 to p2
            direction = Screen.vec_subtract(self.p2, self.p1)
            direction = Screen.normalize(direction)

            # Perpendicular
            perp = (-direction[1], direction[0])

            # Half thickness offset
            offset = Screen.vec_scale(perp, self.thickness / 2)

            # Four corners of thick line (quad)
            p1a = Screen.vec_add(self.p1, offset)
            p1b = Screen.vec_subtract(self.p1, offset)
            p2a = Screen.vec_add(self.p2, offset)
            p2b = Screen.vec_subtract(self.p2, offset)

            # Draw as two triangles
            Screen.triangle(self.screen, self.age, p1a, p2a, p2b, self.color).draw()
            Screen.triangle(self.screen, self.age, p1a, p2b, p1b, self.color).draw()
    class polygon():
        def __init__(self,screen,age,center,radius,sides,color,thickness=0,angle=0):
            self.screen = screen
            self.age = age if isinstance(age, list) else [age]
            self.center = center
            self.color, self.thickness = color, thickness
            self.radius = radius
            self.sides = sides
            self.angle = angle
            screen.elements.append(self)
        def draw(self):
            if self.screen.age in self.age:
                for i in range(self.sides):
                    p1 = (self.center[0] + self.radius*math.cos(i/self.sides * 2 * math.pi+self.angle),self.center[1] + self.radius*math.sin(i/self.sides * 2 * math.pi+self.angle))
                    p2 = (self.center[0] + self.radius*math.cos((i+1)/self.sides * 2 * math.pi+self.angle),self.center[1] + self.radius*math.sin((i+1)/self.sides * 2 * math.pi+self.angle))
                    Screen.line(self.screen, self.age,p1, p2, self.color, self.thickness).draw()
    class animate():
        def ease_mode(ease_mode):
            if ease_mode.upper().replace(" ", "")=="SINE":
                return lambda x:(-math.cos(x*math.pi)+1)/2
            elif ease_mode.upper().replace(" ", "")=="LINEAR":
                return lambda x:x
            
        def animate(screen, element, t_start, t_end, ease="SINE", full=False):
            if element.__class__ == Screen.line:
                a,b = element.p1
                c,d = element.p2
                dg = .1
                t_start,t_end = t_start[0] if isinstance(t_start, list) else t_start,t_end[0] if isinstance(t_end, list) else t_end
                clamp = lambda time:0 if time == t_start else 0 if (time - t_start) / (t_end - t_start) < 0 else 1 if (time - t_start) / (t_end - t_start) > 1 else (time - t_start) / (t_end - t_start)
                g = Screen.animate.ease_mode(ease)(clamp(screen.age))
                DIGGY = g-dg
                Screen.line(

                    screen, 
                    [_ for _ in range(t_start, t_end)],
                    element.p1 if full else (a*(1-DIGGY)+c*DIGGY,b*(1-DIGGY)+d*DIGGY), 
                    (a*(1-g)+c*g,b*(1-g)+d*g), 
                    element.color,
                    element.thickness
                    ).draw()
            if element.__class__ == Screen.polygon:
                clamp = lambda time:0 if time == t_start else 0 if (time - t_start) / (t_end - t_start) < 0 else 1 if (time - t_start) / (t_end - t_start) > 1 else (time - t_start) / (t_end - t_start)
                g = Screen.animate.ease_mode(ease)(clamp(screen.age))
                t_start,t_end = t_start[0] if isinstance(t_start, list) else t_start,t_end[0] if isinstance(t_end, list) else t_end
                dg = .1
                for i in range(int(g*element.sides)):
                    p1 = (element.center[0] + element.radius*math.cos(i/element.sides * 2 * math.pi+element.angle),element.center[1] + element.radius*math.sin(i/element.sides * 2 * math.pi+element.angle))
                    p2 = (element.center[0] + element.radius*math.cos((i+1)/element.sides * 2 * math.pi+element.angle),element.center[1] + element.radius*math.sin((i+1)/element.sides * 2 * math.pi+element.angle))
                    Screen.line(element.screen, [_ for _ in range(t_start, t_end)],p1, p2, element.color, element.thickness).draw()
                

                a,b = (element.center[0] + element.radius*math.cos(int(g*element.sides)/element.sides * 2 * math.pi+element.angle),element.center[1] + element.radius*math.sin(int(g*element.sides)/element.sides * 2 * math.pi+element.angle))
                c,d = (element.center[0] + element.radius*math.cos((int(g*element.sides)+1)/element.sides * 2 * math.pi+element.angle),element.center[1] + element.radius*math.sin((int(g*element.sides)+1)/element.sides * 2 * math.pi+element.angle))
                DIGGY = (g*element.sides%1)-dg
                Screen.line(

                    screen, 
                    [_ for _ in range(t_start, t_end)],
                    (a,b) if full else (a*(1-DIGGY)+c*DIGGY,b*(1-DIGGY)+d*DIGGY), 
                    (a*(1-(g*element.sides%1))+c*(g*element.sides%1),b*(1-(g*element.sides%1))+d*(g*element.sides%1)), 
                    element.color,
                    element.thickness
                    ).draw()
        def interpolate(screen, p1, p2, t_start, t_end, ease="SINE"):
            a,b = p1
            c,d = p2
            clamp = lambda time:0 if time == t_start else 0 if (time - t_start) / (t_end - t_start) < 0 else 1 if (time - t_start) / (t_end - t_start) > 1 else (time - t_start) / (t_end - t_start)
            g = Screen.animate.ease_mode(ease)(clamp(screen.age))
            return (a*(1-g)+c*g,b*(1-g)+d*g)
    class camera3():
        def __init__(self, pos3=(1,0,0),look=(1,0,0), up=(0,1,0), focal_len=(2,2)):
            def normalize(x):
                m = math.sqrt(x[0]**2 + x[1]**2 + x[2]**2)
                if m == 0:
                    return [0,0,0]
                return [x[0]/m, x[1]/m, x[2]/m]
            self.pos  = pos3
            self.look = normalize([self.pos[i]+look[i] for i in range(3)])
            self.up   = up
            self.fl   = (focal_len, focal_len) if isinstance(focal_len, (int,float)) else focal_len if isinstance(focal_len, tuple) else (3,3)
    
    class point3():
        def __init__(self, screen, age, pos3=(0,0,0), color=(255,255,255)):
            self.screen = screen
            self.age    = age
            self.pos    = pos3
            self.color  = color
        def project(self, camera):
            x,y,z       = self.pos
            rel = [
                x - camera.pos[0],
                y - camera.pos[1],
                z - camera.pos[2]
            ]
            x_cam = rel[0]
            y_cam = rel[1]
            z_cam = rel[2]
            cam   = [x_cam, y_cam, z_cam]
            #print(cam)
            if z_cam <= 0:
                return None
            x_prime = cam[0]/cam[2] * camera.fl[0]
            y_prime = cam[1]/cam[2] * camera.fl[1]
            if x_prime > self.screen.rx/2 or x_prime < -self.screen.rx/2:
                return None
            if y_prime > self.screen.ry/2 or y_prime < -self.screen.ry/2:
                return None
            return (x_prime+self.screen.rx/2,-y_prime+self.screen.ry/2)
        def draw(self, camera):
            if self.project(camera):
                Screen.Pixel.draw(self.screen, self.project(camera), self.color)
    def clock_step(self, step):
        self.age += 1
        self.clock.tick(step)

    def set_bg_image(self, img):
        self.bg_image = pygame.transform.scale(pygame.image.load(img), self.resolution)
    def set_bg(self, col):
        r,g,b=col
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

    def run(self, function=lambda: None, *fargs, **fkargs):
        while all([event.type != pygame.QUIT for event in pygame.event.get()]):

            if self.bg_image:
                self.screen.blit(self.bg_image, (0,0))
                self.pixels = pygame.surfarray.array3d(self.bg_image).copy()
                self.bg_image = None
            if self.clear_on_flip:
                self.set_bg(self.bg_col)
            function(*fargs, **fkargs)
            pygame.surfarray.blit_array(self.screen, self.pixels)
            if self.show_fps:
                fps = self.clock.get_fps()
                self.screen.blit(self.Arial.render(f"FPS: {round(fps, 2)}, AGE: {self.age}", True, (255,255,255)), (0,0))
            pygame.display.flip()
            self.clock_step(self.max_fps)


s = Screen(resolution="MAX",max_fps=60, bg_col=(0,0,0), show_fps=True,clear_on_flip=True)
A = []
for i in range(10):
    for j in range(20):
        A.append(Screen.point3(s, [_ for _ in range(10000)], ((j - 10)/10, 0, i/10), Screen.color.r if j % 2 ==0 else Screen.color.g))
def guh():
    cam = Screen.camera3((0,1,-1+s.age/100), (0,0,1), (0,1,0), (s.rx/50, s.ry/50))
    for i in range(len(A)-1):
        q = A[i]
        q.pos = (q.pos[0], math.cos((j + s.age/10)/10), q.pos[2])
        q.draw(cam)
        if q.project(cam) and A[i+1].project(cam):
            Screen.line(s, [_ for _ in range(10000)], q.project(cam), A[i+1].project(cam),(255,255,255),1).draw()


a = s.random_pixel()
b = s.random_pixel()
def line_test():
    Screen.line(s, [_ for _ in range(10000)], a, b, random.choice(Screen.color.rainbow),5).draw()

def triangle_test():
    Screen.triangle(s, [_ for _ in range(1000)],(200,200), (s.age,300), (220,220), random.choice(Screen.color.rainbow)).draw()
s.run(guh)
