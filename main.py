import logging, os
from modules.utils import update_item_database
from bot import bot
from dotenv import load_dotenv

logging.basicConfig(level='INFO')
load_dotenv()

if __name__ == '__main__':
    TOKEN = os.environ.get('TOKEN')
    print('Starting bot')
    bot.run(TOKEN)
