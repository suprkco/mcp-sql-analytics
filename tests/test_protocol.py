import os
import sys

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from analytics.seed import seed


def test_real_stdio_session(tmp_path):
    path = tmp_path / 'demo.db'
    seed(path)
    async def exercise():
        parameters = StdioServerParameters(command=sys.executable, args=['-m', 'analytics.server'], env={**os.environ, 'ANALYTICS_DB': str(path)})
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.list_tools()
                assert {t.name for t in result.tools} == {'inspect_schema', 'query_readonly'}
                success = await session.call_tool('query_readonly', {'sql': 'SELECT COUNT(*) AS n FROM orders'})
                assert not success.is_error
                blocked = await session.call_tool('query_readonly', {'sql': 'DROP TABLE orders'})
                assert blocked.is_error
    anyio.run(exercise)
