from flask import (Flask, render_template, session, url_for, request, redirect,
                   send_from_directory)
from functools import wraps
import datetime
from db import db_conn, db_query_one
from local_config import SECRET_KEY
import users
import workouts

app = Flask(__name__)
app.secret_key = SECRET_KEY

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
    with db_query_one('SELECT * FROM users') as cursor:
        for row in cursor:
            print row
    return render_template('index.html', title='Home Page')

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
    w = workouts.get_workouts_for_user(conn, user.uid, limit=101,
                                       offset=offset)

    type_lut = {wt.wtid: wt for wt in t}

    return render_template('workouts.html',
                           title='{}\'s workouts'.format(user.first_name),
                           page=int(offset) / 100 + 1,
                           user=user,
                           type_lut=type_lut,
                           workouts=w[:100],
                           has_next_page=len(w) > 100,
                           has_prev_page=offset > 0)

@app.route('/workouttypes')
def workouttypes():
    with db_conn() as conn:
        workout_types = workouts.get_workout_types(conn)
        return render_template('workout_types.html', title='Workout Types', workout_types=workout_types)

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
    if (request.args.get('email') and request.args.get('pw') and
        request.args.get('first_name') and request.args.get('last_name')):

        email = request.args.get('email')
        pw = request.args.get('pw')
        first_name = request.args.get('first_name')
        last_name = request.args.get('last_name')

        with db_conn() as conn:
            try:
                if users.create_user(conn, first_name, last_name, email, pw):
                    return redirect('/profile')
                return 'Unexpected error'
            except ValueError:
                return render_template('signup.html', title='Signup', error='User already exists!')
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
    # conn = kwargs.pop('conn')
    return render_template('profile.html', user=user, title='{}\'s \
                           profile'.format(user.first_name))


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

    return render_template('snapshots.html', user=user, title='Snapshots for \
                           {}'.format(user.first_name), snapshots=ss)


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

        return render_template('summary.html', uids=uids, title='Summary',
                               us_by_user=us_by_user, wl_by_user=wl_by_user)

@app.route('/goals')
def goals():
    

@app.route('/s/<path:path>')
def send_bower(path):
    return send_from_directory('bower_components', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
