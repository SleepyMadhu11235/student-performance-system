"""
Using PyMySQL (pure Python) as the MySQL driver instead of mysqlclient.
This avoids needing system-level build tools / libmysqlclient-dev on the
host machine while still using Django's standard 'django.db.backends.mysql'
engine. This shim must run before Django touches the database backend,
which is why it lives here in config/__init__.py (imported first).
"""
try:
    import pymysql

    pymysql.install_as_MySQLdb()
except ImportError:
    # Only a problem if DB_ENGINE=mysql and PyMySQL wasn't installed —
    # Django will raise a clear "No module named MySQLdb" error in that case.
    pass
