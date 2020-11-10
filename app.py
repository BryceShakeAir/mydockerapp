from flask import Flask, render_template, url_for, request, session, redirect
import pymongo
import random
import os
from PIL import Image
from PIL.ExifTags import TAGS
import logging
import six

app = Flask(__name__)

app.logger.info("started logging")

app.config["IMAGE_UPLOADS"]="./static"
logging.basicConfig(level=logging.DEBUG)
myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
app.logger.info(myclient)


mongo = myclient["imagesystem"]

@app.route('/')
@app.route('/index/')
def index():

    allData = mongo.images.find()
    images = []
    header = []
    meta = []
    for data in allData :

        images.append(data['filename'])
        tempHeader = []
        tempMeta = []
        for elem in data :
            tempHeader.append(elem)
            tempMeta.append(data[elem])

        header.append(tempHeader)
        meta.append(tempMeta)

    return render_template('index.html',images=images,headers=header,meta=meta)
    
def convert2unicode(mydict):
    for k, v in mydict.items():
        if isinstance(v, str):
            try :
                mydict[k] = v.encode('utf-8','replace')
            except :
                mydict[k] = ''
        elif isinstance(v, dict):
            convert2unicode(v)
def getMetaData(image_file,filename) :

    try:
        image = Image.open(image_file)
    except IOError:
        pass
    # raise an IOError if file cannot be found,or the image cannot be opened.

    # dictionary to store metadata keys and value pairs.
    exif = {}

    # iterating over the dictionary 
    for tag, value in image._getexif().items():

    #extarcting all the metadata as key and value pairs and converting them from numerical value to string values
        if tag in TAGS:
            exif[TAGS[tag]] = value

    #checking if image is copyrighted      
    try:
        if 'Copyright' in exif:
            print("Image is Copyrighted, by ", exif['Copyright'])
    except KeyError:
        pass

    exif['filename']=filename
    convert2unicode(exif)
    return exif

@app.route('/add/',methods =['GET','POST'])
def add():

    if request.method=='POST' :

        if request.files['image'] :

            image = request.files['image']
            image.filename = "img"+str(random.randint(0,100000)) +".jpg"

            filepath = os.path.join(app.config['IMAGE_UPLOADS'],
                image.filename)
            image.save(filepath)

            newRecord = getMetaData(filepath,image.filename)
            
            mongo.images.insert(newRecord)

    return render_template('add.html')


@app.route('/logout/')
def logout():
    session.clear()
    return render_template('logout.html')

def parseForm() :

    dict1 = {}

    if( len(request.form['Yresolution1'] ) > 0 and
        len(request.form['Yresolution2'] ) > 0 ):

        dict1['YResolution'] = [ int(request.form['Yresolution1']) , 
        int(request.form['Yresolution2']) ]

    if( len(request.form['Xresolution1'] ) > 0 and
        len(request.form['Xresolution2'] ) > 0 ):

        dict1['XResolution'] = [ int(request.form['Xresolution1']) , 
        int(request.form['Xresolution2']) ]

    if( len(request.form['shutter1'] ) > 0 and
        len(request.form['shutter2'] ) > 0 ):

        dict1['ShutterSpeedValue'] = [ int(request.form['shutter1']) , 
        int(request.form['shutter2']) ]

    if( len(request.form['make']) >0 ) :

        dict1['Make'] = request.form['make']

    if( len(request.form['flash']) >0 ) :

        dict1['Flash'] = int(request.form['flash'])    

    return dict1

def updateImage(image1,queries) :

    for q in queries :
        image1.append(q['filename'])


@app.route('/search/' ,methods=['GET','POST'])
def search():

    queries = []
    image1 = []
    if(request.method=='POST') :

        record1 = parseForm()
        q1 = mongo.images.find(record1)
        for query in q1 :
            queries.append(query)
        updateImage(image1,queries)


    return render_template('search.html',queries=queries,image1=image1)

@app.route('/login/', methods=['POST','GET'])
def login():
    
    if(request.method=='POST') :

        users = mongo.users
        login_user = users.find_one({'name': request.form['username']})

        if login_user:
            if request.form['pass'] == login_user['password']:
                session['username'] = request.form['username']
                session['log']=True
                return redirect(url_for('index'))

        return 'Invalid username or password'
    return render_template('login.html')
@app.route('/register/',methods=['GET','POST'] )
def register() :

    if(request.method=='POST') :

        session['unameerror'] =False
        session['pwderror'] =False
        session['success'] =False

        if(len(request.form['username'])<0) :
            session['unameerror'] =True
        elif (len(request.form['username'])<0) :
            session['pwderror'] =True
        else :
            users = mongo.users
            register_user = users.find_one({'name': request.form['username']})

            if register_user :
                session['unameerror'] = True
            else :
                users.insert({ 'name' : request.form['username'] , 'password' :
                request.form['pass'] })
                session['success'] = True
                    
    return render_template( 'register.html' )

if __name__ == '__main__':
    app.secret_key = 'mysecret'
    app.run(debug=True)
