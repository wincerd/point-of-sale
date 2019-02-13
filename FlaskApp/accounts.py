from datetime import datetime 
class Journal():
    def record_transaction(self, accounts,amount):
        self.accounts = accounts
        self.amount = amount
        dr = self.accounts[0]
        cr = self.accounts[1]
        dat = (dt.datetime.now()).strftime("%Y%m%d")
        c.execute("""INSERT INTO journal(dat,debit,credit,amount)
VALUES (%s,%s, %s, %s)""",(dat,dr,cr,self.amount ))