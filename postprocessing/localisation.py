import os
import re
import zipfile

class Localisation:
    def __init__(self, dirs, locale='en'):
        self.locale = locale        
        self.EMPTY_CATEGORY = "no-category"
        self.dataPerMod = self.crawlLocalisation(dirs)
        self.data = {}

        for arr in self.dataPerMod.values():
            for category, items in arr.items():
                if not category in self.data:
                    self.data[category] = {}
                #for k, v in items.items():
                #    if k in self.data[category]:
                #        print(f"WARN  Overriding localised string '{category}-{k}'")
                self.data[category].update(items)

        print("\nINFO  Sucessfully loaded locale data.")


    def resolve(self, resource, warn=True):
        result = self.__resolve(resource, warn)
        if result is None:
            if warn:
                print(f"\nWARN: Failed to localize: {resource}")
            return ""
        else:
            return result

    def __resolve(self, resource, warn=True):
        if not isinstance(resource, list):
            return resource
        
        splits = resource[0].split('.', 1)

        if len(splits) == 1:
            # This is a regular string, not a localized string to lookup

            if resource[0] == "":
                # Quote: 
                # The special locale key: "" is used to concatenate, [...]
                result = ""
                for paritalResource in resource:
                    result += self.resolve(paritalResource, warn)
                return result
            else:
                # You can have basic stuff like '10' or 'and' in parts of a localized string
                return resource[0]

        assert(len(splits) == 2)   

        # Do the localized string lookup
        if splits[0] in self.data and splits[1] in self.data[splits[0]]:
            result = self.data[splits[0]][splits[1]]
        else:
            return None

        if len(resource) > 1:
            # @Incomplete: There are some weird hardcoded replacement patters.
            newResult = ""
            parts = re.split(r'(__\d__)', result)
            for part in parts:
                if re.match(r'(__\d__)', part):
                    arg = int(part[2:-2])
                    assert(len(resource) > arg)
                    newResult += self.resolve(resource[arg])
                else:
                    newResult += part

            return newResult
        else:
            return result
 
    def crawlLocalisation(self, dirs):
        result = {}
 
        # first crawl core and the base mod
        core = dirs['game'] / 'data' / 'core'
        base = dirs['game'] / 'data' / 'base'
        result['core'] = self.parseLocaleDataForSingleMod(core)
        result['base'] = self.parseLocaleDataForSingleMod(base)

        # Now third-party mods
        for modDir in dirs['mods'].iterdir():
            if modDir.is_dir() or modDir.suffix == '.zip':    # @Incomplete: zip
                modName = modDir.stem
                result[modName] = self.parseLocaleDataForSingleMod(modDir)
        
        return result

    def parseLocaleDataForSingleMod(self, modDir):
        result = {}

        if zipfile.is_zipfile(modDir):
            with zipfile.ZipFile(modDir, 'r') as modZip:
                files = modZip.namelist()
                zipInternalPath = f'{modDir.stem}/locale/{self.locale}'
                files = filter(lambda f: f.startswith(zipInternalPath) and f.endswith('.cfg'), files)
    
                for fileName in files:
                    with modZip.open(fileName, 'r') as cfgFile:
                        inputData = cfgFile.read().decode('utf-8').splitlines()
                        self.parseSingleFile(inputData, fileName, result)
        
        else:
            for localeFile in (modDir / 'locale' / self.locale).glob('*.cfg'):
                with open(localeFile) as f:
                    inputData = f.read().splitlines()
                    self.parseSingleFile(inputData, localeFile, result)
        
        return result

            
    def parseSingleFile(self, inputData, fileName, outputDict):
        currentCategory = self.EMPTY_CATEGORY

        for line in inputData:
            if line.startswith('['):
                currentCategory = line[1:-1]
                if not currentCategory in outputDict:
                    outputDict[currentCategory] = {}
            elif line == '' or line.isspace() or line.startswith(';'):
                continue
            else:
                splits = line.split('=')    # @Robustness
                if currentCategory == self.EMPTY_CATEGORY and not self.EMPTY_CATEGORY in outputDict:
                    outputDict[self.EMPTY_CATEGORY] = {}
                outputDict[currentCategory][splits[0]] = splits[1]

        if self.EMPTY_CATEGORY in outputDict:
            print(f'WARN  Localised strings without category ({fileName})')
