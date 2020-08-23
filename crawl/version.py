import difflib
from difflib import SequenceMatcher
from person import Person

def unificar_versiones(old,new):
    personas_old=[x.keys()[0] for x in old]
    cambios=[]
    for persona in new:
        if persona.keys()[0] in personas_old:
            tm_nombre=persona.keys()[0]
            tm_info=persona.values()[0][0]
            person_update={}
            index=personas_old.index(tm_nombre)
            atrperson={}
            for key,value in tm_info.iteritems():
                old_values=values_from_key(old[index][tm_nombre],key)
                if key !='f_consulta' and old_values:
                    if criterio_diferencia(value,old_values):
                        atrperson[key]=value
                else:
                    atrperson[key]=value
            if len(atrperson)>1:
                person_update[tm_nombre]=atrperson
                cambios.append(person_update)
        else:
            cambios.append(persona)
    return cambios

def values_from_key(array_obj,key):
    values=[]
    for item in array_obj:
        if key in item:
            values.append(item[key])
    return values

def criterio_diferencia(basicstr,array_strs):
    criterio=0
    if type(basicstr) == "str":
        for strvalue in array_strs:
            s = SequenceMatcher(None, basicstr.lower(),strvalue.lower())
            if s.quick_ratio() > criterio:
                criterio=s.quick_ratio()
        if criterio < 0.84:
            return 1
        else:
            return 0
    else:
        return 0

