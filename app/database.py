import pymongo

from .configure import Configure


spider_mongo_client = pymongo.MongoClient(Configure.SPIDER_MONGODB_URI)
javbus_coll = spider_mongo_client[Configure.SPIDER_JAVBUS_MONGODB_DB][Configure.SPIDER_JAVBUS_MONGODB_CO]