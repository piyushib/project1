from sqlalchemy.sql import text
 
WORKOUT_TYPE_FIELDS = ('wtid', 'name', 'description', 'calories')
WORKOUT_FIELDS = ('wid', 'uid', 'type', 'start', 'duration')
 
def get_workout_types(conn):
    	return conn.execute(text('SELECT * FROM workouttype')).fetchall()
 
def get_workouts_for_user(conn, uid, limit=10, offset=0):
    	return conn.execute(text('SELECT * FROM workout WHERE uid=:uid LIMIT :limit \
                        OFFSET :offset'), uid=uid, limit=limit,
                        offset=offset).fetchall()
 
def create_workout(conn, uid, wtid, start_time, duration):
    	query = text(
        	"""
        	INSERT INTO workout (uid, type, start, duration)
        	VALUES (:uid, :wtid, :start_time, :duration)
        	"""
    	)
    	return conn.execute(query, uid=uid, wtid=wtid, start_time=start_time,
                        duration=duration)
