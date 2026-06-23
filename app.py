from flask import Flask,render_template,request,redirect,url_for

import mysql.connector
app=Flask(__name__)
def get_db_connection():

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

@app.route('/signin',methods=["POST","GET"])
def signin():
    email=request.form['email']
    password=request.form['password']
    conn=get_db()
    cursor=conn.cursor()
    cursor.execute(""" select * from users where email=%s and password=%s
                   """,(email,password))
    user=cursor.fetchone()

    return render_template("home.html")




if __name__== "__main__":
    app.run(debug=True)