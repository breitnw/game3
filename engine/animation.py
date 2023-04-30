import pygame, os, json

global anim_frame_database
anim_frame_database = {}
global anim_higher_database
anim_higher_database = {}

def load_anim_sequence(path, durations, colorkey = (255, 255, 255)):
    '''Loads a single animation sequence. 

    "path" should be the path to the directory containing the animation frames, including a / at the end. "durations" should 
    be a tuple with all of the individual frame durations. It must be the same length as the number of frames in the folder.'''

    global anim_frame_database
    frame_data = []
    for frame_index, duration in enumerate(durations):
        image_id = path + path.split('/')[-2] + '_' + str(frame_index)
        image = pygame.image.load(image_id + '.png').convert()
        image.set_colorkey(colorkey)
        anim_frame_database[image_id] = image.copy()
        for i in range(duration):
            frame_data.append(image_id)
    return frame_data


def load_anims(path, colorkey = (255, 255, 255)):
    '''Loads all of the animations in a directory. 
    
    "path" is the path to the directory containing the "animation_data.json" file, ending in a /. This directory should 
    also contain all of the entity animation directories. All animation frames should be named in the format [animation]_[frame].'''

    global anim_higher_database
    with open(path + 'animation_data.json', 'r') as file:
        data = json.load(file)

    for anim_path in data:
        num_frames = len([name for name in os.listdir(path + anim_path) if not name.startswith(".")])
        entity_info = anim_path.split('/')
        entity_name = entity_info[0]
        anim_id = entity_info[1]
        duration_data = data[anim_path]['durations']
        if isinstance(duration_data, int):
            duration_data = [duration_data for i in range(num_frames)]
        anim = load_anim_sequence(path + anim_path, duration_data, colorkey)
        tags = data[anim_path]['tags']

        if entity_name not in anim_higher_database:
            anim_higher_database[entity_name] = {}
        anim_higher_database[entity_name][anim_id] = (anim.copy(), tags)
