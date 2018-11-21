Python分布式事务实现:
1. [***TX specification***](http://archive.opengroup.org/publications/archive/CDROM/c504.pdf)
2. [***XA specification***](http://pubs.opengroup.org/onlinepubs/009680699/toc.pdf)

运行环境：python2.7，所支持的db为：
1. mysql(>=5.7) + MySQLdb(>=1.2.3)
2. mysql(>=5.7) + mysql-connector(>=2.1.0)
3. postgresql(>=8.4) + psycopg2


安装:
获取源码，并进入源码目录
```
# python setup.py install
```

用法：（暂不支持用unix_socket连接mysql）
```python
import MySQLdb
from python_dtp import local_db, MySQLResourceManager, PostgreSQLResourceManager, TransactionManager

def test():
    conn1, conn2 = MySQLdb.connect(**db1_conf), MySQLdb.connect(**db2_conf)
    # conn1, conn2也可以是mysql.connector.connection对象，或psycopg2.connection对象

    rm1, rm2 = MySQLResourceManager(conn1), MySQLResourceManager(conn2)
    cursor1, cursor2 = conn1.cursor(), conn2.cursor()

    local_db.path = '/path/to/dtp.sqlite3' # 很重要，记录执行失败的事务信息，crash恢复
    
    tm = TransactionManager(rm1, rm2)
    tm.tx_begin()
    cursor1.execute('insert into test1 values(1, "bbb")', ())
    cursor2.execute('insert into test2 values(NULL, "aaa")', ())
    tm.tx_commit()
```

在同一台机器上，跑如下脚本，用来crash恢复：
```python
from python_dtp import monitor, local_db

local_db.path = '/path/to/dtp.sqlite3' # 和上面的local_db.path一致

# 定义db的连接参数
db1_conf = {'host':'xxx', 'port':3306, 'user':'xxx', 'passwd':'xxx', 'db':'xxx'} # for mysql, 必须是MySQLdb能识别的参数
db2_conf = {'host':'xxx', 'port':3306, 'user':'xxx', 'password':'xxx', 'dbname':'xxx'} # for postgresql

# 告诉monitor，如何去连接db，其中key的值为形如(host, port)的tuple
monitor.db_config = {
    ('127.0.0.1', 60000) : db1_conf,
    ('localhost', 3307) : db2_conf,
    ('123.38.76.10', 3306) : db3_conf,
    ('test_db.nease.net', 3306) : db4_conf,
}


monitor.run() # 启动monitor，一直运行
```
