from flask import Flask, render_template, flash, request, url_for, redirect, session, g
from functools import wraps
from flask_wtf import Form
from wtforms import TextField, BooleanField, validators, PasswordField, Form
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as thwart
from datetime import datetime 
import gc

import MySQLdb

conn = MySQLdb.connect(host='localhost',
user = 'root',
passwd = '7055',
db='pos')

c = conn.cursor()

    
# TOPIC_DICT = Content()

app = Flask(__name__)

# kept gett this error RuntimeError: The session is unavailable because no secret key was set.  Set the secret_key on the application to something unique and secret.
# So I googled this answer for making app.secret_key

app.secret_key = 'my unobvious secret key'
@app.route('/home')
def homepage():
    return render_template("home.html")

@app.route('/')
def dashboard():
    query = "SELECT * from journal"
    c.execute(query)
    data = c.fetchall()
    conn.close()
    print(type(data))
    return render_template('main.html',data=data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')


@app.errorhandler(405)
def method_not_found(e):
    return render_template('405.html')

class RegistrationForm(Form):
    username = TextField('Username', [validators.Length(min=4, max=20)])
    email = TextField('Email Address', [validators.Length(min=6, max=50)])
    password = PasswordField('New Password', [validators.Required(),
                                              validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the Terms of Service and Privacy Notice (updated Jan 22, 2015)',
                              [validators.Required()])

@app.route('/product', methods=['GET', 'POST'])
def inventory():
    print("hear")
    if request.method == 'POST':
        name = request.form ['name']
        productid = request.form['productid']
        description = request.form["desc"]
        cog = request.form['cost']
        price= request.form['price']
        account = request.form['account']
        category = request.form['category'] 
        size = request.form['size']
        c.execute("INSERT INTO products (name, product_num,size,category,description,cog,price,account) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", 
        (name,productid,size,category,description,cog,price,account))
        conn.commit()
        conn.close()
        return render_template("sale.html")


@app.route('/sale/', methods=['GET', 'POST'])
def sales_page():
    if request.method == 'POST':
        data = request.json
        c.execute("INSERT INTO products (name, product_num,size,category,description,cog,price,account) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", 
        (ord["id"], ord["status_order_id"], ord["customer_id"]))
#     data = [
#     {"name":"Tom", "gender":"male"},
#     {"name":"Jack", "gender":"male"},
#     {"name":"Lee", "gender":"male"}]
# cursor.executemany("""
#     INSERT INTO foo (name, gender)
#     VALUES (%(name)s, %(gender)s)""", data)
# db.commit() 
#     else:
#         pass
    return render_template('sale.html')
@app.route('/test/')
def test():
    return render_template('test.html')
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('you need to login first')
            return redirect(url_for('login_page'))
    return wrap
    
@app.route('/login/', methods=['GET', 'POST'])
def login_page():
    error = ''
    try:
        if request.method == 'POST':
            data = c.execute('SELECT * FROM users WHERE username = (%s)',
                             (thwart(request.form['username']),))
            data = c.fetchone()[1]
            if sha256_crypt.verify(request.form['password'], data) :
                session['logged_in'] = True
                session['username'] = request.form['username']
                flash('You are now logged in')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid credentials check Your Password, try again.'
        gc.collect()
        return render_template('login.html', error=error)
    except Exception as e:
        error = 'Invalid credentials, Check your username try again.'
        return render_template('login.html', error=error)
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out!')
    gc.collect()
    return redirect(url_for('homepage'))
@app.route('/register/', methods=["GET", "POST"])
def register_page():
    try:
        form = RegistrationForm(request.form)

        if request.method == "POST" and form.validate():
            username = form.username.data
            email = form.email.data
            password = sha256_crypt.encrypt((str(form.password.data)))
            # c, conn = connection()
            # x = c.execute("SELECT * FROM users WHERE username = %s",(thwart(username)),)
            x = c.execute("""SELECT * FROM users WHERE username  =  %s""", (thwart(username),))
            if int(x) > 0:
                flash("That username is already taken, please choose another")
                return render_template('register.html', form=form)
            else:
                c.execute("""INSERT INTO users (username, userpass, email) VALUES (%s, %s, %s)""",
                          (thwart(username), thwart(password), thwart(email)))
                conn.commit()
                flash("Thanks for registering!")
                # c.close()
                # conn.close()
                gc.collect()
                session['logged_in'] = True
                session['username'] = username
                return redirect(url_for('dashboard'))
        return render_template("register.html", form=form)

    except Exception as e:
        return (str(e))
def Date():
    date =  (dt.datetime.now()).strftime("%Y%m%d")
    return date 

class Journal():
    def record_transaction(self, accounts,amount):
        self.accounts = accounts
        self.amount = amount
        dr = self.accounts[0]
        cr = self.accounts[1]
        dat = Date()
        c.execute("""INSERT INTO journal(dat,debit,credit,amount)
VALUES (%s,%s, %s, %s)""",(dat,dr,cr,self.amount ))

if __name__ == '__main__':
    app.run(debug=True)
