import pygame
import time
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

def image_to_matrix(img, threshold=128):
    img = img.point(lambda p: p > threshold and 1)  # Convert to binary using threshold
    matrix = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            row.append(img.getpixel((x, y)))
        matrix.append(row)
    return matrix

image_path = "p11.png"
img = Image.open(image_path).convert('L')  # Convert to grayscale
matrix = image_to_matrix(img)

WINDOW_WIDTH, WINDOW_HEIGHT = img.width, img.height
BACKGROUND_COLOR = (0, 0, 0)
DRONE_COLOR = (255, 0, 0)
TRACK_COLOR = (50, 50, 50)
HISTORY_COLOR = (255, 255, 0)

VELOCITY = 2
DRONE_RADIUS = (int) (3000 / 2.5)

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('3D Modeling with Drone Sensors')
executor = ThreadPoolExecutor()
class Drone:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.history = []
        self.is_in_return = False
        self.directions = [(1 * VELOCITY, 0), ((-1) * VELOCITY, 0), (0, (-1) * VELOCITY), (0, 1 * VELOCITY)]
        self.directions_coloring = [(1, 0), ((-1), 0), (0, (-1)), (0, 1)]
        self.current_readings = []
        self.direction = "up"

    def calculate_directions_step(self, velocity):
        self.directions = [(1 * velocity, 0), ((-1) * velocity, 0), (0, (-1) * velocity), (0, 1 * velocity)]
        
    def draw(self):
        # Draw the line part of the arrow
        end = (self.x+1, self.y)
        arrow_length = 20
        # Determine the direction of the arrowhead
        direction = self.direction
        if direction == "up":
            arrow_dir = pygame.math.Vector2(0, -1)
        elif direction == "down":
            arrow_dir = pygame.math.Vector2(0, 1)
        elif direction == "left":
            arrow_dir = pygame.math.Vector2(-1, 0)
        elif direction == "right":
            arrow_dir = pygame.math.Vector2(1, 0)
        else:
            raise ValueError("Invalid direction. Use 'up', 'down', 'left', or 'right'.")
        
        # Normalize the direction
        arrow_dir = arrow_dir.normalize()
        
        # Calculate the end points of the arrowhead
        left_end = end + arrow_dir.rotate(150) * arrow_length
        right_end = end + arrow_dir.rotate(-150) * arrow_length
        
        # Draw the arrowhead
        pygame.draw.polygon(screen, DRONE_COLOR, [end, left_end, right_end])
        # pygame.draw.circle(screen, DRONE_COLOR, (self.x, self.y), 10)
        
    
    def check_if_in_track_if_so_color(self, x, y):
        if self.is_inside_track(x, y):
            self.history.append((x, y))
    
    def append_radius(self):
        if(self.is_in_return):
            return
        directions = []
        current_readings = self.get_sensor_readings(self.directions_coloring)
        for index in range(current_readings[0]):
           directions.append((self.x + index, self.y))
        for index in range(current_readings[1]):
            directions.append((self.x - index, self.y))
        for index in range(current_readings[2]):
            directions.append((self.x, self.y - index))
        for index in range(current_readings[3]):
            directions.append((self.x, self.y + index))
                
        executor.map(lambda d: self.check_if_in_track_if_so_color(d[0], d[1]), directions)
        
    def move(self, dx, dy):
        new_x = int(self.x + dx)
        new_y = int(self.y + dy)
        if self.is_inside_track(new_x, new_y):
            self.history.append((self.x, self.y))
            self.append_radius()
            self.x = new_x
            self.y = new_y

    def is_inside_track(self, x, y):
        result = (matrix[y][x] == 1)
        return result

    def draw_history(self):
        for point in self.history:
            pygame.draw.circle(screen, HISTORY_COLOR, point, 2)

    def get_sensor_readings(self, directions):
        readings = list(executor.map(lambda d: self.calculate_sensor_range( d[0], d[1]), directions))
        self.current_readings = readings
        return readings
    
    def calculate_sensor_range(self, dx, dy):
        distance = 0
        while distance < max(WINDOW_WIDTH, WINDOW_HEIGHT):
            x = self.x + dx * distance
            y = self.y + dy * distance
            if x < 0 or x >= WINDOW_WIDTH or y < 0 or y >= WINDOW_HEIGHT or not self.is_inside_track(x, y):
                break
            if(distance > DRONE_RADIUS):
                return distance
            distance += 1
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

def find_closest_track_point(start_x, start_y, track):
    min_distance = float('inf')
    closest_point = (start_x, start_y)

    for segment in track:
        center_x, center_y = segment.center
        distance = ((center_x - start_x) ** 2 + (center_y - start_y) ** 2) ** 0.5
        if distance < min_distance:
            min_distance = distance
            closest_point = (center_x, center_y)

    return closest_point

def main():
    matrix = image_to_matrix(img)
    cell_size = 1

    track = build_track_from_matrix(matrix, cell_size)
    start_x, start_y = 125, 125

    initial_rect = pygame.Rect(start_x, start_y, 1, 1)
    if not any(segment.colliderect(initial_rect) for segment in track):
        start_x, start_y = find_closest_track_point(start_x, start_y, track)

    drone = Drone(start_x, start_y)

    clock = pygame.time.Clock()
    running = True

    is_going_up = True
    is_going_down = True
    is_going_left = True
    is_going_right = True
    
    steps = []

    def go_left(drone):
        drone.direction = "left"
        drone.move((-1) * VELOCITY, 0)

    def go_right(drone):
        drone.direction = "right"
        drone.move(1 * VELOCITY, 0)

    def go_up(drone):
        drone.direction = "up"
        drone.move(0, (-1) * VELOCITY)

    def go_down(drone):
        drone.direction = "down"
        drone.move(0, 1 * VELOCITY)
        
    start_time = time.time()
        

    while running:
        start_time_running = time.time()
        screen.fill(BACKGROUND_COLOR)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        if(time.time() - start_time) > 8*60 or (drone.x == start_x and drone.y == start_y and drone.is_in_return):
            break
        elif(time.time() - start_time) > 4*60:
            drone.is_in_return = True
            drone.calculate_directions_step(5)
            
            func = steps.pop()
            func(drone)
        else:

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                go_left(drone)
            if keys[pygame.K_RIGHT]:
                go_right(drone)
            if keys[pygame.K_UP]:
                go_up(drone)
            if keys[pygame.K_DOWN]:
                go_down(drone)

            current_readings = drone.get_sensor_readings(drone.directions)

            if(current_readings[2] > 1) and is_going_up:
                is_going_right = True
                is_going_left = True
                go_up(drone)
                steps.append(go_down)
            elif(current_readings[0] > 1) and is_going_right:
                is_going_up = True
                go_right(drone)
                steps.append(go_left)
            elif(current_readings[3] > 1) and is_going_down:
                is_going_right = True
                is_going_up = False
                go_down(drone)
                steps.append(go_up)
            elif(current_readings[1] > 1) and is_going_left:
                is_going_right = False
                is_going_down = True
                is_going_up = False
                go_left(drone)
                steps.append(go_right)
            else:
                is_going_up = False
                is_going_down = False
                is_going_right = False
                is_going_left = True
                go_up(drone)
                steps.append(go_down)
            

        draw_track(track)
        drone.draw_history()
        drone.draw()

        readings = current_readings
        print(f"right: {readings[0]}, left: {readings[1]}, up: {readings[2]}, down: {readings[3]}")

        pygame.display.flip()
        clock.tick(300)
        print(f"time in running = {time.time() - start_time_running}")
        print(f"speed = {VELOCITY /(time.time() - start_time_running)}")

    pygame.quit()

if __name__ == "__main__":
    main()
