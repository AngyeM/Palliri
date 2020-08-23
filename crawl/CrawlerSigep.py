from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from bs4 import BeautifulSoup
from crawl import dcrawl
from person import Person
import requests
import json
import time

def to_unicode_or_bust(obj, encoding="latin1"):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj=unicode(obj, encoding)
    return obj

class extraerSigep():
    def __init__(self):
        self.driver=dcrawl()
        self.total_links=[]
        self.BusqButXpath =("//input[@id='find']")
        self.BusqFieldXpath=("//input[@id='query']")
        self.SigPagXpath=("//ul[1]/li[@class='next']/a[@class='step']")

    def setup(self):
        self.driver.setup("https://www.funcionpublica.gov.co/dafpIndexerBHV/",2)
        self.BusqButElement = self.driver.getelement(self.BusqButXpath)
        self.BusqFieldElement = self.driver.getelement(self.BusqFieldXpath)
       
    def buscar(self,texto):
        self.BusqFieldElement.clear()
        self.BusqFieldElement.send_keys(texto)
        self.BusqButElement.click()
        

    def obtener_enlaces(self):
        enlaces=self.driver.getlinks("//table/tbody/tr/td/span/a")
        
        for link in enlaces:
            self.extraer_hv(link)

        if self.siguiente_pagina():
            self.obtener_enlaces()

    def obtener_total_enlaces(self):
        enlaces=self.driver.getlinks("//table/tbody/tr/td/span/a")
        self.total_links=self.total_links+enlaces

        if self.siguiente_pagina():
            self.obtener_total_enlaces()
        return self.total_links

    
    def siguiente_pagina(self):
        try:
            SigPagElement=self.driver.getelement(self.SigPagXpath)
            SigPagElement.click()
            print "Siguiente"
            return True
        except:
            print "No hay siguiente"
            return False
    
    def extraer_hv(self,link):
        estudios = []
        experiencia =[]
        persona=Person()
        self.driver.get(link)
        persona.add_name(self.driver.gettext("//span[@class='nombre_funcionario']|//p[@class='nombre_funcionario']"))
        persona.add_attribute('cargo',self.driver.gettext("//span[@class='cargo_funcionario']|//p[@class='cargo_funcionario']"))
        persona.add_attribute('institucion',self.driver.gettext("//span[@class='institucion_funcionario']|//p[@class='institucion_funcionario']"))
        persona.add_attribute('email',self.driver.gettext("//span[@class='texto_detalle_directorio'][1]|//p[@class='texto_detalle_directorio'][1]"))
        persona.add_attribute('telefono',self.driver.gettext("//span[@class='texto_detalle_directorio'][2]|//p[@class='texto_detalle_directorio'][2]"))
        persona.add_attribute('l_nac',self.driver.gettext(".//*[@class='zona_directorio_detail']/span[4][text()]"))
        
        try:
            item_estudios=self.driver.getrows(".//*[@class='zona_directorio_detail']/ul/li[text()]")
            item_estudios=[(x.text).split('-') for x in item_estudios]

            for item in item_estudios:
                det_estudio = {}
                if len(item)==3:
                    det_estudio['nivel'],det_estudio['titulo'],det_estudio['estado']=item
                    det_estudio['nivel']=to_unicode_or_bust(det_estudio['nivel'])
                    det_estudio['titulo']=to_unicode_or_bust(det_estudio['titulo'])
                    det_estudio['estado']=to_unicode_or_bust(det_estudio['estado'])
                else:
                    det_estudio['nivel']=item
                estudios.append(det_estudio)
            persona.add_attribute('estudios',estudios)
        except Exception as e:
            print "No tiene estudios registrados", e

        try:
            item_experiencias=self.driver.getrows(".//div[@class='zona_directorio_detail']/table[@class='directorio_tabla']/tbody/tr[position() > 1]")
            for exp in item_experiencias:
                det_experiencia =  {}
                tds=[x.text for x in (exp.find_elements_by_xpath(".//td[@class='directorio_td_data'][text()]"))]
                det_experiencia['cargo'],det_experiencia['entidad'],det_experiencia['f_inicio'],det_experiencia['f_fin']=tds
                det_experiencia['cargo']=to_unicode_or_bust(det_estudio['cargo'])
                det_experiencia['entidad']=to_unicode_or_bust(det_estudio['entidad'])
                det_experiencia['f_inicio']=to_unicode_or_bust(det_estudio['f_inicio'])
                det_experiencia['f_fin']=to_unicode_or_bust(det_estudio['f_fin'])
                experiencia.append(det_experiencia)
            persona.add_attribute('experiencia',experiencia)
        except Exception as e:
            print "No tiene experiencia laboral registrada",e
            
        self.driver.back()
        return persona

        

    def cerrar(self):
        self.driver.close()


    
