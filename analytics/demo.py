import json
import tempfile
from pathlib import Path

from analytics.database import Analytics, QueryRejected
from analytics.seed import seed


def main():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'demo.db'
        seed(path)
        engine = Analytics(path)
        report = {'data': '120 synthetic orders', 'result': engine.query('SELECT region, SUM(revenue_cents) AS revenue_cents FROM orders GROUP BY region ORDER BY region')}
        try:
            engine.query('DELETE FROM orders')
        except QueryRejected:
            report['write_attempt'] = 'blocked'
        print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
