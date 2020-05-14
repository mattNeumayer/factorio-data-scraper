from PIL import Image, ImageChops
import re
import zipfile
import sys
from pathlib import Path
import io

# Process the IconSpecification:
# https://wiki.factorio.com/Types/IconSpecification
# iconSpec should contain either 'icon' or 'icons'

outputSize = 64     # @Feature: Make CLI arg
overflowCounter = 0
overflowCounterBad = 0

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
    with open(dirs['icons'] / outputFileName, 'wb') as f:
        image.save(f)
    return (outputFileName, oldIconSpec)


def processSingleIcon(iconSpec, dirs):
    iconSize = iconSpec["icon_size"]    
    with openImage(iconSpec['icon'], dirs) as image:
        image = image.crop((0, 0, iconSize, iconSize))
        return image.resize((outputSize, outputSize))


def processMultipleIcons(iconSpec, dirs, slack=0):
    ## 
    #
    # The Factorio behaviour is as follows: 
    #   If layers do NOT specify 'scale' they are resized to 32px* (which is usually also 
    #   the size of the final icon), otherwise their 'icon_size' is scaled by 'scale'.
    # In addition, the first layer drives the final size of the icon:
    #   If it does NOT specify 'scale' it will be resized to 32px* (just like other layers) and
    #   therefore the final size is 32px*, otherwise if the first layer DOES specify 'scale'
    #   (this NEVER happens in vanilla!) the first layer will be scaled and the final icon size 
    #   changes (increases if scale > 1, decreases if scale < 1). 
    #
    # Note: 
    #   This affects the other layers because if they do NOT specify 'scale' and the final
    #   icon size changes, they will still be resized to 32px*, which is now smaller 
    #   (1st layer scale > 1) or larger relative to the final icon size. 
    #
    # Example 1: 1st layer: { icon_size: 32 }, 2nd layer { icon_size: 64, scale: 0.25 }
    #            => The 1st layer has no 'scale' -> rescaled to 32px and the final size is also 32px.
    #            => The 2nd layer is drawn IN THE CENTER (!) with size 64*0.25 = 16px.
    #
    # Example 2: 1st layer: { icon_size: 64, scale: 2 }, 2nd layer { icon_size: 32 }
    #            => The 1st layer is scaled to 128px -> final size also increases to 128px.
    #            => (!!!) The 2nd layer has no 'scale' and will be drawn at fixed size 32px.
    #            => in-game the icon will be scaled from 128px to whatever size needed,
    #               the result is that the first layer fills the icon, but the 2nd layer is only
    #               has 1/4 of the width and height !!!
    #  
    # The result of example 2 is somewhat unintuitive because the 2nd layer never specified a scale
    # but it is drawn as if it had 'scale'=0.25 ...
    #
    # (*) Conclusion:
    #   Whenever I said 32px is the "size of the final icon" that is assumed based on the fact that
    #   icons are scaled to 32px-equivalent by default, i.e. 'scale'=1 is equivalent to no scale only 
    #   if 'icon_size'=32.
    #   Of course, internally you could increase the default "final size" of icons and then load 
    #   layers that don't specify 'scale' at whatever your 32px-equivalent is. 
    #   (!) If fact, Factorio DOES this because specifying a 'scale' on the 1st layer does not result
    #   in a more pixelated icon => There is a minimum final size.
    #   BUT Factorio 0.18.22 will crash if the 1st layer has an insanely large scale ('scale'=50 for me)!
    #
    # Shifting: 
    #   Shifting is also in 32px-equivalent (i.e. shift by 8 shifts by 1/4 the icon size).
    #
    # [Sources]
    # https://forums.factorio.com/viewtopic.php?p=482444#p482444
    # My own experiments
    ##

    ## 
    # My approach:
    # 
    # Definitons: 
    #   outputSize:     The real "final size" we want to output. 
    #   requestedSize:  The relative size that the first layer wants to be (usually == 32px).
    #   implicitScale:  The scale factor between what **we** want (outputSize) and 
    #                   what **the first layer** wants (requestedSize)
    #
    # Then 'implicitScale' converts from the relative (32px-equivalent) size to the real outputSize,
    # i.e everything gets scaled by implicitScale.
    #
    ##

    iconSizes = []
    for layer in iconSpec['icons']:
        if 'icon_size' in layer: 
            iconSizes.append(layer['icon_size'])
        else:
            iconSizes.append(iconSpec['icon_size'])


    firstLayer = iconSpec['icons'][0]
    if 'scale' in firstLayer:
        requestedSize = firstLayer['scale'] * iconSizes[0]
    else:
        # 99% of the time the 1st layer has no scale and we end up here!
        requestedSize = 32

    implicitScale = outputSize / requestedSize

    result = Image.new('RGBa', (outputSize + slack, outputSize + slack), (0, 0, 0, 0))

    lostAlpha = False
    for idx, layer in enumerate(iconSpec['icons']):
        with openImage(layer['icon'], dirs) as im:
            # Everything in Factorio is using pre-multiplied alpha
            im = im.convert('RGBa')

            # First crop the image to its real size, making it square and getting rid of mipmaps.
            im = im.crop((0, 0, iconSizes[idx], iconSizes[idx]))

            # Applying the tint is independent of scaling.
            if 'tint' in layer:
                tint = layer['tint']
                tintAsArray = []

                # Convert {'r','b','g'} into array
                if isinstance(tint, list):
                    tintAsArray = tint.copy()
                else:
                    for k in ['r','g','b']:
                        if k in tint:
                            tintAsArray.append(tint[k])
                        else:
                            tintAsArray.append(0)
                    if 'a' in tint:
                        tintAsArray.append(tint['a'])
                
                # Determine if range is 0-1.0 or 0-255 and normalize to 0-255
                if max(tintAsArray[0:2]) <= 1.0:
                    tintAsArray = [int(x * 255) for x in tintAsArray]

                if len(tintAsArray) == 3:
                    # Default alpha is 255
                    tintAsArray.append(255)
                elif len(tintAsArray) == 4 and tintAsArray[3] == 0:
                    lostAlpha = True
                    pass

                im = applyTint(im, tintAsArray)


            if 'scale' in layer:
                # im.size[0] * layer['scale'] == size in 32px-equivalent
                scaledSize = im.size[0] * layer['scale'] * implicitScale
                im = resizeLayer(im, scaledSize, outputSize=outputSize + slack)
            else:
                # If no 'scale': Load as 32px (in 32px-equivalent)
                scaledSize = 32 * implicitScale
                im = resizeLayer(im, scaledSize, outputSize=outputSize + slack)

            assert(im.size == result.size)

            if 'shift' in layer:
                # 'shift' is in 32px-equivalent
                leftShift = int(layer['shift'][0] * implicitScale)
                topShift  = int(layer['shift'][1] * implicitScale)               

                if slack == 0:
                    # Give some slack for icons that barely overflow... 
                    # This icon business is so f*ing difficult even mod devs don't understand it...
                    data = im.getbbox()
                    overflow = 0
                    direction = ""

                    if data != None:
                        (left, upper, right, lower) = data

                        if (left + leftShift) < 0:
                            overflow = max(overflow, abs(left + leftShift))
                            direction = "left"
                        if (right + leftShift) > outputSize:
                            overflow = max(overflow, (right + leftShift) - outputSize)
                            direction = "right" 
                        if (upper + topShift) < 0:
                            overflow = max(overflow, abs(upper + topShift))
                            direction = "top"
                        if (lower + topShift) > outputSize:
                            overflow = max(overflow, (lower + topShift) - outputSize)
                            direction = "bottom"
                    
                    if overflow > 0:
                        if overflow > 4:
                            global overflowCounterBad
                            overflowCounterBad += 1
                            print(f"\nWARN  Icon overflows by {overflow} on the {direction} ({iconSpec['name']})")
                        else:
                            global overflowCounter
                            overflowCounter += 1
                        
                        # Start over with slack...
                        return processMultipleIcons(iconSpec, dirs, slack=min(4, overflow))

                transparent = Image.new('RGBa', result.size, (0, 0, 0, 0))
                transparent.paste(im, box=(leftShift + slack, topShift + slack))
                im = transparent
            
            result = blend(result, im)


    if lostAlpha:
        bands = result.split()
        mapToBlack = [0, 0, 0] + [255] * 253
        mask = bands[0].point(mapToBlack, mode='1')
        mask = ImageChops.add(mask, bands[1].point(mapToBlack, mode='1'))
        mask = ImageChops.add(mask, bands[2].point(mapToBlack, mode='1'))
        mask = ImageChops.subtract(mask, bands[3].point(mapToBlack, mode='1'))

        background = Image.new('RGBa', result.size, color=(0,0,0,0))
        grey = Image.new('RGBa', result.size, color=(113,113,113,200))
        background.paste(grey, mask=mask)
    
        result = blend(background, result)

    return result.convert('RGBA')


# Resizes image to newSize and centers it on a transparent background of outputSize.
# => The returned image is of outputSize, with scaled input image at the center!
def resizeLayer(im, newSize, outputSize):
    resized = im.resize((int(newSize), int(newSize)))   
    if (newSize == outputSize):
        return resized
    else:
        canvas = Image.new('RGBa', (outputSize, outputSize), (0, 0, 0, 0))
        offset = int((outputSize - newSize) / 2)
        canvas.paste(resized, box=(offset, offset))
        return canvas


def applyTint(im, tint):
    assert(im.mode == 'RGBa')
    assert(len(tint) == 4)
    assert(type(tint[0]) == int)
    ## 
    # Multiply each channel individually with the corresponting value in tint.
    # This can NOT clip because tint is in [0, 255]
    #
    # Equivalent to:
    # bands = []  
    # for i, b in enumerate(im.split()):
    #   monoColor = Image.new(mode='L', size=im.size, color=int(tint[i] * 255))
    #   bands.append(ImageChops.multiply(b, monoColor))
    #
    ##
    tintColor = Image.new(mode='RGBA', size=im.size, color=tuple(tint))     # Here, RGBA is correct!
    return ImageChops.multiply(im, tintColor)


def blend(dest, src):
    assert(dest.mode == 'RGBa')
    assert(src.mode == 'RGBa')

    # RGB_src + RGB_dest * (1 - alpha_src) 
    # None of the composite / blend functions in PIL do this ?!?
    bands = [] 
    alphaSrc = src.getchannel('a')
    for destBand, srcBand in zip(dest.split(), src.split()):
        result = ImageChops.add(srcBand, ImageChops.multiply(destBand, ImageChops.invert(alphaSrc)))
        bands.append(result)

    return Image.merge(bands=bands, mode='RGBa')


def openImage(path, dirs):
    parts = re.split(r'__(.*)__/', path)[1:]
    assert(len(parts) == 2)
    
    mod = parts[0]
    relativePath = parts[1]
    
    if mod == "base" or mod == "core":
        modDir = dirs['game'] / 'data' / mod
    else:
        modDir = dirs['mods'] / mod

    image = None
    if modDir.is_dir():
        image = Image.open(modDir / relativePath)
    else:
        # @Incomplete: This just guesses the mod version, bad if 2 versions are there.
        modDir = list(modDir.parent.glob(f'{mod}*.zip'))[0] 
        if zipfile.is_zipfile(modDir):
            modZip = zipfile.ZipFile(modDir, 'r') 
            resultBytes = io.BytesIO(modZip.read(modDir.stem + "/" + relativePath))
            image = Image.open(resultBytes)
        else:
            sys.exit("ERROR  Failed to access mod '{}': It is neither a .zip file nor a folder")

    return image.convert('RGBA')


def reportOverFlow():
    if overflowCounter > 0:
        print(f"\nINFO  {overflowCounter} icon(s) overflowed, but were fixed")
    if overflowCounterBad > 0:
        print(f"WARN  {overflowCounterBad} icon(s) overflowed badly (>4 pixels) and were clipped...")