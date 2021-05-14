#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
from telebot.credentials import bot_token

from Crawler.process_reviews import process as reviewProcess
from NLP.fact_extract import FaceExtraction
import os
import sys
import time
import json
from json.decoder import JSONDecodeError
from threading import Thread
"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


user_start = {}

# Check if the user didnot start the bot
def check(username):
    if username not in user_start:
        return False
    return user_start[username]

def write_userStart_file():
    with open("./telebot/user_start.json", "w") as write_file:
        json.dump(user_start, write_file)

# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    user_start[update.message.chat.username] = True
    write_userStart_file()
    update.message.reply_text('Hi! \n Welcome to reviews-summary bot. Please input your product link to take overview !')


def help(update, context):
    """Send a messfactExtractage when the command /help is issued."""
    start_text = "If you didnot start the bot, please type command '/start' to start! \n"
    started_text = "If you already started the bot, please input product's link to get summary! \n"
    update.message.reply_text(start_text + started_text)

def end(update, context):
    """End bot to this user when command /end is issued."""
    user_start[update.message.chat.username] = False
    write_userStart_file()
    update.message.reply_text("Thank you for enjoying bot. See you later!")


def echo(update, context):
    """Echo the user message."""
    user = update.message.chat.username
    if check(user) == False:
        update.message.reply_text("Please start the bot!")
        return
     
    update.message.reply_text("Please wait us to collect and process data for you! \n Loading... ")
    url = update.message.text
    file_data_path = reviewProcess(url)
    response = fact_extraction.factExtract(file_data_path)
    text = ""
    for item in response:
        if len(response[item]) == 0:
            continue
        
        text = '<b>' + item + '</b>'
        text = text + '\n'
        
        for index, sent in enumerate(response[item]):
            text = text + str(index+1) + '. '  + sent +  '\n'

        update.message.reply_text(text, parse_mode=ParseMode.HTML)


def error(update, context):
    """Log Errors caused by Updates."""
    update.message.reply_text("Please correct your link. Keep calm and wait our server work on it")
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    
    updater = Updater(bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("end", end))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, echo))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    try:
        with open("./telebot/user_start.json", "r") as read_file:
            user_start = json.load(read_file)
    except JSONDecodeError:
        pass
    fact_extraction = FaceExtraction()
    main()
