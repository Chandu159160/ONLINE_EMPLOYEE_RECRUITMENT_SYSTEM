from flask import Flask, render_template, request, redirect,session,url_for,flash
import mysql.connector
from flask_session import Session
from key import secret_key,salt
from itsdangerous import URLSafeTimedSerializer
from stoken import token
from cmail import sendmail
app = Flask(__name__)
app.secret_key=secret_key
app.config['SESSION_TYPE']='filesystem'

# MySQL configurations
db_config=mysql.connector.connect(host="localhost",user="root",password="admin",db="employee_recruitment")

# Routes
@app.route('/')
def index():
    return render_template('title.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('home'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=db_config.cursor(buffered=True)
        cursor.execute('SELECT count(*) from users where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
            return render_template('login.html')
    return render_template('login.html')
@app.route('/homepage')
def home():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('login'))
@app.route('/registration',methods=['GET','POST'])
def registration():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        email=request.form['email']
        cursor=db_config.cursor(buffered=True)
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from users where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('registration.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('registration.html')
        data={'username':username,'password':password,'email':email}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('registration.html')
@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt,max_age=180)
    except Exception as e:
        #print(e)
        return 'Link Expired register again'
    else:
        cursor=db_config.cursor(buffered=True)
        username=data['username']
        cursor.execute('select count(*) from users where username=%s',[username])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into users values(%s,%s,%s)',[data['username'],data['password'],data['email']])
            db_config.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))

@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if session.get('user'):
        if request.method == 'POST':
          name = request.form['name']
          position = request.form['position']
          experience = request.form['experience']
          cursor=db_config.cursor(buffered=True)
          cursor.execute('insert into candidates (name,position,experience) values(%s,%s,%s)',[name, position, experience])
          db_config.commit()
          cursor.close()
          return redirect('/candidates')
        return render_template('add_candidates.html')
    else:
        return redirect(url_for('login'))


@app.route('/submit', methods=['POST'])
def submit():
    # Retrieve form data
   
     name = request.form['name']
     position = request.form['position']
     experience = request.form['experience']
    # Insert feedback data into the database
     cursor=db_config.cursor()
     cursor.execute("INSERT INTO candidates (name,position,experience) VALUES (%s, %s, %s)", (name,position,experience))
     db_config.commit()
     return redirect(url_for('view'))
@app.route('/view')
def view():
    if session.get('user'):
        username=session.get('user')
        cursor=db_config.cursor(buffered=True)
        cursor.execute('select * from candidates')
        data=cursor.fetchall()      
        cursor.close()
        return render_template('index.html',data=data)
    else:
        return redirect(url_for('login'))

    # Retrieve all candidates from the database
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        flash('Successfully loged out')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

app.run(debug=True,use_reloader=True)