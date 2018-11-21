#!/usr/bin/env python

import os
import sys
from setuptools import setup, Extension

if not hasattr(sys, "hexversion") or sys.hexversion < 0x02070000:
    raise Error("Python 2.7 or newer is required")

setup(name='python_dtp',
      version='0.9.2',
      description='Python implementation of distributed transaction processing with MySQL, MySQLdb',
      author='yueshuaijie',
      author_email='ysj@love.com',
      url='https://git-cbg.nie.netease.com/yueshuaijie/python_dtp',
      packages=['python_dtp'],
	  #install_requires=['MySQL-python', 'mysql-connector', 'psycopg2'],
 )
