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
user = '',
passwd = '',
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
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    new_journal = Journal()
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form ['name']
        productid = request.form['productid']
        description = request.form["desc"]
        cog = request.form['cost']
        price= request.form['price']
        account = request.form['account']
        category = request.form['category'] 
        size = request.form['size']
        accounts = ("cash","inventory")
        new_journal.record_transaction(accounts,price)
        c.execute("INSERT INTO products (name, product_num,size,category,description,cog,price,account) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", 
        (name,productid,size,category,description,cog,price,account))
        conn.commit()
        conn.close()
        return render_template("sale.html")
@app.route('/products/')
def products():
    c = conn.cursor()
    query = "SELECT * from products"
    c.execute(query)
    data = c.fetchall()
    conn.close()
    return render_template("products.html",data=data)
@app.route('/contacts/<cont>/', methods=["POST", "GET"])
def contacts(cont):
    c = conn.cursor()
    if cont == 'suppliers':
        c.execute("select * from contact where type = %s""", ('supplier',))
        data = c.fetchall()
        return render_template("contacts.html",data = data)
    elif cont == 'customers':
        c.execute("""select * from contact where type =%s""", ('customers',))
        data = c.fetchall() 
        return render_template("contacts.html",data = data)
    if request.method == 'POST':
        name = request.form ['name']
        typ = cont 
        number = request.form["number"]
        c_id =request.form["id"]
        c.execute("INSERT INTO contact (name,type,number,c_id) VALUES (%s,%s,%s,%s)", 
        (name,typ,number,c_id))
        conn.commit()
        conn.close()
        return render_template("contacts.html",data = data)
@app.route('/sale/', methods=['GET', 'POST'])
def sales_page():
    #cash/sales\
    new_journal = Journal()
    if request.method == 'POST': 
        data = request.get_json()
        #check for empty  rows
        for row in data:
            save = [] 
            for cell  in row:
                if row[cell] == "":
                    pass
                else:
                    save.append(row[cell])     
                    #save the table data if all rows exists 
                    if len(save) > 4:
                        amount= save[4]
                        account = ("cash","sale")
                        new_journal.record_transaction(account,amount)
                        c.execute("INSERT INTO sale(ID,item,description,size,amount) VALUES (%s,%s,%s,%s,%s)", 
        (save[0],save[1],save[2],save[3],save[4]))
                        conn.commit()
                        conn.close()
    return render_template('sale.html')        
@app.route('/addacc/', methods=["GET", "POST"])
def add_account():
    new = Journal()
    if request.method == 'POST':
        name = request.form ['name']
        typ = request.form ['type']
        ID  = request.form ['ID']
        new_acc = new.create_account(ID,name,typ)

def Date():
    date =  (datetime.now()).strftime("%Y%m%d")
    return date 

class Journal():
    ACCOUNT_TYPES = ('asset', 'liability', 'equity', 'revenue', 'expense')
    def init(self):
        '''Initialize the database.'''
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS `Account` (
        `ID` text,
        `name` text,
        `typ` int(11) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        CREATE TABLE IF NOT EXISTS `contact` (
          `c_id` int(11) DEFAULT NULL,
          `name` varchar(100) DEFAULT NULL,
          `mobile` int(11) DEFAULT NULL,
          `type` varchar(20) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        CREATE TABLE IF NOT EXISTS `journal` (
          `ID` int(50) NOT NULL,
          `dat` varchar(50) DEFAULT NULL,
          `debit` varchar(11) NOT NULL,
          `credit` varchar(11) NOT NULL,
          `amount` int(11) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;

        CREATE TABLE IF NOT EXISTS `Posting` (
          `ID` text,
          `account_id` text,
          `journal_id` text,
          `amount` int(11) DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        CREATE TABLE IF NOT EXISTS `products` (
          `name` varchar(50) NOT NULL,
          `product_num` int(50) NOT NULL,
          `category` varchar(50) NOT NULL,
          `description` varchar(50) NOT NULL,
          `cog` int(6) NOT NULL,
          `price` int(6) NOT NULL,
          `account` varchar(50) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        CREATE TABLE IF NOT EXISTS `sale` (
          `ID` int(50) NOT NULL,
          `item` varchar(50) NOT NULL,
          `description` varchar(50) NOT NULL,
          `size` int(6) NOT NULL,
          `amount` int(6) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        CREATE TABLE IF NOT EXISTS `users` (
          `username` varchar(100) NOT NULL,
          `userpass` varchar(100) NOT NULL,
          `email` varchar(100) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=latin1;
        ''')
        self.db.commit()
    def drop(self):
        '''Reset the ledger.'''
        self.db.executescript('''
        DROP TABLE IF EXISTS transaction_items;
        DROP TABLE IF EXISTS transactions;
        DROP TABLE IF EXISTS accounts;
        ''')
        self.db.commit()
    def record_transaction(self, accounts,amount):
        self.accounts = accounts
        self.amount = amount
        dr = self.accounts[0]
        cr = self.accounts[1]
        dat = Date()
        c.execute("select * from journal where ID =( SELECT MAX(ID) FROM journal)")
        ID= c.fetchone()
        if ID == None:
            ID = 1
        c.execute("select * from Posting where ID =( SELECT MAX(ID) FROM Posting)")
        jID= c.fetchone()
        if jID == None:
            jID = 1
        else:
            jID = int(ID)+ 1
        c.execute("""INSERT INTO journal(dat,debit,credit,amount)
            VALUES (%s,%s, %s, %s)""",(dat,dr,cr,self.amount ))
        for account in accounts:
            c.execute('''INSERT INTO Posting (ID,journal_id,account_code,amount)
                VALUES (%s,%s,%s,%s)''',(jID,ID,account,amount))
    def create_account(self, id , name, type):
        '''Create an account with a given code and name.'''
        if type not in self.ACCOUNT_TYPES:
            raise ValueError('unknown account type {}'.format(type))
        if self.get_account(code):
            raise LedgerError('The account "{}" already exists'.format(code))
        self.db.execute(
            'INSERT INTO accounts(code, name, type) VALUES (?, ?, ?)',
            (id, name, type)
        ).close()
        self.db.commit()
    def get_balance_sheet(self, date):
        '''Return a balance sheet.'''
        rows = self.db.execute('''
        SELECT
            a.code, a.name, a.type, SUM(
                CASE
                    WHEN date(t.date) <= date(?) THEN ti.amount
                    ELSE 0
                END
            )
            FROM accounts a
            LEFT JOIN transaction_items ti ON a.code = ti.account_code
            LEFT JOIN transactions t ON ti.transaction_id = t.id
            GROUP BY a.code
        ''', (date,)).fetchall()

        retained_earnings = 0
        accounts_by_type = {'asset': {}, 'liability': {}, 'equity': {}}
        for code, name, type, balance in rows:
            if type in ('revenue', 'expense'):
                retained_earnings -= balance
            else:
                accounts_by_type[type][Account(code, name, type)] = balance

        return BalanceSheet(
            date=date,
            retained_earnings=retained_earnings,
            **accounts_by_type
        )

    def get_income_statement(self, start_date, end_date):
        '''Return an income statement.'''
        rows = self.db.execute('''
        SELECT
            a.code, a.name, a.type, SUM(
                CASE
                    WHEN date(?) <= date(t.date) AND date(t.date) <= date(?)
                        THEN ti.amount
                    ELSE 0
                END
            )
            FROM accounts a
            LEFT JOIN transaction_items ti ON a.code = ti.account_code
            LEFT JOIN transactions t ON ti.transaction_id = t.id
            WHERE a.type IN ("revenue", "expense")
            GROUP BY a.code
        ''', (start_date, end_date)).fetchall()

        accounts_by_type = {'revenue': {}, 'expense': {}}
        for code, name, type, balance in rows:
            accounts_by_type[type][Account(code, name, type)] = balance

        return IncomeStatement(
            start_date=start_date,
            end_date=end_date,
            **accounts_by_type
        )

if __name__ == '__main__':
    app.run(debug=True)
