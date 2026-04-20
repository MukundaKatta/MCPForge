# MCPForge

MCPForge is a lightweight toolkit for scaffolding and validating Model Context Protocol servers locally.

This first slice focuses on two practical workflows:

- `mcpforge init` creates a minimal stdio MCP starter project
- `mcpforge check` runs a smoke test against a local server and validates the basic MCP handshake

## Why MCPForge

MCP server development still has a lot of repeated setup work:

- creating a starter project structure
- wiring up a local stdio server loop
- checking whether the server starts and responds correctly
- documenting a runnable local workflow for the next contributor

MCPForge exists to make that first setup and validation loop repeatable.

## Install

From the repository root:

```bash
python -m pip install -e .
```

## Usage

Create a starter project:

```bash
mcpforge init ./my-server
```

That command generates:

- `server.py` with a minimal stdio MCP server
- `README.md` with local run instructions
- `.gitignore` for basic Python artifacts

Run the generated server locally:

```bash
cd my-server
python server.py
```

In another terminal, validate the server:

```bash
mcpforge check .
```

Successful output looks like:

```text
PASS: stdio server handshake succeeded.
Server: starter-mcp-server 0.1.0
Verified methods: initialize, tools/list, resources/list, prompts/list
```

## Current Scope

The current implementation is intentionally small:

- one scaffold command
- one local stdio smoke-test command
- one minimal project template

That is enough to make the repo usable while keeping the first implementation easy to understand and extend.

## Next Steps

Likely next improvements include:

- richer starter templates
- configurable server names and metadata
- deeper MCP protocol validation
- CI-friendly check output
- packaging and deployment helpers

## Project Structure

```text
MCPForge/
├── .gitignore
├── README.md
├── pyproject.toml
└── mcpforge/
    ├── __init__.py
    ├── cli.py
    └── templates.py
```
