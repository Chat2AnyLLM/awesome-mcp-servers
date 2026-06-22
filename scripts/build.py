#!/usr/bin/env python3
"""Build unified dist/ artifacts from sources configured in config.yaml."""

import csv
import io
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml
from jsonschema import Draft202012Validator

# Increase CSV field size limit for large description texts.
csv.field_size_limit(10 * 1024 * 1024)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yaml"
SERVER_SCHEMA_PATH = REPO_ROOT / "schema" / "mcp-server.schema.json"
DIST_DIR = REPO_ROOT / "dist"
SCRAPED_DIR = REPO_ROOT / "scraped"

VERSION = "1.0.0"
DEFAULT_CATEGORY = "other"


def load_schema(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_config() -> dict:
    """Load config.yaml."""
    if not CONFIG_PATH.exists():
        print(f"FAIL: missing config file: {CONFIG_PATH}")
        sys.exit(1)

    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"FAIL: invalid config.yaml: {e}")
        sys.exit(1)

    if not isinstance(config, dict):
        print("FAIL: config.yaml must contain a mapping")
        sys.exit(1)
    if not isinstance(config.get("sources"), list):
        print("FAIL: config.yaml must contain a sources list")
        sys.exit(1)

    return config


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text[:80]


def fetch_url(url: str) -> str:
    """Fetch URL content as text. Returns an empty string on fetch errors."""
    req = Request(url, headers={"User-Agent": "awesome-mcp-servers-builder/1.0"})
    try:
        with urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except (URLError, OSError, TimeoutError) as e:
        print(f"    WARNING fetching {url}: {e}")
        return ""


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract (user, repo) from a GitHub URL."""
    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url)
    if match:
        return match.groups()
    return ("", "")


def get_default_branch(user: str, repo: str) -> str:
    """Get default branch via GitHub API."""
    api_url = f"https://api.github.com/repos/{user}/{repo}"
    content = fetch_url(api_url)
    if content:
        try:
            return json.loads(content).get("default_branch", "main")
        except json.JSONDecodeError:
            pass
    return "main"


def normalize_server(
    server: dict,
    source_name: str,
    defaults: dict | None = None,
) -> dict | None:
    """Normalize a server entry from any source into the unified dist shape."""
    if not isinstance(server, dict):
        return None

    if server.get("name") and server.get("installations"):
        normalized = dict(server)
        normalized.setdefault("display_name", normalized["name"])
        normalized.setdefault("slug", slugify(normalized["name"]))
        normalized.setdefault("title", normalized.get("display_name") or normalized["name"])
        repository = normalized.get("repository")
        if isinstance(repository, dict):
            normalized.setdefault("url", repository.get("url", ""))
        normalized.setdefault("url", normalized.get("homepage", ""))
        normalized.setdefault("category", first_category(normalized.get("categories")))
        normalized["source"] = source_name
        return normalized

    defaults = defaults or {}
    title = str(
        server.get("title")
        or server.get("name")
        or server.get("act")
        or defaults.get("title")
        or ""
    ).strip()
    description = str(
        server.get("description")
        or server.get("desc")
        or defaults.get("description")
        or ""
    ).strip()
    url = str(
        server.get("url")
        or server.get("homepage")
        or server.get("link")
        or ""
    ).strip()

    if not title or not description or len(description) < 10:
        return None

    slug = slugify(server.get("slug") or title)
    if not slug:
        return None

    tags = server.get("tags", defaults.get("tags", ["imported"]))
    if isinstance(tags, str):
        tags = [tag.strip() for tag in re.split(r"[,;]", tags) if tag.strip()]
    if not tags:
        tags = ["imported"]

    installations = normalize_installations(server)
    if not installations:
        return None

    normalized = {
        "name": slug,
        "display_name": title,
        "slug": slug,
        "title": title,
        "description": description,
        "url": url,
        "tags": tags,
        "category": str(
            server.get("category") or defaults.get("category") or DEFAULT_CATEGORY
        ).strip(),
        "author": str(
            server.get("author") or defaults.get("author") or source_name
        ).strip(),
        "installations": installations,
        "source": source_name,
    }

    for optional_field in ("npm", "docker", "license"):
        if optional_field in server:
            normalized[optional_field] = server[optional_field]

    return normalized


def first_category(categories: object) -> str:
    """Return the first usable CAM category or the default category."""
    if isinstance(categories, list) and categories:
        category = str(categories[0]).strip()
        if category:
            return category
    return DEFAULT_CATEGORY


def normalize_installations(server: dict) -> dict:
    """Build CAM-compatible installation entries from source metadata."""
    installations = server.get("installations")
    if isinstance(installations, dict) and installations:
        return installations

    npm = str(server.get("npm", "")).strip()
    if npm:
        return {"npm": {"type": "npm", "command": "npx", "args": ["-y", npm]}}

    docker = str(server.get("docker", "")).strip()
    if docker:
        return {"docker": {"type": "docker", "command": "docker", "args": ["run", "--rm", docker]}}

    return {}


def validate_server_file(file_path: Path, data: dict, schema: dict) -> None:
    """Validate a local server YAML file and fail the build if invalid."""
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(data))
    if errors:
        print(f"FAIL: {file_path.name}")
        for err in errors:
            print(f"  {err.json_path}: {err.message}")
        sys.exit(1)

    identifier = data.get("slug") or data.get("name")
    if data.get("slug") and identifier != file_path.stem:
        print(f"FAIL: {file_path.name} - identifier does not match filename")
        sys.exit(1)


def load_local_source(source: dict, server_schema: dict) -> list[dict]:
    """Load and validate servers from a local directory of YAML files."""
    source_name = source.get("name", "Local")
    path = Path(source.get("path", "servers/"))
    source_dir = path if path.is_absolute() else REPO_ROOT / path

    if not source_dir.exists():
        print(f"    WARNING: local path does not exist: {source_dir}")
        return []

    servers = []
    local_files = sorted(source_dir.rglob("*.yaml")) + sorted(source_dir.rglob("*.json"))
    for file_path in local_files:
        with open(file_path, encoding="utf-8") as f:
            if file_path.suffix == ".json":
                data = json.load(f)
            else:
                data = yaml.safe_load(f)
        if data is None:
            print(f"FAIL: {file_path.name} is empty")
            sys.exit(1)

        validate_server_file(file_path, data, server_schema)
        normalized = normalize_server(data, source_name)
        if normalized:
            servers.append(normalized)

    return servers


def servers_from_csv(content: str, source_name: str) -> list[dict]:
    servers = []
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        normalized = normalize_server(row, source_name)
        if normalized:
            servers.append(normalized)
    return servers


def servers_from_text_file(file_name: str, content: str, source_name: str) -> list[dict]:
    if not content or len(content.strip()) < 20:
        return []
    name = Path(file_name).stem
    normalized = normalize_server(
        {
            "slug": slugify(name),
            "title": name.replace("-", " ").replace("_", " ").title(),
            "description": content.strip()[:300],
        },
        source_name,
    )
    return [normalized] if normalized else []


def servers_from_yaml(content: str, file_name: str, source_name: str) -> list[dict]:
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return []

    items = data if isinstance(data, list) else [data]
    servers = []
    for item in items:
        defaults = {"title": Path(file_name).stem.replace("-", " ").title()}
        normalized = normalize_server(item, source_name, defaults)
        if normalized:
            servers.append(normalized)
    return servers


def servers_from_json(content: str, source_name: str) -> list[dict]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    items = data if isinstance(data, list) else data.get("servers", [])
    servers = []
    for item in items:
        normalized = normalize_server(item, source_name)
        if normalized:
            servers.append(normalized)
    return servers


def list_github_directory(user: str, repo: str, dir_path: str) -> list[dict]:
    encoded_dir = quote(dir_path or "", safe="/")
    api_url = f"https://api.github.com/repos/{user}/{repo}/contents/{encoded_dir}"
    content = fetch_url(api_url)
    if not content:
        return []
    try:
        items = json.loads(content)
    except json.JSONDecodeError:
        return []
    return items if isinstance(items, list) else []


def fetch_github_file(user: str, repo: str, branch: str, file_path: str) -> str:
    encoded_path = quote(file_path, safe="/")
    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{encoded_path}"
    return fetch_url(raw_url)


def scrape_github_text_files(
    user: str,
    repo: str,
    branch: str,
    file_path: str,
    fmt: str,
    source_name: str,
) -> list[dict]:
    extensions = (".txt",) if fmt == "txt" else (".md",)

    if file_path and any(file_path.lower().endswith(ext) for ext in extensions):
        content = fetch_github_file(user, repo, branch, file_path)
        return servers_from_text_file(file_path, content, source_name)

    skip_files = {
        "readme.md",
        "readme.txt",
        "license.md",
        "contributing.md",
        "changelog.md",
        "code_of_conduct.md",
    }
    items = list_github_directory(user, repo, file_path or "")
    matching_files = [
        item
        for item in items
        if isinstance(item, dict)
        and any(item.get("name", "").lower().endswith(ext) for ext in extensions)
        and item.get("name", "").lower() not in skip_files
    ]

    servers = []
    for item in matching_files[:500]:
        path = item.get("path", item.get("name", ""))
        content = fetch_github_file(user, repo, branch, path)
        servers.extend(servers_from_text_file(path, content, source_name))
    return servers


def scrape_github_yaml_files(
    user: str,
    repo: str,
    branch: str,
    file_path: str,
    source_name: str,
) -> list[dict]:
    if file_path and file_path.lower().endswith((".yaml", ".yml")):
        content = fetch_github_file(user, repo, branch, file_path)
        return servers_from_yaml(content, file_path, source_name)

    items = list_github_directory(user, repo, file_path or "")
    yaml_files = [
        item
        for item in items
        if isinstance(item, dict)
        and item.get("name", "").lower().endswith((".yaml", ".yml"))
    ]

    servers = []
    for item in yaml_files[:100]:
        path = item.get("path", item.get("name", ""))
        content = fetch_github_file(user, repo, branch, path)
        servers.extend(servers_from_yaml(content, path, source_name))
    return servers


def scrape_github_json_file(
    user: str,
    repo: str,
    branch: str,
    file_path: str,
    source_name: str,
) -> list[dict]:
    if not file_path:
        return []
    content = fetch_github_file(user, repo, branch, file_path)
    return servers_from_json(content, source_name)


def save_scraped_servers(source_name: str, servers: list[dict]) -> int:
    """Cache scraped servers in scraped/<source-slug>/ as YAML files."""
    source_slug = slugify(source_name)
    output_dir = SCRAPED_DIR / source_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    for file_path in output_dir.glob("*.yaml"):
        file_path.unlink()

    saved = 0
    seen_slugs = set()
    for server in servers:
        slug = server.get("slug") or server.get("name", "")
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        out_file = output_dir / f"{slug}.yaml"
        with open(out_file, "w", encoding="utf-8") as f:
            yaml.dump(server, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        saved += 1

    return saved


def load_github_source(source: dict) -> list[dict]:
    """Load servers by scraping a configured GitHub repo source."""
    source_name = source.get("name", "GitHub Source")
    url = source.get("url", "")
    fmt = source.get("format", "")
    file_path = source.get("file_path", "") or ""

    user, repo = parse_github_url(url)
    if not user or not repo:
        print(f"    WARNING: cannot parse GitHub URL: {url}")
        return []

    branch = get_default_branch(user, repo)
    print(f"    Repo: {user}/{repo} (branch: {branch}, format: {fmt})")

    if fmt == "csv":
        content = fetch_github_file(user, repo, branch, file_path or "servers.csv")
        servers = servers_from_csv(content, source_name)
    elif fmt in ("md", "txt"):
        servers = scrape_github_text_files(user, repo, branch, file_path, fmt, source_name)
    elif fmt in ("yaml", "yml"):
        servers = scrape_github_yaml_files(user, repo, branch, file_path, source_name)
    elif fmt == "json":
        servers = scrape_github_json_file(user, repo, branch, file_path, source_name)
    else:
        print(f"    WARNING: unsupported GitHub source format: {fmt}")
        return []

    saved = save_scraped_servers(source_name, servers)
    print(f"    Cached: {saved} servers")
    return servers


def load_json_url_source(source: dict) -> list[dict]:
    """Load servers from a remote JSON URL."""
    source_name = source.get("name", "JSON URL Source")
    url = source.get("url", "")
    if not url:
        print("    WARNING: json_url source missing url")
        return []

    content = fetch_url(url)
    if not content:
        return []
    return servers_from_json(content, source_name)


def load_source(source: dict, server_schema: dict) -> list[dict]:
    """Dispatch a configured source to its loader."""
    source_type = source.get("type")
    if source_type == "local":
        return load_local_source(source, server_schema)
    if source_type == "github":
        return load_github_source(source)
    if source_type == "json_url":
        return load_json_url_source(source)

    print(f"    WARNING: unsupported source type: {source_type}")
    return []


def dedupe_servers(servers: list[dict]) -> list[dict]:
    """Deduplicate servers by slug. First source in config wins."""
    deduped = []
    seen_slugs = set()
    for server in servers:
        slug = server.get("slug") or server.get("name")
        if not slug or slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        deduped.append(server)
    return deduped


def write_servers_json(servers: list[dict], output_dir: Path) -> None:
    """Write unified dist/servers.json."""
    output = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(servers),
        "servers": servers,
    }
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "servers.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  Written: {output_path} ({len(servers)} servers)")


def write_servers_csv(servers: list[dict], output_dir: Path) -> None:
    """Write unified dist/servers.csv."""
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "servers.csv"
    fieldnames = [
        "slug",
        "title",
        "description",
        "url",
        "tags",
        "category",
        "author",
        "source",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        for server in servers:
            row = {k: server.get(k, "") for k in fieldnames if k != "tags"}
            row["tags"] = ";".join(server.get("tags", []))
            writer.writerow(row)
    print(f"  Written: {output_path} ({len(servers)} servers)")


def write_sources_json(sources: list[dict], output_dir: Path) -> None:
    """Write dist/sources.json."""
    output = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": len(sources),
        "sources": sources,
    }
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "sources.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  Written: {output_path}")


def write_index_json(servers: list[dict], sources: list[dict], output_dir: Path) -> None:
    """Write dist/index.json — a single entry point for consumers."""
    output = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "servers": {
            "count": len(servers),
            "file": "servers.json",
        },
        "sources": {
            "count": len(sources),
            "file": "sources.json",
        },
    }
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "index.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  Written: {output_path}")


def main() -> int:
    print("Building unified MCP server collection...")

    config = load_config()
    server_schema = load_schema(SERVER_SCHEMA_PATH)
    sources = config.get("sources", [])
    output_dir = REPO_ROOT / config.get("output", {}).get("dir", "dist")

    all_servers = []
    source_summaries = []
    for source in sources:
        name = source.get("name", "unknown")
        print(f"  [{name}]")
        servers = load_source(source, server_schema)
        print(f"    Loaded: {len(servers)} servers\n")
        all_servers.extend(servers)
        source_summary = dict(source)
        source_summary["count"] = len(servers)
        source_summaries.append(source_summary)

    servers = dedupe_servers(all_servers)
    skipped = len(all_servers) - len(servers)
    if skipped:
        print(f"Deduplicated: skipped {skipped} duplicate server(s)")

    write_servers_json(servers, output_dir)
    write_servers_csv(servers, output_dir)
    write_sources_json(source_summaries, output_dir)
    write_index_json(servers, source_summaries, output_dir)

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
