# Awesome MCP Servers

A curated collection of high-quality Model Context Protocol (MCP) servers, stored in a machine-readable format for programmatic consumption.

This repo contains two types of content:

| Type | Where it lives | What it is |
|------|---------------|------------|
| **Local servers** | `servers/*.yaml` | Hand-curated MCP server entries maintained in this repo |
| **External sources** | `sources/*.yaml` + `config.yaml` | Links to GitHub repos that aggregate MCP servers |

The build system (`make build`) fetches all sources, merges them into `dist/`, and updates this README automatically.

## What is MCP?

[MCP](https://modelcontextprotocol.io/) is an open protocol that enables AI models to securely interact with local and remote resources through standardized server implementations. MCP servers extend AI capabilities through file access, database connections, API integrations, and other contextual services.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Build the unified collection from all sources
make build

# Or run everything (validate + test + build + readme update)
make all
```

## For Consumers

Fetch the unified collection:

```bash
# Index entry point
curl -s https://raw.githubusercontent.com/Chat2AnyLLM/awesome-mcp-servers/main/dist/index.json

# All servers
curl -s https://raw.githubusercontent.com/Chat2AnyLLM/awesome-mcp-servers/main/dist/servers.json
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details. Two ways to contribute:

1. **Add a server directly** — write `servers/<slug>.yaml`
2. **Add an external source** — write `sources/<slug>.yaml` pointing to a GitHub repo

---

## Server Directory

### 📂 <a name="file-systems"></a>File Systems

> File I/O, directory operations, cloud storage

| Server | Description | Tags |
|--------|-------------|------|
| [filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | Access local files with secure defaults | `official` `filesystem` |

### 🗄️ <a name="databases"></a>Databases

> Database access, queries, migrations

| Server | Description | Tags |
|--------|-------------|------|
| [sqlite](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite) | SQLite database access with query capabilities | `official` `database` `sql` |

### 🔄 <a name="version-control"></a>Version Control

> Git, GitHub, GitLab, code hosting

| Server | Description | Tags |
|--------|-------------|------|
| [github](https://github.com/modelcontextprotocol/servers/tree/main/src/github) | GitHub API integration | `official` `github` |

### 🌐 <a name="web"></a>Web

> Web search, scraping, HTTP clients

| Server | Description | Tags |
|--------|-------------|------|
| [brave-search](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search) | Web and local search via Brave Search API | `official` `search` |

### ☁️ <a name="cloud-platforms"></a>Cloud Platforms

> AWS, Azure, GCP, cloud services

*(No local entries yet — add one via `servers/`)*

### 🤖 <a name="ai-ml"></a>AI/ML

> AI model serving, inference, training

*(No local entries yet — add one via `servers/`)*

### 🛠️ <a name="developer-tools"></a>Developer Tools

> CI/CD, monitoring, debugging, IDE integration

*(No local entries yet — add one via `servers/`)*

### 💬 <a name="communication"></a>Communication

> Email, messaging, notifications, Slack

*(No local entries yet — add one via `servers/`)*

### 🔒 <a name="security"></a>Security

> Authentication, secrets, vulnerability scanning

*(No local entries yet — add one via `servers/`)*

### 📊 <a name="data"></a>Data

> Data processing, ETL, analytics

*(No local entries yet — add one via `servers/`)*

### 🏢 <a name="productivity"></a>Productivity

> Task management, notes, calendars

*(No local entries yet — add one via `servers/`)*

### 🔗 <a name="other"></a>Other

*(No local entries yet — add one via `servers/`)*

---

## External Sources

These GitHub repos are aggregated via the build system. Servers from external sources appear in `dist/servers.json` under their source name.

| Source | Type | Format | Description |
|--------|------|--------|-------------|
| Punkpeye Awesome MCP Servers | github | md | Community-curated list of MCP servers |
| Official MCP Servers | github | md | Reference implementations from the MCP team |

<details>
<summary><strong>Punkpeye Awesome MCP Servers</strong> (scraped)</summary>

See the full list at [github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)

</details>

<details>
<summary><strong>Official MCP Servers</strong> (scraped)</summary>

See the full list at [github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

</details>

---

## Stats

| Metric | Count |
|--------|-------|
| Unified servers (in `dist/servers.json`) | 5 |
| Direct servers (from `servers/`) | 4 |
| Configured sources | 3 |
| Scraped servers cached in `scraped/` | 2 |

### Configured Sources

| Source | Type | Location | Format | Loaded |
|--------|------|----------|--------|--------|
| Local Servers | local | `servers/` | - | 4 |
| Punkpeye Awesome MCP Servers | github | [https://github.com/punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | md | 1 |
| Official MCP Servers | github | [https://github.com/modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | md | 1 |

### Scraped Servers

<details>
<summary><strong>Official Mcp Servers</strong> (1 servers)</summary>

| # | Title | Description |
|---|-------|-------------|
| 1 | Readme | # Model Context Protocol servers  This repository is a coll… |

</details>

<details>
<summary><strong>Punkpeye Awesome Mcp Servers</strong> (1 servers)</summary>

| # | Title | Description |
|---|-------|-------------|
| 1 | Readme | [![ไทย](https://img.shields.io/badge/Thai-Click-blue)](READ… |

</details>
## License

MIT
