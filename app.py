from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from compreface import CompreFace
from compreface.service import RecognitionService
from compreface.collections import FaceCollection
from compreface.collections.face_collections import Subjects
from flask_cors import CORS, cross_origin  
from datetime import date 
from functools import wraps
import simplejson as json  
import secrets
import requests
import base64
import os
from flask import jsonify
app = Flask(__name__)   
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type' 
app.secret_key = '\xfd{H\xe5<\x95\xf9\xe3\x96.5\xd1\x01O<!\xd5\xa2\xa0\x9fR"\xa1\xa8'
bcrypt = Bcrypt(app)
DOMAIN: str = 'http://localhost'
PORT: str = '8000'
API_KEY: str = '6b608248-7019-4257-bd37-c58ce8c557d7'

client = MongoClient('mongodb://localhost:27017/')
db = client.user_management
users_collection = db.users
attendance_collection = db.attendance
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def format_date(date):
    return date.strftime("%d-%m-%Y")
@app.route('/')
def index():
    return redirect(url_for('login'))
#Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users_collection.find_one({"username": username})
        if user:
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('register'))
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            user = {"username": username, "password": hashed_password, "image_uploaded": False}
            users_collection.insert_one(user)
            flash('Registration successful.')
            return redirect(url_for('login'))
    return render_template('register.html')
#Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({"username": username})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['face_verified'] = False
            session['username'] = username
            session['image_uploaded'] = user['image_uploaded']
            if username == 'admin':
                return redirect(url_for('admin'))
        
            if not user['image_uploaded']:
                return redirect(url_for('initial_upload'))
            else:
                flash('Login successful.')
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid login credentials.')
    return render_template('login.html')    
#Route to handle initial image collection and onboarding
@app.route('/initial_upload', methods=['GET', 'POST'])
def initial_upload():
    
    if request.method == 'POST':
        username = session['username']
        users_collection.update_one({"username": username}, {"$set": {"image_uploaded": True}})
        flash('Initial image upload and face detection completed successfully.')
        return redirect(url_for('dashboard'))
    if request.method == 'GET':
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        elif 'logged_in' in session :
            if not session['image_uploaded'] :
                return render_template('initial_upload.html', username=session['username'])
            else:
                return redirect(url_for('dashboard'))
            

#route to control the dashboard
@app.route('/dashboard')
def dashboard():
    if 'logged_in' in session:
        return render_template('dashboard.html', username=session['username'])
    elif 'logged_in' not in session:
        return redirect(url_for('login'))
    #return render_template('dashboard.html')
#route to control the  logout flow
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

#route for face verification before logging attendance
@app.route('/verify',methods=['GET','POST'])
@cross_origin()
def verify():
    print(session['username'],flush=True)
    username = session['username']
    compre_face: CompreFace = CompreFace(DOMAIN, PORT, {
    "limit": 0,
    "det_prob_threshold": 0.8,
    "prediction_count": 1,
    "status": "true"
    })
    recognition: RecognitionService = compre_face.init_face_recognition(API_KEY)
    data = request.get_json()
    img_base64 = data['img']
    img_bytes = base64.b64decode(img_base64)
    random_string = secrets.token_hex(5)
    with open(fr'/home/rdksuper/pclubattend/{random_string}.jpg', 'wb') as f:
        f.write(img_bytes)
    image_path: str = fr'/home/rdksuper/pclubattend/{random_string}.jpg'
    data1 = recognition.recognize(image_path)
    print(data1,flush=True) 
    #response =  jsonify(data1)
    subjects_data = json.dumps(data1)
    subjects_data_parsed = json.loads(subjects_data)    
    if os.path.exists(image_path):
        os.remove(image_path)
        #flash('Image deleted successfully.')
    else :
        print('not deleted',flush=True)
    
    #logic for face recognition 
    try:
        if subjects_data_parsed['code'] == 28 :
            response = jsonify({'msg':"No face in the Image",'code':"0"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
    except KeyError:
        pass

    if subjects_data_parsed['result'][0]['subjects'][0]['subject'] == username and subjects_data_parsed['result'][0]['subjects'][0]['similarity'] > 0.6 :

        response = jsonify({'msg':"Verification Succesful",'code':"1"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        session['face_verified'] = True
        return response

    else :
        response = jsonify({'msg':"Verification Unsuccesful",'code':"0"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
#route to log attendance to  a mongodb document in a collection
@app.route('/log_attendance',methods=['GET'])
@login_required
@cross_origin()
def log_attendance():
    username = session['username']
    verification_status = session['face_verified']
    present_date = format_date(date.today())
    status = 'Present'
    user = attendance_collection.find_one({"username": username})
    if user:
        if verification_status:
            for att in user.get("attendance", []):
                if att["date"] == present_date:
                    response = jsonify({"msg": "Attendance for this date already logged", "code": "0"})
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
            attendance_collection.update_one(
                {"username": username},
                {"$push": {"attendance": {"date": present_date, "status": status}}})
            response = jsonify({"msg": "Attendance logged successfully", "code": "1"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        else:
            response = jsonify({"msg": "Face not verified", "Code": "2"})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
    else:
        attendance_collection.insert_one({
            "username": username,
            "attendance": [{"date": present_date, "status": status}]

        })
        response = jsonify({"msg": "Attendance logged successfully", "code": "1"})
#route to allow a user to view their own attendance
@app.route('/view_attendance',methods=['GET'])
@login_required
@cross_origin()
def view_attendance():
    username = session['username']
    user = attendance_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found"}), 404
    # Pass the attendance data to the template
    return render_template('attendance.html', user=user,username=session['username']), 200
#route for admin panel
@app.route('/admin',methods=['GET'])
@login_required
def admin():
    username = session['username']
    if username == 'admin' :
        users = attendance_collection.find()
        return render_template('admin.html', users=users)
    else :
        return redirect(url_for('dashboard'))
#route for admin to access everyones attendance
@app.route('/user_attendance',methods=['GET','POST'])
@login_required
def user_attendance():
    username = session['username']
    if username == 'admin' :
        user_name = request.form['user']
        user_data = attendance_collection.find_one({"username": user_name})
        return render_template('attendance_user.html',data=user_data)
    else :
        return jsonify({"msg":"Unauthorized"}),403


if __name__ == '__main__':
    app.run(debug=True)






    

