import pymongo
import random
import string
import sys

# establish a connection to the database
class MetadataDAO():

    def __init__(self,database):
        self.db=database
        self.meta=database.metadatapage

    def add_metadata(self,metadata):
        if "_id" not in metadata:
            meta_id = self.get_random_str(32)
            metadata['_id']=meta_id
        else:
            meta_id=metadata['_id']
        try:
            self.meta.insert_one(metadata)
        except:
            print "Unexpected error on insert metadata: ",metadata['_id'], sys.exc_info()[0]
            return None
        return str(meta_id)

    def get_metadata(self, meta_id):
        metadata=None
        if meta_id is None:
            return None
        metadata = self.meta.find_one({'_id': meta_id})
        return metadata

    def get_metadata_by_url(self, url):
        metadata=None
        if url is None:
            return None
        if "https://aspirantes.presidencia.gov.co/" in url:
            filtro={"root":"https://aspirantes.presidencia.gov.co/"}
            metadata = self.meta.find_one(filtro)
        else:
            filtro={"urls":url}
            metadata = self.meta.find_one(filtro)
        return metadata

    def get_metadata_by_entity(self, name):
        if name is None:
            return None
        else:
            filtro={"entidad":name}
        metadata = self.meta.find_one(filtro)
        return metadata

    def update_urls(self,id,urls):
        try:
            self.meta.update_one({'_id':id},{'$set':{'urls':urls}})
            print "Updated Document with _id = {_id}".format(_id=id)
            return 1
        except pymongo.errors.AutoReconnect as e:
            print ("Exception writing doc with _id = {_id}. " +
                   "{te}: {e}").format(_id=id, te=type(e), e=e)
            return 0

    def get_random_str(self, num_chars):
        random_string = ""
        for i in range(num_chars):
            random_string = random_string + random.choice(string.ascii_letters)
        return random_string
