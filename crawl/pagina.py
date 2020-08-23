from datetime import datetime
import string

class Pagina():
    def __init__(self,url,entidad):
        self.pagina={}
        self.auditoria={}
        self.personas=[]
        self.pagina['f_inicio']=self.fecha_auditoria()
        self.pagina['url']=url
        self.pagina['entidad']=entidad
        self.pagina['personas']=self.personas

    def agregar_persona(self,persona):
        if persona and len(persona.values()[0][0])>1:
            self.personas.append(persona)

    def fecha_auditoria(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def finalizar(self):
        self.pagina['f_fin']=self.fecha_auditoria()

    def new_version(self):
        self.pagina['version']=1
        self.pagina['f_creacion']=self.fecha_auditoria()

    def __setitem__(self, key, item):
        self.data[key] = item
