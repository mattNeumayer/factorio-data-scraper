# Factorio Data Scraper

This repo contains two projects:
1. A Factorio mod that allows you to export the Factorio prototypes used in your (potentially modded) game.
2. A Python script (in postprocessing) which can be used to post-process the JSON files exported by the mod.

## Features
* Export data from **any mod configuration**
* Export **localisation** (see [Tutorial:Localisation](https://wiki.factorio.com/Tutorial:Localisation))
* Collect and normalize **icons** for all item, recipes, etc. (see [IconSpecification](https://wiki.factorio.com/Types/IconSpecification))

## Factorio Mod (aka zzythumdatascraper) 
The mod can be added just like any other mod:
Either clone this repo into your mods folder or use the zip file which can be found in Releases.
**Note**: The directory needs to be called 'zzythumdatascraper_0.1.0'!

The mod works in two stages:
1. It will export data during the startup of the game (data stage) and write this data to your factory-current.log.
2. Then, it will export the Lua Prototype data once you create a new game or load a save.

| Filename  	| Exported Data  	| Location | Description   	|
|---	|---	|---	|---	|
| factorio-current.log  	| [data.raw](https://wiki.factorio.com/Data.raw) | Factorio install folder	| This is the data submitted by mods. See data-final-fixes.lua for more information   	|
| recipes.json  	| [LuaRecipePrototypes](https://lua-api.factorio.com/latest/LuaRecipePrototype.html)   	| script-output/  	| All recipes available in-game |
| items.json  	| [LuaItemPrototypes](https://lua-api.factorio.com/latest/LuaItemPrototype.html)   	| script-output/ 	| All items available in-game |
| fluids.json  	| [LuaFluidPrototypes](https://lua-api.factorio.com/latest/LuaFluidPrototype.html)   	| script-output/ 	| All fluids available in-game |
| entities.json  	| [LuaEntityPrototypes](https://lua-api.factorio.com/latest/LuaEntityPrototype.html)   	| script-output/ 	| **Only** crafting-machines, belts and pipes |

**Note**: You need to create a new game or load a save for this mod to work!
 
The script-output folder can either be where your mods are saved (e.g. %appdata%) or in your Factorio install folder.

#### Issues
- For now, I only output some of the LuaEntityPrototypes and only some of their properties, because the entities are quite large and contains lots of circular dependencies which have to be manually resolved.
- Mods are loaded in their dependency order fist, then by number of dependencies, and finally by [natural sort order](https://lua-api.factorio.com/latest/Data-Lifecycle.html). 
  Therefore, some mods can have there data-final-fixed.lua executed after this mod. This is somewhat mitigated by the weird name of this mod.
  **If any mods are loading after this one, you should add those mods to the dependencies of this mod!**
  
## Python Post-Processing
The [postprocessing folder](../postprocessing) contains the python postprocessor. 
The main features are:
- Localisation
- Icon collection
- Data normalization and pruning
- Merging all data into a single .json and a folder of icons

Usage:
```bash
python3 postprocessing/main.py <Output-Folder>
```
This will try to guess the Factorio install and mod folder based on your OS and some default install locations. Optionally, you can specify the paths like this:
```bash
python3 postprocessing/main.py <Output-Folder> --game <Factorio-Folder> --mods <Mod-Folder>
```
**Note**: The script will write output.json and /icons/*.png into \<Output-Folder\>. Most nodes in the JSON will have a 'icon' property which contains the filename of a file in /icons .

The output.json has the following format:
```javascript
{
  'recipes': {
      '<recipe-name>': { ... },
      ...
  },
  'items': {
      '<item-name>': { ... },
      ...
  },
  'fluids': {
      '<fluid-name>': { ... },
      ...
  },
  'entities': {
      'crafting-machine': { ... },
      'belt': { ... },
      'pipe': { ... },
  },
  'groups': {
      '<group-name>': {
          'subgroups':  { ... },
             ...
      },
   },
}
```
The output.json can be quite large so please open it only in a browser or some good text editor! 

