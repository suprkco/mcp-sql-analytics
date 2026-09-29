"""Bounded read-only SQL, enforced by SQLite rather than keyword filtering."""
import hashlib
import json
import logging
import sqlite3
import time
from pathlib import Path

ALLOWED_TABLES = frozenset({'orders', 'products'})
ALLOWED_FUNCTIONS = frozenset({'count', 'sum', 'avg', 'min', 'max', 'round', 'coalesce', 'ifnull', 'lower', 'upper', 'length', 'abs', 'date', 'strftime'})
logger = logging.getLogger(__name__)

class QueryRejected(ValueError):
    """The query violated policy or could not be completed within the budget."""

def authorize(action, arg1, arg2, database, trigger):
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK
    # SQLite may omit the database name for table-only reads (e.g. COUNT(*)).
    if action == sqlite3.SQLITE_READ and (database == 'main' or (database is None and arg2 == '')) and arg1 in ALLOWED_TABLES:
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and (arg2 or '').lower() in ALLOWED_FUNCTIONS:
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY

class Analytics:
    def __init__(self, path, row_limit=100, timeout_seconds=0.25):
        self.path = Path(path).resolve(strict=True)
        if not 1 <= row_limit <= 1000 or not 0 < timeout_seconds <= 5:
            raise ValueError('Invalid query budget')
        self.row_limit = row_limit
        self.timeout_seconds = timeout_seconds

    def connect(self):
        connection = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True, timeout=1)
        connection.execute('PRAGMA query_only=ON')
        connection.enable_load_extension(False)
        return connection

    def schema(self):
        connection = self.connect()
        try:
            return {table: [{'name': row[1], 'type': row[2]} for row in connection.execute(f'PRAGMA table_info("{table}")')]
                for table in sorted(ALLOWED_TABLES)}
        finally:
            connection.close()

    def query(self, sql, parameters=None):
        if not isinstance(sql, str) or not sql.strip() or len(sql) > 8000:
            raise QueryRejected('SQL must contain 1 to 8000 characters')
        if parameters is None:
            parameters = []
        if not isinstance(parameters, list) or len(parameters) > 100:
            raise QueryRejected('At most 100 positional parameters are allowed')
        if any(not isinstance(v, (str, int, float, type(None))) or (isinstance(v, str) and len(v) > 2000) for v in parameters):
            raise QueryRejected('Unsupported or oversized parameter')
        started = time.monotonic()
        status = 'rejected'
        connection = self.connect()
        deadline = started + self.timeout_seconds
        connection.set_progress_handler(lambda: int(time.monotonic() > deadline), 100)
        connection.set_authorizer(authorize)
        if hasattr(connection, 'setlimit'):
            connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 100_000)
            connection.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 8000)
        try:
            cursor = connection.execute(sql, parameters)
            if cursor.description is None:
                raise QueryRejected('Only result-producing queries are allowed')
            rows = cursor.fetchmany(self.row_limit + 1)
            columns = [column[0] for column in cursor.description]
            if len(set(columns)) != len(columns):
                raise QueryRejected('Use unique column aliases')
            output = [dict(zip(columns, row)) for row in rows[:self.row_limit]]
            if len(json.dumps(output, default=str).encode()) > 100_000:
                raise QueryRejected('Result exceeds 100 KB; select fewer columns or aggregate')
            status = 'ok'
            return {'columns': columns, 'rows': output, 'truncated': len(rows) > self.row_limit,
                    'row_limit': self.row_limit}
        except (sqlite3.Error, sqlite3.Warning):
            raise QueryRejected('Query denied, invalid, or resource budget exceeded') from None
        finally:
            connection.close()
            logger.info(json.dumps({'query_sha256': hashlib.sha256(sql.encode()).hexdigest(),
                'status': status, 'milliseconds': round((time.monotonic()-started)*1000, 2)}))
