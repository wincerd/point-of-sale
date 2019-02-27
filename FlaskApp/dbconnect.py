import MySQLdb

def connection():
    conn = MySQLdb.connect(host='localhost',
    user = 'user',
    passwd = 'password',
    db='pos')

    c = conn.cursor()

    return c, conn

