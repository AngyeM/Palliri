import redis
from settings import *

class connection_to_redis():

    def __init__(self,database):
        self.pool =redis.ConnectionPool(host=REDIS["HOST"], port=REDIS["PORT"], db=database)
        self.r=redis.StrictRedis(connection_pool=self.pool)


    def existe(self,clave):
        return self.r.exists(clave)

    def get_hash_atribute(self,enlace,clave):
        return self.r.hget(enlace,clave)

    def put_hash_atribute(self,enlace,clave,valor):
        return self.r.hset(enlace,clave,valor)

    def inhabilitar(self,enlace):
        if self.r.exists(enlace):
            self.r.hset(enlace,'estado',2)
            self.r.sadd('estado:2',enlace)
            self.r.srem('estado:0',enlace)
            self.r.srem('estado:1',enlace)

    def new_link(self,enlace,json):
        self.r.hmset(enlace,json)
        self.r.sadd('estado:0',enlace)

    def update_link(self,enlace,json):
        if self.r.exists(enlace):
            self.r.hmset(enlace,json)
            self.updated_link(enlace)

    def updated_link(self,enlace):
        self.r.sadd('estado:1',enlace)
        self.r.srem('estado:0',enlace)
        self.r.srem('estado:2',enlace)

    def add_people(self,array,page_id):
        for persona in array:
            self.r.sadd(persona.keys()[0],page_id)

    def add_person(self,name,page_id):
        self.r.sadd(name,page_id)

    def get_key(self,key):
        result=self.r.keys('*'+key+'*')
        return result

    def search(self,keywords):
        kw=keywords.split(' ')
        result=set()
        for i in kw:
            result.update(self.get_key(i))
        return list(result)

    def get_mongoid(self,keyword):
        result=self.r.smembers(keyword)
        return result
