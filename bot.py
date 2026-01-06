#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  4 19:06:08 2018

@author: mparvin
"""

import subprocess
import configparser
import os
import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging


# Configure logging - reduce noise from telegram library
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Suppress verbose logging from telegram and urllib3
logging.getLogger('telegram.vendor.ptb_urllib3.urllib3.connectionpool').setLevel(logging.ERROR)
logging.getLogger('telegram.ext.updater').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Try to read config file
config = configparser.ConfigParser()
try:
    if not os.path.exists("config"):
        logger.error("Config file not found. Please create a 'config' file based on config.example")
        logger.info("Bot cannot start without configuration. Exiting gracefully...")
        sys.exit(0)  # Exit gracefully so the web server can continue
    
    config.read("config")
    ### Get admin chat_id from config file
    ### For more security replies only send to admin chat_id
    adminCID = config["SecretConfig"]["admincid"]
except (KeyError, configparser.Error) as e:
    logger.error(f"Error reading config file: {e}")
    logger.info("Bot cannot start without valid configuration. Exiting gracefully...")
    sys.exit(0)  # Exit gracefully so the web server can continue
### This function run command and send output to user
def runCMD(bot, update):
    if not isAdmin(bot, update):
        return
    usercommand = update.message.text
    cmdProc = subprocess.Popen(
        usercommand, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
    )
    cmdOut, cmdErr = cmdProc.communicate()
    if cmdOut:
        bot.sendMessage(text=str(cmdOut, "utf-8"), chat_id=adminCID)
    else:
        bot.sendMessage(text=str(cmdErr, "utf-8"), chat_id=adminCID)


### This function ping 8.8.8.8 and send you result
def ping8(bot, update):
    if not isAdmin(bot, update):
        return
    cmdOut = str(
        subprocess.check_output(
            "ping 8.8.8.8 -c4", stderr=subprocess.STDOUT, shell=True
        ),
        "utf-8",
    )
    bot.sendMessage(text=cmdOut, chat_id=adminCID)


def startCMD(bot, update):
    if not isAdmin(bot, update):
        return
    bot.sendMessage(
        text="Welcome to TSMB bot, this is Linux server/PC manager, Please use /help and read carefully!!",
        chat_id=adminCID,
    )


def helpCMD(bot, update):
    if not isAdmin(bot, update):
        return
    bot.sendMessage(
        text="This bot has access to your server/PC, So it can do anything. Please use Telegram local password to prevent others from accessing to this bot.",
        chat_id=adminCID,
    )


def evalCMD(bot, update):
    """Execute Python code and return the result
    
    SECURITY NOTE: This command allows arbitrary Python code execution.
    It is restricted to admin users only via isAdmin() check.
    This is intentional for remote server management but should be used
    with caution. Only authorized administrators should have access.
    """
    if not isAdmin(bot, update):
        return
    
    # Get the Python code from the message (remove /eval command)
    code = update.message.text.replace("/eval", "", 1).strip()
    
    if not code:
        bot.sendMessage(
            text="Please provide Python code to evaluate.\nUsage: /eval <python_code>",
            chat_id=adminCID,
        )
        return
    
    try:
        # Create a safe namespace for eval
        namespace = {
            '__builtins__': __builtins__,
            'os': os,
            'subprocess': subprocess,
        }
        
        # Try to evaluate as expression first
        try:
            result = eval(code, namespace)
            output = str(result)
        except SyntaxError:
            # If it fails, try to execute as statement
            exec(code, namespace)
            output = "Code executed successfully (no return value)"
        
        bot.sendMessage(text=f"✅ Result:\n{output}", chat_id=adminCID)
    except Exception as e:
        bot.sendMessage(text=f"❌ Error:\n{type(e).__name__}: {str(e)}", chat_id=adminCID)


def topCMD(bot, update):
    if not isAdmin(bot, update):
        return
    cmdOut = str(subprocess.check_output("top -n 1", shell=True), "utf-8")
    bot.sendMessage(text=cmdOut, chat_id=adminCID)


def HTopCMD(bot, update):
    ## Is this user admin?
    if not isAdmin(bot, update):
        return
    ## Checking requirements on your system
    htopCheck = subprocess.call(["which", "htop"])
    if htopCheck != 0:
        bot.sendMessage(
            text="htop is not installed on your system, Please install it first and try again",
            chat_id=adminCID,
        )
        return
    ahaCheck = subprocess.call(["which", "aha"])
    if ahaCheck != 0:
        bot.sendMessage(
            text="aha is not installed on your system, Please install it first and try again",
            chat_id=adminCID,
        )
        return
    os.system("echo q | htop | aha --black --line-fix  > ./htop-output.html")
    with open("./htop-output.html", "rb") as fileToSend:
        bot.sendDocument(document=fileToSend, chat_id=adminCID)
    if os.path.exists("./htop-output.html"):
        os.remove("./htop-output.html")


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def isAdmin(bot, update):
    chat_id = update.message.chat_id
    if str(chat_id) == adminCID:
        return True
    
    update.message.reply_text(
        "You cannot use this bot, because you are not Admin!!!!"
    )
    alertMessage = """Some one try to use this bot with this information:\n chat_id is {} and username is {} """.format(
        update.message.chat_id, update.message.from_user.username
    )
    bot.sendMessage(text=alertMessage, chat_id=adminCID)
    return False


def main():
    try:
        logger.info("Starting Telegram bot...")
        updater = Updater(config["SecretConfig"]["Token"])
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", startCMD))
        dp.add_handler(CommandHandler("ping8", ping8))
        dp.add_handler(CommandHandler("top", topCMD))
        dp.add_handler(CommandHandler("htop", HTopCMD))
        dp.add_handler(CommandHandler("help", helpCMD))
        dp.add_handler(CommandHandler("eval", evalCMD))
        dp.add_handler(MessageHandler(Filters.text, runCMD))

        dp.add_error_handler(error)
        
        logger.info("Bot configured successfully. Starting polling...")
        updater.start_polling()
        logger.info("✅ Telegram bot is now running and listening for commands!")
        updater.idle()
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {type(e).__name__}: {str(e)}")
        logger.info("This is normal if running in an environment without Telegram API access (e.g., Hugging Face Spaces)")
        logger.info("The web server will continue to run. Configure the bot with valid credentials to enable Telegram functionality.")
        # Exit gracefully - let the web server continue running
        sys.exit(0)


if __name__ == "__main__":
    main()
