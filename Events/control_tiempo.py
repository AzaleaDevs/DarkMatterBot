import discord
from discord.ext import commands
from datetime import datetime

class ControlTiempo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}  # Guardamos tiempos por usuario

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = member.id

        # -----------------------------------------------------------
        # ENTRADA A CANAL DE VOZ
        # -----------------------------------------------------------
        if before.channel is None and after.channel is not None:
            self.voice_sessions[user_id] = datetime.utcnow()

            try:
                await member.send("⏱️ Inicia el temporizador.")
            except:
                print(f"No pude enviar DM a {member}")

            print(f"[+] {member} entró a voz. Timer iniciado.")


        # -----------------------------------------------------------
        # SALIDA DE CANAL DE VOZ
        # -----------------------------------------------------------
        elif before.channel is not None and after.channel is None:
            if user_id in self.voice_sessions:
                start_time = self.voice_sessions[user_id]
                end_time = datetime.utcnow()

                seconds = int((end_time - start_time).total_seconds())

                try:
                    await member.send(f"⏳ Tiempo total transcurrido: **{seconds} segundos**.")
                except:
                    print(f"No pude enviar DM a {member}")

                print(f"[-] {member} salió de voz. Tiempo: {seconds} segundos.")

                del self.voice_sessions[user_id]


        # -----------------------------------------------------------
        # CAMBIO DE CANAL DE VOZ
        # -----------------------------------------------------------
        elif before.channel != after.channel:
            if user_id in self.voice_sessions:
                start_time = self.voice_sessions[user_id]
                end_time = datetime.utcnow()

                
                seconds = int((end_time - start_time).total_seconds())

                try:
                    await member.send(f"🔁 Cambiaste de canal. Tiempo acumulado: **{seconds} segundos**.")
                except:
                    print(f"No pude enviar DM a {member}")

                print(f"[~] {member} cambió de canal. Sumó {seconds} sec.")

            self.voice_sessions[user_id] = datetime.utcnow()

            try:
                await member.send("⏱️ Inicia un nuevo temporizador en este canal.")
            except:
                print(f"No pude enviar DM a {member}")

# -----------------------------------------------------------
# FUNCIÓN NECESARIA PARA CARGAR LA EXTENSIÓN
# -----------------------------------------------------------
async def setup(bot):
    await bot.add_cog(ControlTiempo(bot))
