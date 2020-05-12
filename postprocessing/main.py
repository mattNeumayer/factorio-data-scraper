import argparse
import json
import sys
from pathlib import Path

import factorioPaths
import processing


def parseArgs():
    parser = argparse.ArgumentParser(description='Post-process the scraped Factorio data.')
    parser.add_argument('outputDir', help='Output directory for the icons and JSON file')
    parser.add_argument("-g", "--game", help='path of your factorio install (Optional: If not given tries to find Factorio at some default locations)')
    parser.add_argument("-m", "--mods", help='path of your mods directory (Optional: If not given tries to find /mods at some default locations)')

    args = parser.parse_args()
    dirs = factorioPaths.getPaths(args)

    dirs['output'] = Path(args.outputDir) if args.outputDir else Path.cwd()
    dirs['icons'] = dirs['output'] / 'icons'

    if not Path(dirs['output']).is_dir():
        sys.exit(f"ERROR  The given output path is not a directory!")

    dirs['icons'].mkdir(exist_ok=True)
    return dirs


def loadData(dirs):
    dataRaw = parseDataRaw(dirs)
    
    scriptOutput = dirs['game'] / "script-output"
    if not scriptOutput.is_dir():
        scriptOutput = dirs['mods'] / "script-output"
        if not scriptOutput.is_dir():
            sys.exit(f"ERROR Unable to find script-output. You have to run Factorio and create a new game (or load a save).")
    
    try:
        with open(scriptOutput / "recipes.json", 'r') as f:
            recipes = json.load(f)
        with open(scriptOutput / "items.json", 'r') as f:
            items = json.load(f)
        with open(scriptOutput / "fluids.json", 'r') as f:
            fluids = json.load(f)
        with open(scriptOutput / "entities.json", 'r') as f:
            entites = json.load(f)
    except:
        sys.exit(f"ERROR  Unable to open the script output. You have to run Factorio and create a new game (or load a save).")

    return {"raw": dataRaw, "recipes": recipes, "items": items, "fluids": fluids, "entities": entites}


def parseDataRaw(dirs):
    MARKER_START = "---- data export start ----"
    MARKER_END   = "---- data export end   ----"

    logFile = dirs['game'] / "factorio-current.log"
    if not logFile.is_file():
        sys.exit(f"ERROR  Unable to find factorio-current.log in: {dirs['game']}")

    # Slightly dumb code: parses the data between MARKER_START and MARKER_END as JSON.
    jsonData = ""
    with open(logFile, 'r') as f:
        foundStart = False
        for line in f:
            if MARKER_START in line:
                foundStart = True
            elif MARKER_END in line:
                break
            elif foundStart:
                jsonData += line

    if not jsonData:
        sys.exit(f"ERROR  Unable to parse factorio-current.log in: {dirs['game']}")
    return json.loads(jsonData)


if __name__ == "__main__":
    dirs = parseArgs()
    data = loadData(dirs)
    processing.process(data, dirs)