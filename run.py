from flask import Flask, render_template, request, session, redirect
import hashlib
import MySQLdb
import json

app = Flask(__name__)
app.secret_key = "a6(*&sKJH9*dflKJH9*&)&"

@app.route('/')
@app.route('/overview')
def overview():
	if (not loggedIn()):
		return redirect('/login', code=302)

	calls = {'calls':[]}
	results = query("SELECT `CALL`.FNAME, `CALL`.LNAME, `CALL`.POSITION, STATUS.STATUS, `CALL`.CALL_TIME FROM `CALL`, STATUS WHERE `CALL`.STATUS = STATUS.ID")
	for call in results:
		calltime = call[4]
		calls['calls'].append({'fname':call[0], 'lname':call[1], 'position':call[2], 'status':call[3], 'calltime':calltime })

	return render_template('overview.html', data=calls)

@app.route('/login', methods=["GET","POST"])
def login():
	session.clear()
	try:
		phone = request.form['phone']
		result = query ("SELECT * FROM USER WHERE phone=%s" % phone )
		if len(result)>0:
			session['phone'] = result[0][1]
			session['uid'] = result[0][0]
			session['loggedin'] = True
			return redirect('/overview', code=302)
	except:
		pass
	return render_template('login.html')

@app.route('/schedule')
def schedule():
	return render_template('schedule.html')

@app.route('/logout')
def logout():
	session.clear()
	return redirect('/login', code=302)

@app.route('/addcall', methods=['POST'])
def addcall():
	if(not loggedIn()):
		return prepare_for_departure(success=False)

	data = request.form
	sql = "INSERT INTO `CALL` (PHONE, FNAME, LNAME, POSITION, DESCRIPTION, STATUS, REP_ID) VALUES('%s', '%s', '%s', '%s', '%s', 2, '%s')" % (data['phone'], data['fname'], data['lname'], data['position'], data['description'], session['uid'])
	query(sql)
	return prepare_for_departure(success=True)

#utilities
def loggedIn():
	if ('loggedin' in session):
		if(session['loggedin'] == True):
			return True
	return False

def query(stmt):
	print "QUERY-> "+stmt
	try:
		db = MySQLdb.connect("localhost","root","sked","telesked")
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
