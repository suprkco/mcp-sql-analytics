import argparse
import json
import tempfile
from pathlib import Path

from analytics.database import Analytics, QueryRejected
from analytics.seed import seed


def main():
    parser = argparse.ArgumentParser(description='Read-only SQL terminal demo on synthetic data')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / 'demo.db'
        seed(path)
        engine = Analytics(path)
        report = {'data': '120 synthetic orders', 'result': engine.query('SELECT region, SUM(revenue_cents) AS revenue_cents FROM orders GROUP BY region ORDER BY region')}
        try:
            engine.query('DELETE FROM orders')
        except QueryRejected:
            report['write_attempt'] = 'blocked'
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print('sql / read-only analytics\n120 synthetic orders\n')
            print('REGION       REVENUE (CENTS)')
            for row in report['result']['rows']:
                print(f"{row['region']:<12} {row['revenue_cents']:>15}")
            print('\nWrite attempt: ' + report['write_attempt'])

if __name__ == '__main__':
    main()
