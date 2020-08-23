import json
import re
from datetime import datetime

abreviaturas='Dr.|Dra.|Ing.|Sr.|Prof.|Sra.|Dir.|Gral.|Gob.'
nostrip=['perfil','email','foto','sigep','estudios','experiencia','f_pub']

class Person:
    def __init__(self):
        self.persona={}
        self.datos = {}
        self.informacion=[]
        self.informacion.append(self.datos)
        self.name=""

    def add_name(self,nombre):
        nombre=self.beautify(nombre.title(),abreviaturas,1)
        self.name=nombre

    def add_attribute(self,key,value):
        if value != '' and value != ' ':
            if key=='nombre':
                self.add_name(self.beautify(value,'-|;|,|:',1))
            elif key=='cargo':
                self.datos[key]=self.beautify(value,'-|;|,',0)
            elif key in nostrip:
                self.datos[key]=value
            else:
                self.datos[key]=self.beautify(value,':',1)

    def set_timestamp(self):
        self.datos['f_consulta']=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.persona[self.name]=self.informacion

    def beautify(self,stringval,regex,index):
        mod=re.split(regex,stringval,1)
        if len(mod) > 1:
            return mod[index].strip()
        else:
            return mod[0].strip()

    def returnJSON(self):
        a={}
        self.set_timestamp()
        a['persona']=self.persona
        return a

