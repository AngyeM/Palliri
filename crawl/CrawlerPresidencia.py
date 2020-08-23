from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from crawl import dcrawl
from person import Person
from pagina import Pagina
from version import *
import requests
import json
import time
import re
import urlparse
import unidecode
import metadataDAO
import pageDAO
import pymongo
from sets import Set
from connection_redis import connection_to_redis
from datetime import datetime
from json_to_neo4j import JsonToNeo4j
from connection_mongo import connection_to_pages
from settings import *

"""
Configura de los drivers y variables globales necesarias
Entrada: URL de la pag a analizar, tiempo de espera max en segundos
"""
db_mongo = connection_to_pages()
database =PageDAO(db_mongo.get_db())

def fecha_auditoria():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class extraerPresidencia():
    def __init__(self):
        self.driver=dcrawl()
        self.nombre=None
        self.entidad=None
        self.all_options=[]
        self.selectElement=None
        self.xpathRegresar=".//div[@id='ctl00_MainContent_btnRegresar_CD']"
        self.xpathBusqAvan="//div[@id='ctl00_MainContent_btnBusquedaAvanzada']"
        self.xpathSelect="//select[@id='ctl00_MainContent_ddlAreacon']"
        self.xpathBuscar="//div[@id='ctl00_MainContent_btOK_CD']"
        self.xpathCancelar="//div[@id='ctl00_MainContent_btnCancel_CD']"
        self.xpathNombre="//input[@id='ctl00_MainContent_txtNombreAspirante']"

    def setUp(self):
        self.url="https://aspirantes.presidencia.gov.co/"
        self.driver.setup(self.url,2)
        self.btnBusqAvan = self.driver.getelement(self.xpathBusqAvan)
        self.selectElement = self.driver.getelement(self.xpathSelect)
        self.btnBuscar = self.driver.getelement(self.xpathBuscar)
        self.btnCancelar = self.driver.getelement(self.xpathCancelar)
        self.metadatapages=metadataDAO.MetadataDAO(database)
        self.pages=pageDAO.PageDAO(database)
        self.redis=connection_to_redis(1)
        self.redispeople=connection_to_redis(2)
        self.metadata=self.metadatapages.get_metadata_by_entity("ASPIRANTESPRESIDENCIA")

    def Buscar(self,nombre=None,entidad=None):

        #Menu de busqueda avanzada de la pagina principal
        self.nombre=nombre
        self.entidad=entidad
        self.btnBusqAvan.click()
        if self.nombre:
            self.nameElement =self.driver.getelement(self.xpathNombre)
            self.nameElement.send_keys(self.nombre)
            self.nameElement.send_keys(Keys.RETURN)
        if self.entidad:
            Select(self.selectElement).select_by_value(entidad)
        self.btnBuscar.click()

        #Pagina resultado de la busqueda
        PagBusq = BeautifulSoup(self.driver.get_page_source(),"html5lib")
        filas=PagBusq.find_all("tr",id=re.compile('^ctl00_MainContent_gvw_DXDataRow'))
        nuevos=Set()
        for item in filas:
            cols=item.find_all('td')
            link = cols[1].find('a').get('href')
            name=cols[2].text.strip()
            name=name.encode('utf-8','ignore').decode('utf-8')
            name=unidecode.unidecode(name)
            name=name.replace(" ", "_")

            date=cols[3].text.strip()
            date=datetime.strptime(date[:10],'%d/%m/%Y').strftime("%Y%m%d")
            link_parse=self.url+"?cc="+item.find('a').text+"&name="+name+"&date="+date
            if not self.redis.existe(link_parse):
                nuevos.add(link_parse)
                self.redis.new_link(link_parse,{'estado':0,"metadata_id":self.metadata['_id'],"fecha":fecha_auditoria(),'tipo':self.metadata['t_estructura']})
            version=self.BuscarRegistro(link,link_parse)
            self.validar_versiones(version)
        almacenadas=Set(self.metadata['urls'])
        almacenadas=almacenadas.union(nuevos)
        self.metadatapages.update_urls(self.metadata['_id'],list(almacenadas))

    """
    Reinicia la busqueda dado que la accion de regresar en la interfaz limpia los resultados
    """
    def reiniciarBusqueda(self):
        self.btnBusqAvan =self.driver.getelement(self.xpathBusqAvan)
        self.nameElement =self.driver.getelement(self.xpathNombre)
        self.selectElement =self.driver.getelement(self.xpathSelect)
        self.btnBuscar =self.driver.getelement(self.xpathBuscar)
        self.btnCancelar =self.driver.getelement(self.xpathCancelar)
        self.btnBusqAvan.click()

        if self.nombre:
            self.nameElement =self.driver.getelement(self.xpathNombre)
            self.nameElement.clear()
            self.nameElement.send_keys(self.nombre)
            self.nameElement.send_keys(Keys.RETURN)
        if self.entidad:
            Select(self.selectElement).select_by_value(self.entidad)
        self.btnBuscar.click()


    """
    Entrada: enlace de la hoja de vida de una persona
    Salida: hoja de vida en formato json
    """
    def BuscarRegistro(self,enlace,link_parse):
        persona=Person()
        new_version=Pagina(link_parse,self.metadata['entidad'])
        estudios=[]
        experiencia=[]
        try:
            self.driver.execute_script(enlace)
            persona.add_attribute('nombre',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblnombresapellidos'][text()]"))
            persona.add_attribute('t_id',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lbltipoidentificacion'][text()]"))
            persona.add_attribute('n_id',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblnumeroidentificacion'][text()]"))
            persona.add_attribute('f_pub',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblfechapublicacion'][text()]"))
            persona.add_attribute('cargo_postulacion',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblcargo'][text()]"))
            persona.add_attribute('entidad',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblentidad'][text()]"))
            persona.add_attribute('sector',self.driver.explotar_tipo("//span[@id='ctl00_MainContent_lblsector'][text()]"))

            item_estudios =  self.driver.getrows("//tr[starts-with(@id,'ctl00_MainContent_gvwCont_DXDataRow')]")

            for estudio in item_estudios:
                det_estudio = {}
                tds=estudio.find_elements_by_xpath(".//td[@class='dxgv'][text()]")
                det_estudio['nivel']=tds[0].text
                det_estudio['estado']=tds[1].text
                det_estudio['titulo']=tds[2].text
                det_estudio['inst']=tds[3].text
                estudios.append(det_estudio)
            persona.add_attribute('estudios',estudios)

            item_experiencia =  self.driver.getrows("//tr[starts-with(@id,'ctl00_MainContent_gvwCont0_DXDataRow')]")
            for regExperienciaL in item_experiencia:
                det_experiencia =  {}
                tds=regExperienciaL.find_elements_by_xpath(".//td[@class='dxgv'][text()]")
                det_experiencia['entidad']=tds[0].text
                det_experiencia['f_inicio']=tds[1].text
                det_experiencia['f_fin']=tds[2].text
                det_experiencia['cargo']=tds[3].text
                experiencia.append(det_experiencia)
            persona.add_attribute('experiencia',experiencia)
            persona.set_timestamp()
            if persona.name:
                new_version.agregar_persona(persona.persona)
            new_version.finalizar()
            
            self.btnRegresar=self.driver.getelement(self.xpathRegresar)
            if self.btnRegresar:
                self.btnRegresar.click()
            self.reiniciarBusqueda()
        except Exception as e:
            pass
        return new_version


    """
    Cierra el driver de navegacion
    """    
    def Cerrar(self):
        self.driver.close()

    """
    Carga todas las opciones de entidades disponibles de la pagina
    Salida: all_options
    """
    def cargarOpciones(self):
        self.btnBusqAvan.click()
        opc =  self.driver.getrows("//option")
        opc = opc[1:]
        
        for option in opc:
            self.all_options.append(option.get_attribute("value"))    

        self.btnCancelar.click()

    
    def validar_versiones(self,v1_pag):
        try:
            jpage=json.dumps(v1_pag.pagina, ensure_ascii=False).encode("latin1").decode("latin1")
        except Exception as e:
            jpage=json.dumps(v1_pag.pagina, ensure_ascii=False)
        
        a=JsonToNeo4j(jpage)
        a.main_map()

        page_id=self.redis.get_hash_atribute(v1_pag.pagina['url'],'id_page_vers')
        if page_id:
            old_version=self.pages.get_page(page_id)
            personas=unificar_versiones(old_version['personas'],v1_pag.pagina['personas'])
            if personas:
                for persona in personas:
                    self.pages.update_people(page_id,persona) # agregar actualizaciones a cada persona
                    self.redispeople.add_person(persona.keys()[0],page_id)# redis cada persona
            self.pages.update_version(page_id)
            self.pages.update_date(page_id,'f_inicio',v1_pag.pagina['f_inicio'])
            self.pages.update_date(page_id,'f_fin',v1_pag.pagina['f_fin'])
            self.redis.put_hash_atribute(v1_pag.pagina['url'],'fecha',fecha_auditoria())
        else:
            v1_pag.new_version()
            page_id=self.pages.add_page(v1_pag.pagina)
            self.redis.update_link(v1_pag.pagina['url'],{'estado':1,"id_page_vers":page_id,"fecha":fecha_auditoria()})
            self.redispeople.add_people(v1_pag.pagina['personas'],page_id)
