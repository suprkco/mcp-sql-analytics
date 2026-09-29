import logging
import os

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from analytics.database import Analytics

server = MCPServer('Read-only SQL analytics', instructions='Inspect the schema first. Use SELECT with positional parameters. Only synthetic orders and products are exposed. Results may be truncated.')

def database():
    return Analytics(os.getenv('ANALYTICS_DB', 'demo.db'))

@server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def inspect_schema() -> dict:
    """List columns of the two allowed analytics tables."""
    return database().schema()

@server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False))
def query_readonly(sql: str, parameters: list[str | int | float | None] | None = None) -> dict:
    """Execute one bounded read-only SQL statement against allowed tables. Use ? placeholders for values."""
    return database().query(sql, parameters)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server.run(transport='stdio')
