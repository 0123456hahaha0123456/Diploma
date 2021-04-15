#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.
from telebot.credentials import bot_token
from Crawler.process_reviews import process as reviewProcess
from NLP.fact_extract import FaceExtraction
import os
import sys
import time
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


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""

    update.message.reply_text('Hi! \n Welcome to reviews summary bot. Please input your product link to take overview !')


def help(update, context):
    """Send a messfactExtractage when the command /help is issued."""
    update.message.reply_text('Help!')


def echo(update, context):
    """Echo the user message."""
    url = update.message.text
    file_data_path = reviewProcess(url)
    response = fact_extraction.factExtract(file_data_path)
    # print(type(response))
    text = ""
    for item in response:
        text = '<b>' + item + '</b>'
        text = text + '\n'
        text = text + '\n'.join(response[item])
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
    fact_extraction = FaceExtraction()
    main()
