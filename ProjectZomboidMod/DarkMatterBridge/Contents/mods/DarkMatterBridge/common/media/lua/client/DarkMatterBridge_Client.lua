local MODULE = "DarkMatterBridge"

local function safeNumber(value)
    return tonumber(value) or 0
end

local function getCharacterName(player)
    local ok, name = pcall(function()
        local descriptor = player:getDescriptor()
        local forename = tostring(descriptor:getForename() or "")
        local surname = tostring(descriptor:getSurname() or "")
        return (forename .. " " .. surname):match("^%s*(.-)%s*$")
    end)
    if ok then
        return name
    end
    return ""
end

local function onPlayerDeath(player)
    if not isClient() or not player then
        return
    end

    sendClientCommand(player, MODULE, "playerDeath", {
        displayName = tostring(player:getDisplayName() or player:getUsername()),
        characterName = getCharacterName(player),
        hoursSurvived = safeNumber(player:getHoursSurvived()),
        zombieKills = safeNumber(player:getZombieKills()),
        x = math.floor(safeNumber(player:getX())),
        y = math.floor(safeNumber(player:getY())),
        z = math.floor(safeNumber(player:getZ()))
    })
end

Events.OnPlayerDeath.Add(onPlayerDeath)
