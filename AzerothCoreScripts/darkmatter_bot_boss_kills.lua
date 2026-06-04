-- Envia boss kills de AzerothCore/Eluna al bot DarkMatter.
-- Requiere curl disponible en el host/contenedor donde corre worldserver.

local BOT_HOST = "192.168.4.59"
local BOT_PORT = 8088
local BOT_PATH = "/azerothcore/boss-kill"
local BOT_TOKEN = "00013071993"

local NOTIFY_ALL_BOSSES = true

local BOSSES = {
    -- Si NOTIFY_ALL_BOSSES es false, solo se notifican estos entries.
    -- Si NOTIFY_ALL_BOSSES es true, puedes usar esta tabla para sobrescribir nombres.
    [10184] = "Onyxia",
}

local function JsonEscape(value)
    value = tostring(value or "")
    value = value:gsub("\\", "\\\\")
    value = value:gsub("\"", "\\\"")
    value = value:gsub("\n", "\\n")
    value = value:gsub("\r", "\\r")
    return value
end

local function ShellQuote(value)
    value = tostring(value or "")
    return "'" .. value:gsub("'", "'\\''") .. "'"
end

local function SendToBot(json)
    local request = "POST " .. BOT_PATH .. " HTTP/1.1\r\n" ..
        "Host: " .. BOT_HOST .. ":" .. BOT_PORT .. "\r\n" ..
        "Content-Type: application/json\r\n" ..
        "X-Darkmatter-Token: " .. BOT_TOKEN .. "\r\n" ..
        "Content-Length: " .. #json .. "\r\n" ..
        "Connection: close\r\n\r\n" ..
        json

    local bash = "exec 3<>/dev/tcp/" .. BOT_HOST .. "/" .. BOT_PORT ..
        " && printf %s " .. ShellQuote(request) ..
        " >&3 && cat <&3 >/dev/null"

    local command = "bash -lc " .. ShellQuote(bash) .. " >/dev/null 2>&1 &"

    os.execute(command)
end

local function ShouldNotify(creature)
    if NOTIFY_ALL_BOSSES and (creature:IsWorldBoss() or creature:IsDungeonBoss()) then
        return true
    end

    return BOSSES[creature:GetEntry()] ~= nil
end

local function OnCreatureKilled(event, killer, creature)
    if not creature or not ShouldNotify(creature) then
        return
    end

    local entry = creature:GetEntry()
    local bossName = BOSSES[entry]
    if not bossName or bossName == "" then
        bossName = creature:GetName()
    end

    local killerName = "jugadores desconocidos"
    if killer then
        killerName = killer:GetName()
    end

    local zoneId = creature:GetZoneId() or 0
    local mapId = creature:GetMapId() or 0

    local json = "{" ..
        "\"boss_entry\":" .. entry .. "," ..
        "\"boss_name\":\"" .. JsonEscape(bossName) .. "\"," ..
        "\"killer_name\":\"" .. JsonEscape(killerName) .. "\"," ..
        "\"zone\":\"" .. zoneId .. "\"," ..
        "\"map\":\"" .. mapId .. "\"" ..
    "}"

    SendToBot(json)
end

RegisterPlayerEvent(7, OnCreatureKilled)
