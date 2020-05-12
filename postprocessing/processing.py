import json 
from pathlib import Path

from localisation import Localisation
from progressbar import ProgressBar

import icon

# main post-processing method
def process(data, dirs):
    loc = Localisation(dirs)

    data['groups'] = {}

    processItemsAndFuilds(data, loc, dirs)    
    processRecipes(data, loc, dirs)
    processEntities(data, loc, dirs)

    processGroups(data, loc, dirs)

    del data['raw']
    outFile = dirs['output'] / 'output.json'
    print(f"\nDone. Writing to:  {outFile}")
    with open(outFile, 'w') as f:
        json.dump(data, f)


def processItemsAndFuilds(data, loc, dirs):
    raw = data['raw']
    whitelists = createItemProperityWhitelists()

    def doProcessing(baseType):
        plural = baseType + 's'
        progress = ProgressBar(plural, len(data[plural]))
        for counter, (key, item) in enumerate(data[plural].items()):
            if counter % 50 == 0:
                progress.update(counter)
            
            if not 'type' in item:
                item['type'] = baseType
            
            rawItem = raw[item['type']][key]

            ## Localisation
            item["localised_name"]        = loc.resolve(item["localised_name"])
            item["localised_description"] = loc.resolve(item["localised_description"], warn=False)

            ## Icon
            newFilename, origIconSpec = icon.process(rawItem, dirs, outputFileName=f"{baseType}-{item['name']}.png")
            # Note: the icon data was on rawItem, we attach *both* the new filename ('icon') 
            # and the original icon data ('orig_icon') to item, the rest of rawItem will be discarded!   @Size
            item['icon'] = newFilename
            # item['orig_icon'] = origIconSpec

            addGroupData(data['groups'], item, 'recipes')

            if baseType == 'item':                
                fuelRelatedKey = ['fuel_category', 'fuel_value', 'fuel_acceleration_multiplier', 'fuel_top_speed_multiplier', 'fuel_emissions_multiplier']
                if item['fuel_category']:
                    item['fuel'] = {k: item[k] for k in fuelRelatedKey}
                
                ## Prune item data  @Size   
                for k in fuelRelatedKey:
                     del item[k]    
                deleteKeys(item, whitelists[item['type']])

        progress.finish()

    doProcessing('item')
    doProcessing('fluid')


def processRecipes(data, loc, dirs):
    raw = data['raw']
    progress = ProgressBar("recipes", len(data['recipes']))

    for counter, (key, recipe) in enumerate(data['recipes'].items()):
        if counter % 50 == 0:
            progress.update(counter)

        rawRecipe = raw['recipe'][key]
        
        ## Localisation
        recipe["localised_name"]        = loc.resolve(recipe["localised_name"])
        recipe["localised_description"] = loc.resolve(recipe["localised_description"], warn=False)

        ## Icon        
        # The newFilename is 'recipe-<name>.png'
        newFilename, origIconSpec = icon.process(rawRecipe, dirs, outputFileName='recipe-' + recipe['name'] + ".png", warn=False)
        if newFilename:
            recipe['icon'] = newFilename
            #recipe['orig_icon'] = origIconSpec
        else:
            if recipe['main_product']:
                # Fallback to the main_product
                fallback = recipe['main_product']
            else: 
                # Just use something...
                fallback = recipe['products'][0]

            fallbackType = fallback['type'] + 's'
            fallbackItem = data[fallbackType][fallback['name']]
            recipe['icon'] = fallbackItem['icon']
            #recipe['orig_icon'] = fallbackItem['orig_icon']

        addGroupData(data['groups'], recipe, 'recipes')
    
    progress.finish()


def processEntities(data, loc, dirs):
    raw = data['raw']

    total = sum([len(x) for x in data['entities'].values()])
    progress = ProgressBar("entities", total)

    counter = 0
    for (entityType, entitiesInType) in data['entities'].items():
        for (key, entity) in entitiesInType.items():
            if counter % 50 == 0:
                progress.update(counter)

            rawEntity = raw[entity['type']][key]

            ## Localisation
            entity["localised_name"]        = loc.resolve(entity["localised_name"])
            entity["localised_description"] = loc.resolve(entity["localised_description"], warn=False)

            ## Icon        
            newFilename, origIconSpec = icon.process(rawEntity, dirs, outputFileName='recipe-' + entity['name'] + ".png", warn=False)
        
            counter += 1
            
    progress.finish()


def processGroups(data, loc, dirs):
    groups = data['groups']
    raw = data['raw']

    empty_groups = set()
    for (key, rawGroup) in raw['item-group'].items():
        if key in groups:
            group = groups[key]
        else:
            empty_groups.add(key)
            print(f"WARN  Found empty item-group: {key}")
            continue

        ## Localisation
        group["localised_name"] = loc.resolve(group["localised_name"])

        ## Icon        
        newFilename, origIconSpec = icon.process(rawGroup, dirs, outputFileName='group-' + group['name'] + ".png")
        group['icon'] = newFilename
        group['orig_icon'] = origIconSpec

    
    for (key, rawSubgroup) in raw['item-subgroup'].items():
        parentGroupName = rawSubgroup['group']
        if parentGroupName in groups:
            parentGroup = groups[parentGroupName]
        else:
            if not parentGroupName in empty_groups:
                print(f"WARN  Found item-subgroup '{key}' with unknown parent: '{parentGroupName}'")
            continue
            
        if key in parentGroup['subgroups']:
            subgroup = parentGroup['subgroups'][key]
        else:
            print(f"WARN  Found empty item-subgroup: '{key}' (group: '{parentGroupName}')")
            continue

        ## Localisation
        subgroup["localised_name"] = loc.resolve(subgroup["localised_name"])


def addGroupData(groups, obj, itemType):
    group    = obj['group']
    subgroup = obj['subgroup']
    groupName    = group['name']
    subGroupName = subgroup['name']

    if not groupName in groups:
        group['subgroups'] = {}
        groups[groupName] = group

    storedGroup = groups[groupName]
    if not subGroupName in storedGroup['subgroups']:
        subgroup['items'] = []
        subgroup['recipes'] = []
        storedGroup['subgroups'][subGroupName] = subgroup

    storedGroup['subgroups'][subGroupName][itemType].append(obj['name'])
    obj['group'] = groupName
    obj['subgroup'] = subGroupName


# This is used to remove contitional fields (e.g. an item has 'reload_time' only if applicable).
def deleteKeys(obj, whitelist):
    toDelete = [k for k in obj.keys() if not k in whitelist]

    for key in toDelete:    
        #if obj[key]:
        #   print(f"WARN  Lost data: '{obj['name']}' had '{key}' (not whitelisted for: {obj['type']})")
        del obj[key]


# @Incomplete: This function is way to complicated for what is does...
def createItemProperityWhitelists():
    itemKeyInfo = json.load(open(Path(__file__).parent / 'iteminfo.json'))

    # Collect all transitive whitelist information
    whitelists = {}
    for itemType, info in itemKeyInfo.items():
        whitelists[itemType] = set(info['whitelist'])
        parent = info['parent']
        while parent:
            info = itemKeyInfo[parent]
            whitelists[itemType].update(info['whitelist'])
            parent = info['parent']

    return whitelists