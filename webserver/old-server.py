#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import (Flask, request, render_template, session, url_for, send_from_directory, g, redirect, Response)
from functools import wraps
import datetime
from db import db_conn, db_query_one
from local_config import SECRET_KEY
import users
import workouts

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
app.secret_key = SECRET_KEY


#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#postgresql://USER:PASSWORD@w4111db.eastus.cloudapp.azure.com/username
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@w4111db.eastus.cloudapp.azure.com/ewu2493"
#
DATABASEURI = "postgresql://ry2242:VYNCVK@w4111db.eastus.cloudapp.azure.com/ry2242"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
	"""
	This function is run at the beginning of every web request 
  	(every time you enter an address in the web browser).
  	We use it to setup a database connection that can be used throughout the request

  	The variable g is globally accessible
  	"""
	try:
    		g.conn = engine.connect()
  	except:
    		print "uh oh, problem connecting to database"
    		import traceback; traceback.print_exc()
    		g.conn = None

@app.teardown_request
def teardown_request(exception):
  	"""
  	At the end of the web request, this makes sure to close the database connection.
  	If you don't the database could run out of memory!
  	"""
  	try:
    		g.conn.close()
  	except Exception as e:
    		pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
def require_login(func):
	@wraps(func)
    	def func_wrapper(*args, **kwargs):
        	if 'email' in session and 'pw' in session:
            		with db_conn() as conn:
                		user = users.get_user_by_email_hash(conn, session['email'], session['pw'])
                		if user:
                    			kwargs['user'] = user
                    			kwargs['conn'] = conn
                    			return func(*args, **kwargs)
        	return redirect(url_for('login'))

    	return func_wrapper

@app.route('/')
def index():
  	"""
  	request is a special object that Flask provides to access web request information:

  	request.method:   "GET" or "POST"
  	request.form:     if the browser submitted a form, this contains the data in the form
  	request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  	See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  	"""
	with db_query_one('SELECT * FROM users') as cursor:
		for row in cursor:
			print row
	return render_template('index.html', title='Home Page')

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/workouts', methods=('GET', 'POST'))
@require_login
def userworkouts(**kwargs):
	user = kwargs.pop('user')
	conn = kwargs.pop('conn')

	t = workouts.get_workout_types(conn)
	if request.method == 'POST':
		wt = request.form['type']
		st = request.form['start_time']
		dur = request.form['duration']

		now = datetime.datetime.now()
		dt = datetime.datetime.strptime(st, '%H:%M %p')
		v = now.replace(hour=dt.hour, minute=dt.minute)
		
		workouts.create_workout(conn, user.uid, wt, v, dur)
	
	offset = request.args.get('offset', 0)
	w = workouts.get_workouts_for_user(conn, user.uid, limit=101, offset=offset)

	type_lut = {wt.wtid: wt for wt in t}

	return render_template('workouts.html', title='{}\'s workouts'.format(user.first_name), page=int(offset) / 100 +1, user=user, type_lut=type_lut, workouts=w[:100], has_next_page=len(w) > 100, has_prev_page= offset > 0)

@app.route('/workouttypes')
def workouttypes():
	with db_conn() as conn:
		workout_types = workouts.get_workout_types(conn)
		return render_templates('workout_types.html', title='Workout Types', workout_types=workout_types)


@app.route('/login')
def login():
	if request.args.get('email') and request.args.get('pw'):
        	email = request.args.get('email')
        	pw = request.args.get('pw')
        	with db_conn() as conn:
            		user = users.get_user_by_credentials(conn, email, pw)
            		return_path = request.args.get('ref')
            		if user:
                		session['email'] = email
                		session['pw'] = user.password # hashed version
                		if return_path:
                    			return redirect(return_path)
                		else:
                    			return redirect(url_for('profile'))
	return render_template('login.html', title='Login')
@app.route('/signup')
def signup():
	if (request.args.get('email') and request.args.get('pw') and request.args.get('first_name') and request.args.get('last_name')):
		email = request.args.get('email')
		pw = request.args.get('pw')
		first_name = request.args.get('first_name')
		last_name = request.args.get('last_name')

		with db_conn() as conn:
			try:
				if users.create_user(conn, first_name, last_name, email. pw):
					return redirect('/profile')
				return 'Unexpected error'
			except ValueError:
				return render_template('signup.html', title = 'Signup', error = 'User already exits!')
		return redirect('/profile')
	return render_template('signup.html', title='Signup')

@app.route('/logout')
def logout():
	del session['email']
	del session['pw']
	return redirect(url_for('login'))

@app.route('/profile')
@require_login
def profile(**kwargs):
	user = kwargs.pop('user')
	return render_template('profile.html', user=user, title='{}\'s \ profile'.format(user.first_name))

@app.route('/snapshots', methods=('GET', 'POST'))
@require_login
def snapshots(**kwargs):
	user = kwargs.pop('user')
	conn = kwargs.pop('conn')

	if request.method == 'POST':
		height = request.form['height']
		weight = request.form['weight']
		age = request.form['age']
		users.create_usersnapshot(conn, user.uid, height, weight, age)

	ss = users.get_snapshots_for_user(conn, user.uid)

	return render_templates('snapshots.html', user=user, title='Snapshots for \ ()'.format(user.first_name), snapshots=ss)

@app.route('/summary')
def summary():
	with db_conn() as conn:
		us_by_user = users.get_user_snapshots_by_user(conn)
		wl_by_user = users.get_user_weightloss_by_user(conn)
		uids = set()
		for u in us_by_user:
			uids.add(u.uid)
		for u in wl_by_user:
			uids.add(u.uid)

		return render_templates('summary.html', uids=uids, title='Summary', us_by_user=us_by_user, wl_by_user=wl_by_user)
 
@app.route('/s/<path:path>')
def send_bower(path):
	return send_from_directory('bower_components', path)

if __name__ == "__main__":
	import click

	@click.command()
	@click.option('--debug', is_flag=True)
	@click.option('--threaded', is_flag=True)
	@click.argument('HOST', default='0.0.0.0')
	@click.argument('PORT', default=8111, type=int)
	def run(debug, threaded, host, port):
    		"""
		This function handles command line parameters.
	    	Run the server using
	
       		python server.py	
    		Show the help text using
       		python server.py --help
    		"""
		HOST, PORT = host, port
    		print "running on %s:%d" % (HOST, PORT)
    		app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  	run()
