import pygame
import time
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

image_path = "p11.png"
img = Image.open(image_path).convert('L')  # Convert to grayscale

WINDOW_WIDTH, WINDOW_HEIGHT = img.width, img.height
BACKGROUND_COLOR = (0, 0, 0)
DRONE_COLOR = (255, 255, 255)
TRACK_COLOR = (50, 50, 50)
HISTORY_COLOR = (255, 255, 0)

DRONE_RADIUS = 10
VELOCITY = 5

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('3D Modeling with Drone Sensors')
executor = ThreadPoolExecutor()
class Drone:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.history = []

    def draw(self):
        pygame.draw.circle(screen, DRONE_COLOR, (self.x, self.y), DRONE_RADIUS)
    
    def move(self, dx, dy, track):
        new_x = self.x + dx
        new_y = self.y + dy
        if self.is_inside_track(new_x, new_y, track):
            self.history.append((self.x, self.y))
            self.x = new_x
            self.y = new_y

    def is_inside_track(self, x, y, track):
        start_time = time.time()
        for segment in track:
            if segment.collidepoint(x, y):
                print(f"is_inside_track duration={time.time() - start_time}")
                return True
        print(f"is_inside_track duration={time.time() - start_time}")
        return False

    def draw_history(self):
        for point in self.history:
            pygame.draw.circle(screen, HISTORY_COLOR, point, 2)

    def get_sensor_readings(self, track):
        start_time = time.time()
        directions = [(1 * VELOCITY, 0), ((-1) * VELOCITY, 0), (0, (-1) * VELOCITY), (0, 1 * VELOCITY)]
        readings = list(executor.map(lambda d: self.calculate_sensor_range(track, d[0], d[1]), directions))
        # print(f"get_sensor_readings duration={time.time() - start_time}")
        return readings

    def calculate_sensor_range(self, track, dx, dy):
        start_time = time.time()
        distance = 0
        while distance < max(WINDOW_WIDTH, WINDOW_HEIGHT):
            x = self.x + dx * distance
            y = self.y + dy * distance
            if x < 0 or x >= WINDOW_WIDTH or y < 0 or y >= WINDOW_HEIGHT or not self.is_inside_track(x, y, track):
                break
            distance += 1
            if(distance > 4):
                return distance
        # print(f"calculate_sensor_range duration={time.time() - start_time}")
        return distance

def draw_track(track):
    for segment in track:
        pygame.draw.rect(screen, TRACK_COLOR, segment)

def build_track_from_matrix(matrix, cell_size):
    track = []
    for y in range(len(matrix)):
        for x in range(len(matrix[0])):
            if matrix[y][x] == 1:
                rect = pygame.Rect(x * cell_size, y * cell_size, cell_size, cell_size)
                track.append(rect)
    return track

def image_to_matrix(img, threshold=128):
    img = img.point(lambda p: p > threshold and 1)  # Convert to binary using threshold
    matrix = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            row.append(img.getpixel((x, y)))
        matrix.append(row)
    return matrix
def main():
    
    matrix = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 0, 0, 0, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    
    matrix = image_to_matrix(img)
    cell_size = 1

    track = build_track_from_matrix(matrix, cell_size)
    start_x, start_y = 125, 125
    drone = Drone(start_x, start_y)

    clock = pygame.time.Clock()
    running = True

    is_going_up = True
    is_going_down = True
    is_going_left = True
    is_going_right = True
    speed = VELOCITY
    
    def go_left(drone, track):
        drone.move((-1) * speed, 0, track)
    
    def go_right(drone, track):
        drone.move(1 * speed, 0, track)
    
    def go_up(drone, track):
        drone.move(0, (-1) * speed, track)
    
    def go_down(drone, track):
        drone.move(0, 1 * speed, track)
        
    while running:
        start_time = time.time()
        screen.fill(BACKGROUND_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            go_left(drone, track)
        if keys[pygame.K_RIGHT]:
            go_right(drone, track)
        if keys[pygame.K_UP]:
            go_up(drone, track)
        if keys[pygame.K_DOWN]:
            go_down(drone, track)
        
        
        current_readings = drone.get_sensor_readings(track)
            
        if(current_readings[2] > 1) and is_going_up:
            is_going_right = True
            is_going_left = True
            go_up(drone, track)
        elif(current_readings[0] > 1) and is_going_right:
            is_going_up = True
            go_right(drone, track)
        elif(current_readings[3] > 1) and is_going_down:
            is_going_right = True
            is_going_up = False
            go_down(drone, track)
        elif(current_readings[1] > 1) and is_going_left:
            is_going_right = False
            is_going_down = True
            is_going_up = False
            go_left(drone, track)
        else:
            is_going_up = False
            is_going_down = False
            is_going_right = False
            is_going_left = True
            go_up(drone, track)

        draw_track(track)
        drone.draw_history()
        drone.draw()

        readings = current_readings
        # print(f"right: {readings[0]}, left: {readings[1]}, up: {readings[2]}, down: {readings[3]}") 

        pygame.display.flip()
        clock.tick(30)
        
    pygame.quit()

if __name__ == "__main__":
    main()
