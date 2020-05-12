-- JSON serialization with support for Factorio's LuaObjects

local luaObjectInfo = require("luaobjectinfo")

-- @Cleanup: Helpers from json.lua
local function escape_str(s)
    local in_char  = {'\\', '"', '/', '\b', '\f', '\n', '\r', '\t'}
    local out_char = {'\\', '"', '/',  'b',  'f',  'n',  'r',  't'}
    for i, c in ipairs(in_char) do
        s = s:gsub(c, '\\' .. out_char[i])
    end
    return s
end

local function isArray(obj)
    if type(obj) ~= 'table' then return false end
    
    local i = 1
    for _ in pairs(obj) do
        if obj[i] ~= nil then i = i + 1 else return false end
      end
    return true
end

-- The keys are all numeric => Write a JSON array instead of a JSON object.
-- Assumes isArray(data) == true 
local function serializeArray(data, keyInParent)
    local i = 1
    local t = {}

    for _ in pairs(data) do
        if #t > 0 then t[#t + 1] = ', ' end
        t[#t + 1] = serialize(data[i], keyInParent)
        i = i + 1
    end 

    return '[ '..table.concat(t)..' ]'
end


-- This is regular lua table (or LuaCustomTable).
local function serializeEasyTable(data, keyInParent)
    if isArray(data) then 
        -- Parse into a JSON array instead of a JSON object
        return serializeArray(data, keyInParent)
    end

    local t = {}
    for k, v in pairs(data) do 
        if #t > 0 then t[#t + 1] = ', ' end
        t[#t + 1] = '"'..k..'": '
        t[#t + 1] = serialize(v, k)
    end

    return '{ '..table.concat(t)..' }'
end

-- Data is a LuaObject defined by the Factorio API.
-- These things can't be iterated (pairs/ipairs), which sucks for exporting but is great for
-- filtering by type...
local function serializeLuaObject(data, keyInParent)
    -- I took this vtype stuff from the Factorio Debug Extension
    -- https://github.com/justarandomgeek/vscode-factoriomod-debug
    -- https://factorio.com/blog/post/fff-337

    local vtype = data.object_name    

    local t = {} 
    -- Thanks to justarandomgeek we have predefined keys for all LuaObject types!
    local keys = luaObjectInfo.expandKeys[vtype]            
    if not keys then print("\nERROR: Missing keys for class " .. vtype) end

    for k, keyprops in pairs(keys) do
        if #t > 0 then t[#t + 1] = ', ' end
        t[#t + 1] = '"'..k..'": '
        t[#t + 1] = serialize(data[k], k)
    end

    -- LuaGroup is weird: It can be a group or subgroup, and depending on that
    -- different keys are present. 
    if vtype == 'LuaGroup' then 
        if keyInParent == 'group' then 
            -- group
            t[#t + 1] = ', "order_in_recipe": '
            t[#t + 1] = serialize(data.order_in_recipe)

            t[#t + 1] = ', "subgroups": [ '
            local t2 = {}
            -- @Cleanup: We only add the subgroup names to prevent infinite recursion 
            for k, v in ipairs(data.subgroups) do 
                if #t2 > 0 then t2[#t2 + 1] = ', ' end
                t2[#t2 + 1] = serialize(v.name)
            end
            t[#t + 1] = table.concat(t2)
            t[#t + 1] = ' ]'
        else
            -- subgroup
            -- @Cleanup: We only add the parent groups name to prevent infinite recursion 
            t[#t + 1] = ', "group": '
            t[#t + 1] = serialize(data.group.name)
        end  
    end

    if vtype == 'LuaEntityPrototype' then 
        t[#t + 1] = ', "next_upgrade": '
        if data.next_upgrade ~= nil then 
            t[#t + 1] = serialize(data.next_upgrade.name)
        else
            t[#t + 1] =  serialize(nil)
        end
    end

    return '{ '..table.concat(t)..' }'
end

local function serializeTable(data, keyInParent)
    if not (type(data.__self) == "userdata" and getmetatable(data) == "private") then
        -- I don't know why, but accoring to vscode-factoriomod-debug thats how you detect regular tables.
        return serializeEasyTable(data, keyInParent)
    end 

    -- This is a Factorio LuaObject (object_name is the "real" type)
    local vtype = data.object_name    

    if vtype == 'LuaCustomTable' then
        -- CustomTables are regular tables just lazy evaled.
        return serializeEasyTable(data, keyInParent)
    else
        return serializeLuaObject(data, keyInParent)
    end
end

function serialize(data, keyInParent)
    local vtype = type(data)

    if vtype == 'table' then
        return serializeTable(data, keyInParent)
    elseif vtype == 'string' then    
        return '"' .. escape_str(data) .. '"'
    elseif vtype == 'number' then    
        local numberStr = tostring(data)
        if as_key then
            -- This is kinda weird: a numberic key in a non-array?
            return '"' .. numberStr .. '"'
        elseif numberStr == 'inf' then
            return '"Infinity"'
        elseif numberStr == '-inf' then 
            return '"-Infinity"'
        elseif numberStr == 'nan' then 
            return '"NaN"'
        else
            return numberStr
        end
    elseif vtype == 'boolean' then
        return tostring(data)
    elseif vtype == 'nil' then
        return 'null'
    else
        -- Only userdata, threads and functions reach this branch....
        print("\nERROR: Can not serialize " .. vtype)
        return 'null'
    end
end


local serializer = {}
function serializer.stringify(data)
    return serialize(data, nil)
end
return serializer