-- This is the second export state (see data-final-fixes.lua for more information).
-- Here, we export the actual in-game prototypes that were generated by factorio.
-- The user has to create a new game or load a save for this file to execute!

local serializer = require("serialize")

-- Write to <factorio-dir>/script-output/filename
local function writeDataToFile(filename, data)
    game.write_file(filename, data)
end

local function scrapeData()
    -- @Feature: add SplitOutput mod setting
    writeDataToFile("recipes.json", serializer.stringify(game.recipe_prototypes))
    writeDataToFile("items.json", serializer.stringify(game.item_prototypes))
    writeDataToFile("fluids.json", serializer.stringify(game.fluid_prototypes))

    local craftingMachines = {}
    local belts = {}
    local pipes = {}
    for k, v in pairs(game.entity_prototypes) do
        if v.type == 'assembling-machine' or v.type == 'rocket-silo' or v.type == 'furnace' then
            craftingMachines[k] = v
        elseif v.type == 'transport-belt' then
            belts[k] = v
        elseif v.type == 'pipe' then
            pipes[k] = v
        end
    end

    local entities = {["crafting-machine"]=craftingMachines, belt=belts, pipe=pipes}
    writeDataToFile("entities.json", serializer.stringify(entities))
end
 
script.on_event(defines.events.on_player_created, function(event)
    scrapeData()
    game.players[event.player_index].print("Successfully scraped the game data!")
end)