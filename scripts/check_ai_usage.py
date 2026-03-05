#!/usr/bin/env python3
"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_command(args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 127, "", "not installed"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def summarize_cli_error(raw: str, fallback: str) -> str:
    text = (raw or "").strip()
    if not text:
        return fallback

    if "Unexpected token '??='" in text:
        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."

    if "Missing optional dependency @openai/codex-" in text:
        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
        dep = match.group(1) if match else "@openai/codex-<platform>"
        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
            return line[:220]
    return lines[0][:220]


def format_epoch(value: Any) -> str:
    try:
        if value is None:
            return "n/a"
        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return "n/a"


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "n/a"


def newest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = list(root.rglob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
    if not root.exists():
        return []
    files = list(root.rglob(pattern))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def check_claude() -> list[str]:
    lines = ["[Claude Code]"]
    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "auth status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        try:
            data = json.loads(stdout)
            logged = "yes" if data.get("loggedIn") else "no"
            subscription = data.get("subscriptionType", "n/a")
            org_name = data.get("orgName", "n/a")
            lines.append(f"- Logged in: {logged}")
            lines.append(f"- Subscription: {subscription}")
            lines.append(f"- Org: {org_name}")
        except json.JSONDecodeError:
            lines.append("- CLI auth output could not be parsed")

    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
    if not candidate_files:
        lines.append("- Local usage event: not found")
    else:
        latest_usage: dict[str, Any] | None = None
        latest_model = "n/a"
        latest_ts: datetime | None = None
        latest_ts_raw = "n/a"
        for latest_jsonl in candidate_files:
            try:
                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                    for raw in handle:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            item = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        message = item.get("message")
                        if not isinstance(message, dict):
                            continue
                        usage = message.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        ts_raw = item.get("timestamp")
                        ts = parse_iso(ts_raw)
                        if latest_ts is None or (ts and ts >= latest_ts):
                            latest_ts = ts or latest_ts
                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
                            latest_usage = usage
                            latest_model = str(message.get("model", "n/a"))
            except OSError:
                continue

        if not latest_usage:
            lines.append("- Local usage event: not found")
        else:
            in_tokens = (
                int(latest_usage.get("input_tokens", 0))
                + int(latest_usage.get("cache_creation_input_tokens", 0))
                + int(latest_usage.get("cache_read_input_tokens", 0))
            )
            out_tokens = int(latest_usage.get("output_tokens", 0))
            lines.append(f"- Latest local model: {latest_model}")
            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
            lines.append(f"- Latest local event time: {latest_ts_raw}")

    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
    return lines


def check_codex() -> list[str]:
    lines = ["[GPT-Codex]"]
    code, stdout, stderr = run_command(["codex", "login", "status"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "login status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        status_text = stdout or stderr or "available"
        lines.append(f"- Login status: {status_text}")

    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
    if latest_jsonl is None:
        lines.append("- Local rate-limit snapshot: not found")
    else:
        latest_rate: dict[str, Any] | None = None
        latest_usage: dict[str, Any] | None = None
        latest_ts = "n/a"
        try:
            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if item.get("type") != "event_msg":
                        continue
                    payload = item.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue
                    rate = payload.get("rate_limits")
                    info = payload.get("info") or {}
                    usage = info.get("total_token_usage")
                    if isinstance(rate, dict):
                        latest_rate = rate
                        latest_usage = usage if isinstance(usage, dict) else None
                        latest_ts = str(item.get("timestamp", "n/a"))
        except OSError:
            latest_rate = None

        if not latest_rate:
            lines.append("- Local rate-limit snapshot: not found")
        else:
            primary = latest_rate.get("primary", {})
            secondary = latest_rate.get("secondary", {})
            lines.append(
                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
            )
            lines.append(
                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
            )
            if latest_usage:
                total = latest_usage.get("total_tokens")
                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
            lines.append(f"- Snapshot time: {latest_ts}")

    lines.append("- API dashboard: https://platform.openai.com/usage")
    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
    return lines


def check_gemini() -> list[str]:
    lines = ["[Gemini CLI]"]
    code, stdout, stderr = run_command(["gemini", "--version"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "version check failed")
        lines.append(f"- CLI check failed: {err}")
    else:
        lines.append(f"- CLI version: {stdout}")

    has_env_auth = any(
        os.getenv(key)
        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
    )
    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")

    prompt_count = 0
    latest_prompt_ts: datetime | None = None
    latest_prompt_raw = "n/a"
    tmp_root = Path.home() / ".gemini" / "tmp"
    if tmp_root.exists():
        for log_file in tmp_root.rglob("logs.json"):
            try:
                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, list):
                continue
            for row in data:
                if not isinstance(row, dict) or row.get("type") != "user":
                    continue
                prompt_count += 1
                ts_raw = row.get("timestamp")
                ts = parse_iso(ts_raw)
                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
                    latest_prompt_ts = ts
                    latest_prompt_raw = str(ts_raw)
    lines.append(f"- Local prompts recorded: {prompt_count}")
    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
    lines.append("- Dashboard: https://aistudio.google.com/")
    return lines


def open_dashboards() -> None:
    urls = [
        "https://console.anthropic.com/settings/usage",
        "https://platform.openai.com/usage",
        "https://chatgpt.com/",
        "https://aistudio.google.com/",
    ]
    opener = None
    if sys.platform == "darwin":
        opener = "open"
    elif sys.platform.startswith("linux"):
        opener = "xdg-open"
    if not opener:
        return
    for url in urls:
        subprocess.run([opener, url], check=False, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
    parser.add_argument(
        "--open-dashboards",
        action="store_true",
        help="Open provider usage dashboards in your browser.",
    )
    args = parser.parse_args()

    print("AI usage snapshot (local + dashboard links)")
    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("Note: provider billing dashboards remain the source of truth.\n")

    for section in (check_claude(), check_codex(), check_gemini()):
        for line in section:
            print(line)
        print()

    if args.open_dashboards:
        open_dashboards()
        print("Opened dashboards in browser.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
