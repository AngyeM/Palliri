from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from person import Person
import requests
import json
import time
import re

pattern_img=re.compile("^.*img$")
pattern_text=re.compile("^.*text\(\)\]$")
pattern_url=re.compile("^.*\/a$")

class dcrawl:

    def __init__(self,**dictionary):
        if dictionary:
            self.__dict__.update(dictionary)
            self.wait=5
        else:
            #self.driver= webdriver.PhantomJS()
            self.driver= webdriver.Firefox()
            self.wait=1
            self.driver.set_window_size(1920,1080)
            self.htmlString=""


    def setup(self,url,tipo):
        # 1 static 2 dynamic
        if tipo==1:
            try:
                self.driver.get("data:text/html;charset=utf-8," + requests.get(url).text);
            except Exception as error:
                print error
        else:
            try:
                self.driver.get(url)
            except Exception as error:
                print error

    def getelement(self,xpathelement):
        limit=2
        for x in range(limit):
            try:
                button=WebDriverWait(self.driver,self.wait).until(lambda driver:self.driver.find_element_by_xpath(xpathelement))
                return button
            except Exception as error:
                if x==limit-1:
                    return ''
                else:
                    pass

    def getelement_byid(self,id):
        limit=2
        for x in range(limit):
            try:
                button=WebDriverWait(self.driver,self.wait).until(lambda driver:self.driver.find_element_by_id(id))
                return button
            except Exception as error:
                print "no ", id
                print "error  ....", error
                if x==limit-1:
                    return ''
                else:
                    pass

    def getimg(self,xpathimg):
        try:
            img_data=WebDriverWait(self.driver,self.wait).until(lambda driver:self.driver.find_element_by_xpath(xpathimg)).get_attribute('src')
            return img_data
        except Exception as error:
            return ''

    def gettext(self,xpathtext):
        limit=2
        for x in range(limit):
            try:
                text_data=[x.text for x in (WebDriverWait(self.driver,self.wait).until(lambda driver: self.driver.find_elements_by_xpath(xpathtext)))]
                t_result=''.join(text_data)
                try:
                    t_result=t_result.decode("latin-1")
                except Exception as e:
                    pass;
                return t_result
            except Exception as error:
                if x==limit-1:
                    return ''
                else:
                    pass

    def geturl(self,xpathurl):
        try:
            url_data=WebDriverWait(self.driver,self.wait).until(lambda driver: self.driver.find_element_by_xpath(xpathurl)).get_attribute('href')
            return url_data
        except Exception as error:
            return ''
    def getlinks(self,xpathlinks):
        try:
            contenedores=WebDriverWait(self.driver,self.wait).until(lambda driver: self.driver.find_elements_by_xpath(xpathlinks))
            contenedores=[x.get_attribute('href') for x in contenedores]
            return contenedores
        except Exception as error:
            return []
    def getrows(self,xpathrows):
        try:
            rows=WebDriverWait(self.driver,self.wait).until(lambda driver: self.driver.find_elements_by_xpath(xpathrows))
            return rows
        except Exception as error:
            return []
    def get(self,url):
        try:
            self.driver.get(url)
        except Exception as error:
            print error
    def back(self):
        try:
            self.driver.back()
        except Exception as error:
            print error
    def close(self):
        try:
            self.driver.quit()
        except Exception as error:
            print error

    def explotar_tipo(self,xpathattribute):
        if pattern_img.match(xpathattribute):
            data=self.getimg(xpathattribute)
        elif pattern_text.match(xpathattribute):
            data=self.gettext(xpathattribute)
        elif pattern_url.match(xpathattribute):
            data=self.geturl(xpathattribute)
        else:
            data=''
        return data

    def exp_pag_sencilla_sub(self,metadata,sub=None):
        if sub:
            self.driver=sub
        persona=Person()
        for dato in metadata['info']:
            result_data=self.explotar_tipo(metadata['info'][dato])
            persona.add_attribute(dato,result_data)
        persona.set_timestamp()
        if persona.name:
            return (persona.persona)
        else:
            return {}
    def get_page_source(self):
        return self.driver.page_source

    def execute_script(self,link):
        self.driver.execute_script(link)
