import pymongo
import metadataDAO
import json
import sys
from datetime import datetime
from connection_redis import connection_to_redis
from connection_mongo import connection_to_pages
redis=connection_to_redis(1)

db_mongo = connection_to_pages()
database =PageDAO(db_mongo.get_db())
metadatapages=metadataDAO.MetadataDAO(database)

def fecha_auditoria():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open('json_pages.json', 'r') as f:
    pages_dict = json.load(f)

for metadata in pages_dict:
    metadatapages.add_metadata(metadata)
    print metadata["_id"]
    for enlace in metadata['urls']:
        redis.new_link(enlace,{'estado':0,"metadata_id":metadata['_id'],"fecha":fecha_auditoria(),'tipo':metadata['t_estructura']})

