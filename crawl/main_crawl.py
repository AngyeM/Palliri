from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from version import *
import filemanager
from bs4 import BeautifulSoup
import requests
import json
import time
from crawl import dcrawl
from person import Person
from pagina import Pagina
from connection_redis import connection_to_redis
import re
import sys
import requests
from datetime import datetime
from sets import Set
import pymongo
import metadataDAO
import pageDAO
from CrawlerSigep import extraerSigep
from CrawlerPresidencia import extraerPresidencia
from json_to_neo4j import JsonToNeo4j
import urlparse
from connection_mongo import connection_to_pages

db_mongo = connection_to_pages()
database =PageDAO(db_mongo.get_db())
metadatapages=metadataDAO.MetadataDAO(database)
pages=pageDAO.PageDAO(database)
redis=connection_to_redis(1)
redispeople=connection_to_redis(2)


def exp_pag_sencilla(metadata,url):
    driver=dcrawl()
    driver.setup(url,2)
    persona=Person()
    new_version=Pagina(url,metadata['entidad'])
    for dato in metadata['info']:
        result_data=driver.explotar_tipo(metadata['info'][dato])
        persona.add_attribute(dato,result_data)
    driver.close()
    persona.set_timestamp()
    if persona.name:
        new_version.agregar_persona(persona.persona)
    new_version.finalizar()
    return new_version

def exp_pag_sigep(metadata,url):
    sigep=extraerSigep()
    persona=sigep.extraer_hv(url)
    sigep.cerrar()
    new_version=Pagina(url,metadata['entidad'])
    persona.set_timestamp()
    if persona.name:
        new_version.agregar_persona(persona.persona)
    new_version.finalizar()
    return new_version

def busqueda_sigep(texto):
    sigep=extraerSigep()
    sigep.setup()
    sigep.buscar(texto)
    result=sigep.obtener_total_enlaces()
    sigep.cerrar()
    nuevos=Set()
    metadata=metadatapages.get_metadata_by_entity("SIGEP")
    id_metadata=""
    for enlace in result:
        if estado_pagina(enlace):
            if redis.existe(enlace):
                id_metadata=redis.get_hash_atribute(enlace,'metadata_id')
            else:
                nuevos.add(enlace)
        else:
            if redis.existe(enlace):
                redis.put_hash_atribute(enlace,'estado',2)
    nuevos_enlaces(nuevos,None,metadata['_id'],5);

def busqueda_presidencia(texto):
    presidencia=extraerPresidencia()
    presidencia.setUp()
    presidencia.cargarOpciones()
    presidencia.Buscar(texto,None)
    presidencia.Cerrar()


def exp_pag_enlaces(metadata,url):
    driver=dcrawl()
    driver.setup(url,1)
    enlaces=driver.getlinks(metadata['enlaces'])
    for enlace in enlaces:
        driver.get(enlace)
        exp_pag_sencilla_sub(metadata,driver)
        driver.back()
    driver.close()

def update_enlaces(metadata,url):
    driver=dcrawl()
    driver.setup(url,1)
    enlaces=driver.getlinks(metadata['enlaces'])
    driver.close()
    nuevos=Set()
    id_metadata=""
    for enlace in enlaces:
        if estado_pagina(enlace):
            if redis.existe(enlace):
                id_metadata=redis.get_hash_atribute(enlace,'metadata_id')
            else:
                nuevos.add(enlace)
        else:
            if redis.existe(enlace):
                redis.put_hash_atribute(enlace,'estado',2)
    redis.updated_link(url)
    nuevos_enlaces(nuevos,metadata,id_metadata);

def update_enlaces_limites(metadata,url):
    nuevos=Set()
    id_metadata=""
    for i in range(metadata['lim_inf'],metadata['lim_sup']+1):
        enlace=metadata['urls'][0]+str(i)
        if estado_pagina(enlace):
            if redis.existe(enlace):
                id_metadata=redis.get_hash_atribute(enlace,'metadata_id')
            else:
                nuevos.add(enlace)
        else:
            redis.inhabilitar()
    redis.updated_link(url)
    nuevos_enlaces(nuevos,metadata,id_metadata);

def nuevos_enlaces(urls,metadata,id,tipo=1):
    if urls:
        if id:
            metadataresult=metadatapages.get_metadata(id)
            almacenadas=Set(metadataresult['urls'])
            almacenadas=almacenadas.union(urls)
            result=metadatapages.update_urls(metadataresult['_id'],list(almacenadas))
            if result:
                for enlace in urls:
                    redis.new_link(enlace,{'estado':0,"metadata_id":metadataresult['_id'],"fecha":fecha_auditoria(),'tipo':metadataresult['t_estructura']})
        else:
            metadata['t_estructura']=str(tipo)
            borrar=['enlaces','url','lim_inf','lim_sup']
            for item in borrar:
                if item in metadata:
                    del metadata[item]
            metadata['urls']=list(urls)
            result_id=metadatapages.add_metadata(metadata)
            for enlace in urls:
                 redis.new_link(enlace,{'estado':0,"metadata_id":result_id,"fecha":fecha_auditoria(),'tipo':tipo})

def exp_pag_contenedor(metadata,url):
    driver=dcrawl()
    driver.setup(url,1)
    filas=driver.getrows(metadata['contenedores'])
    new_version=Pagina(url,metadata['entidad'])
    for fila in filas:
        result=driver.exp_pag_sencilla_sub(metadata,fila)
        new_version.agregar_persona(result)
    driver.close()
    new_version.finalizar()
    return new_version

def validar_versiones(v1_pag):
    # update neo4j information
    try:
        jpage=json.dumps(v1_pag.pagina, ensure_ascii=False).encode("latin1").decode("latin1")
    except Exception as e:
        jpage=json.dumps(v1_pag.pagina, ensure_ascii=False)
    
    a=JsonToNeo4j(jpage)
    a.main_map()

    page_id=redis.get_hash_atribute(v1_pag.pagina['url'],'id_page_vers')

    if page_id:
        #Previous version find
        old_version=pages.get_page(page_id)
        personas=unificar_versiones(old_version['personas'],v1_pag.pagina['personas'])
        if personas:
            for persona in personas:
                pages.update_people(page_id,persona) # agregar actualizaciones a cada persona
                redispeople.add_person(persona.keys()[0],page_id)# redis cada persona
        pages.update_version(page_id)
        pages.update_date(page_id,'f_inicio',v1_pag.pagina['f_inicio'])
        pages.update_date(page_id,'f_fin',v1_pag.pagina['f_fin'])
        redis.put_hash_atribute(v1_pag.pagina['url'],'fecha',fecha_auditoria())

    else:
        #Create new page version
        v1_pag.new_version()
        page_id=pages.add_page(v1_pag.pagina)
        redis.update_link(v1_pag.pagina['url'],{'estado':1,"id_page_vers":page_id,"fecha":fecha_auditoria()})
        redispeople.add_people(v1_pag.pagina['personas'],page_id)


def exp_pag_enlaces_limites(metadata,url):
    driver=dcrawl()
    driver.setup(url,2)
    for i in range(metadata['lim_inf'],metadata['lim_sup']+1):
        driver.get(metadata['urls'][0]+str(i))
        exp_pag_sencilla_sub(metadata,driver)
        driver.back()
    driver.close()

def fecha_auditoria():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def estado_pagina(url):
    status=requests.get(url)
    if 200 <= status.status_code <= 208:
        return 1
    else:
        return 0

def analizar_pagina(url):
    metadata=metadatapages.get_metadata_by_url(url)
    page_id=redis.existe(url)
    if page_id==0 and metadata:
        redis.new_link(url,{'estado':0,"metadata_id":metadata['_id'],"fecha":fecha_auditoria(),'tipo':metadata['t_estructura']})
    if metadata:
        if metadata['t_estructura'] == "1" or metadata['t_estructura'] =="sencilla" or metadata['t_estructura'] ==1:
            version=exp_pag_sencilla(metadata,url)
            validar_versiones(version)
        #enlaces
        if metadata['t_estructura'] == '4':
            update_enlaces(metadata,url)
        #contenedores
        if metadata['t_estructura'] == '2':
            version=exp_pag_contenedor(metadata,url)
            validar_versiones(version)
        #limites
        if metadata['t_estructura'] == '3':
            update_enlaces_limites(metadata,url)
        #sigep
        if metadata['t_estructura'] == '5':
            version=exp_pag_sigep(metadata,url)
            validar_versiones(version)
        #presidencia
        if metadata['t_estructura'] == '6':
            parsed = urlparse.urlparse(url)
            p=urlparse.parse_qs(parsed.query)
            if p:
                if 'name' in p:
                    presidencia=extraerPresidencia()
                    presidencia.setUp()
                    presidencia.cargarOpciones()
                    presidencia.Buscar(p['name'][0].replace('_',' '),None)
                    presidencia.Cerrar()

def busqueda(texto):
    busqueda_sigep(texto)
    busqueda_presidencia(texto)

