import logging
from modules.utils import update_item_database
from bot import bot

logging.basicConfig(level='INFO')

if __name__ == '__main__':
    print('Updating item database')
    update_item_database()
    TOKEN = 'token'
    print('Starting bot')
    bot.run(TOKEN)
