-- Slightly modifed version of:
-- https://gist.github.com/tylerneylon/59f4bcf316be525b30ab

local json = {}

-- Internal functions.

local function kind_of(obj)
  if type(obj) ~= 'table' then return type(obj) end
  local i = 1
  for _ in pairs(obj) do
    if obj[i] ~= nil then i = i + 1 else return 'table' end
  end
  if i == 1 then return 'table' else return 'array' end
end

local function escape_str(s)
  local in_char  = {'\\', '"', '/', '\b', '\f', '\n', '\r', '\t'}
  local out_char = {'\\', '"', '/',  'b',  'f',  'n',  'r',  't'}
  for i, c in ipairs(in_char) do
    s = s:gsub(c, '\\' .. out_char[i])
  end
  return s
end

local function contains(table, element)
  if table == nil then return false end
  
  for _, value in pairs(table) do
    if value == element then
      return true
    end
  end
  return false
end

-- Public values and functions.

function json.stringify(obj, as_key, containsField, ignoreAlways, ignoreToplevel)
  local s = {}  -- We'll build the string as an array of strings to be concatenated.
  local kind = kind_of(obj)  -- This is 'array' if it's an array or type(obj) otherwise.
  
  if kind == 'array' then
    if as_key then error('Can\'t encode array as key.') end

    s[#s + 1] = '['

    local t = {}
    for i, val in ipairs(obj) do
      if #t > 0 then t[#t + 1] = ',' end
      t[#t + 1] = json.stringify(val, false, containsField, ignoreAlways)
    end

    s[#s + 1] = table.concat(t)..']'

  elseif kind == 'table' then
    if as_key then error('Can\'t encode table as key.') end

    for k, v in pairs(obj) do
      if contains(containsField, k) then
        return 'null'
      end
    end


    s[#s + 1] = '{'

    local t = {}
    for k, v in pairs(obj) do
      if not contains(ignoreAlways, k) and not contains(ignoreToplevel, k) then
        if #t > 0 then t[#t + 1] = ',' end
        if ignoreToplevel then 
          t[#t + 1] = "\n\n\n"
        end

        t[#t + 1] = json.stringify(k, true, containsField, ignoreAlways)
        t[#t + 1] = ': '
        t[#t + 1] = json.stringify(v, false, containsField, ignoreAlways)
      end
    end

    s[#s + 1] = table.concat(t)..'}'
    
  elseif kind == 'string' then    
    return '"' .. escape_str(obj) .. '"'

  elseif kind == 'number' then    
    local numberStr = tostring(obj)
    if as_key or numberStr == "inf" or numberStr == "-inf" then
      return '"' .. numberStr .. '"'
    end
    return tostring(obj)

  elseif kind == 'boolean' then
    if obj == true then return 1 else return 0 end

  elseif kind == 'nil' then
    return 'null'
    
  else
    error('Unjsonifiable type: ' .. kind .. '.')
  end

  return table.concat(s)
end

return json