-- This file should run after all* other mods have completed their data stage.
-- The allows us to intercept the exact data which factorio will use to generate the prototypes.
-- In the control stage we will export these prototypes which allows us to later match and compare
-- the data provided by mods vs the prototypes used at gameplay time.
--
-- This two staged approach is necessary because the data stage has information that is not available
-- at the control stage (e.g. filepaths for sprites and localisation). BUT, on the other hand, the 
-- control stage has the *real* ground truth which we want to refer to for most of the information.
-- In addition the control stage can write to file, will in here in the data stage we can only dump to
-- log, which is super messy.
--
-- * the mods are loaded in alphabetical order, so hopefully no mod uses data-final-fixes after us..
--

local json = require("json")


-- We use these string to seperate our exported data from the rest of the log. 
local markerStart = "\n---- data export start ----\n"
local markerEnd   = "\n---- data export end   ----\n"

-- These lists can be configured for your liking. @Feature: Maybe convert these into mod settings.
-- Things in 'ignoreTopLevel' are only ignored at the top level of the data.raw struct.
-- Refer to https://wiki.factorio.com/Data.raw and for information about the format of data.raw. 
local ignoreToplevel = {
    -- audio and visual-only
    "ambient-sound",   
    "artillery-flare",
    "beam",
    "corpse",                   -- Misnamed: These are remnants, 'character-corpse' is *the* corpse!
    "decorative",
    "explosion",
    "leaf-particle",
    "optimized-decorative",
    "optimized-particle",
    "particle",
    "particle-source",
    "rail-remnants",
    "tile-effect",
    "trivial-smoke",
    "utility-sounds",  

    -- gui-ish stuff
    "arrow",
    "flying-text",
    "font", 
    "gui-style",
    "highlight-box",
    "tutorial",

    -- resource generation
    "autoplace-control",
    "noise-expression",
    "noise-layer",

    -- input stuff
    "custom-input",
    "shortcut",

    -- combat; some of this stuff might be needed??
    "artillery-projectile",
    "flame-thrower-explosion",  -- explosion + damage
    "projectile",
    "stream",
    "unit",
    "unit-spawner",

    -- Yeah... I dunno about these...
    "tree",         -- Kinda useful, but there are ~20 of these, maybe just export one?
    "tile",         -- These are the ingame tile visuals,  the item used to place(placeable_by) is listed under 'item'
    "cliff",        -- No one likes these anyways
}

-- These things are ignored throughout the whole data.raw tree. 
-- These tend to be either relatively large or their size adds up as they are used everywhere.
local ignoreAlways = { 
    "autoplace",                            -- Types/AutoplaceSpecification; data for resource gen => SUPER large (like 10MB)
    "animations", "animation",              -- Types/Animation; Huge arrays (frames) of these things
    "pictures", "picture",                  -- Types/Sprite; similar to sprites
    "circuit_wire_connection_points",       -- Types/WireConnectionPoint; these are actually kinda light-weight...
    "circuit_wire_connection_point",        --
    "circuit_connector_sprites",            -- Types/CircuitConnectorSprites
    "sprites", "sprite",                    -- Types/Sprite; sprites are NOT icons, they are the rendered placed-entities
}

-- Ignore any tables that contain the these fields (keys).
-- This is helpful because the 'ignoreAlways' uses the key to identity the type of data, but sometimes 
-- the type is used under many different keys, and listing all those keys would be annoying.
-- @Hack: In this case we don't remove the key, instead we just set the value to null...
local containsField = { 
    "hr_version",          -- Type: Sprite, RotatedSprite, Animation
    "connector_main",      -- Type: CircuitConnectorSprites
    "frame_count",         -- Type: AnimationVariations (and Animation)
    "rotations"            -- Type: AnimatedVector
}

-- @Cleanup: We could maybe use serialize.lua here
local jsonData = json.stringify(data.raw, false, containsField, ignoreAlways, ignoreToplevel)
log(markerStart..jsonData..markerEnd)
