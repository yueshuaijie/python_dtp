
import json, sqlite3, time, datetime


path = '/tmp/python_dtp_local_db.sqlite3'

CREATE_TABLE_STMT = '''
	CREATE TABLE IF NOT EXISTS dtp
	(xid VARCHAR(128) PRIMARY KEY NOT NULL,
	create_time timestamp NOT NULL,
	modify_time timestamp NOT NULL,
	status TINYINT NOT NULL DEFAULT 0,
	rms TEXT NOT NULL);
'''

CREATE_INDEX_STMT = '''
	CREATE INDEX IF NOT EXISTS status_create_time ON dtp (status, create_time);
'''

INSERT_RECORD_STMT = 'INSERT INTO dtp values(?, ?, ?, ?, ?)'

STATUS_INITIAL = 0
STATUS_PREPARED_SUCCESS = 1
STATUS_PREPARED_FAILED = 2

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Condition(object):
	def __init__(self, value):
		self.value = value

	def operator(self):
		return '='

class Lt(Condition):
	def operator(self):
		return '<'

class Gt(Condition):
	def operator(self):
		return '>'

class Lte(Condition):
	def operator(self):
		return '<='

class Gte(Condition):
	def operator(self):
		return '>='

class Ne(Condition):
	def operator(self):
		return '!='

class LocalDB(object):
	def __init__(self, path):
		self._db = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
		self._db.row_factory = dict_factory
		self._db_cursor = self._db.cursor()
		self._db_cursor.execute(CREATE_TABLE_STMT)
		self._db_cursor.execute(CREATE_INDEX_STMT)
		self._db.commit()

	def make_condition(self, conds):
		operator = lambda x:x.operator() if isinstance(x, Condition) else '='
		value = lambda x:x.value if isinstance(x, Condition) else x
		return ' AND '.join('%s %s ?' % (k, operator(v)) for k, v in conds.items()),\
				tuple([value(v) for k, v in conds.items()])

	def add_record(self, xid, dbs):
		self._db_cursor.execute(INSERT_RECORD_STMT,
				(str(xid), datetime.datetime.now(), datetime.datetime.now(),
					STATUS_INITIAL, json.dumps(dbs)))
		self._db.commit()

	def get_records(self, conds):
		sql = 'SELECT * FROM dtp WHERE '
		where_sql, paras = self.make_condition(conds)
		sql += where_sql
		return self._db_cursor.execute(sql, paras).fetchall()

	def modify_record(self, xid, update_fields):
		items = update_fields.items()
		sql = 'UPDATE dtp SET ' + ','.join(['%s = ?' % item[0] for item in items]) +\
				' WHERE xid = ?'
		params = [item[1] for item in items] + [str(xid)]
		self._db_cursor.execute(sql, params)
		self._db.commit()

	def remove_records(self, conds):
		sql = 'DELETE FROM dtp WHERE '
		where_sql, paras = self.make_condition(conds)
		sql += where_sql
		self._db_cursor.execute(sql, paras)
		self._db.commit()
