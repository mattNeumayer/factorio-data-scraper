from PIL import Image
import re
import zipfile
import sys
from pathlib import Path
import io

# Process the IconSpecification:
# https://wiki.factorio.com/Types/IconSpecification
# iconSpec should contain either 'icon' or 'icons'

def process(iconSpec, dirs, outputFileName, warn=True):
    if 'icon' in iconSpec:
        oldIconSpec = iconSpec['icon']
        image = processSingleIcon(iconSpec, dirs)
    elif 'icons' in iconSpec:
        oldIconSpec = iconSpec['icons']
        image = processMultipleIcons(iconSpec, dirs)
    else:
        if warn:
            if 'name' in iconSpec:
                print(f"\nWARN No icon or icons found for {iconSpec['name']}")
            else:
                print("\nWARN No icon or icons found")
        return (None, None)
    
    iconSpec['icon'] = outputFileName
    image.save(dirs['output'] / outputFileName)
    return (outputFileName, oldIconSpec)


def processMultipleIcons(iconSpec, dirs):
    if 'icon_size' in iconSpec:
        iconSize = iconSpec['icon_size']

    background = None
    for icon in iconSpec['icons']:
        if 'icon_size' in icon:
            layerSize = icon['icon_size']
        else:
            layerSize = iconSize
        
        # tint, shift, scale
        with openImage(icon['icon'], dirs) as image:
            image = image.crop((0, 0, layerSize, layerSize))
            if 'tint' in icon:
                tint = icon['tint']

                tintArr = [0.0, 0.0, 0.0, 1.0]
                if isinstance(tint, list):
                    tintArr = tint
                    if len(tintArr) == 3:
                        tintArr[3] = 1.0
                else:
                    for i, k in enumerate(['r', 'g', 'b', 'a']):
                        if k in tint:
                            tintArr[i] = tint[k]
                
                bands = image.split()
                r = bands[0].point(lambda i: i * tintArr[0])
                g = bands[1].point(lambda i: i * tintArr[1])
                b = bands[2].point(lambda i: i * tintArr[2])
                a = bands[3].point(lambda i: i * tintArr[3])
                image = Image.merge('RGBA', [r,g,b,a])
            if not background:
                background = image
            else:
                background.alpha_composite(image)
            
    return background


def processSingleIcon(iconSpec, dirs):
    iconSize = iconSpec["icon_size"]    
    with openImage(iconSpec['icon'], dirs) as image:
        image = image.crop((0, 0, iconSize, iconSize))
        return image


def openImage(path, dirs):
    parts = re.split(r'__(.*)__/', path)
    assert(len(parts) == 3)     # the first part is empty string because regex reasons
    
    mod = parts[1]
    relativePath = parts[2]
    
    if mod == "base" or mod == "core":
        modDir = dirs['game'] / 'data' / mod
    else:
        modDir = dirs['mods'] / mod

    if modDir.is_dir():
        return Image.open(modDir / relativePath).convert('RGBA')
    else:
        modDir = list(modDir.parent.glob(f'{mod}*.zip'))[0] # @Incomplete: This just guesses the mod version, bad if 2 versions are there.
        if zipfile.is_zipfile(modDir):
            modZip = zipfile.ZipFile(modDir, 'r') 
            resultBytes = io.BytesIO(modZip.read(modDir.stem + "/" + relativePath))
            return Image.open(resultBytes).convert('RGBA')
        else:
            sys.exit("ERROR  Failed to access mod '{}': It is neither a .zip file nor a folder")

