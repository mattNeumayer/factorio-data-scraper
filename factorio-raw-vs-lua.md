This documents compares the data struct used in the data stage (data.raw) with the ones used during gameplay (i.e. the suff avaiable through the Lua API).

# Prototype/Recipe vs. LuaRecipePrototype

| Data.raw               	    | Lua                           	| Description 	                |
|-----------------------------  |--------------------------------	|----------------------------   |
| crafting_machine_tint  	    |                               	| Visual-only  	                |
| icons, icon, icon_size 	    |                               	| Icons        	                |
| expensive, normal        	    |                               	| Data.raw allows you to specify two recipe modes. Lua only uses one, Lua can query this using 'game.difficulty_settings.recipe_difficulty'                 |
| type                   	    |                               	| Must be "recipe" 	            |
|                        	    | group                         	| ????         	                |
| result, result_count, results	| products                          | Same data in different format |

##### Note: LuaRecipe vs. LuaRecipePrototype
LuaRecipe has:
    - a 'force' property because LuaRecipe are per force
    - a 'prototype' property to access the underlying LuaRecipePrototype
    - the 'enabled' property is writeable and reflects the current research progress
Except for that, LuaRecipe it is a *strict* subset of LuaRecipePrototype!


# Prototype/Item vs. LuaItemPrototype

| Data.raw               	| Lua                           	| Description 	                |
|------------------------	|--------------------------------	|----------------------------   |
| dark_background_icons, dark_background_icon  	|               | Icons       	                |
| icons, icon, icon_size 	|                               	| Icons        	                |
| fuel_glow_color        	|                               	| Visual-only                   |
| pictures                  |                               	| Visual-only 	                |
|                           | can_be_mod_opened                 | ??? 	                        |
|                           | group                             | ???        	                |


## Prototype/AmmoItem
- Both: 
    - magazine_size
    - reload_time
- Both (different names):
    - ammo_type vs. get_ammo_type()

## Prototype/Capsule
- Both: 
    - capsule_action
    - robot_action
- Only Data.raw: 
    - radius_color

## Prototype/Gun
- Both: 
    - attack_parameters

## Prototype/ItemWithLabel
- Both: 
    - default_label_color
    - draw_label_for_cursor_render

## Prototype/ItemWithInventory
- Both: 
    - inventory_size
    - filter_mode, insertion_priority_mode
    - item_filters
    - item_group_filters
    - item_subgroup_filters

- Only Data.raw: 
    - 
- Both (different names):
    * filter_message_key vs. localised_filter_message
    * extends_inventory_by_default vs. extend_inventory_by_default


## Prototype/BlueprintBook
- Both: show_in_library

## Prototype/SelectionTool
- Both:     
    - (alt_)selection_cursor_box_type
    - (alt_)entity_filters
    - (alt_)entity_type_filters
    - (alt_)tile_filters
    - (alt_)entity_filter_mode
    - (alt_)tile_filter_mode
    - always_include_tiles
    - show_in_library

- Both (different names):
    - (alt_)selection_color vs. (alt_)selection_border_color
    - (alt_)selection_mode vs. (alt_)selection_mode_flags

- Only Data.raw:
    - mouse_cursor 

## Prototype/CopyPasteTool
- Only Data.raw:
    - cuts

## Prototype/DeconstructionItem
- Both (different names):
    - entity_filter_count vs. entity_filter_slots
    - tile_filter_count vs. tile_filter_slots
 
## Prototype/UpgradeItem
- Both:
    - mapper_count

## Prototype/Module
- Both:
    - category
    - tier
    - limitation_message_key
- Both (different names):
    - limitation vs. limitations
    - effect vs. module_effects

## Prototype/RailPlanner
- Both:
    - curved_rail
    - straight_rail 

## Prototype/Tool
- Both:
    - durability
    - durability_description_key
    - infinite
- Only Data.raw:
    - durability_description_value

## Prototype/Armor
- Both:
    - equipment_grid
    - inventory_size_bonus
    - resistances

## Prototype/RepairTool
- Both:
    - speed
    - repair_result