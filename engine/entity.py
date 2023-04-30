import pygame
from . import animation

def blit_center(target_surface, surface, pos):
    center_x = int(surface.get_width() / 2)
    center_y = int(surface.get_height() / 2)
    target_surface.blit(surface, (pos[0] - center_x, pos[1] - center_y))

class Entity:
    global anim_database, anim_higher_database

    def __init__(self, x, y, width, height, entity_type):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rotation = 0
        self.rect = pygame.rect.Rect(x, y, width, height)
        self.img_offset = [0, 0]
        self.anim_action = 'idle'
        self.anim_tags = []
        self.anim_frame = 0
        self.anim_sequence = []
        self.flip = False
        self.type = entity_type

        self.set_action(self.anim_action, True)

    def collision_test(self, rect, tiles):
        hit_list = []
        for tile in tiles:
            if rect.colliderect(tile):
                hit_list.append(tile)
        return hit_list

    def move(self, movement, tiles):
        collision_types = {'top': False, 'bottom': False, 'left': False, 'right': False}

        self.x += movement[0]
        self.rect.x = int(self.x)
        hit_list = self.collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[0] > 0:
                self.rect.right = tile.left
                collision_types['right'] = True
            elif movement[0] < 0:
                self.rect.left = tile.right
                collision_types['left'] = True
            self.x = self.rect.x
        
        self.y += movement[1]
        self.rect.y = int(self.y)
        hit_list = self.collision_test(self.rect, tiles)
        for tile in hit_list:
            if movement[1] > 0:
                self.rect.bottom = tile.top
                collision_types['bottom'] = True
            elif movement[1] < 0:
                self.rect.top = tile.bottom
                collision_types['top'] = True
            self.y = self.rect.y

        return collision_types
    
    def set_img_offset(self, offset):
        self.img_offset = offset
    
    def get_center(self):
        x = int(self.width / 2)
        y = int(self.height / 2)
        return (x, y)

    def set_action(self, action_id, force = False):
        if self.anim_action != action_id or force:
            self.anim_action = action_id 
            new_anim = animation.anim_higher_database[self.type][action_id]
            self.anim_sequence = new_anim[0]
            self.anim_tags = new_anim[1]
            self.anim_frame = 0
    
    def change_frame(self, amount):
        self.anim_frame += amount
        while self.anim_frame >= len(self.anim_sequence):
            if 'loop' in self.anim_tags:
                self.anim_frame -= len(self.anim_sequence)
            else:
                self.anim_frame = len(self.anim_sequence) - 1
        while self.anim_frame < 0:
            if 'loop' in self.anim_tags:
                self.anim_frame -= len(self.anim_sequence)
            else:
                self.anim_frame = 0
    
    def set_flip(self, value: bool):
        self.flip = value

    def get_current_img(self):
        return pygame.transform.flip(animation.anim_frame_database[self.anim_sequence[self.anim_frame]], self.flip, False)
    
    #TODO: Fix center blit -----------------------------------------------------------------------------------------------###
    def blit_self(self, surface, scroll):
        img = self.get_current_img()
        img_half_width, img_half_height = img.get_width() / 2, img.get_height() / 2
        img_rotated = pygame.transform.rotate(img, self.rotation)
        blit_center(surface, img_rotated, (
            int(self.x) - scroll[0] - self.img_offset[0] + img_half_width,
            int(self.y) - scroll[1] - self.img_offset[1] + img_half_height,
        ))

    
    
        