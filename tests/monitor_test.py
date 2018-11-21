#!/usr/bin/env python

import os, sys, copy, pprint
sys.path.insert(0, '.')
#sys.path.insert(0, '/home/yueshuaijie/svn/MySQLdb1/build/lib.linux-x86_64-2.7')

from python_dtp import monitor, local_db


local_db.path = './dtp.sqlite3'

db1_conf = {
	'host':'127.0.0.1',
	'port':60000,
	'passwd':'mysql',
	'user':'root',
	'db':'test_dtp',
	'autocommit':True,
}
db2_conf = copy.copy(db1_conf)
db2_conf['port'] = 60001

db3_conf = {
		'dbname':'test_dtp',
		'user':'postgres',
		'password':'postgresql',
		'host':'127.0.0.1',
		'port':5432,
}

monitor.db_config = {
	('127.0.0.1', 60000) : db1_conf,
	('127.0.0.1', 60001) : db2_conf,
	#('127.0.0.1', 5432) : db3_conf,
}



if __name__ == '__main__':
	monitor.run()
