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
        self.lineup = []
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
    def render_3d(self, camera):
        sorted(self.lineup, key=lambda obj: obj.z_order).reverse()
        for i in self.lineup:
            i.draw(camera)
        self.lineup = []
    def _dist(points, cam):
        pp = [numpy.subtract(i.pos,cam.pos) for i in points]
        k = 0
        for i in pp:
            k=numpy.add(k, i)
        k = numpy.divide(k, len(pp))
        return float(sum([i**2 for i in k]))
    def _clamp(val, range):
        return val if range[0] < val < range[1] else range[0] if val < range[0] else range[1]
    class Color:
        def random():
            return tuple([random.randrange(0, 255) for _ in range(3)])
        RED,R = (255,0,0),(255,0,0)
        GREEN,G = (0,255,0),(0,255,0)
        BLUE,B = (0,0,255),(0,0,255)
        WHITE,W = (255,255,255),(255,255,255)
    class Shapes:
        class Triangle3():
            def __init__(self, screen, age, p1, p2, p3, color):
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.screen = screen
                self.points = [p1, p2, p3]
                self.color = color
                self.z_order = 0
            def add(self, camera):
                self.z_order = Screen._dist(self.points, camera)
                self.screen.lineup.append(self)
            def draw(self, cam):
                if self.screen.age not in self.age:
                    return

                x1, y1 = self.points[0].project(cam)
                x2, y2 = self.points[1].project(cam)
                x3, y3 = self.points[2].project(cam)

                # Bounding box
                xmin = max(min(x1, x2, x3), 0)
                xmax = min(max(x1, x2, x3), self.screen.rx - 1)
                ymin = max(min(y1, y2, y3), 0)
                ymax = min(max(y1, y2, y3), self.screen.ry - 1)

                if xmin > xmax or ymin > ymax:
                    return

                xmin, xmax, ymin, ymax = map(int, (xmin, xmax, ymin, ymax))
                xs = numpy.arange(xmin, xmax + 1)
                ys = numpy.arange(ymin, ymax + 1)
                X = xs[:, None]
                Y = ys[None, :]
                w0 = (x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)
                w1 = (x3 - x2) * (Y - y2) - (y3 - y2) * (X - x2)
                w2 = (x1 - x3) * (Y - y3) - (y1 - y3) * (X - x3)
                iy = [0 < y < self.screen.ry for y in Y[0]]
                ix = [0 < x < self.screen.rx for x in X]

                area = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
                if area == 0:
                    return
                q = 0
                if area > 0:
                    mask = (w0 >= q) & (w1 >= q) & (w2 >= q) & iy & ix
                else:
                    mask = (w0 <= q) & (w1 <= q) & (w2 <= q) & iy & ix

                region = self.screen.pixels[xmin:xmax+1, ymin:ymax+1]

                if region.size == 0:
                    return
                region[mask] = self.color
        class Polygon():
            def __init__(self, screen, age, center=(0,0), radius=50, sides=6, color=(255,255,255)):
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.screen = screen
                self.center = center
                self.sides = sides
                self.color = color
                self.points = [
                    numpy.add(numpy.multiply((math.cos(i*2*math.pi/self.sides),math.sin(i*2*math.pi/self.sides)),radius),center) for i in range(self.sides) if center is not None
                ]
            def draw(self):
                if len(self.points) > 0:
                    for i in range(self.sides):
                        if self.points[i] is not None:
                            Screen.Shapes.Triangle(self.screen, self.age, self.center, self.points[i],self.points[(i+1)%self.sides],self.color).draw()
        class Triangle():
            def __init__(self, screen, age, p1, p2, p3, color):
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.screen = screen
                self.points = [p1, p2, p3]
                self.color = color
            def draw(self):
                if self.screen.age not in self.age:
                    return

                x1, y1 = self.points[0]
                x2, y2 = self.points[1]
                x3, y3 = self.points[2]

                # Bounding box
                xmin = max(min(x1, x2, x3), 0)
                xmax = min(max(x1, x2, x3), self.screen.rx - 1)
                ymin = max(min(y1, y2, y3), 0)
                ymax = min(max(y1, y2, y3), self.screen.ry - 1)

                if xmin > xmax or ymin > ymax:
                    return

                xmin, xmax, ymin, ymax = map(int, (xmin, xmax, ymin, ymax))
                xs = numpy.arange(xmin, xmax + 1)
                ys = numpy.arange(ymin, ymax + 1)
                X = xs[:, None]
                Y = ys[None, :]
                w0 = (x2 - x1) * (Y - y1) - (y2 - y1) * (X - x1)
                w1 = (x3 - x2) * (Y - y2) - (y3 - y2) * (X - x2)
                w2 = (x1 - x3) * (Y - y3) - (y1 - y3) * (X - x3)
                iy = [0 < y < self.screen.ry for y in Y[0]]
                ix = [0 < x < self.screen.rx for x in X]

                area = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
                if area == 0:
                    return
                q = 0
                if area > 0:
                    mask = (w0 >= q) & (w1 >= q) & (w2 >= q) & iy & ix
                else:
                    mask = (w0 <= q) & (w1 <= q) & (w2 <= q) & iy & ix

                region = self.screen.pixels[xmin:xmax+1, ymin:ymax+1]

                if region.size == 0:
                    return
                region[mask] = self.color
        class Line():
            def __init__(self,screen, age, p1,p2, color, thickness=0):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
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
                self.age    = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.pos    = pos3
                self.color  = color
                self.distance = 0
            def project(self, camera):
                cam = numpy.subtract(self.pos,camera.pos)
                self.distance = sum([i**2 for i in cam])
                if self.distance > camera.draw_dist:
                    return None
                cam = cam @ camera.rotation
                #print(cam)
                if cam[2] <= 0:
                    return None
                b = [cam[0]/cam[2] * camera.fl[0], -1 * cam[1]/cam[2] * camera.fl[1]]
                return numpy.add(b, [self.screen.rx/2-1, self.screen.ry/2-1])
            def draw(self, camera):
                if self.project(camera) is not None:
                    X,Y = self.project(camera)
                    X,Y = int(X),int(Y)
                    if 0 < X < self.screen.rx and 0 < Y < self.screen.ry:
                        self.screen.pixels[X,Y] = self.color
                        
        class line3():
            def __init__(self,screen, age, p1,p2, color, thickness=0):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.p1, self.p2 = p1, p2
                self.color = color
                self.thickness = thickness
                screen.elements.append(self)
            def draw(self,cam):
                if self.screen.age not in self.age:
                    return
                a = self.p1.project(cam)
                b = self.p2.project(cam)
                if a is not None and b is not None:
                    direction = numpy.subtract(numpy.array(a), numpy.array(b))
                    q = numpy.linalg.norm(direction)
                    if q == 0:
                        return 
                    direction = direction / q

                    perp = (-direction[1], direction[0])


                    offset1 = numpy.divide(numpy.multiply(perp, self.thickness*5), self.p1.distance)
                    offset2 = numpy.divide(numpy.multiply(perp, self.thickness*5), self.p2.distance)

                    p1a = numpy.add(a, offset1)
                    p1b = numpy.subtract(a, offset1)
                    p2a = numpy.add(b, offset2)
                    p2b = numpy.subtract(b, offset2)

                    Screen.Shapes.Triangle(self.screen, self.age, p1a, p2a, p2b, self.color).draw()
                    Screen.Shapes.Triangle(self.screen, self.age, p1a, p2b, p1b, self.color).draw()
        class quad3():
            def __init__(self,screen, age, pos=(0,0,0), v1=(0,0,1), v2=(1,0,0), color=(255,255,255), lighting=None):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.pos = pos
                self.vectors = [v1, v2]
                self.color = color
                self.points = [
                    Screen.Shapes.point3(self.screen, self.age, self.pos, self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, v1), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(numpy.add(self.pos, v1),v2), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, v2), self.color),
                ]
                self.color = color
                self.lighting = lighting
            def TriangleColor(self, v1, v2):
                pass
            def add(self, cam):
                Screen.Shapes.Triangle3(self.screen, self.age, self.points[0], self.points[1], self.points[2],self.color if isinstance(self.color, tuple) else self.color[0] if isinstance(self.color, list) else (255,255,255)).add(cam)
                Screen.Shapes.Triangle3(self.screen, self.age, self.points[2], self.points[3], self.points[0],self.color if isinstance(self.color, tuple) else self.color[1] if isinstance(self.color, list) else (255,255,255)).add(cam)


        class FloorGrid():
            def __init__(self, screen, age, size, distancing=1, wire=False):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.size = size
                self.distancing = distancing
                self.wire = wire
            def draw(self, camera):
                if self.screen.age not in self.age:
                    return
                size = self.size
                if not self.wire:
                    for i in range(size-1):
                        for j in range(size-1):
                            Screen.Shapes.point3(self.screen, self.age, ((i-size/2)*self.distancing, 0, (j-size/2)*self.distancing)).draw(camera)
                if self.wire:
                    for i in range(size+1):
                        a = Screen.Shapes.point3(self.screen, self.age, ((i-size/2)*self.distancing, 0, (0-size/2)*self.distancing),(255,255,255))
                        b = Screen.Shapes.point3(self.screen, self.age, ((i-size/2)*self.distancing, 0, ((size)-size/2)*self.distancing),(255,255,255))
                        Screen.Shapes.line3(self.screen, self.age, a,b, (255,255,255),3).draw(camera)
                    for i in range(size+1):
                        a = Screen.Shapes.point3(self.screen, self.age, ((0-size/2)*self.distancing, 0, (i-size/2)*self.distancing),(255,255,255))
                        b = Screen.Shapes.point3(self.screen, self.age, (((size)-size/2)*self.distancing, 0, (i-size/2)*self.distancing),(255,255,255))
                        Screen.Shapes.line3(self.screen, self.age, a,b, (255,255,255),3).draw(camera)
        class Axis():
            def __init__(self, screen, age, size_tuple):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.size = size_tuple
            def draw(self, camera):
                if self.screen.age not in self.age:
                    return
                center = Screen.Shapes.point3(self.screen, self.age, (0,0,0),(255,255,255))
                x,y,z = Screen.Shapes.point3(self.screen, self.age, (self.size[0],0,0),(255,255,255)),Screen.Shapes.point3(self.screen, self.age, (0,self.size[1],0),(255,255,255)),Screen.Shapes.point3(self.screen, self.age, (0,0,self.size[2]),(255,255,255))
                Screen.Shapes.line3(self.screen, self.age, center,x, (255,0,0),3).draw(camera)
                Screen.Shapes.line3(self.screen, self.age, center,y, (0,255,0),3).draw(camera)
                Screen.Shapes.line3(self.screen, self.age, center,z, (0,0,255),3).draw(camera)
        class Voxel():
            def __init__(self, screen, age, pos, color, wire, size=(1,1,1)):
                self.screen = screen
                self.age = age if isinstance(age, list) else [age] if isinstance(age, int) else [_ for _ in range(99999)]
                self.pos = pos
                self.color = color
                self.wire = wire
                self.x, self.y, self.z = size
                self.points = [
                    Screen.Shapes.point3(self.screen, self.age, self.pos, self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (0,0,self.z)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (0,self.y,0)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (0,self.y,self.z)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (self.x,0,0)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (self.x,0,self.z)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (self.x,self.y,0)), self.color),
                    Screen.Shapes.point3(self.screen, self.age, numpy.add(self.pos, (self.x,self.y,self.z)), self.color)
                ]
            def draw(self, camera):
                if not self.wire:
                    for i in self.points:
                        i.draw(camera)
                elif self.wire:
                    Screen.Shapes.line3(self.screen, self.age,self.points[0],self.points[1],self.color,3).draw(camera)
                    Screen.Shapes.line3(self.screen, self.age,self.points[0],self.points[2],self.color,3).draw(camera)
                    Screen.Shapes.line3(self.screen, self.age,self.points[0],self.points[4],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[1],self.points[3],self.color,3).draw(camera)
                    Screen.Shapes.line3(self.screen, self.age,self.points[1],self.points[5],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[2],self.points[3],self.color,3).draw(camera)
                    Screen.Shapes.line3(self.screen, self.age,self.points[2],self.points[6],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[3],self.points[7],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[4],self.points[5],self.color,3).draw(camera)
                    Screen.Shapes.line3(self.screen, self.age,self.points[4],self.points[6],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[5],self.points[7],self.color,3).draw(camera)

                    Screen.Shapes.line3(self.screen, self.age,self.points[6],self.points[7],self.color,3).draw(camera)
                   
        class camera3():
            def __init__(self, pos3=(0,0,0), focal_len=2, draw_dist=500):
                self.pos = numpy.array(pos3, dtype=float)
                self.yaw = 0.0
                self.pitch = 0.0
                self.roll = 0.0
                self.draw_dist = draw_dist
                self.fl = (focal_len, focal_len) if isinstance(focal_len, (int,float)) else focal_len
                self.rotation = numpy.array([[0,0,0],[0,0,0],[0,0,0]])
            def update_rotation(self):
                cos = math.cos
                sin = math.sin

                a = self.pitch
                b = self.yaw

                rot_x = numpy.array([
                    [1,0,0],
                    [0,cos(a),-sin(a)],
                    [0,sin(a),cos(a)]
                ])

                rot_y = numpy.array([
                    [cos(b),0,sin(b)],
                    [0,1,0],
                    [-sin(b),0,cos(b)]
                ])

                self.rotation = rot_y @ rot_x
            def focus_on(self, point):
                direction = numpy.subtract(point if isinstance(point, tuple) else point.pos, self.pos)
                #print(direction)
                self.yaw = math.atan2(direction[0],direction[2])
                self.pitch = -math.atan2(direction[1],math.sqrt(direction[0]**2 + direction[2]**2))
                self.update_rotation()

s = Screen(resolution="MAX",max_fps=60, bg_col=(0,0,0), show_fps=True,clear_on_flip=True)

cos = math.cos
sin = math.sin
cam = Screen.Shapes.camera3((5*cos(s.age/100),1,5*sin(s.age/100)), focal_len=s.rx/5, draw_dist=1000)
def camera_rotations():
    global cam
    cam = Screen.Shapes.camera3((5*cos(s.age/100),1,5*sin(s.age/100)), focal_len=s.rx/5, draw_dist=1000)
    cam.pitch = -.1
    cam.yaw = -math.pi/2-s.age/100
    cam.update_rotation()
def func():
    camera_rotations()
    #Screen.Shapes.Axis(s,size_tuple=(1,1,1),age=[_ for _ in range(10000)]).draw(cam)
    Screen.Shapes.Voxel(s, s.age, (-.5,0,-.5),(255,0,0),True).draw(cam)
    Screen.Shapes.Voxel(s, s.age, (-.5,1,-.5),(255,0,0),True).draw(cam)
    Screen.Shapes.Voxel(s, s.age, (-.5,2,-.5),(255,0,0),True).draw(cam)
    Screen.Shapes.Voxel(s, s.age, (-1.5,0,-.5),(255,0,0),True).draw(cam)
    Screen.Shapes.FloorGrid(s, s.age, 5,wire=True).draw(cam)
C = Screen.Color
a,b,c,d=C.RED, C.GREEN, C.BLUE, C.WHITE
CL = Screen._clamp
def func2():
    camera_rotations()
    Screen.Shapes.FloorGrid(s, s.age, 5,wire=True).draw(cam)

    one = Screen.Shapes.quad3(s, s.age, (-2.5,0,-2.5), (5,0,0), (0,0,5))
    one.color = (CL(Screen._dist(one.points, cam)*5,[0,255]),0,0)
    two = [Screen.Shapes.quad3(s, s.age, (-2.5,0,1.5), (0,1,0), (0,0,1),C.random()),Screen.Shapes.quad3(s, s.age, (-2.5,0,.5), (0,1,0), (0,0,1),C.random()),Screen.Shapes.quad3(s, s.age, (-2.5,0,-.5), (0,1,0), (0,0,1),C.random()),Screen.Shapes.quad3(s, s.age, (-2.5,0,-1.5), (0,1,0), (0,0,1),C.random()),Screen.Shapes.quad3(s, s.age, (-2.5,0,-2.5), (0,1,0), (0,0,1),C.random())]
    one.add(cam)
    for i in two:
        i.add(cam)
    s.render_3d(cam)

def func3():
    cam = Screen.Shapes.camera3((5*sin(s.age/30), 5, 5*-cos(s.age/30)), focal_len=s.rx/5, draw_dist=1000)
    q = (2.5,0,2.5)
    cam.focus_on(q)
    Screen.Shapes.FloorGrid(s, s.age, 20,distancing=.1,wire=True).draw(cam)
    a=Screen.Shapes.point3(s, s.age, pos3=q)
    Screen.Shapes.Polygon(s,s.age,center=a.project(cam),radius=10,sides=10,color=(255,0,0)).draw()
s.run(func3)
