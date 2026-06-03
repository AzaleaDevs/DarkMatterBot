# Notificaciones de boss kill a Discord

Hay dos formas:

1. `discord_webhook_boss_kills.lua`: AzerothCore manda el mensaje directamente a un webhook de Discord.
2. `darkmatter_bot_boss_kills.lua`: AzerothCore manda el evento al bot Python, y el bot publica el embed en Discord.

La opcion directa por webhook es la mas simple. La opcion del bot es mejor si quieres guardar estadisticas, rankings o reutilizar comandos del bot.

## Configuracion del bot

Anade esto a `config.json` y cambia los valores:

```json
"BOSS_KILL_API": {
    "ENABLED": true,
    "HOST": "0.0.0.0",
    "PORT": 8088,
    "TOKEN": "cambia-este-token-largo",
    "CHANNEL_ID": "id-del-canal-de-discord"
}
```

Instala dependencias nuevas:

```bash
pip install -r requirements.txt
```

Endpoint del bot:

```text
POST http://IP_DEL_BOT:8088/azerothcore/boss-kill
Header: X-Darkmatter-Token: cambia-este-token-largo
```

## Configuracion de AzerothCore

Copia el script Lua elegido dentro de la carpeta `lua_scripts` de AzerothCore/Eluna y reinicia el worldserver.

En ambos scripts debes:

- Rellenar la lista `BOSSES`.
- Cambiar el webhook o la URL/token del bot.
- Confirmar que `curl` existe en la Raspberry.
