from flask import Flask, render_template,session, request, redirect, url_for, session
import random
import smtplib
from email.message import EmailMessage
from datetime import date
import jwt
import razorpay
import os
from werkzeug.utils import secure_filename
import datetime
from flask import make_response
from flask import jsonify
today = date.today()

import mysql.connector
app=Flask(__name__)
RAZORPAY_KEY_ID = "rzp_test_T6AXHPADOQfHfG"

RAZORPAY_KEY_SECRET = "JFT7f46XrY7iazUQpX0A07d7"

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)
UPLOAD_FOLDER = "static/images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
JWT_SECRET = "freshsave_jwt_secret"
JWT_ALGORITHM = "HS256"
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

    payload = {
    "user_id": user["id"],
    "name": user["name"],
    "role": user["role"],
    "exp": datetime.datetime.now(datetime.timezone.utc)+ datetime.timedelta(hours=2)
        }

    token = jwt.encode(
            payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

    response = make_response(
            redirect(url_for("customer"))
            if user["role"] == "Customer"
            else redirect(url_for("owner"))
        )

    response.set_cookie(
            "token",
            token,
            httponly=True
        )

    return response
    


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
    
@app.route("/customer")
def customer():
    token = request.cookies.get("token")

    if not token:
        return redirect(url_for("home"))
    try:
        data = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = data["user_id"]
        user_name = data["name"]
        user_role = data["role"]
        if user_role != "Customer":
            return redirect(url_for("home"))

    except jwt.ExpiredSignatureError:
        return redirect(url_for("home"))

    except jwt.InvalidTokenError:
        return redirect(url_for("home"))
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY expiry_date ASC
    """)

    products = cursor.fetchall()
    print(products)
    for product in products:
        product["days_left"] = (product["expiry_date"] - today).days
        product["discount"] = int(
            ((product["original_price"] - product["discount_price"])
             / product["original_price"]) * 100
        )
    cursor.close()
    conn.close()

    return render_template(
        "customer.html",
        products=products,
        user_name=user_name,
        razorpay_key=RAZORPAY_KEY_ID
    )
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    token = request.cookies.get("token")

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    info = request.get_json()

    product_id = info["product_id"]

    quantity = info["quantity"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM cart
        WHERE user_id=%s
        AND product_id=%s
    """,(user_id,product_id))

    item = cursor.fetchone()

    if item:

        cursor.execute("""
            UPDATE cart
            SET quantity=quantity+%s
            WHERE user_id=%s
            AND product_id=%s
        """,(quantity,user_id,product_id))

    else:

        cursor.execute("""
            INSERT INTO cart
            (user_id,product_id,quantity)
            VALUES(%s,%s,%s)
        """,(user_id,product_id,quantity))

    conn.commit()

    cursor.close()

    conn.close()

    return jsonify({
        "message":"Added to cart!"
    })   
@app.route("/cart_count")
def cart_count():

    token=request.cookies.get("token")

    data=jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id=data["user_id"]

    conn=get_db()
    cursor=conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT SUM(quantity) total
        FROM cart
        WHERE user_id=%s
    """,(user_id,))

    total=cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return jsonify({
        "count": total if total else 0
    })
@app.route("/place_order", methods=["POST"])
def place_order():
    print("PLACE ORDER CALLED")

    token = request.cookies.get("token")

    if not token:
        return jsonify({"success": False})

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Get cart items
    cursor.execute("""
        SELECT
            c.product_id,
            c.quantity,
            p.discount_price,
            p.shop_id
        FROM cart c
        JOIN products p
        ON c.product_id = p.id
        WHERE c.user_id=%s
    """, (user_id,))

    cart_items = cursor.fetchall()

    if len(cart_items) == 0:

        cursor.close()
        conn.close()

        return jsonify({
            "success": False,
            "message": "Cart is empty"
        })

    # Calculate total
    total = 0

    for item in cart_items:
        total += float(item["discount_price"]) * item["quantity"]

    shop_id = cart_items[0]["shop_id"]

    # Create order
    cursor.execute("""
        INSERT INTO orders
        (user_id, shop_id, total, status)
        VALUES(%s,%s,%s,'Pending')
    """, (user_id, shop_id, total))

    order_id = cursor.lastrowid

    # Save each ordered product
    for item in cart_items:

        cursor.execute("""
            INSERT INTO order_items
            (order_id, product_id, quantity, price)
            VALUES(%s,%s,%s,%s)
        """, (
            order_id,
            item["product_id"],
            item["quantity"],
            item["discount_price"]
        ))

        # Reduce stock
        cursor.execute("""
            UPDATE products
            SET quantity = quantity - %s
            WHERE id=%s
        """, (
            item["quantity"],
            item["product_id"]
        ))

    # Empty cart
    cursor.execute("""
        DELETE FROM cart
        WHERE user_id=%s
    """, (user_id,))
    print("Commit Done")
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Order placed successfully!"
    })

@app.route("/cart")
def get_cart():

    token = request.cookies.get("token")

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.id,
            p.name,
            p.image,
            p.discount_price,
            c.quantity
        FROM cart c
        JOIN products p
            ON c.product_id = p.id
        WHERE c.user_id = %s
    """, (user_id,))

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(items)
@app.route("/create_order", methods=["POST"])
def create_order():

    token = request.cookies.get("token")

    if not token:
        return jsonify({"success": False})

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            p.discount_price,
            c.quantity
        FROM cart c
        JOIN products p
            ON c.product_id = p.id
        WHERE c.user_id=%s
    """,(user_id,))

    items = cursor.fetchall()

    total = 0

    for item in items:
        total += float(item["discount_price"]) * item["quantity"]
    print("Cart items:", items)
    print("Total =", total)
    amount = int(total * 100)    # Razorpay uses paise
    try:
        razorpay_order = client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        print("RAZORPAY ERROR:", e)
        return jsonify({
        "success": False,
        "error": str(e)
        })

    cursor.close()
    conn.close()

    return jsonify({
        "success": True,
        "order_id": razorpay_order["id"],
        "amount": amount,
        "key": RAZORPAY_KEY_ID
    })

@app.route("/increase_cart", methods=["POST"])
def increase_cart():
    print("Increase route called")
    token = request.cookies.get("token")

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    product_id = request.get_json()["product_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE cart
        SET quantity = quantity + 1
        WHERE user_id=%s
        AND product_id=%s
    """,(user_id,product_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify(success=True)

@app.route("/decrease_cart", methods=["POST"])
def decrease_cart():

    token = request.cookies.get("token")

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    product_id = request.get_json()["product_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT quantity
        FROM cart
        WHERE user_id=%s
        AND product_id=%s
    """,(user_id,product_id))

    item = cursor.fetchone()

    if item["quantity"] > 1:

        cursor.execute("""
            UPDATE cart
            SET quantity=quantity-1
            WHERE user_id=%s
            AND product_id=%s
        """,(user_id,product_id))

    else:

        cursor.execute("""
            DELETE FROM cart
            WHERE user_id=%s
            AND product_id=%s
        """,(user_id,product_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify(success=True)

@app.route("/delete_cart", methods=["POST"])
def delete_cart():

    token = request.cookies.get("token")

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    user_id = data["user_id"]

    product_id = request.get_json()["product_id"]

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM cart
        WHERE user_id=%s
        AND product_id=%s
    """,(user_id,product_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify(success=True)
@app.route("/logout")
def logout():

    response = make_response(redirect(url_for("home")))

    # Remove JWT cookie
    response.set_cookie(
        "token",
        "",
        expires=0
    )

    return response

@app.route("/owner")
def owner():

    token = request.cookies.get("token")

    if not token:
        return redirect(url_for("home"))

    try:
        data = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = data["user_id"]
        user_name = data["name"]

    except:
        return redirect(url_for("home"))

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Find the shop owned by this user
    cursor.execute("""
        SELECT id
        FROM shops
        WHERE owner_id=%s
    """, (user_id,))

    shop = cursor.fetchone()

    if not shop:

        cursor.close()
        conn.close()

        return "No shop found for this owner."

    shop_id = shop["id"]

    # Fetch products belonging to that shop
    cursor.execute("""
        SELECT *
        FROM products
        WHERE shop_id=%s
        ORDER BY expiry_date
    """, (shop_id,))

    products = cursor.fetchall()

    total_products = len(products)

    # Revenue
    cursor.execute("""
        SELECT COALESCE(SUM(total),0) AS revenue
        FROM orders
        WHERE shop_id=%s
    """, (shop_id,))

    revenue = cursor.fetchone()["revenue"]

    # Orders Today
    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM orders
        WHERE shop_id=%s
        AND DATE(order_date)=CURDATE()
    """, (shop_id,))

    today_orders = cursor.fetchone()["total"]
    food_saved = total_products * 2

    cursor.close()
    conn.close()

    return render_template(
        "owner.html",
        user_name=user_name,
        products=products,
        total_products=total_products,
        today_orders=today_orders,
        revenue=revenue,
        food_saved=food_saved
    )
@app.route("/add_product", methods=["POST"])
def add_product():

    token = request.cookies.get("token")

    if not token:
        return redirect(url_for("home"))

    try:
        data = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
    except:
        return redirect(url_for("home"))

    owner_id = data["user_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Find owner's shop
    cursor.execute("""
        SELECT id
        FROM shops
        WHERE owner_id=%s
    """, (owner_id,))

    shop = cursor.fetchone()

    if not shop:
        cursor.close()
        conn.close()
        return "Shop not found"

    shop_id = shop["id"]

    # Read form data
    name = request.form["name"]
    category = request.form["category"]
    quantity = request.form["quantity"]
    expiry_date = request.form["expiry_date"]
    original_price = request.form["original_price"]
    discount_price = request.form["discount_price"]

    # Upload image
    image = request.files["image"]

    filename = secure_filename(image.filename)

    image.save(
        os.path.join(
            app.config["UPLOAD_FOLDER"],
            filename
        )
    )

    # Save product
    cursor.execute("""
        INSERT INTO products
        (
            shop_id,
            name,
            category,
            quantity,
            expiry_date,
            original_price,
            discount_price,
            image
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        shop_id,
        name,
        category,
        quantity,
        expiry_date,
        original_price,
        discount_price,
        filename
    ))

    conn.commit()

    cursor.close()
    conn.close()
    return redirect(url_for("owner"))
@app.route("/delete_product", methods=["POST"])
def delete_product():

    token = request.cookies.get("token")

    if not token:
        return jsonify(success=False)

    data = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM]
    )

    owner_id = data["user_id"]

    product_id = request.get_json()["product_id"]

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Find owner's shop
    cursor.execute("""
        SELECT id
        FROM shops
        WHERE owner_id=%s
    """,(owner_id,))

    shop = cursor.fetchone()

    if not shop:

        cursor.close()
        conn.close()

        return jsonify({
            "success":False,
            "message":"Shop not found"
        })

    shop_id = shop["id"]

    # Delete only if it belongs to this shop
    cursor.execute("""
        DELETE FROM products
        WHERE id=%s
        AND shop_id=%s
    """,(product_id,shop_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "success":True,
        "message":"Product deleted successfully!"
    })

if __name__== "__main__":
    app.run(debug=True)