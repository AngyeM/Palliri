# coding:utf-8
from flask import Flask
from flask import render_template, request
from connection_redis import connection_to_redis
from pageDAO import PageDAO
from connection_mongo import connection_to_pages
from flask import jsonify
import json
from flask_mail import Mail
from flask_mail import Message
from settings import *

app = Flask(__name__)
app.config.update(MAIL)
mail = Mail(app)

@app.route('/', methods=['get', 'post'])
def init():
    return render_template('index.html',var='')

@app.route('/', methods=['get', 'post'])
def search():
    return render_template('index.html',var='')

def prettify(texto):
    outtext=""
    try:
        outtext=texto.decode("utf-8")
    except Exception as e:
        outtext=texto
    return outtext


@app.route('/search_item',methods=['get', 'post'])
def search_item():
    msg = ''
    result=None
    template=None
    if request.method == 'POST':
        keywords = request.form["keywords"]
        item = request.form["items"]
        if item == 'person':
            template='index.html'
            redispeople=connection_to_redis(2)
            result1=redispeople.search(keywords)
            result=[prettify(item) for item in result1]
        else:
            database = connection_to_pages()
            db_mongo =PageDAO(database.get_db())
            results=db_mongo.search(keywords)           
            if len(results)>0:
                try:
                    result2=json.dumps(results, sort_keys = True, indent = 4, separators = (',', ': '), ensure_ascii=False).encode("latin1").decode('latin1')
                except Exception as e:
                    result2=json.dumps(results, sort_keys = True, indent = 4, separators = (',', ': '))
                    pass
                result=result2
                template='result_crawler.html'
            else:
                template='index.html'

    return render_template(template,result2=result)
   

@app.route('/get_item',methods=['get', 'post'])
def get_item():
    database = connection_to_pages()
    keyword = request.args.get("keyword")
    redispeople=connection_to_redis(2)
    result2=[]
    result_ids=redispeople.get_mongoid(keyword)
    page=PageDAO(database.get_db())
    for version_id in result_ids:
        version=page.get_page_formatted(version_id)
        result2.append(version)
    try:
        result2=json.dumps(result2, sort_keys = True, indent = 4, separators = (',', ': '), ensure_ascii=False).encode("latin1").decode('latin1')
    except Exception as e:
        result2=json.dumps(result2, sort_keys = True, indent = 4, separators = (',', ': '))
    return render_template('result_crawler.html',result2=result2)

@app.route('/get_item_graph',methods=['get', 'post'])
def get_item_graph():
    keyword = request.args.get("keyword")
    return render_template('graph_view.html',key=keyword)

@app.route('/contact',methods=['get', 'post'])
def contact():
    return render_template('contact.html')

@app.route('/send_mail',methods=['get', 'post'])
def send_mail():
    name=""
    if request.method == 'POST':
        try:
            message = request.form["message"]
            name = request.form["inputname"]
            email = request.form["inputEmail3"]
            msg = Message("Palliri",
                          recipients=[MAIL["MAIL_DEFAULT_SENDER"]])
            if "send_copy" in request.form:
                send_copy = request.form["send_copy"]
                if (send_copy =='on'):
                    msg.add_recipient(email)
            msg.body=message
            mail.send(msg)
        except Exception as e:
            pass;
        
    return render_template('thanks_contact.html',name=name)

@app.route('/about',methods=['get', 'post'])
def about():
    return render_template('about.html')

@app.route('/graph',methods=['get', 'post'])
def graph():
    return render_template('graph_view.html')

if __name__=='__main__':
    app.debug = True
    app.run(host='0.0.0.0',port=8000)
    