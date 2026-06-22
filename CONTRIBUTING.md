# Contributing

There are two ways to contribute MCP servers to this collection:

## Option 1: Add a Server Directly

Best for: MCP servers you built or have permission to include.

1. Create `servers/<slug>.yaml` (lowercase, hyphens only):

```yaml
slug: my-mcp-server
title: My MCP Server
description: A one-line summary of what this MCP server does.
url: https://github.com/username/my-mcp-server
tags:
  - relevant
  - tags
category: developer-tools
author: your-github-username
```

2. Validate and build:

```bash
pip install -r requirements.txt
make ci
```

3. Commit all changes (including `dist/`) and open a PR.

### Server Schema Rules

- `slug` must match the filename (without `.yaml`)
- `slug` format: `^[a-z0-9]+(-[a-z0-9]+)*$`
- `category` must be one of: `ai-ml`, `databases`, `file-systems`, `version-control`, `communication`, `cloud-platforms`, `developer-tools`, `web`, `productivity`, `security`, `data`, `other`
- `tags` must have at least one entry, no duplicates
- `url` must be a valid URL (typically a GitHub repo URL)
- `description` must be at least 10 characters

---

## Option 2: Link an External Source

Best for: pointing to a GitHub repo or file that contains MCP server listings (YAML, Markdown, CSV, JSON).

1. Create `sources/<slug>.yaml`:

```yaml
slug: my-source-name
title: My Source Name
description: A one-line summary of what this source contains.
url: https://github.com/username/repo-with-mcp-servers
format: yaml
type: collection
tags:
  - relevant
  - tags
category: developer-tools
author: your-github-username
notes: |
  Optional notes about how the servers are organized in this repo,
  which files to look at, or how a consumer should use them.
```

2. Validate and build:

```bash
make ci
```

3. Commit and open a PR.

### Source Schema Rules

- `slug` must match the filename (without `.yaml`)
- `url` must be a GitHub URL (`https://github.com/...`)
- `format`: what format the server files are in — `yaml`, `md`, `csv`, `json`, or `mixed`
- `type`: `single-server` (link to one server file) or `collection` (link to a repo with many)
- `notes` is optional but encouraged — helps consumers know how to parse the source

### What Makes a Good Source Link

- The linked repo should contain actual MCP server content (not just a README listing)
- Servers should be in a parseable format (YAML, Markdown, CSV, or JSON)
- The repo should be actively maintained or at least stable
- Include `notes` explaining the file structure so a consumer tool can fetch and parse it

---

## Guidelines

- Write clear, specific descriptions that explain what the MCP server provides
- Include the GitHub URL so consumers can find and install the server
- One server per file (for direct entries)
- Test that the server link works and the repo is accessible
- For external sources, verify the link works and the repo is accessible
