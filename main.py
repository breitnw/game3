#!/usr/local/bin/python3

# TODO:

# fix weird display issues on windows (likely colorkey issue)
# finish (?) implementing vector2 class in engine and main
# change animation system to using sprite sheets
# finish pass 2 generation
# fix entity move code if it's bad
# maybe make a better way to break background blocks

import sys, random, json, noise
import pygame as pg
import engine.entity as entity
import engine.animation as animation
from engine.math import *
from engine.coroutine import *
from pygame.locals import *

#---------------------------------------------------------------------------------------------- SETUP

clock = pg.time.Clock()
pg.mixer.pre_init(44100, -16, 2, 512)
pg.init()
pg.mixer.set_num_channels(16)
pg.display.set_caption('pg test')

#SERIALIZATION
serializaton_file = 'data/serialized_data.json'
serialized_data = {}
with open(serializaton_file, 'r') as f:
    serialized_data = json.load(f)
def serialize(**data):
    with open(serializaton_file, 'w') as f:
        json.dump(data, f, indent=4)

#WINDOW
WINDOW_SIZE = (600, 400)
screen = pg.display.set_mode(WINDOW_SIZE, 0, 32)
DISPLAY_SIZE = (300, 200)
display = pg.Surface(DISPLAY_SIZE, 0, 32)
display = display.copy()
display.set_colorkey((0, 0, 0))

#IMAGE LOADING
animation.load_anims('data/textures/entities/')

grass_img = pg.image.load('data/textures/blocks/grass_side.png').convert()
dirt_img = pg.image.load('data/textures/blocks/dirt.png').convert()
stone_img = pg.image.load('data/textures/blocks/stone.png').convert()
fence_img = pg.image.load('data/textures/blocks/fence.png').convert()
flower_img = pg.image.load('data/textures/blocks/flower.png').convert()
planks_oak_img = pg.image.load('data/textures/blocks/planks_oak.png').convert()
volume_button_imgs = [
    pg.image.load('data/textures/gui/volume_button_on.png').convert(),
    pg.image.load('data/textures/gui/volume_button_off.png').convert()
]
flower_img.set_colorkey((0, 0, 0))
fence_img.set_colorkey((0, 0, 0))

TILE_SIZE = grass_img.get_width()

def get_darkened_img(image: pg.Surface, percent: float):
    image = image.copy()
    darken_percent = .50
    dark = pg.Surface(image.get_size()).convert_alpha()
    dark.fill((0, 0, 0, darken_percent * 255))
    image.blit(dark, (0, 0))
    return image

#SOUND LOADING
sounds = {
    'jump': pg.mixer.Sound('data/sounds/jump.wav'),
    'grass': (
        pg.mixer.Sound('data/sounds/grass_0.wav'),
        pg.mixer.Sound('data/sounds/grass_1.wav')
    )
}
for sound in sounds['grass']:
    sound.set_volume(0.1)

music = pg.mixer.music.load('data/sounds/music.wav')
pg.mixer.music.play(-1)

#---------------------------------------------------------------------------------------------- VARIABLES

#COLORS
palette = (
    (251, 245, 239),
    (242, 211, 171),
    (198, 159, 165),
    (139, 109, 156),
    (73, 77, 126),
    (39, 39, 68)
)

#PARALLAX OBJECTS
background_objects = [[0.25,[120,10,70,400]],[0.25,[280,30,40,400]],[0.5,[30,40,40,400]],[0.5,[130,90,100,400]],[0.5,[300,80,120,400]]]

#VARIABLES
right = False
left = False
shift_held = False

y_vel = 0
x_vel = 0
player_movement = [0, 0]
on_ground = False
in_wall_slide = False
air_x_accel = 0.2 # added

INITIAL_POS = (70, 30)
SPEED = 2
MAX_Y_VEL = 5
GRV = 0.15
AIR_X_DECEL = 0.9 # multiplied by
JUMP_SPEED = 3.2
JUMP_BUFFER_DURATION = 6
BONK_DECEL = 1
WALL_SLIDE_VEL = 1

dt = 0
def dtf(dt):
    return dt / 1000 * 60

#PLAYER
PLAYER_RECT_DIMENSIONS = (10, 13)
PLAYER_RECT_OFFSET = (2, 1)
player = entity.Entity(*INITIAL_POS, *PLAYER_RECT_DIMENSIONS, 'player')
player.set_img_offset(PLAYER_RECT_OFFSET)

#GUI
volume_button_rect = pg.Rect(DISPLAY_SIZE[0] - 16, 8, 8, 8)
show_button_rect = pg.Rect(DISPLAY_SIZE[0] - 24, 2, 22, 22)

vol_muted = False
if 'vol_muted' in serialized_data:
    vol_muted = serialized_data['vol_muted']
pg.mixer.music.set_volume(not vol_muted)

def show_volume_button(target_surface):
    if mouse_in_rect(show_button_rect):
        target_surface.blit(volume_button_imgs[vol_muted], (volume_button_rect.x, volume_button_rect.y))
def gui_click():
    global vol_muted
    channels = [pg.mixer.Channel(i) for i in range(pg.mixer.get_num_channels())]
    if mouse_in_rect(volume_button_rect):
        vol_muted = not vol_muted
        pg.mixer.music.set_volume(not vol_muted)
        for channel in channels:
            channel.set_volume(0)
        return True
    return False
#TODO: important functions, move to engine?
def mouse_in_rect(rect) -> bool:
    mouse_pos = scaled_mouse_pos()
    return pg.Rect.collidepoint(rect, *mouse_pos)
def scaled_mouse_pos():
    original_pos = pg.mouse.get_pos()
    return [original_pos[i] * DISPLAY_SIZE[i] / WINDOW_SIZE[i] for i in range(2)]

#GAME MAP
map_img_dict = {
    1: grass_img,
    2: dirt_img,
    3: stone_img,
    4: flower_img,
    5: planks_oak_img,
}
map_bg_img_dict = {key : get_darkened_img(value, 50) for (key, value) in map_img_dict.items()}

chunk_map = {}
CHUNK_SIZE = 16

SEED = random.randint(0, 128)
print('seed:', SEED)

class Chunk:
    def __init__(self, x, y):
        self.foreground_data = {}
        self.background_data = {}
        self.x = x
        self.y = y
        self.pass_1()
    def pass_1(self):
        for y_pos in range(CHUNK_SIZE):
            for x_pos in range(CHUNK_SIZE):
                target_x = self.x * CHUNK_SIZE + x_pos
                target_y = self.y * CHUNK_SIZE + y_pos

                height = int(noise.pnoise1(target_x * 0.03, repeat = 65536, octaves = 3, base = SEED, persistence = 0.7) * 20)
                cavenoise = noise.pnoise2(target_x * 0.05, target_y * 0.05, repeatx = 65536, repeaty = 65536, octaves = 3, base = SEED)

                tile_type = 0 # nothing
                if target_y > 12 - height / 2:
                    tile_type = 3 # stone
                elif target_y > 8 - height:
                    tile_type = 2 # dirt
                elif target_y == 8 - height:
                    tile_type = 1 # grass
                elif target_y == 7 - height:
                    if random.randint(1,5) == 1:
                        tile_type = 4 # plant
                if cavenoise > 0.15:
                    tile_type = 0 # create caves

                self.foreground_data[(target_x, target_y)] = tile_type

                bg_tile_type = 0 # nothing
                if target_y > 12 - height / 2:
                    bg_tile_type = 3 # stone
                elif target_y > 9 - height:
                    bg_tile_type = 2 # dirt

                self.background_data[(target_x, target_y)] = bg_tile_type

def process_tiles(display, scroll):
    tile_rects = []
    for y in range(4):
        for x in range(4):
            target_x = x - 1 + int(round(scroll[0] / (CHUNK_SIZE * TILE_SIZE)))
            target_y = y - 1 + int(round(scroll[1] / (CHUNK_SIZE * TILE_SIZE)))
            target_pos = (target_x, target_y)
            if target_pos not in chunk_map:
                chunk_map[target_pos] = Chunk(target_x, target_y)
            for tile_pos, tile_type in chunk_map[target_pos].foreground_data.items():
                if tile_type != 0:
                    display.blit(map_img_dict[tile_type], (tile_pos[0] * TILE_SIZE - scroll[0], tile_pos[1] * TILE_SIZE - scroll[1]))
                    if tile_type != 4:
                        tile_rects.append(pg.Rect(tile_pos[0] * TILE_SIZE, tile_pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                else:
                    bg_tile_type = chunk_map[target_pos].background_data[tile_pos]
                    if bg_tile_type != 0:
                        display.blit(map_bg_img_dict[bg_tile_type],(tile_pos[0] * TILE_SIZE - scroll[0], tile_pos[1] * TILE_SIZE - scroll[1]))
    return tile_rects

#TILE MODIFICATION
def get_tile(tile_x: int, tile_y: int, background = False):
    chunk_x, chunk_y = tile_x // CHUNK_SIZE, tile_y // CHUNK_SIZE
    target_chunk = chunk_map[(chunk_x, chunk_y)]
    target_dict = target_chunk.background_data if background else target_chunk.foreground_data
    return target_dict[tile_x, tile_y]

def set_tile(tile_x: int, tile_y: int, tile_type: int, background = False):
    chunk_x, chunk_y = tile_x // CHUNK_SIZE, tile_y // CHUNK_SIZE
    target_chunk = chunk_map[(chunk_x, chunk_y)]
    target_dict = target_chunk.background_data if background else target_chunk.foreground_data
    target_dict[tile_x, tile_y] = tile_type

def world_to_tile(world_x, world_y):
    return (world_x // TILE_SIZE, world_y // TILE_SIZE)

#CAMERA SCROLLING
true_scroll = [0, 0]
SCROLL_LAG = 15
SCROLL_OFFSET = (
    (DISPLAY_SIZE[0] - player.rect.width) / 2,
    (DISPLAY_SIZE[1] - player.rect.height) / 2
)

#DRAWING
def draw_bordered_rect(surface, border_color, fill_color, rect, width = 0, border_radius = 0, border_top_left_radius = -1,
border_top_right_radius = -1, border_bottom_left_radius = -1, border_bottom_right_radius = -1):
    args = locals()
    del args['border_color'], args['fill_color']
    args['color'], args['width'] = fill_color, 0
    pg.draw.rect(**args)
    args['color'], args['width'] = border_color, width
    pg.draw.rect(**args)


#---------------------------------------------------------------------------------------------- COROUTINES
jump_coroutine = None #stores both regular and wall jumps
fall_coroutine = None
ground_timer_coroutine = None
wall_slide_timer_coroutine = None

def jump(squat_duration):
    global y_vel
    global on_ground
    global fall_coroutine

    player.set_action('jump_squat')
    yield squat_duration

    y_vel = -JUMP_SPEED
    sounds['jump'].play()
    fall_coroutine = queue_coroutine(fall())
    on_ground = False
    yield 1

def wall_jump(reduced_accel_duration):
    global air_x_accel
    global y_vel
    global x_vel
    global in_wall_slide
    global fall_coroutine
    global on_ground

    player.set_flip(not player.flip)
    x_vel = -JUMP_SPEED if player.flip else JUMP_SPEED
    y_vel = -JUMP_SPEED
    sounds['jump'].play()
    in_wall_slide = False

    stop_coroutine(fall_coroutine)
    fall_coroutine = queue_coroutine(fall())

    air_x_accel = 0.05
    yield reduced_accel_duration / dtf(dt)
    air_x_accel = 0.2
    yield 1

def fall():
    while(player_movement[1] < 0):
        player.set_action('jump')
        yield 1
    while(not on_ground):
        player.set_action('fall')
        yield 1
    player.set_action('jump_squat')
    yield 6

def play_grass_sounds():
    while(1):
        if player_movement[0] != 0 and on_ground:
            random.choice(sounds['grass']).play()
            yield 18 / dtf(dt)
        else:
            yield 5

def reset_ground_timer():
    global on_ground
    on_ground = True
    yield dtf(dt) * JUMP_BUFFER_DURATION
    on_ground = False
    yield 1

def reset_wall_slide_timer():
    global in_wall_slide
    in_wall_slide = True
    yield dtf(dt) * JUMP_BUFFER_DURATION
    in_wall_slide = False
    yield 1

queue_coroutine(play_grass_sounds())


#---------------------------------------------------------------------------------------------- GAME LOOP
while 1:
    #MOVE THE CAMERA
    scroll_target = (
        player.rect.x - SCROLL_OFFSET[0],
        player.rect.y - SCROLL_OFFSET[1]
    )
    true_scroll[0] += dtf(dt) * (scroll_target[0] - true_scroll[0]) / SCROLL_LAG
    true_scroll[1] += dtf(dt) * (scroll_target[1] - true_scroll[1]) / SCROLL_LAG
    scroll = [int(true_scroll[0]), int(true_scroll[1])]

    #DRAW THE BACKGROUND AND TILES
    display.fill(palette[0])

    pg.draw.rect(display, palette[2], pg.Rect(0, 120, 300, 80))
    for bg_obj in background_objects:
        obj_rect = pg.Rect(
            bg_obj[1][0] - scroll[0] * bg_obj[0],
            bg_obj[1][1] - scroll[1] * bg_obj[0],
            bg_obj[1][2],
            bg_obj[1][3]
        )
        indicator_color = palette[2] if bg_obj[0] == 0.5 else palette[2]
        draw_bordered_rect(display, indicator_color, palette[0], obj_rect, width = 1, border_radius = 2)

    tile_rects = process_tiles(display, scroll)

    #MOVE THE PLAYER
    player_movement = [0, 0]
    if coroutine_running(fall_coroutine):
        if right - left == 0:
            x_vel *= AIR_X_DECEL
            #TODO: fix dtf(dt) maybe
        else:
            x_vel += (right - left) * air_x_accel * dtf(dt)
        x_vel = max(min(x_vel, SPEED), -SPEED)
    else:
        x_vel = (right - left) * SPEED
    player_movement[0] = x_vel * dtf(dt)

    player_movement[1] += y_vel * dtf(dt)
    y_vel += GRV * dtf(dt)
    y_vel = min(y_vel, MAX_Y_VEL)

    collisions = player.move(player_movement, tile_rects)

    #PERFORM ACTIONS BASED ON COLLISIONS
    if collisions['bottom'] and not coroutine_running(jump_coroutine):
        y_vel = 0
        stop_coroutine(ground_timer_coroutine)
        ground_timer_coroutine = queue_coroutine(reset_ground_timer())

    if collisions['top']:
        y_vel += BONK_DECEL * dtf(dt)

    if (collisions['left'] or collisions['right']) and not on_ground:
        x_vel = 0
        if y_vel > -2 and not coroutine_running(jump_coroutine):
            player.set_flip(collisions['left'])
            stop_coroutine(wall_slide_timer_coroutine)
            wall_slide_timer_coroutine = queue_coroutine(reset_wall_slide_timer())
    if in_wall_slide:
        stop_coroutine(fall_coroutine)
        y_vel = min(y_vel, WALL_SLIDE_VEL * dtf(dt))

    #PLAYER ANIMATION (and falling)
    if in_wall_slide:
        player.set_action('wall_slide')
    elif not (coroutine_running(jump_coroutine) or coroutine_running(fall_coroutine)):
        if not on_ground:
            fall_coroutine = queue_coroutine(fall())
        elif player_movement[0] > 0:
            player.set_action('run')
            player.set_flip(False)
        elif player_movement[0] < 0:
            player.set_action('run')
            player.set_flip(True)
        else:
            player.set_action('idle')

    player.change_frame(1)
    player.blit_self(display, scroll)

    # TILE BREAK / PLACE INDICATOR
    indicator_pos = world_to_tile(scaled_mouse_pos()[0] + scroll[0], scaled_mouse_pos()[1] + scroll[1]) # in tile coordinates
    indicator_rect = pg.Rect(indicator_pos[0] * TILE_SIZE, indicator_pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
    indicator_rect_scrolled = pg.Rect(indicator_rect.x - scroll[0], indicator_rect.y - scroll[1], TILE_SIZE, TILE_SIZE)
    indicator_color = palette[0] if True in pg.mouse.get_pressed() else palette[5]
    pg.draw.rect(display, indicator_color, indicator_rect_scrolled, width = 1)

    #RECEIVE INPUT
    for event in pg.event.get():
        if event.type == KEYDOWN:
            if event.key == K_a:
                left = True
            elif event.key == K_d:
                right = True
            elif event.key == K_SPACE:
                if on_ground and not coroutine_running(jump_coroutine):
                    jump_coroutine = queue_coroutine(jump(4))
                elif in_wall_slide:
                    jump_coroutine = queue_coroutine(wall_jump(20))
            elif event.key == K_LSHIFT:
                shift_held = True

        if event.type == KEYUP:
            if event.key == K_a:
                left = False
            elif event.key == K_d:
                right = False
            elif event.key == K_LSHIFT:
                shift_held = False

        if event.type == MOUSEBUTTONDOWN:
            if not gui_click():
                mouse_presses = pg.mouse.get_pressed()
                if mouse_presses[2]:
                    if shift_held:
                        if get_tile(*indicator_pos, True) == 0:
                            set_tile(*indicator_pos, 5, True)
                    else:
                        if get_tile(*indicator_pos) == 0 and not player.rect.colliderect(indicator_rect):
                            set_tile(*indicator_pos, 5)
                elif mouse_presses[0]:
                    set_tile(*indicator_pos, 0, shift_held)

        if event.type == pg.QUIT:
            serialize(vol_muted = vol_muted)
            pg.quit()
            sys.exit()

    show_volume_button(display)

    surf = pg.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    pg.display.update()

    advance_coroutines()
    dt = clock.tick(60)
