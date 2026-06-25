from flask import Flask, render_template, request, redirect, url_for, session
import random
import smtplib
from email.message import EmailMessage

import mysql.connector
app=Flask(__name__)
app.secret_key = "freshsave_secret"
def get_db():

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Anju@2005",
        database="freshsave"
    )

    return conn
@app.route('/',methods=["POST","GET"])
def home():
    

    return render_template("home.html")

@app.route('/signin',methods=["POST"])
def signin():
    email=request.form['email']
    password=request.form['password']
    conn=get_db()
    cursor=conn.cursor(dictionary=True)
    cursor.execute(""" select * from users where email=%s and password=%s
                   """,(email,password))
    user=cursor.fetchone()
    cursor.close()
    conn.close()
    if not user:
        return render_template("home.html",message="Invalid Username or Password")

    if user['role'] == 'Customer':
        return render_template("customer.html")
    elif user['role'] == 'Owner':
        return render_template("owner.html")
    return render_template("home.html")


@app.route('/signup', methods=['POST'])
def signup():

    role = request.form['role']

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    email_to_check = request.form['email'] if role == 'customer' else request.form['owner_email']

    cursor.execute(
        "SELECT * FROM users WHERE email=%s",
        (email_to_check,)
    )

    existing_user = cursor.fetchone()
    cursor.close()
    conn.close()
    if existing_user:
        
        
        return {"success": False, "message": "Email already registered"}
    
    otp = str(random.randint(100000, 999999))

    session['otp'] = otp
    session['role'] = role

    if role == 'customer':

        session['fullname'] = request.form['fullname']
        session['email'] = request.form['email']
        session['password'] = request.form['password']
        session['phone'] = request.form['phone']


    else:

        session['owner_name'] = request.form['Owner name']
        session['owner_email'] = request.form['owner_email']
        session['owner_password'] = request.form['owner_password']
        session['owner_phone'] = request.form['phone']


    send_otp_email(
        session.get('email', session.get('owner_email')),
        otp
    )

    return {"success": True}

@app.route('/verify-otp', methods=['POST'])
def verify_otp():

    entered_otp = request.form['otp']

    if entered_otp != session['otp']:
        return {"success": False}

    conn = get_db()
    cursor = conn.cursor()

    if session['role'] == 'customer':

        cursor.execute("""
            INSERT INTO users
            (name,email,password,phone,role)
            VALUES (%s,%s,%s,%s,%s)
        """,
        (
            session['fullname'],
            session['email'],
            session['password'],
            session['phone'],
            'Customer'
        ))

    else:

        cursor.execute("""
            INSERT INTO users
            (name,email,password,phone,role)
            VALUES (%s,%s,%s,%s,%s)
        """,
        (
            session['owner_name'],
            session['owner_email'],
            session['owner_password'],
            session['owner_phone'],
            'Owner'
        ))

    conn.commit()

    cursor.close()
    conn.close()

    return {"success": True}


def send_otp_email(email, otp):

    msg = EmailMessage()

    msg["Subject"] = "FreshSave OTP Verification"
    msg["From"] = "leniparker142@gmail.com"
    msg["To"] = email

    msg.set_content(f"Your OTP is {otp}")

    server = smtplib.SMTP("smtp.gmail.com", 587)

    server.starttls()

    server.login(
        "leniparker142@gmail.com",
        "zlav lhxr dhfy vgiu"
    )

    server.send_message(msg)

    server.quit()
    

   
   
        

if __name__== "__main__":
    app.run(debug=True)