
import json, random, string, socket, traceback, logging

import errors, xa, local_db


TX_NOT_SUPPORTED = 1 # normal execution
TX_OK = 0 # normal execution
TX_OUTSIDE = -1 # application is in an RM local transaction
TX_ROLLBACK = -2 # transaction was rolled back
TX_MIXED = -3 # transaction was partially committed and partially rolled back
TX_HAZARD = -4 # transaction may have been partiall committed and partially rolled bac
TX_PROTOCOL_ERROR = -5 # routine invoked in an improper context
TX_ERROR = -6 # transient error
TX_FAIL = -7 # fatal error
TX_EINVAL = -8 # invalid arguments were given
TX_COMMITTED = -9 # the transaction was heuristically committed
TX_NO_BEGIN = -100 # transaction committed plus new transaction could not be started
TX_ROLLBACK_NO_BEGIN = TX_ROLLBACK + TX_NO_BEGIN # transaction rollback plus new transaction could not be started
TX_MIXED_NO_BEGIN = TX_MIXED + TX_NO_BEGIN # mixed plus transaction could not be started
TX_HAZARD_NO_BEGIN = TX_HAZARD + TX_NO_BEGIN # hazard plus transaction could not be started
TX_COMMITTED_NO_BEGIN = TX_COMMITTED + TX_NO_BEGIN # heuristically committed plus transaction could not be started

TX_COMMIT_COMPLETED = 0
TX_COMMIT_DECISION_LOGGED = 1
COMMIT_RETURN = TX_COMMIT_COMPLETED, TX_COMMIT_DECISION_LOGGED

TX_UNCHAINED = 0
TX_CHAINED = 1
TRANSACTION_CONTROL = TX_UNCHAINED, TX_CHAINED

DEFAULT_TRANSACTION_TIMEOUT = 5

# No RMs have been opened or initialised. An application thread of control cannot start a global transaction
# until it has successfully opened its RMs via tx_open( ).
STATE_INITIAL = 0
# The thread has opened its RMs but is not in a transaction.
STATE_OPEN = 1
# The thread has opened its RMs and is in a transaction.
STATE_TRANSACTION = 2

COMMIT_RETRY_TIMES = 3

def generate_random_str(length):
	return ''.join(random.choice(string.letters + string.digits) for i in range(length))

local_ip = socket.gethostbyname(socket.gethostname())

LOGGER_NAME = '__python_dtp'

class TransactionManager(object):

	def __init__(self, *rms):
		super(TransactionManager, self).__init__()
		if not rms:
			raise errors.DTPException('Must specify at least one rm')
		self.rms = rms
		self.commit_return = TX_COMMIT_COMPLETED
		self.transaction_control = TX_UNCHAINED
		self.transaction_timeout = DEFAULT_TRANSACTION_TIMEOUT
		self.in_transaction = False
		self._local_db = local_db.LocalDB(local_db.path)

	def _generate_xid(self):
		xid = xa.XID('%s-%s' % (local_ip, generate_random_str(xa.MAXGTRIDSIZE -\
			len(local_ip) - 1)))
		return xid

	def tx_begin(self):
		if self.in_transaction:
			return TX_PROTOCOL_ERROR
		self.xid = self._generate_xid()
		succ_rms = []
		for rm in self.rms:
			try:
				rm.xa_start(self.xid)
			except:
				self.__log_exception()
				while succ_rms:
					rm = succ_rms.pop()
					try:
						rm.xa_end(self.xid)
						rm.xa_rollback(self.xid)
					except:
						self.__log_exception()
				raise
			else:
				succ_rms.append(rm)
		self.in_transaction = True
		return TX_OK

	def record_status(self, status):
		self._local_db.modify_record(self.xid, {'status':status})

	def remove_record(self):
		self._local_db.remove_records({'xid':str(self.xid)})

	def tx_close(self):
		return TX_OK

	def __log_exception(self):
		logger = logging.getLogger(LOGGER_NAME)
		logger.info(traceback.format_exc())

	def __xa_end_all(self):
		success, failed = [], []
		for rm in self.rms:
			try:
				rm.xa_end(self.xid)
			except:
				self.__log_exception()
				failed.append(rm)
			else:
				success.append(rm)

		if failed:
			for rm in success:
				try:
					rm.xa_rollback(self.xid)
				except:
					self.__log_exception()
			for rm in failed:
				try:
					rm.xa_end(self.xid)
					rm.xa_rollback(self.xid)
				except:
					self.__log_exception()
			return False
		else:
			return True

	def __xa_prepare_all(self):
		self._local_db.add_record(self.xid, [{'rm_info':r.rm_info,
			'rm_type':r.rm_type} for r in self.rms])
		for rm in self.rms:
			try:
				rm.xa_prepare(self.xid)
			except:
				self.__log_exception()
				self.record_status(local_db.STATUS_PREPARED_FAILED)
				for rm in self.rms:
					try:
						rm.xa_rollback(self.xid)
					except:
						self.__log_exception()
				return False
		self.record_status(local_db.STATUS_PREPARED_SUCCESS)
		return True

	def __xa_commit_all(self):
		has_failed = False
		for rm in self.rms:
			for x in xrange(COMMIT_RETRY_TIMES):
				# Make sure the transaction is committed. Always retry
				try:
					rm.xa_commit(self.xid)
				except errors.RMXIDNotExists, e:
					# if xid not exists, the transaction has be committed already
					break
				except:
					self.__log_exception()
				else:
					break
			else:
				has_failed = True
		if not has_failed:
			self.remove_record()
		return True

	def tx_commit(self):
		if not self.in_transaction:
			return TX_PROTOCOL_ERROR

		if not self.__xa_end_all():
			return TX_ROLLBACK

		# Phase 1
		if not self.__xa_prepare_all():
			return TX_ROLLBACK

		# Phase 2
		if not self.__xa_commit_all():
			return TX_ROLLBACK

		self.in_transaction = False
		return TX_OK

	def tx_info(self):
		return self

	def tx_open(self):
		return TX_OK

	def tx_rollback(self):
		if not self.in_transaction:
			return TX_PROTOCOL_ERROR
		for rm in self.rms:
			rm.xa_end(self.xid)
			rm.xa_rollback(self.xid)
		return TX_OK

	def tx_set_commit_return(self, commit_return):
		if commit_return not in COMMIT_RETURN:
			raise errors.DTPException('tx_set_commit_return() invalid value:%s' % commit_return)
		self.commit_return = commit_return
		return TX_OK

	def tx_set_transaction_control(self, transaction_control):
		if transaction_control not in TRANSACTION_CONTROL:
			raise errors.DTPException('tx_set_transaction_control() invalid value:%s' % transaction_control)
		self.transaction_control = transaction_control
		return TX_OK

	def tx_set_transaction_timeout(self, transaction_timeout):
		if not isinstance(transaction_timeout, (int, long)) or transaction_timeout < 0:
			raise errors.DTPException('tx_set_transaction_timeout() invalid value:%s' % transaction_timeout)
		self.transaction_timeout = transaction_timeout
		return TX_OK

