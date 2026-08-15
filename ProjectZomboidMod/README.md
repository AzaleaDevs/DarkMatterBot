# DarkMatter Project Zomboid Bridge

Integracion para servidores Project Zomboid Build 42 alojados en GTXGaming.

## Funcionamiento

El mod genera dos archivos dentro de la carpeta Lua del servidor:

- DarkMatterBridge_state.json: hora ingame y jugadores conectados.
- DarkMatterBridge_events.jsonl: registro incremental de muertes.

DarkMatter consulta esos archivos por SFTP cada 30 segundos. Las muertes se publican en el canal configurado y /time muestra la fecha y hora ingame.

## Instalar el mod

La carpeta que debe publicarse o copiarse como mod es:

    ProjectZomboidMod/DarkMatterBridge

Para Steam Workshop, usa Project Zomboid > Workshop > Create and Update Items, crea el item y publica esta carpeta. Despues instala el item desde el boton Steam Workshop del panel GTXGaming.

El Mod ID que debe aparecer en la configuracion del servidor es:

    DarkMatterBridge

Si el servidor usa un ClientCommandFilter restrictivo, permite:

    +DarkMatterBridge.*

Reinicia el servidor. Al arrancar, busca estos archivos desde el File Manager o SFTP para obtener sus rutas absolutas:

    DarkMatterBridge_state.json
    DarkMatterBridge_events.jsonl

En este servidor GTXGaming se crean bajo /188.165.119.37_17200/World/Lua/.

## Configurar DarkMatter

Activa PROJECT_ZOMBOID en config.json y rellena:

- CHANNEL_ID
- SFTP_HOST
- SFTP_PORT
- SFTP_USERNAME
- STATE_PATH
- EVENTS_PATH

En la Raspberry, anade la contrasena solo a .env:

    PZ_SFTP_PASSWORD=tu_contrasena_sftp

Tambien puedes definir host, puerto y usuario mediante PZ_SFTP_HOST, PZ_SFTP_PORT y PZ_SFTP_USERNAME.

El primer acceso confia en la clave SSH presentada por GTXGaming y la guarda en data/project_zomboid_known_hosts. Los accesos posteriores verifican esa clave.

## Prueba

1. Arranca el servidor y entra con un jugador.
2. Ejecuta /time en Discord.
3. Mata un personaje de prueba.
4. Espera hasta 30 segundos para recibir la notificacion.

No publiques .env, la contrasena SFTP ni el token del bot.
