import logging
import os

from dotenv import load_dotenv

from bot import bot

logging.basicConfig(level='INFO')
load_dotenv()

if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    print('Starting bot')
    bot.run(TOKEN)
