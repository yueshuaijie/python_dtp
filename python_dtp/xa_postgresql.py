
import string


#from . import *
import xa, errors


STMT_XA_BEGIN = string.Template('BEGIN')
STMT_XA_END = string.Template('')
STMT_XA_PREPARE = string.Template('PREPARE TRANSACTION "$gtrid"')
STMT_XA_COMMIT = string.Template('COMMIT PREPARED "$gtrid"')
STMT_XA_ROLLBACK = string.Template('ROLLBACK PREPARED "$gtrid"')
STMT_XA_RECOVER = string.Template('SELECT * FROM pg_prepared_xacts')


ER_XAER_RMFAIL = 1399 # The command cannot be executed when global transaction is in the %s state
ER_XAER_OUTSIDE = 1400 # Some work is done outside global transaction
ER_XAER_NOTA = 1397 # Unknown XID
ER_LOST_CONNECTION = 2013 # Lost connection to MySQL server during
ER_GONE_AWAY = 2006 # MySQL server has gone away

ER_XID_NOT_EXISTS = '42704'
ER_CONNECTION_CLOSE = '57P01'

RM_TYPE = 'postgresql'

def decorator(func):
	def wrapper(*args, **kwargs):
		import psycopg2
		try:
			return func(*args, **kwargs)
		except psycopg2.Error, e:
			if e.pgcode == ER_XID_NOT_EXISTS:
				raise errors.RMXIDNotExists(e)
			elif e.pgcode == ER_CONNECTION_CLOSE:
				raise errors.RMConnectionLost(e)
			else:
				raise errors.RMException(e)
			'''
			for k in ('args', 'cursor', 'diag', 'message', 'pgcode',
					'pgerror'):
				print k, getattr(e, k)
			import traceback
			print traceback.format_exc()
			raise Exception('111 %s' % e)
			'''
	return wrapper

class PostgreSQLResourceManager(xa.ResourceManager):
	def __init__(self, resource):
		super(PostgreSQLResourceManager, self).__init__(resource)
		self.conn = resource
		self._in_transaction = False
		import psycopg2
		dsn_params = dict((item.split('=') for item in self.conn.dsn.split(' ')))
		self.rm_info = {
			'host':dsn_params['host'],
			'port':int(dsn_params['port']),
		}
		self.rm_type = RM_TYPE

	@decorator
	def xa_commit(self, *args):
		if self._in_transaction:
			self.conn.tpc_commit()
			self._in_transaction = False
		else:
			self.conn.tpc_commit(*map(str, args))

	@decorator
	def xa_end(self, xid):
		pass

	@decorator
	def xa_prepare(self, *args):
		self.conn.tpc_prepare()

	@decorator
	def xa_recover(self):
		return self.conn.tpc_recover()

	@decorator
	def xa_rollback(self, *args):
		if self._in_transaction:
			self.conn.tpc_rollback()
			self._in_transaction = False
		else:
			self.conn.tpc_rollback(*map(str, args))

	@decorator
	def xa_start(self, xid):
		self._in_transaction = True
		self.conn.tpc_begin(str(xid))
