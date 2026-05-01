#!/usr/bin/env python3
"""
Stop hook for agent-twin: silently captures the ending Claude Code session
and saves extracted turns to personalized/saves/session/<date>_<session-id[:12]>/.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically: write to <path>.tmp, then os.replace to final.

    os.replace is atomic on POSIX and atomic-ish on Windows NTFS for same-volume
    renames. A killed process (Stop hook timeout, OS shutdown, disk full) can no
    longer leave a half-written JSON file at the final path; the worst case is a
    leftover .tmp sibling that subsequent runs will overwrite.
    """
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding=encoding)
    os.replace(tmp, path)


def extract_text_from_content(content):
    if isinstance(content, list):
        return " ".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    return str(content) if content else ""


DATA_ROOT = Path.home() / ".claude" / "agent-twin"


def ensure_data_dirs():
    (DATA_ROOT / "personalized" / "saves" / "session").mkdir(parents=True, exist_ok=True)
    (DATA_ROOT / "personalized" / "results" / "profile").mkdir(parents=True, exist_ok=True)


def main():
    ensure_data_dirs()

    try:
        raw_stdin = sys.stdin.read()
        data = json.loads(raw_stdin)
        session_id = data.get("session_id", "")
    except Exception:
        return

    if not session_id:
        return

    # Find the JSONL file across all project dirs under ~/.claude/projects/
    claude_projects = Path.home() / ".claude" / "projects"

    # Guard against fresh installs / first-ever Stop hook fire: if Claude Code
    # has not yet created ~/.claude/projects/ (or it is somehow not a directory),
    # there is nothing to scan — no-op cleanly instead of crashing on iterdir().
    if not claude_projects.exists() or not claude_projects.is_dir():
        return

    jsonl_file = None
    for project_dir in claude_projects.iterdir():
        if project_dir.is_dir():
            candidate = project_dir / f"{session_id}.jsonl"
            if candidate.exists():
                jsonl_file = candidate
                break

    if not jsonl_file:
        return

    saves_base = DATA_ROOT / "personalized" / "saves" / "session"
    session_prefix = session_id[:12]

    # Reuse the existing directory for this session if one exists (handles cross-day sessions).
    # Directory names follow the pattern <date>_<session-prefix>.
    save_dir = None
    if saves_base.exists():
        for d in saves_base.iterdir():
            if d.is_dir() and d.name.endswith(f"_{session_prefix}"):
                save_dir = d
                break

    if save_dir is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        save_dir = saves_base / f"{date_str}_{session_prefix}"

    save_dir.mkdir(parents=True, exist_ok=True)

    # Parse JSONL into (user, model) turn pairs
    turns = []
    order = 0
    pending_user = None
    assistant_chunks = []

    def flush():
        nonlocal order, pending_user, assistant_chunks
        if pending_user is not None:
            turns.append({
                "order": order,
                "user": pending_user,
                "model": " ".join(assistant_chunks).strip(),
            })
            order += 1
        pending_user = None
        assistant_chunks = []

    try:
        raw = jsonl_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        return

    for line in raw:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue

        # Claude Code JSONL: events have a "type" field ("user" | "assistant" | ...)
        # and a "message" object containing role + content.
        msg = event.get("message", {})
        role = msg.get("role") or event.get("type", "")

        if role == "user":
            flush()
            pending_user = extract_text_from_content(
                msg.get("content") or event.get("content", "")
            )
            assistant_chunks = []
        elif role == "assistant":
            text = extract_text_from_content(
                msg.get("content") or event.get("content", "")
            )
            if text:
                assistant_chunks.append(text)

    flush()

    if not turns:
        return

    out = save_dir / "conversation.json"
    atomic_write_text(out, json.dumps(turns, ensure_ascii=False, indent=2))

    meta = {
        "session_id": session_id,
        "turn_count": len(turns),
        "saved_at": datetime.now().isoformat(),
    }
    atomic_write_text(
        save_dir / "session_meta.json",
        json.dumps(meta, ensure_ascii=False, indent=2),
    )


if __name__ == "__main__":
    main()
