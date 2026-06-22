#!/usr/bin/env python3
"""Update README.md with current server stats and scraped server listing."""

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
README_PATH = REPO_ROOT / "README.md"
CONFIG_PATH = REPO_ROOT / "config.yaml"
DIST_DIR = REPO_ROOT / "dist"
SCRAPED_DIR = REPO_ROOT / "scraped"

# Max servers to show per source in the table
MAX_PER_SOURCE = 30


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')[:80]


def count_scraped() -> dict[str, int]:
    """Count scraped servers per source."""
    counts = {}
    if not SCRAPED_DIR.exists():
        return counts
    for source_dir in sorted(SCRAPED_DIR.iterdir()):
        if source_dir.is_dir():
            count = len(list(source_dir.glob("*.yaml")))
            if count > 0:
                counts[source_dir.name] = count
    return counts


def load_config_sources() -> list[dict]:
    """Load sources from config.yaml."""
    if not CONFIG_PATH.exists():
        return []
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("sources", [])


def abbreviate(text: str, max_len: int = 60) -> str:
    """Truncate text and add ellipsis."""
    text = text.replace("\n", " ").replace("|", "/").strip()
    if len(text) > max_len:
        return text[:max_len - 1] + "…"
    return text


def generate_stats_section() -> str:
    """Generate the Stats section with source tables."""
    servers_json = DIST_DIR / "servers.json"
    servers_count = 0
    direct_count = 0
    if servers_json.exists():
        with open(servers_json, encoding="utf-8") as f:
            data = json.load(f)
        servers_count = data.get("count", 0)
        direct_count = sum(
            1
            for server in data.get("servers", [])
            if server.get("source") == "Local Servers"
        )

    sources = load_config_sources()
    scraped = count_scraped()
    total_scraped = sum(scraped.values())

    lines = [
        "## Stats",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| Unified servers (in `dist/servers.json`) | {servers_count} |",
        f"| Direct servers (from `servers/`) | {direct_count} |",
        f"| Configured sources | {len(sources)} |",
        f"| Scraped servers cached in `scraped/` | {total_scraped} |",
        "",
    ]

    if sources:
        lines.append("### Configured Sources")
        lines.append("")
        lines.append("| Source | Type | Location | Format | Loaded |")
        lines.append("|--------|------|----------|--------|--------|")
        for s in sources:
            name = s.get("name", "?")
            source_type = s.get("type", "?")
            location = s.get("url") or s.get("path", "")
            fmt = s.get("format", "-")
            slug = slugify(name)
            count = scraped.get(slug, 0)
            if source_type == "local":
                count = direct_count
            location_cell = f"[{location}]({location})" if str(location).startswith("http") else f"`{location}`"
            lines.append(f"| {name} | {source_type} | {location_cell} | {fmt} | {count} |")
        lines.append("")

    # Generate per-source server tables
    if SCRAPED_DIR.exists():
        lines.append("### Scraped Servers")
        lines.append("")
        for source_dir in sorted(SCRAPED_DIR.iterdir()):
            if not source_dir.is_dir():
                continue
            yaml_files = sorted(source_dir.glob("*.yaml"))
            if not yaml_files:
                continue

            source_name = source_dir.name.replace("-", " ").title()
            lines.append(f"<details>")
            lines.append(f"<summary><strong>{source_name}</strong> ({len(yaml_files)} servers)</summary>")
            lines.append("")
            lines.append("| # | Title | Description |")
            lines.append("|---|-------|-------------|")

            for i, yf in enumerate(yaml_files[:MAX_PER_SOURCE], 1):
                try:
                    data = yaml.safe_load(yf.read_text())
                    title = abbreviate(data.get("title", yf.stem), 40)
                    desc = abbreviate(data.get("description", ""), 60)
                    lines.append(f"| {i} | {title} | {desc} |")
                except Exception:
                    continue

            if len(yaml_files) > MAX_PER_SOURCE:
                lines.append(f"| … | *+{len(yaml_files) - MAX_PER_SOURCE} more* | See `scraped/{source_dir.name}/` |")

            lines.append("")
            lines.append("</details>")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    stats_section = generate_stats_section()

    readme_content = README_PATH.read_text(encoding="utf-8")

    # Replace existing Stats section or insert before License
    stats_pattern = r'## Stats\n.*?(?=\n## [^SC]|\Z)'
    if re.search(stats_pattern, readme_content, re.DOTALL):
        readme_content = re.sub(stats_pattern, stats_section.rstrip(), readme_content, flags=re.DOTALL)
    else:
        license_match = re.search(r'\n## License', readme_content)
        if license_match:
            insert_pos = license_match.start()
            readme_content = readme_content[:insert_pos] + "\n" + stats_section + "\n" + readme_content[insert_pos:]
        else:
            readme_content += "\n" + stats_section

    README_PATH.write_text(readme_content, encoding="utf-8")
    print("README.md updated with current stats.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
