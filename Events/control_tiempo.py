import discord
from discord.ext import commands
from datetime import datetime
import aiosqlite
import os

DB_PATH = os.path.join("Databases", "darkmatter_pro.db")
AFK_CHANNEL_ID = 911591892590931999

class ControlTiempo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_sessions = {}  # Store start times per user

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = member.id

        # -----------------------------------------------------------
        # JOINING A VOICE CHANNEL
        # -----------------------------------------------------------
        if before.channel is None and after.channel is not None:
            # User joined a voice channel
            # Only start timer if NOT in AFK channel
            if after.channel.id != AFK_CHANNEL_ID:
                self.voice_sessions[user_id] = datetime.utcnow()
                print(f"[+] {member} joined voice channel {after.channel.name}. Timer started.")
            else:
                print(f"[+] {member} joined AFK channel. No timer started.")

        # -----------------------------------------------------------
        # LEAVING A VOICE CHANNEL
        # -----------------------------------------------------------
        elif before.channel is not None and after.channel is None:
            # User left a voice channel
            if user_id in self.voice_sessions:
                # Calculate time spent
                start_time = self.voice_sessions[user_id]
                end_time = datetime.utcnow()
                
                total_seconds = int((end_time - start_time).total_seconds())
                minutes_earned = total_seconds // 60  # Round down
                
                # Update database with euros earned
                if minutes_earned > 0:
                    await self.add_euros_to_user(user_id, minutes_earned)
                    print(f"[-] {member} left voice. Time: {total_seconds}s ({minutes_earned} euros earned).")
                else:
                    print(f"[-] {member} left voice. Time: {total_seconds}s (no euros earned).")
                
                # Remove from active sessions
                del self.voice_sessions[user_id]
            else:
                print(f"[-] {member} left voice (was in AFK or no timer).")

        # -----------------------------------------------------------
        # SWITCHING VOICE CHANNELS
        # -----------------------------------------------------------
        elif before.channel != after.channel:
            # User switched channels
            
            # If they had an active timer (not in AFK), calculate and award
            if user_id in self.voice_sessions:
                start_time = self.voice_sessions[user_id]
                end_time = datetime.utcnow()
                
                total_seconds = int((end_time - start_time).total_seconds())
                minutes_earned = total_seconds // 60  # Round down
                
                # Update database with euros earned
                if minutes_earned > 0:
                    await self.add_euros_to_user(user_id, minutes_earned)
                    print(f"[~] {member} switched channels. Previous time: {total_seconds}s ({minutes_earned} euros earned).")
                else:
                    print(f"[~] {member} switched channels. Previous time: {total_seconds}s (no euros earned).")
                
                # Remove old timer
                del self.voice_sessions[user_id]
            
            # Start new timer if new channel is NOT AFK
            if after.channel.id != AFK_CHANNEL_ID:
                self.voice_sessions[user_id] = datetime.utcnow()
                print(f"[~] {member} new timer started in {after.channel.name}.")
            else:
                print(f"[~] {member} moved to AFK channel. No timer started.")

    async def add_euros_to_user(self, user_id: int, euros: int):
        """
        Adds euros to the user's account in the USUARIOS table.
        """
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE USUARIOS SET euros = euros + ? WHERE id = ?",
                (euros, user_id)
            )
            await db.commit()

# -----------------------------------------------------------
# SETUP FUNCTION
# -----------------------------------------------------------
async def setup(bot):
    await bot.add_cog(ControlTiempo(bot))

