import pymongo
import re
from settings import *

class connection_to_pages():
    def __init__(self):
        self.connection_string = MONGO
        self.connection = pymongo.MongoClient(self.connection_string)
        self.database = self.connection.seedpages

    def get_db(self):
        return self.database