# coding=utf-8
import os
import requests
import json
from py2neo import Graph
from py2neo import Path, authenticate
import ast
from settings import *

authenticate(NEO4J["URL"], NEO4J["USER"], NEO4J["PW"])
graph = Graph(NEO4J["CYPHER_URL"])



class JsonToNeo4j():
	def __init__(self,json):
		json=ast.literal_eval(json)
		self.entidad=json.get('entidad')
		self.entidad_key=json.get('entidad').replace(" ","").lower()
		self.source=json.get('url')
		self.json=json
		

	def main_map(self):
		if self.entidad == "SIGEP":
			self.map_sigep()
		elif self.entidad == "ASPIRANTESPRESIDENCIA":
			self.source=self.source[:38]
			self.map_presidencia()
		else:
			self.map_general()

	def map_sigep(self):
		for person in self.json.get('personas'):
			for name,subdata in person.items():
				person_node=name 
				for data in subdata:
					other_fields=[self.entidad_key+"_"+key+":'"+value+"'" for key, value in data.iteritems() if not key in ["estudios","experiencia","cargo","institucion"] and value]
					if other_fields:
						query="MERGE (person:Person {name:\"%s\"}) SET person+={"+" , ".join(other_fields)+"}"
						graph.run(query%(person_node))
					for item in data:
						params={"name":person_node,"source":self.source}
						if "cargo" in data:
							if "institucion" in data:
								params["entidad"]=data['institucion']
							else:
								params["entidad"]="DESCONOCIDO"
							params["cargo"]=data['cargo']
							params["start"]="ACTUAL"
							params["end"]="ACTUAL"

							query="""
							MERGE (entity:Entity {name:{entidad}})
							MERGE (person:Person {name:{name}})
							MERGE (person)-[:WORK_IN {job_title:{cargo},source:{source},start:{start},end:{end}}]->(entity)
							"""
							graph.run(query,params)

						if "estudios" in data :
							query="""
							WITH  {estudios} as xp_items UNWIND xp_items as e
							MERGE (entity:Entity {name:'DESCONOCIDO'})
							MERGE (person:Person {name:{name}})
							WITH entity,person,e
							WHERE  exists(e.estado)
							MERGE (person)-[:STUDY_IN {level:e.nivel,status:e.estado,title:e.titulo,source:{source}}]->(entity)
							"""
							graph.run(query,{"estudios":data['estudios'],"name":person_node,"source":self.source})

						if "experiencia" in data:
							query="""
							WITH  {experiencia} as xp_items UNWIND xp_items
							as e MERGE (entity:Entity {name:e.entidad})
							MERGE (person:Person {name:{name}})
							WITH entity,person,e
							WHERE exists(e.cargo) AND exists(e.f_inicio) AND exists(e.f_fin)
							MERGE (person)-[:WORK_IN {job_title:e.cargo,start:e.f_inicio,end:e.f_fin,source:{source}}]->(entity)
							"""
							graph.run(query,{"experiencia":data['experiencia'],"name":person_node,"source":self.source})

	
	def map_presidencia(self):
		for person in self.json.get('personas'):
			for name,subdata in person.items():
				person_node=name 
				for data in subdata:
					other_fields=[self.entidad_key+"_"+key+":'"+value+"'" for key, value in data.iteritems() if not key in ["estudios","experiencia","cargo_postulacion","entidad","sector"] and value]
					if other_fields:
						query="MERGE (person:Person {name:\"%s\"}) SET person+={"+" , ".join(other_fields)+"}"
						graph.run(query%(person_node))
					for item in data:
						if ("cargo_postulacion" in data and "entidad" in data and "sector" in data):
							query="""
							MERGE (entity:Entity {name:{entidad}})
							MERGE (person:Person {name:{name}})
							MERGE (person)-[:APPLY_TO {job_title:{cargo},source:{source},start:{start},end:{end}}]->(entity)
							"""
							graph.run(query,{"entidad":data['entidad'],"name":person_node,"cargo":data['cargo_postulacion'],"source":self.source,"start":"ACTUAL","end":"ACTUAL"})

						if "estudios" in data :
							query="""
							WITH  {estudios} as xp_items UNWIND xp_items as e
							MERGE (entity:Entity  {name:e.inst})
							MERGE (person:Person {name:{name}})
							WITH entity,person,e
							WHERE  exists(e.estado)
							MERGE (person)-[:STUDY_IN {level:e.nivel,status:e.estado,title:e.titulo,source:{source}}]->(entity)
							"""
							graph.run(query,{"estudios":data['estudios'],"name":person_node,"source":self.source})

						if "experiencia" in data:
							query="""
							WITH  {experiencia} as xp_items UNWIND xp_items
							as e MERGE (entity:Entity {name:e.entidad})
							MERGE (person:Person {name:{name}})
							WITH entity,person,e
							WHERE exists(e.cargo) AND exists(e.f_inicio) AND exists(e.f_fin)
							MERGE (person)-[:WORK_IN {job_title:e.cargo,start:e.f_inicio,end:e.f_fin,source:{source}}]->(entity)
							"""
							graph.run(query,{"experiencia":data['experiencia'],"name":person_node,"source":self.source})

	def map_general(self):
		for person in self.json.get('personas'):
			for name,subdata in person.items():
				person_node=name 
				for data in subdata:
					person_fields=[self.entidad_key+"_"+key+":'"+value+"'" for key, value in data.iteritems() if key in ["perfil","foto","telefono","redes","skype","website","email","twitter","pais_nacimiento","ciudad_nacimiento","cedula","lugar_nacimiento","estudio","experiencia","extension"] and value]
					if person_fields:
						query="MERGE (person:Person {name:\"%s\"}) SET person+={"+" , ".join(person_fields)+"}"
						graph.run(query%(person_node))
					for item in data:
						relationship_fields=[self.entidad_key+"_"+key+":'"+value+"'" for key, value in data.iteritems() if key in ["oficina","comision","partido_politico","depto","comision_constitucional","periodo_constitucional","legislatura","votos","area","orden","tipo_vinculacion","dependencia","grado"] and value]
						relationship_fields.append("source : '"+self.source+"'")
						relationship_fields.append("fconsulta : '"+data['f_consulta']+"'")
						relationship_fields.append("start : 'DESCONOCIDO'")
						relationship_fields.append("end : 'DESCONOCIDO'")

						query="""
						MERGE (entity:Entity {name:\"%s\"})
						MERGE (person:Person {name:\"%s\"})
						MERGE (person)-[:WORK_IN {%s}]->(entity)
						"""
						graph.run(query%(self.entidad,person_node," , ".join(relationship_fields)))


		
