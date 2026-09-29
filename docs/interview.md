# Five-minute interview walkthrough

1. Run `python -m analytics.demo` and explain the synthetic data and cents convention.
2. Run `pytest -q tests/test_protocol.py`: this launches a real stdio server and completes an MCP handshake, tool listing, valid SELECT and denied DROP.
3. Open `analytics/database.py`. Explain why checking whether a string starts with SELECT would be insufficient.
4. Show parameter binding, the authorizer, explicit truncation and query-hash audit logging.
5. Describe the trust boundary: local process configuration is trusted, SQL is untrusted, and an allowlisted table is readable in full.

Questions to prepare: Why is an MCP read-only annotation not a security control? How would PostgreSQL roles and statement timeouts differ? Why is a cooperative progress handler not a hard memory sandbox? What sensitive information can a SELECT still expose?

This is an AI-assisted portfolio prototype, not a production deployment or a client case study.
