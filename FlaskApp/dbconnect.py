import MySQLdb

def connection():
    conn = MySQLdb.connect(host='localhost',
    user = 'root',
    passwd = '7055',
    db='pos')

    c = conn.cursor()

    return c, conn

