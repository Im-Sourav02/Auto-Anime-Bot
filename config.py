# config.py
from os import getenv
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

load_dotenv()
LOGS = logging.getLogger(__name__)

class Var:
    API_ID = getenv("API_ID", "21223629")
    API_HASH = getenv("API_HASH", "920eaaf96c0ed560371add171ff0e573")
    BOT_TOKEN = getenv("BOT_TOKEN", "8657589634:AAGgsR5KBzc1iadCy5h-268cYGslI87JMGU")
    DB_URI = getenv("DB_URI", "mongodb+srv://souravagarwal14092007:szXRs8g7fErCnn4@cluster0.xlsbf3o.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    DB_NAME = getenv("DB_NAME", "Auto-Anime")
    BAN_SUPPORT = getenv("BAN_SUPPORT", "https://t.me/Im_Sukuna02")
    FSUB_LINK_EXPIRY = int(getenv("FSUB_LINK_EXPIRY", "120"))
    CHANNEL_ID = int(getenv("CHANNEL_ID", "-1003822482934"))
    MHCHANNEL_URL = getenv("MHCHANNEL_URL", "https://t.me/+YVvk6nUKVYcwYzBl")
    ANIME = getenv("ANIME", "Is It Wr2131ong to Try to Pi123ck Up Girls in a Dungeon?")
    CUSTOM_BANNER = getenv("CUSTOM_BANNER", "https://i.ibb.co/LDPMX7Fg/x.png")

    PROTECT_CONTENT = True if getenv('PROTECT_CONTENT', "True") == "True" else False 
    BACKUP_CHANNEL = int(getenv("BACKUP_CHANNEL", "-1003896219043"))
    LOG_CHANNEL = int(getenv("LOG_CHANNEL", "-1003711233930"))
    MAIN_CHANNEL = int(getenv("MAIN_CHANNEL", "-1003821772425"))
    FILE_STORE = int(getenv("FILE_STORE", "-1003257368933"))
    ADMINS = list(map(int, getenv("ADMINS", "6123108288").split()))

    RSS_ITEMS = getenv("RSS_ITEMS", "").split()
    SEND_SCHEDULE = getenv("SEND_SCHEDULE", "True").lower() == "true"
    BRAND_UNAME = getenv("BRAND_UNAME", "@AnimeInfinix")

    FFCODE_1080 = getenv("FFCODE_1080")
    FFCODE_720 = getenv("FFCODE_720")
    FFCODE_480 = getenv("FFCODE_480")
    FFCODE_360 = getenv("FFCODE_360")
    FFCODE_HDRip = getenv("FFCODE_HDRip")
    QUALS = getenv("QUALS", "480 720 1080 HDRip").split()

    DISABLE_CHANNEL_BUTTON = getenv("DISABLE_CHANNEL_BUTTON", False) == 'True'
    AS_DOC = getenv("AS_DOC", "True").lower() == "true"
    THUMB = getenv("THUMB", "https://i.ibb.co/LDPMX7Fg/x.png")
    START_PIC = getenv("START_PIC","https://i.ibb.co/LDPMX7Fg/x.png")
    FORCE_PIC = getenv("FORCE_PIC", "https://i.ibb.co/LDPMX7Fg/x.png")


# ✅ Required variable validation (outside the class)
REQUIRED_VARS = ["API_ID", "API_HASH", "BOT_TOKEN", "DB_URI"]
for var_name in REQUIRED_VARS:
    if not getattr(Var, var_name):
        LOGS.critical(f"Missing required environment variable: {var_name}")
        exit(1)
        #--------------------------------------------


LOG_FILE_NAME = "log.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
