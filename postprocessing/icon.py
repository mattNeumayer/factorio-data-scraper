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
    image.save(dirs['icons'] / outputFileName)
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
        
        with openImage(icon['icon'], dirs) as image:
            image = image.crop((0, 0, layerSize, layerSize))

            if 'tint' in icon:
                # The color specs are so forgiving to user...
                tint = icon['tint']
                tintArr = [0.0, 0.0, 0.0, 0.0]

                if isinstance(tint, list):
                    maxVal = 255 if max(icon['tint']) > 1.0 else 1.0
                    tintArr = tint
                    if len(tint) == 3:
                        tintArr.append(maxVal)
                else:
                    maxVal = 255 if max([tint[k] for k in ['r', 'g', 'b', 'a'] if k in tint]) > 1.0 else 1.0
                    tintArr[3] = maxVal
                    for i, k in enumerate(['r', 'g', 'b', 'a']):
                        if k in tint:
                            tintArr[i] = tint[k]
                
                bands = image.split()
                r = bands[0].point(lambda i: i * tintArr[0] / maxVal)
                g = bands[1].point(lambda i: i * tintArr[1] / maxVal)
                b = bands[2].point(lambda i: i * tintArr[2] / maxVal)
                a = bands[3].point(lambda i: i * tintArr[3] / maxVal)
                image = Image.merge('RGBA', [r,g,b,a])

            if 'shift' in icon:
                shift = icon['shift']
                image = image.transform(image.size, Image.AFFINE, (1, 0, shift[0], 0, 1, shift[1]))
                image = image.crop((0, 0, layerSize, layerSize))
            
            if 'scale' in icon:
                newWidth  = int(image.size[0]*icon['scale'])
                newHeight = int(image.size[1]*icon['scale'])
                image = image.resize((newWidth, newHeight))
                # Well, lets be honst the user of this post-processor has to decide about the scale...
                pass
            
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

