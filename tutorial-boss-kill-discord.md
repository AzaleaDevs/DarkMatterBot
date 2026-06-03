# Tutorial: notificaciones de boss kill de AzerothCore a Discord

Este tutorial explica como enviar un mensaje automatico a Discord cuando se mata un boss en AzerothCore usando Eluna Lua y un bot hecho con `discord.py`.

La arquitectura final es:

```text
AzerothCore / Eluna Lua
detecta muerte de boss
        ->
HTTP POST desde worldserver
        ->
bot Python
        ->
embed en Discord
```

## 1. Requisitos

- AzerothCore funcionando.
- Eluna instalado y cargando scripts Lua.
- Bot de Discord funcionando con `discord.py`.
- Un canal de Discord donde el bot pueda escribir.
- Docker, si AzerothCore esta corriendo en contenedores.
- Conectividad de red entre el contenedor `worldserver` y el equipo donde corre el bot.

En este caso concreto:

```text
Raspberry: 192.168.4.59
Usuario SSH: azalea
Repo AzerothCore: /home/azalea/docker/Warcraft/azerothcore-wotlk
Carpeta Lua: /home/azalea/docker/Warcraft/azerothcore-wotlk/lua_scripts
Bot en PC: 192.168.4.71
Puerto del bot: 8088
Token interno: 00013071993
Canal Discord: 1395474837589463114
```

## 2. Preparar el bot de Discord

El bot necesita un endpoint HTTP para recibir eventos desde AzerothCore.

Se anadio `aiohttp` a `requirements.txt`:

```txt
discord.py
aiosqlite
Pillow
aiohttp
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## 3. Configuracion del bot

En `config.json`, ademas del token normal de Discord, se anadio la seccion `BOSS_KILL_API`:

```json
{
    "DISCORD_TOKEN": "TOKEN_REAL_DEL_BOT",
    "GUILD_ID": "1395474837102788749",
    "STATE": "Probando la materia.",
    "BOSS_KILL_API": {
        "ENABLED": true,
        "HOST": "0.0.0.0",
        "PORT": 8088,
        "TOKEN": "00013071993",
        "CHANNEL_ID": "1395474837589463114"
    }
}
```

Notas importantes:

- `DISCORD_TOKEN` es el token real del bot de Discord.
- `BOSS_KILL_API.TOKEN` no es un token de Discord. Es una clave interna inventada para que AzerothCore pueda autenticarse contra el bot.
- `CHANNEL_ID` es el canal donde aparecera el mensaje.
- `HOST` en `0.0.0.0` permite recibir peticiones desde otro equipo de la red.

## 4. Endpoint HTTP en el bot

En `main.py` se anadio un servidor `aiohttp` dentro del bot.

El endpoint queda asi:

```text
POST /azerothcore/boss-kill
Header: X-Darkmatter-Token: 00013071993
Content-Type: application/json
```

Ejemplo de JSON recibido:

```json
{
    "boss_entry": 10184,
    "boss_name": "Onyxia",
    "killer_name": "Jugador",
    "zone": "2159",
    "map": "249"
}
```

El bot crea un embed con:

```text
Titulo: Boss derrotado
Descripcion: NombreBoss ha sido derrotado por NombreJugador.
Campos: Entry, Zona, Mapa, Dificultad si existe
```

Tambien se configuro `Images/avatar.png` como thumbnail del embed.

Si la imagen existe:

```text
Images/avatar.png
```

el bot la adjunta y la usa como:

```text
attachment://avatar.png
```

Si la imagen no existe, el bot manda el embed sin thumbnail y no se rompe.

## 5. Script Lua para AzerothCore

Se creo este script:

```text
AzerothCoreScripts/darkmatter_bot_boss_kills.lua
```

Y se copio a la Raspberry en:

```text
/home/azalea/docker/Warcraft/azerothcore-wotlk/lua_scripts/darkmatter_boss_kills.lua
```

Dentro del contenedor `worldserver`, el archivo aparece en:

```text
/azerothcore/env/dist/bin/lua_scripts/darkmatter_boss_kills.lua
```

El script usa:

```lua
RegisterPlayerEvent(7, OnCreatureKilled)
```

Ese evento se dispara cuando un jugador mata una criatura.

Para saber si la criatura es un boss, se filtra con:

```lua
creature:IsWorldBoss() or creature:IsDungeonBoss()
```

Esto hace que funcione con cualquier boss que AzerothCore tenga marcado como boss o dungeon boss.

Si hay bosses custom que no estan bien marcados en la base de datos, se pueden anadir manualmente:

```lua
local BOSSES = {
    [10184] = "Onyxia",
    [ENTRY_CUSTOM] = "Nombre del boss custom",
}
```

## 6. Por que no se uso curl

Dentro del contenedor `ac-worldserver` se comprobo que no habia:

```text
curl
wget
nc
python
```

Pero si habia `bash`:

```text
/bin/bash
```

Por eso el Lua envia la peticion HTTP usando `/dev/tcp` de bash.

La idea es esta:

```bash
exec 3<>/dev/tcp/192.168.4.71/8088
printf 'POST ...' >&3
```

Ventaja: no hace falta instalar nada dentro del contenedor ni recompilar AzerothCore.

## 7. Copiar el Lua a la Raspberry

Comando usado:

```bash
scp AzerothCoreScripts/darkmatter_bot_boss_kills.lua \
  azalea@192.168.4.59:/home/azalea/docker/Warcraft/azerothcore-wotlk/lua_scripts/darkmatter_boss_kills.lua
```

Despues se verifico que el archivo existia:

```bash
ssh azalea@192.168.4.59
cd docker/Warcraft/azerothcore-wotlk
ls -l lua_scripts/darkmatter_boss_kills.lua
```

Y tambien dentro del contenedor:

```bash
docker exec ac-worldserver sh -lc \
  'ls -l /azerothcore/env/dist/bin/lua_scripts/darkmatter_boss_kills.lua'
```

## 8. Arrancar el bot

Desde la carpeta del bot:

```bash
python main.py
```

En esta prueba se arranco en segundo plano desde Windows y se redirigieron logs:

```powershell
Start-Process -FilePath python `
  -ArgumentList 'main.py' `
  -WorkingDirectory 'D:\AzaleaDevs\Proyecto-Darkmatter' `
  -WindowStyle Hidden `
  -RedirectStandardOutput 'D:\AzaleaDevs\Proyecto-Darkmatter\bot.stdout.log' `
  -RedirectStandardError 'D:\AzaleaDevs\Proyecto-Darkmatter\bot.stderr.log'
```

Para comprobar que escucha en el puerto:

```powershell
Get-NetTCPConnection -LocalPort 8088 -State Listen
```

El log correcto muestra:

```text
Boss kill API listening on 0.0.0.0:8088
BOT RUNNING
Logged in as Dark Matter BOT
```

## 9. Prueba desde el contenedor worldserver

Antes de probar con un boss real, se envio una peticion manual desde dentro del contenedor.

La respuesta correcta fue:

```text
HTTP/1.1 200 OK
{"ok": true}
```

El bot registro:

```text
Boss kill notification sent: Prueba DarkMatter by Codex
```

Eso confirma:

```text
worldserver Docker -> bot en PC -> Discord
```

## 10. Prueba real en el juego

Con el Lua en `lua_scripts` y el bot escuchando, se mato un boss en el juego.

Resultado esperado en Discord:

```text
Boss derrotado
NombreBoss ha sido derrotado por NombreJugador.

Entry: ...
Zona: ...
Mapa: ...
```

Con `Images/avatar.png` como thumbnail del embed.

La prueba real funciono correctamente.

## 11. Troubleshooting

Si no aparece el mensaje en Discord:

1. Comprobar que el bot esta encendido.

```powershell
Get-NetTCPConnection -LocalPort 8088 -State Listen
```

2. Revisar logs del bot.

```powershell
Get-Content bot.stderr.log -Tail 80
```

3. Comprobar que el Lua esta dentro del contenedor.

```bash
docker exec ac-worldserver sh -lc \
  'ls -l /azerothcore/env/dist/bin/lua_scripts/darkmatter_boss_kills.lua'
```

4. Revisar logs del worldserver.

```bash
docker logs --tail 160 ac-worldserver 2>&1 | grep -iE 'eluna|lua|darkmatter|boss|error'
```

5. Comprobar que el boss esta marcado como boss.

El script automatico solo notifica si:

```lua
creature:IsWorldBoss() or creature:IsDungeonBoss()
```

Si el boss es custom y no esta marcado, anadirlo manualmente en la tabla `BOSSES`.

6. Comprobar la IP del bot.

En este caso el bot estaba en:

```text
192.168.4.71
```

Si cambia la IP del PC, hay que cambiar `BOT_HOST` en el Lua.

## 12. Resumen para explicar en video

La idea principal es separar responsabilidades:

- AzerothCore detecta la muerte del boss con Eluna.
- Lua envia un evento HTTP al bot.
- El bot valida un token interno.
- El bot publica un embed en Discord.

La ventaja de hacerlo en Lua es que no hay que recompilar AzerothCore. Si se quiere cambiar el texto, el filtro de bosses o el endpoint, se edita el `.lua` y se recargan scripts o se reinicia el worldserver.

La ventaja de pasar por el bot en lugar de un webhook directo es que despues se pueden anadir estadisticas, rankings, logs, recompensas o comandos de Discord usando la misma informacion.

