import math, pygame, numpy,random,os,time
from screeninfo import get_monitors
from scipy.spatial import Delaunay
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
        return (random.randrange(0, self.rx-1), random.randrange(0, self.ry-1))
    def clock_step(self, step):
        self.age += 1
        self.clock.tick(step)
    def set_bg(self, col):
        r,g,b=col
        self.pixels[:, :, 0] = r
        self.pixels[:, :, 1] = g
        self.pixels[:, :, 2] = b
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
    class Shapes:
        class Triangle():
            def __init__(self, screen, age, p1, p2, p3, color):
                self.age = age
                self.screen = screen
                self.points = [p1, p2, p3]
                self.color = color
            def draw(self):
                if self.screen.age not in self.age:
                    return

                v = numpy.array(self.points)
                x1, y1 = self.points[0]
                x2, y2 = self.points[1]
                x3, y3 = self.points[2]

                # Bounding box
                xmin = int(max(min(x1,x2,x3), 0))
                xmax = int(min(max(x1,x2,x3), self.screen.rx - 1))
                ymin = int(max(min(y1,y2,y3), 0))
                ymax = int(min(max(y1,y2,y3), self.screen.ry - 1))
                xs = numpy.arange(xmin, xmax+1)
                ys = numpy.arange(ymin, ymax+1)
                X, Y = numpy.meshgrid(xs, ys, indexing="ij")
                w0 = (x2 - x1)*(Y - y1) - (y2 - y1)*(X - x1)
                w1 = (x3 - x2)*(Y - y2) - (y3 - y2)*(X - x2)
                w2 = (x1 - x3)*(Y - y3) - (y1 - y3)*(X - x3)


                area = (x2 - x1)*(y3 - y1) - (y2 - y1)*(x3 - x1)

                if area >= 0:
                    mask = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
                else:
                    mask = (w0 <= 0) & (w1 <= 0) & (w2 <= 0)
                region = self.screen.pixels[xmin:xmax+1, ymin:ymax+1]
                r, g, b = self.color
                region[mask, 0] = r
                region[mask, 1] = g
                region[mask, 2] = b
        class Line():
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


                direction = numpy.subtract(numpy.array(self.p1), numpy.array(self.p2))
                direction = direction / numpy.linalg.norm(direction)

                perp = (-direction[1], direction[0])


                offset = numpy.multiply(perp, self.thickness / 2)


                p1a = numpy.add(self.p1, offset)
                p1b = numpy.subtract(self.p1, offset)
                p2a = numpy.add(self.p2, offset)
                p2b = numpy.subtract(self.p2, offset)

                Screen.Shapes.Triangle(self.screen, self.age, p1a, p2a, p2b, self.color).draw()
                Screen.Shapes.Triangle(self.screen, self.age, p1a, p2b, p1b, self.color).draw()
        class point3():
            def __init__(self, screen, age, pos3=(0,0,0), color=(255,255,255)):
                self.screen = screen
                self.age    = age
                self.pos    = pos3
                self.color  = color
            def project(self, camera):
                cam = numpy.subtract(self.pos,camera.pos)
                if sum([i**2 for i in cam]) > camera.draw_dist:
                    return None
                cam = cam @ camera.rot_x @ camera.rot_y @ camera.rot_z
                #print(cam)
                if cam[2] <= 0:
                    return None
                b = [cam[0]/cam[2] * camera.fl[0], -1 * cam[1]/cam[2] * camera.fl[1]]
                if abs(b[0]) > self.screen.rx/2:
                    return None
                elif abs(b[1]) > self.screen.ry/2:
                    return None
                return tuple(numpy.add(b, [self.screen.rx/2-1, self.screen.ry/2-1]))
            def draw(self, camera):
                if self.project(camera):
                    X,Y = self.project(camera)
                    X,Y = int(X),int(Y)
                    r,g,b=self.color
                    self.screen.pixels[X,Y, 0] = r
                    self.screen.pixels[X,Y, 1] = g
                    self.screen.pixels[X,Y, 2] = b
        class FloorGrid():
            def __init__(self, screen, age, size, distancing=1):
                self.screen = screen
                self.age = age
                self.size = size
                self.distancing = distancing
            def draw(self, camera):
                if self.screen.age not in self.age:
                    return
                size = self.size
                for i in range(size):
                    for j in range(size):
                        Screen.Shapes.point3(self.screen, self.age, ((i-size/2)*self.distancing, 0, (j-size/2)*self.distancing)).draw(camera)
        class camera3():
            def __init__(self, pos3=(1,0,0),look=(1,0,0), up=(0,1,0), focal_len=(2,2), euler=(0,0,0),draw_dist=500):
                def normalize(x):
                    m = math.sqrt(x[0]**2 + x[1]**2 + x[2]**2)
                    if m == 0:
                        return [0,0,0]
                    return [x[0]/m, x[1]/m, x[2]/m]
                self.draw_dist = draw_dist
                self.pos  = pos3
                self.look = normalize([self.pos[i]+look[i] for i in range(3)])
                self.up   = up
                self.euler = euler
                cos = math.cos
                sin = math.sin
                a,b,c = self.euler[0],self.euler[1],self.euler[2]
                self.rot_x = numpy.array([[1,0,0],[0,cos(a),-sin(a)],[0,sin(a),cos(a)]])
                self.rot_y = numpy.array([[cos(b), 0, sin(b)],[0, 1, 0],[-sin(b), 0, cos(b)]])
                self.rot_z = numpy.array([[cos(c), -sin(c),0], [sin(c), cos(c),0],[0,0,1]])
                self.fl   = (focal_len, focal_len) if isinstance(focal_len, (int,float)) else focal_len if isinstance(focal_len, tuple) else (3,3)
s = Screen(resolution="MAX",max_fps=60, bg_col=(0,0,0), show_fps=True,clear_on_flip=True)
A = []
for i in range(10):
    for j in range(20):
        A.append(Screen.Shapes.point3(s, [_ for _ in range(10000)], ((j - 20)/10, 0, i/10), (255,0,0) if j % 2 ==0 else (0,255,0)))
#(2*math.cos(s.age/200), 1, 2*math.sin(s.age/200)
def guh():
    cam = Screen.Shapes.camera3((2*math.cos(s.age/200), 3, 2*math.sin(s.age/200)), (0,0,1), (0,1,0), (s.rx/5, s.ry/5), euler=(0,-math.pi/2-s.age/200,0),draw_dist=100)
    Screen.Shapes.FloorGrid(s, [_ for _ in range(10000)], 100, distancing=1).draw(cam)
    for i in range(len(A)-1):
        q = A[i]
        q.pos = (q.pos[0], math.cos((i%20 + s.age/10)/10), q.pos[2])
        q.draw(cam)

def triangle_test():
    Screen.Shapes.Triangle(s, [_ for _ in range(1000)],s.random_pixel(), (s.age,300), (220,220), (255,255,255)).draw()
def line_test():
    Screen.Shapes.Line(s, [_ for _ in range(10000)], s.random_pixel(), s.random_pixel(), (255,255,255),5).draw()
s.run(guh)
