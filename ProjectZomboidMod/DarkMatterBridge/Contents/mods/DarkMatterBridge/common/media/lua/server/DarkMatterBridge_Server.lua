local MODULE = "DarkMatterBridge"
local STATE_FILE = "DarkMatterBridge_state.json"
local WRITE_INTERVAL_MS = 30000
local DEATH_DEDUPLICATION_MS = 10000

local lastStateWrite = 0
local lastDeathByUsername = {}
local deadPlayers = {}

local BACKSLASH = string.char(92)

local function jsonEscape(value)
    local text = tostring(value or "")
    text = text:gsub(BACKSLASH, BACKSLASH .. BACKSLASH)
    text = text:gsub('"', BACKSLASH .. '"')
    text = text:gsub(string.char(8), BACKSLASH .. "b")
    text = text:gsub(string.char(12), BACKSLASH .. "f")
    text = text:gsub(string.char(10), BACKSLASH .. "n")
    text = text:gsub(string.char(13), BACKSLASH .. "r")
    text = text:gsub(string.char(9), BACKSLASH .. "t")
    return text
end
local function jsonString(value)
    return '"' .. jsonEscape(value) .. '"'
end

local function jsonNumber(value)
    local number = tonumber(value) or 0
    if number ~= number or number == math.huge or number == -math.huge then
        number = 0
    end
    return tostring(number)
end

local function callOr(object, methodName, fallback)
    if not object then
        return fallback
    end

    local ok, result = pcall(function()
        return object[methodName](object)
    end)
    if ok and result ~= nil then
        return result
    end
    return fallback
end

local function getCharacterName(player)
    local descriptor = callOr(player, "getDescriptor", nil)
    local forename = tostring(callOr(descriptor, "getForename", ""))
    local surname = tostring(callOr(descriptor, "getSurname", ""))
    return (forename .. " " .. surname):match("^%s*(.-)%s*$")
end

local function gameSnapshotJson()
    local gameTime = getGameTime()
    return table.concat({
        "{",
        '"year":', jsonNumber(gameTime:getYear()), ",",
        '"month":', jsonNumber(gameTime:getMonth() + 1), ",",
        '"day":', jsonNumber(gameTime:getDayPlusOne()), ",",
        '"hour":', jsonNumber(gameTime:getHour()), ",",
        '"minute":', jsonNumber(gameTime:getMinutes()), ",",
        '"days_survived":', jsonNumber(gameTime:getDaysSurvived()), ",",
        '"world_age_hours":', jsonNumber(gameTime:getWorldAgeHours()),
        "}"
    })
end

local function writeTextFile(filename, content, append)
    local writer = getFileWriter(filename, true, append)
    if not writer then
        print("[DarkMatterBridge] Could not open " .. filename)
        return false
    end

    local ok, errorMessage = pcall(function()
        writer:writeln(content)
        writer:close()
    end)

    if not ok then
        print("[DarkMatterBridge] Write failed: " .. tostring(errorMessage))
        pcall(function() writer:close() end)
        return false
    end
    return true
end

local function writeState()
    local players = getOnlinePlayers()
    local playerNames = {}
    for index = 0, players:size() - 1 do
        local player = players:get(index)
        table.insert(playerNames, jsonString(callOr(player, "getUsername", "unknown")))
    end

    local state = table.concat({
        "{",
        '"version":1,',
        '"players_online":', jsonNumber(players:size()), ",",
        '"players":[', table.concat(playerNames, ","), "],",
        '"game":', gameSnapshotJson(),
        "}"
    })

    writeTextFile(STATE_FILE, state, false)
end

local function recordDeath(player, args, source)
    if not player then
        return
    end

    args = args or {}
    local username = tostring(callOr(player, "getUsername", "unknown"))
    local now = getTimeInMillis()
    local previous = lastDeathByUsername[username] or 0
    if now - previous < DEATH_DEDUPLICATION_MS then
        return
    end
    lastDeathByUsername[username] = now

    local displayName = args.displayName
        or callOr(player, "getDisplayName", username)
    local characterName = tostring(args.characterName or "")
    if characterName == "" then
        characterName = getCharacterName(player)
    end
    local hoursSurvived = args.hoursSurvived
        or callOr(player, "getHoursSurvived", 0)
    local zombieKills = args.zombieKills
        or callOr(player, "getZombieKills", 0)
    local x = args.x or callOr(player, "getX", 0)
    local y = args.y or callOr(player, "getY", 0)
    local z = args.z or callOr(player, "getZ", 0)

    local event = table.concat({
        "{",
        '"id":', jsonString(username .. "-" .. tostring(now)), ",",
        '"type":"player_death",',
        '"source":', jsonString(source), ",",
        '"username":', jsonString(username), ",",
        '"display_name":', jsonString(displayName), ",",
        '"character_name":', jsonString(characterName), ",",
        '"hours_survived":', jsonNumber(hoursSurvived), ",",
        '"zombie_kills":', jsonNumber(zombieKills), ",",
        '"x":', jsonNumber(math.floor(tonumber(x) or 0)), ",",
        '"y":', jsonNumber(math.floor(tonumber(y) or 0)), ",",
        '"z":', jsonNumber(math.floor(tonumber(z) or 0)), ",",
        '"game":', gameSnapshotJson(),
        "}"
    })

    print("[DarkMatterBridgeEvent] " .. event)
    print("[DarkMatterBridge] Recorded death for " .. username)
    writeState()
end

local function onCharacterDeath(character)
    if instanceof(character, "IsoPlayer") then
        recordDeath(character, nil, "server")
    end
end

local function onClientCommand(module, command, player, args)
    if module ~= MODULE or command ~= "playerDeath" then
        return
    end
    recordDeath(player, args, "client")
end

local function detectPlayerDeaths()
    local players = getOnlinePlayers()
    local onlinePlayers = {}

    for index = 0, players:size() - 1 do
        local player = players:get(index)
        local username = tostring(callOr(player, "getUsername", "unknown"))
        onlinePlayers[username] = true

        local isDead = callOr(player, "isDead", false)
        if isDead and not deadPlayers[username] then
            deadPlayers[username] = true
            recordDeath(player, nil, "server_poll")
        elseif not isDead then
            deadPlayers[username] = nil
        end
    end

    for username in pairs(deadPlayers) do
        if not onlinePlayers[username] then
            deadPlayers[username] = nil
        end
    end
end

local function onTick()
    detectPlayerDeaths()

    local now = getTimeInMillis()
    if now - lastStateWrite < WRITE_INTERVAL_MS then
        return
    end
    lastStateWrite = now
    writeState()
end

local function onServerStarted()
    print("[DarkMatterBridge] Started")
    writeState()
end

Events.OnCharacterDeath.Add(onCharacterDeath)
Events.OnClientCommand.Add(onClientCommand)
Events.OnServerStarted.Add(onServerStarted)
Events.OnTickEvenPaused.Add(onTick)
