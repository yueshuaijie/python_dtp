
import string

#from . import *
import xa, errors


STMT_XA_BEGIN = string.Template('XA START "$gtrid", "$bqual", $formatID')
STMT_XA_END = string.Template('XA END "$gtrid", "$bqual", $formatID')
STMT_XA_PREPARE = string.Template('XA PREPARE "$gtrid", "$bqual", $formatID')
STMT_XA_COMMIT = string.Template('XA COMMIT "$gtrid", "$bqual", $formatID')
STMT_XA_ROLLBACK = string.Template('XA ROLLBACK "$gtrid", "$bqual", $formatID')
STMT_XA_RECOVER = string.Template('XA RECOVER')


ER_XAER_RMFAIL = 1399 # The command cannot be executed when global transaction is in the %s state
ER_XAER_OUTSIDE = 1400 # Some work is done outside global transaction
ER_XAER_NOTA = 1397 # Unknown XID
ER_LOST_CONNECTION = 2013 # Lost connection to MySQL server during
ER_GONE_AWAY = 2006 # MySQL server has gone away

RM_TYPE = 'mysql'

class MySQLResourceManager(xa.ResourceManager):
	def __init__(self, resource):
		super(MySQLResourceManager, self).__init__(resource)
		self.conn = resource

		MySQLdb = None
		try:
			import MySQLdb
		except ImportError:
			try:
				import mysql.connector
			except ImportError:
				raise Exception('need either MySQLdb or mysql.connector')

		if MySQLdb and isinstance(self.conn, MySQLdb.connection):
			self.rm_info = {
				'host':self.__normalize_mysqldb_host(self.conn.get_host_info()),
				'port':self.conn.port,
			}
		else: # Assume self.conn is  mysql.connector connection object
			self.rm_info = {
				'host':self.conn.server_host,
				'port':self.conn.server_port,
			}
		self.rm_type = RM_TYPE

	def __normalize_mysqldb_host(self, raw):
		# Through test, conn.get_host_info() return a string like:
		# 127.0.0.1 via TCP/IP
		# xxx.somehost.com via TCP/IP
		return raw.split(' via ')[0].lower()

	def xa_commit(self, xid):
		self.__exec_sql(STMT_XA_COMMIT, xid)

	def xa_end(self, xid):
		self.__exec_sql(STMT_XA_END, xid)

	def xa_prepare(self, xid):
		self.__exec_sql(STMT_XA_PREPARE, xid)

	def xa_recover(self):
		return self.__exec_sql(STMT_XA_RECOVER)

	def xa_rollback(self, xid):
		self.__exec_sql(STMT_XA_ROLLBACK, xid)

	def xa_start(self, xid):
		#except MySQLdb.OperationalError, e:
		#	if e.args[0] in (ER_XAER_RMFAIL, ER_XAER_OUTSIDE):
		self.__exec_sql(STMT_XA_BEGIN, xid)

	def __make_stmt(self, stmt, xid=None):
		if xid:
			return stmt.substitute(gtrid=xid.gtrid,
					bqual=xid.bqual, formatID=xid.formatID)
		else:
			return stmt.substitute()

	def __exec_sql(self, stmt, xid=None):
		errors_types = ()
		try:
			import MySQLdb
			errors_types = (MySQLdb.Error, )
		except ImportError:
			pass

		try:
			import mysql.connector
			errors_types += (mysql.connector.errors.Error, )
		except ImportError:
			pass

		cursor = self.conn.cursor()
		try:
			cursor.execute(self.__make_stmt(stmt, xid), ())
		except errors_types, e:
			if e.args[0] == ER_XAER_NOTA:
				raise errors.RMXIDNotExists(e)
			elif e.args[0] in (ER_LOST_CONNECTION, ER_GONE_AWAY):
				raise errors.RMConnectionLost(e)
			else:
				raise errors.RMException(e)
