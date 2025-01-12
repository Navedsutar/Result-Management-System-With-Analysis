from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import pandas as pd
import os


app = Flask(__name__)

#---------------Database connection-------------------
client = MongoClient('mongodb://localhost:27017') #Add your mongodb connection string, If created
db = client['Project'] #Database Name
users_collection = db['users']  #Collection Where Users are saved
collection = db['student_list'] #Collection where data of student are saved
settings_collection = db['setting'] # Collection where data of settings are saved
marks = db['marks'] # Collection where marks of students are saved
excluded_columns = ['_id','year','semester','subject'] 

class User:
    def __init__(self, username, password):     
        self.username = username
        self.password = password    
  
  
        
#---------------------------------Login page Backend-----------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'username': username, 'password': password})

        if ((username=="admin" and password=="221455")):
            return redirect('/homepage') 
        else:
            return render_template('login.html', message='Invalid credentials')

    return render_template('login.html')




#---------------------------Homepage backend-------------------------------
@app.route('/homepage') 
def homepage():
    total_students = collection.count_documents({})
    
    male_students = collection.count_documents({"Gender": "Male"})

    female_students = collection.count_documents({"Gender": "Female"})
    
    first_year_students = collection.count_documents({"Year": "F.E"})
    second_year_students = collection.count_documents({"Year": "S.E"})
    third_year_students =   collection.count_documents({"Year": "T.E"})
    fourth_year_students = collection.count_documents({"Year": "B.E"})
    
    return render_template('homepage.html', total_students=total_students, 
                           male_students=male_students, female_students=female_students,
                           first_year_students=first_year_students, second_year_students=second_year_students,
                           third_year_students=third_year_students, fourth_year_students=fourth_year_students)





#---------------------------------Student List Page backend--------------------------------
@app.route('/student_list')
def student_list():
    student_list_from_mongo = list(collection.find())
    return render_template('student_list.html', student_list=student_list_from_mongo)





#--------------------------------Upload Page backend--------------------------------
@app.route('/UPLOAD')
def UPLOAD():
    return render_template('upload.html')

@app.route('/upload', methods=['POST']) # type: ignore
def upload():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return render_template('upload.html',message='No file Chossen')
    
    if file:
        df = pd.read_excel(file) # type: ignore
        
        data = df.to_dict(orient='records')
        
        collection.insert_many(data)
        
        return render_template('upload_success.html')



#------------------------------Settings page backend------------------------------------
@app.route('/SETTINGS')
def SETTINGS():
    return render_template('settings.html')

@app.route('/submit_settings', methods=['POST']) # type: ignore
def submit_settings():
    year = request.form['year']
    semester = request.form['semester']
    subject = request.form['subject']
    ese = 'ese' in request.form
    iae = 'iae' in request.form
    tw = 'tw' in request.form
    pr = 'pr' in request.form
    
    settings_collection.insert_one({
        'year': year,
        'semester': semester,
        'subject': subject,
        'ese': ese,
        'iae': iae,
        'tw': tw,
        'pr': pr
    })
    
    file = request.files['file']
    
    if file.filename.endswith('.xlsx'):# type: ignore
        df = pd.read_excel(file) # type: ignore
        
        d1 = df.to_dict(orient='records')
        
        for record in d1:
            record['year'] = year
            record['semester'] = semester
            record['subject'] = subject
        
        marks.insert_many(d1)
        
        return render_template('upload_success.html')
    else:
        return render_template('settings.html',message='Please upload a valid Excel file.')



#-------------------------Result sheet Backend-------------------------------
@app.route('/result_sheet')
def result_sheet():
    marks_from_mongo = list(settings_collection.find())
    years = set(doc['year'] for doc in settings_collection.find({}, {'year': 1}))
    semesters = set(doc['semester'] for doc in settings_collection.find({}, {'semester': 1}))
    subjects = set(doc['subject'] for doc in settings_collection.find({}, {'subject': 1}))
    
    return render_template('result_sheet.html',marks=marks_from_mongo, years=years, semesters=semesters, subjects=subjects)

@app.route('/display', methods=['POST'])
def display():
    
    years = []
    semesters = []
    subjects=[]
    data = None
    
    year = request.form['year']
    semester = request.form['semester']
    subject = request.form['subject']
    data = marks.find({"year": year, "semester": semester,"subject":subject})
    
    return render_template("display.html", excluded_columns=excluded_columns,years=years, semesters=semesters,subjects=subjects, data=data)



#------------------------Result Analysis Backend---------------------------------
@app.route('/result_analysis')
def result_analysis():
    years = marks.distinct("year")
    semesters = marks.distinct("semester")
    subjects = marks.distinct("subject")
    return render_template('result_analysis.html', years=years, semesters=semesters, subjects=subjects)

@app.route('/result', methods=['POST'])
def result():
    year = request.form.get('year')
    semester = request.form.get('semester')
    subject = request.form.get('subject')

    query = {"year": year, "semester": semester, "subject": subject}
    data = list(marks.find(query))

    total_students = len(data)
    marks_above_80 = sum(1 for student in data if sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) > 120)
    marks_70_to_80 = sum(1 for student in data if 105 <= sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) <= 120)
    marks_60_to_70 = sum(1 for student in data if 90 <= sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) < 105)
    marks_50_to_60 = sum(1 for student in data if 75 <= sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) < 90)
    marks_40_to_50 = sum(1 for student in data if 60 <= sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) < 75)
    marks_below_40 = sum(1 for student in data if sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) < 60)
    pass_marks = sum(1 for student in data if sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) > 60)
    fail_marks = sum(1 for student in data if sum(student.get(field, 0) for field in ["ESE", "IAE", "TW", "PW"]) < 60)

    return render_template('display_result.html',fail_marks=fail_marks,pass_marks=pass_marks, total_students=total_students, marks_above_80=marks_above_80, marks_70_to_80=marks_70_to_80, marks_60_to_70=marks_60_to_70, marks_50_to_60=marks_50_to_60, marks_40_to_50=marks_40_to_50, marks_below_40=marks_below_40)




#------------------------Check Drop  Backend---------------------------------
@app.route('/CHECK_DROP')
def CHECK_DROP():
    return render_template('check_drop.html')
    
@app.route('/check_drop', methods=['POST']) # type: ignore
def check_drop():
    render_template('check_drop.html')
    current_year = request.form.get('current_year')
    past_year = request.form.get('past_year')
    external_kt = int(request.form.get('external_kt')) # type: ignore
    ise = int(request.form.get('ise'))# type: ignore

    if(current_year=='First'):
        if(past_year=='first'):
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Second year')
            else:
                return render_template('check_drop.html',message='You have a year drop')
            
    elif(current_year=='Second'):
        if(past_year=='first'):
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Second year')
            else:
                return render_template('check_drop.html',message='You have a year drop')    
        else:
            if(past_year=='second'):
                if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                    return render_template('check_drop.html',message='You can go to Third year')
                else:
                    return render_template('check_drop.html',message='You have a year drop')   
                
    elif(current_year=='Third'):
        if(past_year=='first'):
                    return render_template('check_drop.html',message='You have a year drop')
        elif(past_year=='second'):
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Fourth year')
            else:
                return render_template('check_drop.html',message='You have a year drop')
        else:
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Fourth year')
            else:
                return render_template('check_drop.html',message='You have a year drop')
    
    else:   
        if(past_year=='second'):
                    return render_template('check_drop.html',message='You have a year drop')
        elif(past_year=='third'):
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Fourth year')
            else:
                return render_template('check_drop.html',message='You have a year drop')
        else:
            if((external_kt+ise) <= 8 and external_kt<=5 and ise<=10):
                return render_template('check_drop.html',message='You can go to Fourth year')
            else:
                return render_template('check_drop.html',message='You have a year drop')





#------------------------Main Function---------------------------------
if __name__ == '__main__':
    app.run(debug=True,port=5000)
