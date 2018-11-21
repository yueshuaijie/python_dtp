
XIDDATASIZE = 128
MAXGTRIDSIZE = 64
MAXBQUALSIZE = 64
class XID(object):
	def __init__(self, gtrid, bqual='', formatID=1):
		self.gtrid = gtrid
		self.bqual = bqual
		self.formatID = formatID

	def __str__(self):
		parts = [self.gtrid, self.bqual, self.formatID]
		return ','.join(map(str, parts))

# ax_() return codes (transaction manager reports to resource manager)
TM_JOIN = 2 # caller is joining existing transaction branch
TM_RESUME = 1 # caller is resuming association with suspended transaction branch
TM_OK = 0 # normal execution
TMER_TMERR = -1 # an error occurred in the transaction manager
TMER_INVAL = -2 # invalid arguments were given
TMER_PROTO = -3 # routine invoked in an improper context

# xa_() return codes (resource manager reports to transaction manager)
XA_RBBASE = 100 # the inclusive lower bound of the rollback codes
XA_RBROLLBACK = XA_RBBASE # the rollback was caused by an unspecified reason
XA_RBCOMMFAIL = XA_RBBASE+1 # the rollback was caused by a communication failure
XA_RBDEADLOCK = XA_RBBASE+2 # a deadlock was detected
XA_RBINTEGRITY = XA_RBBASE+3 # a condition that violates the integrity of the resources was detected
XA_RBOTHER = XA_RBBASE+4 # the resource manager rolled back the transaction branch for a reason not on this list
XA_RBPROTO = XA_RBBASE+5 # a protocol error occurred in the resource manager
XA_RBTIMEOUT = XA_RBBASE+6 # a transaction branch took too lon
XA_RBTRANSIENT = XA_RBBASE+7 # may retry the transaction branch
XA_RBEND = XA_RBTRANSIENT # the inclusive upper bound of the rollback codes
XA_NOMIGRATE = 9 # resumption must occur where suspension occurred
XA_HEURHAZ = 8 # the transaction branch may have been heuristically completed
XA_HEURCOM = 7 # the transaction branch has been heuristically committed
XA_HEURRB = 6 # the transaction branch has been heuristically rolled back
XA_HEURMIX = 5 # the transaction branch has been heuristically committed and rolled back
XA_RETRY = 4 # routine returned with no effect and may be reissued
XA_RDONLY = 3 # the transaction branch was read-only and has been committed
XA_OK = 0 # normal execution
XAER_ASYNC = -2 # asynchronous operation already outstanding
XAER_RMERR = -3 # a resource manager error occurred in the transaction branch
XAER_NOTA = -4 # the XID is not valid
XAER_INVAL = -5 # invalid arguments were given
XAER_PROTO = -6 # routine invoked in an improper context
XAER_RMFAIL = -7 # resource manager unavailable
XAER_DUPID = -8 # the XID already exists
XAER_OUTSIDE = -9 # resource manager doing work outside ????/ /???? global transaction


class ResourceManager(object):
	def __init__(self, resource):
		self.resource = resource
		self.rm_info = {}
		self.rm_type = 'Unknown'

	def xa_close(self):
		pass

	def xa_commit(self):
		pass

	def xa_complete(self):
		pass

	def xa_end(self):
		pass

	def xa_forget(self):
		pass

	def xa_open(self):
		pass

	def xa_prepare(self):
		pass

	def xa_recover(self):
		pass

	def xa_rollback(self):
		pass

	def xa_start(self):
		pass

	xa_begin = xa_start
