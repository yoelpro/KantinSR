import psycopg2
import subprocess
from configparser import ConfigParser
import os
import psycopg2
from operator import itemgetter

def checkStatus(uId,cursor): #return text based on condition of customer (for customer)
    uId = "'"+uId+"'" 
    cursor.execute("SELECT id, nasi, topping, saus from QUEUE where finish=false and uid ="+uId+";")
    orders = cursor.fetchall();
    cursor.execute("select id from queue where finish=false limit 1;")
    if cursor.fetchone():
        noOrderan = cursor.fetchone()[0]
    cursor.execute("select count(case finish when false then 1 else null end) from queue")
    if cursor.fetchone():
        totalAntrian = int(cursor.fetchone()[0])
    if not orders: #orders is empty and the customer hasnt put on order yet
        text = "No orderan yang sedang dikerjakan: " + str(noOrderan) + "\n"
        text = text + "Total antrian yang ada: " + str(totalAntrian) + "\n"
        text = text + "Perkiraan waktu antrian = " + str(totalAntrian*1.5) + " Menit" #asumsi 1 pesanan memakai 1.5 menit
    else: #customer has some orders
        orders.sort(key=itemgetter(0), reverse=True)
        first = True
        print(orders)
        for order in orders:#text construction
            if first==False:
                text = text + "\n" + "\n"
                text = text + "Urutan = " + order[0] + '\n'
            else:
                text = "Urutan = " + order[0] + '\n'
            text = text + "Nasi = " + order[1] + "; Topping = " + order[2] + '\n'
            text = text + "Saus = " + order[3] + '\n'
            status = ''
            if order[0]==noOrderan:
                status = "Sedang dikerjakan"
            else:
                status = "Sedang mengantri"
            text = text + "Status = " + status + '\n'
            text = text + "Perkiraan waktu = " + str((int(order[0])-int(noOrderan))*1.5) + " Menit"
            first = False
        text = text + '\n' + '\n' + "Anda dapat melihat status pesanan anda diatas \n"
        text = text + "Total antrian didepan anda = " + str(totalAntrian-1) + '\n'
    return text #return all string

def listOrders(cursor): #return list of orders (for seller)
    cursor.execute("SELECT id, uid, nasi, topping, saus from QUEUE where finish=false")
    rows = cursor.fetchall()
    rows.sort(key=itemgetter(0),reverse=True)
    texts = list(range(len(rows)))
    for i in range(0,len(rows)):
        texts[i] = "Urutan = " + rows[i][0] + '\n'
        texts[i] = texts[i] + "Nasi = " + rows[i][2] + "; Topping = " + rows[i][3] + '\n'
        texts[i] = texts[i] + "Saus = " + rows[i][4]
    texts.sort(key=itemgetter(0),reverse=True)
    return texts

def checkSaldo(uid,cursor): #return integer saldo of certain uid
	uidText = "'" + uid + "';"
	cursor.execute("SELECT saldo from CUSTOMERS WHERE uid = "+uidText)
	return cursor.fetchone()[0]

def countRow(tableName,cursor): # return integer of table row
	command = 'SELECT COUNT(*) FROM ' + tableName + ';'
	cursor.execute(command)
	return cursor.fetchone()[0]

def tableExist(tableName,cursor): # return boolean whether table exist or not
	cursor.execute("select exists(select * from information_schema.tables where table_name=%s)", (tableName,))
	return cursor.fetchone()[0]

def tambahPesanan(idNum, uId, nasi, topping, saus, cursor): #add orders into queue
	uId = "'"+uId+"'"
	nasi = "'"+nasi+"'"
	topping = "'"+topping+"'"
	saus = "'"+saus+"'"
	query = "INSERT INTO QUEUE (id,uid,nasi,topping,saus,finish) \n" 
	query = query + "VALUES ("+str(idNum)+","+uId+","+nasi+","+topping+","+saus+",false);"
	cursor.execute(query)

def selesaiPesanan(id,cursor):
    id = str(id)
    query = "UPDATE QUEUE SET FINISH = true WHERE id = '" + id + "';"
    cursor.execute(query)

def updateSaldo(saldo, uid, cursor): #function to update saldo
	cursor.execute("SELECT saldo from CUSTOMERS WHERE uid ='"+uid+"';")
	saldobaru = saldo + cursor.fetchone()[0]
	query = "UPDATE CUSTOMERS SET SALDO = "+ str(saldobaru) + " WHERE uid = '" + uid + "';"
	cursor.execute(query)

def insertDataCustomer(idNum,uId,saldo,cursor): #function to insert new customer data
	query = "INSERT INTO CUSTOMERS (id,uid,saldo) \n" + "VALUES ("+str(idNum)+",'"+uId+"',"+str(saldo)+");"
	cursor.execute(query)

def connect(): #function to provide connection
    """ Connect to the PostgreSQL database server """
    conn = None
    # connect to the PostgreSQL server
    print('Connecting to the PostgreSQL database...')
    DATABASE_URL = os.environ['DATABASE_URL']
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn
        
    