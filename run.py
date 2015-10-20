from flask import Flask, render_template, request, session
import hashlib
import MySQLdb
import json

app = Flask(__name__)
app.secret_key = "a6(*&sKJH9*dflKJH9*&)&"

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html')

#utilities
def query(stmt):
	try:
		db = MySQLdb.connect("localhost","root","bbemt","creditcalc")
		cur = db.cursor()
		cur.execute(stmt)
		results = cur.fetchall()
		db.commit();
		return results
	except:
		print "!! query failed"

def warn(msg):
	return {'level':'warn', 'msg':msg}
def error(msg):
	return {'level':'error', 'msg':msg}

# content: dictionary ex: {'classes':[{'id':1}, {'id':2}]}
# alerts:  array      ex: [{'level':1, 'msg':'a warning occured!'}, {'level':0, 'msg':'a severe error has occured!'}]
def prepare_for_departure(content={}, alerts=[], success=True):
	return_obj = {'content':content, 'alerts':alerts, 'success':success}
	return json.dumps(return_obj, ensure_ascii=False)

if __name__ == '__main__':
	app.run("0.0.0.0", debug=True)
