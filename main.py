import logging
import os

from dotenv import load_dotenv

from bot import bot

logging.basicConfig(level='INFO')
logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
load_dotenv()

if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    print('Starting bot')
    bot.run(TOKEN)
