-- Envia boss kills de AzerothCore/Eluna directamente a un webhook de Discord.
-- Requiere curl disponible en el host/contenedor donde corre worldserver.

local DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/cambia/esto"

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

local function SendWebhook(json)
    local command = "curl -sS -m 5 -X POST " ..
        "-H " .. ShellQuote("Content-Type: application/json") .. " " ..
        "--data " .. ShellQuote(json) .. " " ..
        ShellQuote(DISCORD_WEBHOOK_URL) .. " >/dev/null 2>&1 &"

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

    local description = "**" .. bossName .. "** ha sido derrotado por **" .. killerName .. "**."

    local json = "{" ..
        "\"username\":\"DarkMatter Raids\"," ..
        "\"embeds\":[{" ..
            "\"title\":\"Boss derrotado\"," ..
            "\"description\":\"" .. JsonEscape(description) .. "\"," ..
            "\"color\":15844367," ..
            "\"fields\":[" ..
                "{\"name\":\"Entry\",\"value\":\"" .. entry .. "\",\"inline\":true}," ..
                "{\"name\":\"Zona\",\"value\":\"" .. zoneId .. "\",\"inline\":true}," ..
                "{\"name\":\"Mapa\",\"value\":\"" .. mapId .. "\",\"inline\":true}" ..
            "]" ..
        "}]" ..
    "}"

    SendWebhook(json)
end

RegisterPlayerEvent(7, OnCreatureKilled)
