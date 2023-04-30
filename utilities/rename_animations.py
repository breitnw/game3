from os import listdir, rename
base = 'utilities/textures'
for folder in listdir(base):
    if folder == '.DS_Store':
        continue
    subtract = 0
    for i, file in enumerate(sorted(listdir(base + '/' + folder))):
        if file == '.DS_Store':
            continue
        rename(
            base + '/' + folder + '/' + file, 
            base + '/' + folder + '/' + folder + '_' + str(i - 1) + '.png'
        )