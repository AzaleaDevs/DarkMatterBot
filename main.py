import bot
import asyncio



async def main():
    memeriabot = asyncio.create_task(bot.memeriabot.start(bot.TOKEN))
    await memeriabot

if __name__ == '__main__':
    asyncio.run(main())