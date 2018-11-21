

import logging

import local_db

from xa import *
from tx import *

from xa_mysql import *
from xa_postgresql import *

def config_logging(filename='/tmp/python_dtp.log', level=logging.WARNING):
	logger = logging.getLogger(LOGGER_NAME)
	logger.setLevel(level)
	fh = logging.FileHandler(filename, mode='a', encoding=None, delay=False)
	logger.addHandler(fh)
