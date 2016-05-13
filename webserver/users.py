from local_config import SHA_SALT
import hashlib
from sqlalchemy.sql import text
 
FIELDS = ('uid', 'first_name', 'last_name', 'email', 'password')
 
def hash_password(password):
    	return hashlib.sha256(password + SHA_SALT).hexdigest()
 
def get_user_by_credentials(conn, email, password):
    	return get_user_by_email_hash(conn, email, hash_password(password))
 
def get_user_by_email_hash(conn, email, pwhash):
    	cursor = conn.execute(text('SELECT ' + ', '.join(FIELDS) + ' FROM users \
                               WHERE email=:email AND password=:password'),
                          email=email, password=pwhash)
    	return cursor.fetchone()
 
def get_user_by_email(conn, email):
    	cursor = conn.execute(text('SELECT ' + ', '.join(FIELDS) + ' FROM users \
                               WHERE email=:email'),
                          email=email)
    	return cursor.fetchone()
 
def get_snapshots_for_user(conn, uid):
    	return conn.execute(text('SELECT * FROM usersnapshot WHERE uid=:uid'), uid=uid).fetchall()
 
def get_user_snapshots_by_user(conn):
    	query = """
    	SELECT *
    	FROM usersnapshot u1, users u
    	WHERE u1.ts = (
        	SELECT MAX(ts)
        	FROM usersnapshot u2
        	WHERE u1.uid = u2.uid
    	) AND u.uid = u1.uid
    	"""
    	return conn.execute(query).fetchall()
 
 
def get_user_weightloss_by_user(conn):
    	query = """
    	SELECT  g1.uid,
        	u.first_name,
            	u.last_name,
            	g1.weight - u1.weight AS weight_delta_lbs,
            	g1.target - u1.ts AS time_between_snapshot_and_goal
    	FROM goal g1, usersnapshot u1, users u
    	WHERE g1.target = (
        	SELECT MAX(target)
        	FROM goal g2
        	WHERE g1.uid = g2.uid
    	) AND u1.ts = (
        	SELECT MAX(ts)
        	FROM usersnapshot u2
        	WHERE u1.uid = u2.uid
    	) AND g1.uid = u1.uid AND u1.uid = u.uid;
    	"""
    	return conn.execute(query).fetchall()
 
 
def create_user(conn, first_name, last_name, email, password):
    	hp = hash_password(password)
 	
    	if get_user_by_email(conn, email):
        	raise ValueError('Email already exists!')
 
    	cursor = conn.execute(text('INSERT INTO users (first_name,\
                                                   last_name,\
                                                   email,\
                                                   password)\
                               	VALUES (:first_name,\
                                       :last_name,\
                                       :email,\
                                       :password)'),
                          first_name=first_name,
                          last_name=last_name,
                          email=email,
                          password=hp)
    	return cursor.rowcount
 
 
def create_usersnapshot(conn, uid, height, weight, age):
    	query = text("""
    	INSERT INTO usersnapshot (uid, height, weight, age)
    	VALUES (:uid, :height, :weight, :age)
    	""")
 
    	return conn.execute(query, uid=uid, height=height, weight=weight, age=age)
