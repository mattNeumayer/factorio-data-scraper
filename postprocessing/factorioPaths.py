import os
import platform
import sys
from pathlib import Path


def isPotentialModDir(dir):
    return dir.is_dir() and (dir / 'mod-list.json').is_file()

def isPotentialGameDir(dir):
    return dir.is_dir() and (dir / 'data' / 'core' / 'info.json').is_file()


def guessModsPath():
    # We are usually in a subfolder of the scraper mod, i.e. mods is 2 folder above.
    thisFile = Path(__file__).resolve()
    parents = thisFile.parents
    if len(parents) > 2 and parents[2].name == 'mods':
        if isPotentialModDir(parents[2]):  
            return parents[2]

    # Check the default dir
    osName = platform.system()
    p = None
    if osName == 'Linux':
        p = Path(r'~/.factorio/mods').resolve()
    elif osName == 'Windows':
        p = Path(r'%appdata%/Factorio').resolve()
    elif osName == 'Darwin':
        p = Path(r'~/Library/Application Support/factorio').resolve()
    
    if p and isPotentialModDir(p):
        return p
    else:
        return None


def guessGamePath():
    # On portable installs the mod dir is a subfolder of the game dir
    thisFile = Path(__file__).resolve()
    parents = thisFile.parents
    if len(parents) > 3 and parents[2].name == 'mods':
        if isPotentialGameDir(parents[3]):  
            return parents[3]

    # Check the default dir
    osName = platform.system()
    if osName == 'Linux':
        manualInstall = Path('~/.factorio').resolve()
        if isPotentialGameDir(manualInstall):
            return manualInstall

        steam = Path('~/.steam/steam/SteamApps/common/Factorio').resolve()
        if isPotentialGameDir(steam):
            return steam

    elif osName == 'Windows':
        # Windows mess incoming
        progFiles = Path(os.environ["ProgramW6432"])
        manualInstall = (progFiles / 'Factorio').resolve()
        if isPotentialGameDir(manualInstall):            
            return manualInstall

        import winreg
        with winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Wow6432Node\Valve\Steam') as key:
            steamRoot = Path(winreg.QueryValue(key, 'InstallPath'))
            if steamRoot:
                steam = (steamRoot / 'steamapps' / 'common' / 'Factorio').resolve()
                if isPotentialGameDir(steam):
                    return steam

    elif osName == 'Darwin':
        steam = Path('~/Library/Application Support/Steam/steamapps/common/Factorio/factorio.app/Contents').resolve()
        if isPotentialGameDir(steam):
            return steam
    
    return None


def getPaths(args):
    gamedir = None
    moddir = None

    if args.game:
        gamedir = Path(args.game).resolve()
        if not isPotentialGameDir(gamedir):
            sys.exit(f"ERROR  Invalid game path: {gamedir}")

    
    if args.mods:
        moddir = Path(args.mods).resolve()
        if not isPotentialModDir(moddir):
            sys.exit(f"ERROR  Invalid mod path: {moddir}")

    if not gamedir:
        gamedir = guessGamePath()
        if not gamedir:
            sys.exit(f"ERROR  Unable to find your factorio install. Please specify the --game argument")
    
    if not moddir:
        moddir = guessModsPath()
        if not moddir:
            sys.exit(f"ERROR  Unable to find your mods folder. Please specify the --mods argument")

    print("\nUsing:")
    print(f"  game = {gamedir}")
    print(f"  mods = {moddir}\n")
    return {"game": gamedir, "mods": moddir}
