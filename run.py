from flask import Flask, render_template, request, session, redirect
import hashlib
import MySQLdb
import json
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

app = Flask(__name__)
app.secret_key = "a6(*&sKJH9*dflKJH9*&)&"

@app.route('/')
@app.route('/overview')
def overview():
	if (not loggedIn()):
		return redirect('/login', code=302)

	calls = {'calls':[]}
	results = query("SELECT `CALL`.FNAME, `CALL`.LNAME, `CALL`.POSITION, STATUS.STATUS, `CALL`.CALL_TIME, `CALL`.ID FROM `CALL`, STATUS WHERE `CALL`.STATUS = STATUS.ID AND REP_ID='%s'" % session['uid'])
	for call in results:
		calltime = call[4]
		calls['calls'].append({'fname':call[0], 'lname':call[1], 'position':call[2], 'status':call[3], 'calltime':calltime, 'id':call[5] })

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
	if (not loggedIn()):
		return redirect('/login', code=302)

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
	for elem in data:
		if elem == "description":
			continue
		if data[elem]=="":
			return prepare_for_departure(success=False, alerts=[error("Must complete all required fields")])
			
	date = format_date_for_sql(data['date'], data['time'])
	sql = "INSERT INTO `CALL` (PHONE, FNAME, LNAME, POSITION, DESCRIPTION, STATUS, REP_ID, CALL_TIME) VALUES('%s', '%s', '%s', '%s', '%s', 2, '%s', '%s')" % (data['phone'], data['fname'], data['lname'], data['position'], data['description'], session['uid'], date)
	query(sql)

	sms = "Hey %s, you have been scheduled for an call with [NAME] of [ORG] at %s on %s. Reply 'y' if this works for you or 'n' if not." % (data['fname'], data['time'], data['date'])
	r = requests.post("https://api.plivo.com/v1/Account/MAYZU1ZDC4ODUXODI2Y2/Message/", data = ('{"src":"16622221708","dst":"%s","text":"%s"}' % (data['phone'], sms)), headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}, auth=HTTPBasicAuth('MAYZU1ZDC4ODUXODI2Y2', 'MGFkMTU0MmZmNDcyYjJhZGZkZWRjM2I4NDZkYzg2'))
	return prepare_for_departure(success=True)

@app.route('/getcall/<int:call_id>')
def getcall(call_id):
	result = query("SELECT * FROM `CALL` WHERE ID=%s" % call_id)[0]
	status_id = result[6]
	status = "Declined"
	if status_id==1:
		status = "Accepted"
	if status_id==2:
		status = "Pending"

	call = {'id':result[0], 'phone':result[1], 'fname':result[2], 'lname':result[3], 'position':result[4], 'description':result[5], 'status':status, 'date':str(result[8])}
	return prepare_for_departure(content=call, success=True)

@app.route('/delcall/<int:call_id>')
def delcall(call_id):
	phone = query("SELECT * FROM `CALL` WHERE ID=%s" % call_id)[0][1]
	result = query("DELETE FROM `CALL` WHERE ID=%s" % call_id)
	sms = "Your call has been canceled"
	r = requests.post("https://api.plivo.com/v1/Account/MAYZU1ZDC4ODUXODI2Y2/Message/", data = ('{"src":"16622221708","dst":"%s","text":"%s"}' % (phone,sms)), headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}, auth=HTTPBasicAuth('MAYZU1ZDC4ODUXODI2Y2', 'MGFkMTU0MmZmNDcyYjJhZGZkZWRjM2I4NDZkYzg2'))

	return prepare_for_departure(success=True)

@app.route('/updatecall/<int:call_id>', methods=["POST"])
def updatecall(call_id):
	data = request.form

	# get existing values
	call = query("SELECT * FROM `CALL` WHERE ID=%s" % call_id)[0]
	newcall = { "id":call[0], "phone":call[1], "fname":call[2], "lname":call[3], "position":call[4], "description":call[5], "date":call[8] }

	# overwrite where applicable
	if('phone' in data) and (data['phone'] != newcall['phone']):
		newcall['phone'] = data['phone']
	if('fname' in data) and (data['fname'] != newcall['fname']):
		newcall['fname'] = data['fname']
	if('lname' in data) and (data['lname'] != newcall['lname']):
		newcall['lname'] = data['lname']
	if('position' in data) and (data['position'] != newcall['position']):
		newcall['position'] = data['position']
	if('description' in data) and (data['description'] != newcall['description']):
		newcall['description'] = data['description']
	if('time' in data) and ('date' in data):
		date = format_date_for_sql(data['date'], data['time'])
		newcall['date'] = date
		sms = "Your call has been moved to %s on %s. Reply 'y' if this works for you or 'n' if not." % (data['time'], data['date'])
		r = requests.post("https://api.plivo.com/v1/Account/MAYZU1ZDC4ODUXODI2Y2/Message/", data = ('{"src":"16622221708","dst":"%s","text":"%s"}' % (newcall['phone'],sms)), headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}, auth=HTTPBasicAuth('MAYZU1ZDC4ODUXODI2Y2', 'MGFkMTU0MmZmNDcyYjJhZGZkZWRjM2I4NDZkYzg2'))

	# update record
	query('UPDATE `CALL` SET PHONE="%s", FNAME="%s", LNAME="%s", POSITION="%s", DESCRIPTION="%s", CALL_TIME="%s" WHERE ID="%s"' % (newcall['phone'],newcall['fname'],newcall['lname'],newcall['position'],newcall['description'], newcall['date'], call_id ))

	return prepare_for_departure(success=True)

def format_date_for_sql(date, time):
	d = datetime.strptime((date+" "+time), '%m/%d/%Y %H:%M%p')
	dt = d.strftime('%Y-%m-%d %H:%M:%S')
	print dt
	return dt

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
