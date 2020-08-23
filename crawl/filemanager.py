# -*- coding: utf-8 -*-
import json
import time

def write_file_JSON(file, line):
	try:
		with open(file + ".json",'a') as g:#Open the file
			json.dump(line, g)
			g.write("\n")
	except IOError:
		open(file,'w')
		print "No se puede leer el archivo: ", file
	except Exception as error:
		print error
		#self.recordError("Error: " + str(error))

def write_file(file, line):
	try:
		with open(file ,'a') as g:#Open the file
			g.write(line + "\n")
	except IOError:
		open(file,'w')
		print "No se puede leer el archivo: ", file
	except Exception as error:
		print error
		 #self.recordError("Error: " + error)

def read_file(file):
	try:
		# print "in read_file"
		return open(file,'r')
	except IOError:
		print "No se puede leer el archivo: ", file

def leer_JSON(file):
	try:
		with open(file) as data_file:
			return json.load(data_file)
	except IOError:
		print "No se puede leer el archivo: ", file
