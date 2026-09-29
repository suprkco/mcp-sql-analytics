import hashlib

import pytest

from analytics.database import Analytics, QueryRejected
from analytics.seed import seed


@pytest.fixture
def engine(tmp_path):
    path = tmp_path / 'demo.db'
    seed(path)
    return Analytics(path)

def test_aggregate(engine):
    result = engine.query('SELECT SUM(revenue_cents) AS total, COUNT(*) AS n FROM orders')
    assert result['rows'] == [{'total': 420000, 'n': 120}]

def test_schema(engine):
    assert set(engine.schema()) == {'orders', 'products'}

def test_truncation(engine):
    result = engine.query('SELECT id FROM orders ORDER BY id')
    assert len(result['rows']) == 100 and result['truncated']

def test_parameter_is_not_sql(engine):
    result = engine.query('SELECT id FROM orders WHERE region = ?', ["North' OR 1=1 --"])
    assert result['rows'] == []

@pytest.mark.parametrize('sql', [
    'DELETE FROM orders', 'UPDATE orders SET quantity=0',
    'INSERT INTO products VALUES (9, \'X\', \'Y\')', 'DROP TABLE orders',
    'CREATE TABLE evil (x)', 'PRAGMA query_only=OFF',
    "ATTACH DATABASE ':memory:' AS extra", 'SELECT * FROM sqlite_master',
    "SELECT load_extension('malicious')", 'SELECT randomblob(1000000000)',
    'SELECT * FROM orders; DELETE FROM orders',
    'WITH x AS (SELECT 1) DELETE FROM orders',
    'WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n) SELECT * FROM n',
    'VACUUM', 'BEGIN',
])
def test_guardrails(engine, sql):
    before = hashlib.sha256(engine.path.read_bytes()).hexdigest()
    with pytest.raises(QueryRejected):
        engine.query(sql)
    assert hashlib.sha256(engine.path.read_bytes()).hexdigest() == before

def test_readonly_cte(engine):
    assert engine.query('WITH x AS (SELECT COUNT(*) AS n FROM orders) SELECT n FROM x')['rows'] == [{'n': 120}]

def test_timeout(engine):
    engine.timeout_seconds = 0.001
    with pytest.raises(QueryRejected):
        engine.query('SELECT SUM(a.quantity*b.quantity*c.quantity*d.quantity) FROM orders a, orders b, orders c, orders d')

def test_empty_oversized_and_aliases(engine):
    for query in ['', 'x'*8001, 'SELECT id, id FROM orders']:
        with pytest.raises(QueryRejected):
            engine.query(query)

def test_seed_does_not_overwrite(engine):
    with pytest.raises(FileExistsError):
        seed(engine.path)
