
class DTPException(Exception):
	def __init__(self, msg):
		super(DTPException, self).__init__()
		self.msg = msg
	def __str__(self):
		raw = super(DTPException, self).__str__()
		raw += ' ' + str(self.msg)
		return raw


class RMException(DTPException):
	pass

class RMXIDNotExists(RMException):
	pass

class RMConnectionLost(RMException):
	pass
