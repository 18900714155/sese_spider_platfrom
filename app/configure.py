import random


class Configure(object):
    DEBUG = True
    SECRET_KEY = "".join(str(i) for i in [random.randrange(0, 9) for _ in range(24)])

    # server
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5000

    # spider
    CHROME_WEB_HIDE = True

    # database
    SPIDER_MONGODB_URI = ""
    SPIDER_JAVBUS_MONGODB_DB = "spider"
    SPIDER_JAVBUS_MONGODB_CO = "javbus"