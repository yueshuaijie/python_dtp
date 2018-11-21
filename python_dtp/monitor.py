#!/usr/bin/env python

import os, sys, time, copy, json, datetime, traceback
import errors, local_db, xa, xa_mysql, xa_postgresql


ROLLBACK_PREPARED_TIMEOUT = 60 # Delete initial records after 1 minutes
COMMIT_PREPARED_TIMEOUT = 60 # Delete initial records after 1 minutes

db_config = {}

class DBConfigException(errors.DTPException):
	pass

def make_xid(raw):
	gtrid, bqual, formatID = raw.split(',')
	return xa.XID(gtrid, bqual, int(formatID))

managers = {}

def get_db_config_key(rm):
	return rm['rm_info']['host'], rm['rm_info']['port']

def get_manager_key(rm):
	return json.dumps(rm)

def get_rm(rm):
	if get_manager_key(rm) not in managers:
		if rm['rm_type'] == xa_mysql.RM_TYPE:
			conf = copy.copy(db_config[get_db_config_key(rm)])
			conf['autocommit'] = True
			import MySQLdb
			conn = MySQLdb.connect(**conf)
			managers[get_manager_key(rm)] = xa_mysql.MySQLResourceManager(conn)
		elif rm['rm_type'] == xa_postgresql.RM_TYPE:
			import psycopg2
			conn = psycopg2.connect(**db_config[get_db_config_key(rm)])
			managers[get_manager_key(rm)] = xa_postgresql.PostgreSQLResourceManager(conn)
		else:
			raise 'rm_type not support'
	return managers[get_manager_key(rm)]

def process_records(db, cond, func_name):
	now = datetime.datetime.now()
	records = db.get_records(cond)
	for record in records:
		rms = json.loads(record['rms'])
		for rm in rms:
			if get_db_config_key(rm) not in db_config:
				raise DBConfigException('db config missing:%s' % rm)
		has_failed = False
		xid = make_xid(record['xid'])
		print 'process record', record
		for rm_data in rms:
			print '\t', func_name, rm_data
			manager = get_rm(rm_data)
			try:
				getattr(manager, func_name)(xid)
			except errors.RMXIDNotExists, e:
				print '\txid not exists, success'
				pass #success
			except errors.RMConnectionLost, e:
				print '\tlost connection'
				del managers[get_manager_key(rm_data)]
				get_rm(rm_data)
				has_failed = True
				break
			except:
				print traceback.format_exc()
				has_failed = True
				break
			else:
				print '\tsuccess'
		if not has_failed:
			print 'remove record', record
			db.remove_records({'xid':str(xid)})
		else:
			print 'keep record', record


def run():
	db = local_db.LocalDB(local_db.path)

	while True:
		now = datetime.datetime.now()
		process_records(db, {
			'status':local_db.STATUS_PREPARED_SUCCESS,
			'create_time':local_db.Lte(now -\
					datetime.timedelta(seconds=COMMIT_PREPARED_TIMEOUT)),
		}, 'xa_commit')
		process_records(db, {
			'status':local_db.Ne(local_db.STATUS_PREPARED_SUCCESS),
			'create_time':local_db.Lte(now -\
					datetime.timedelta(seconds=ROLLBACK_PREPARED_TIMEOUT)),
		}, 'xa_rollback')
		time.sleep(5)
