import pymongo
import random
import string
import sys
# establish a connection to the database
class PageDAO():

    def __init__(self,database):
        self.db=database
        self.page=database.pageversion

    def add_page(self,page):
        if "_id" not in page:
            page_id = self.get_random_str(32)
            page['_id']=page_id
        else:
            page_id=page['_id']
        try:
            self.page.insert_one(page)
        except:
            print "Unexpected error on insert page version:", sys.exc_info()[0]
            return None
        return str(page_id)

    def get_page(self, page_id):
        if page_id is None:
            return None
        page = self.page.find_one({'_id': page_id})
        return page

    def get_random_str(self, num_chars):
        random_string = ""
        for i in range(num_chars):
            random_string = random_string + random.choice(string.ascii_letters)
        return random_string

    def update_people(self,id,persona):
        try:
            filtro={"personas.%s"%(persona.keys()[0]):{'$exists':True},"_id":id}
            update=persona.values()[0]
            exists=self.page.find_one(filtro)
            if exists:
                push={"personas.$.%s"%(persona.keys()[0]):update}
                update_result = self.page.update_one(filtro, {'$push':push})
            else:
                filtro={"_id":id}
                push={"personas":{(persona.keys()[0]):update}}
                update_result = self.page.update_one(filtro, {'$push':push})
                
            return update_result.matched_count
        except:
            print "could not Update people , error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0

    def add_person(self,id,persona):
        try:
            print "adding persona: ",persona
            filtro={"_id":id}
            update=persona
            update_result = self.page.update_one(filtro, {'$push':{"personas":update}})
            return update_result.matched_count
        except:
            print "Could not update the collection, error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0

    def update_version(self,id):
        try:
            filtro={"_id":id}
            update_result = self.page.update_one(filtro, {'$inc':{"version":1}})
            return update_result.matched_count
        except:
            print "Could not update version, error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0
    def update_date(self,id,campo,fecha):
        try:
            filtro={"_id":id}
            update_result = self.page.update_one(filtro, {'$set':{campo:fecha}})
            return update_result.matched_count
        except:
            print "Could not update date, error"
            print "Unexpected error:", sys.exc_info()[0]
            return 0
