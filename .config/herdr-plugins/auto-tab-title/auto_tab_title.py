#!/usr/bin/env python3
"""Herdr plugin: name default tabs after the agent's task.

Modes (argv[1]):
  pane          handle the pane from HERDR_PLUGIN_EVENT_JSON / HERDR_PANE_ID
  pane-moved    renumber, then handle the moved pane in its new tab
  tabs-changed  renumber owned tabs, release dead owners
  prune         startup: reset volatile state, renumber, re-report all panes
  all           debug: handle every agent pane

Ownership invariant: a tab is renamed only if its label is all digits
(herdr's default) or exactly the label this plugin last wrote. Anything
else is a manual name and is never touched.

Stdlib only; run with `uv run --no-project`.
"""

from __future__ import annotations

import contextlib
import fcntl
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass

WJ = "⁠"  # word joiner: invisible marker the sidebar rule hides on
SEP = WJ + "·"

DEFAULTS = {
    "agents": ["claude", "codex"],
    # agents whose transcripts we can read to generate a title
    "generate_agents": ["claude"],
    "max_width": 40,
    "title_source": "claude",  # claude | prompt | off
    "claude_command": ["claude"],
    "claude_model": "haiku",
    "generate_timeout": 45,
    "metadata_token": "task",
}

GENERATED_CAP = 500
PENDING_TTL = 120
MAX_ATTEMPTS = 3
HERDR_TIMEOUT = 10

PLACEHOLDERS = {"claude code", "claude", "codex", "openai codex"}
GENERIC = {
    "main", "master", "zsh", "bash", "fish", "sh", "shell", "~", "terminal",
    "node", "python", "python3", "uv", "nvim", "vim", "login", "new chat",
    "untitled", "new session", "-",
}
BUILTIN_COMMANDS = {
    "add-dir", "agents", "bashes", "bug", "clear", "compact", "config",
    "context", "cost", "doctor", "effort", "exit", "export", "fast",
    "feedback", "help", "hooks", "ide", "init", "install-github-app",
    "login", "logout", "mcp", "memory", "model", "output-style",
    "permissions", "plan", "plugin", "plugins", "pr-comments", "privacy-settings",
    "quit", "release-notes", "rename", "resume", "review", "rewind",
    "sandbox", "security-review", "status", "statusline", "terminal-setup",
    "theme", "todos", "upgrade", "usage", "vim", "btw", "loop", "tasks",
}
NOISE_PREFIXES = (
    "<system-reminder>", "<local-command-", "<bash-", "<task-notification>",
    "[Request interrupted", "Caveat:", "<user-prompt-submit-hook>",
)
STRIP_ENV_PREFIXES = ("HERDR_", "CLAUDE_CODE_MESSAGING_")
STRIP_ENV = {
    "CLAUDECODE", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_PLUGIN_DIRS", "CLAUDE_CODE_ENTRYPOINT",
}


def log(msg: str) -> None:
    print(f"auto-tab-title: {msg}", file=sys.stderr)


# --------------------------------------------------------------------------
# Config


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    cdir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if not cdir:
        return cfg
    path = os.path.join(cdir, "config.toml")
    try:
        import tomllib

        with open(path, "rb") as f:
            user = tomllib.load(f)
    except FileNotFoundError:
        return cfg
    except Exception as e:  # bad toml / old python: keep defaults
        log(f"config ignored: {e}")
        return cfg
    for k, v in user.items():
        if k in cfg:
            cfg[k] = v
    for k in ("agents", "generate_agents"):
        if isinstance(cfg[k], str):
            cfg[k] = [cfg[k]]
    if isinstance(cfg["claude_command"], str):
        cfg["claude_command"] = [cfg["claude_command"]]
    return cfg


# --------------------------------------------------------------------------
# Pure text helpers


def char_width(ch: str) -> int:
    if ch == WJ or unicodedata.combining(ch):
        return 0
    if unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(s: str) -> int:
    return sum(char_width(c) for c in s)


def truncate(s: str, width: int) -> str:
    if display_width(s) <= width:
        return s
    out, w = [], 0
    for ch in s:
        cw = char_width(ch)
        if w + cw > width - 1:
            break
        out.append(ch)
        w += cw
    return "".join(out).rstrip() + "…"


_QUOTES = "\"'`“”‘’"
_TRAIL = ".,:;!?…-–— "


def normalize_title(raw: str | None, width: int = 40) -> str:
    if not raw:
        return ""
    s = "".join(
        " " if unicodedata.category(c) in ("Cc", "Zl", "Zp") else c
        for c in raw
        if unicodedata.category(c) != "Cf"
    )
    s = re.sub(r"\s+", " ", s).strip()
    # leading status glyphs (spinners, ✳ etc.)
    i = 0
    while i < len(s) and (s[i] == " " or unicodedata.category(s[i]).startswith("S")):
        i += 1
    s = s[i:]
    s = s.strip(_QUOTES + " ")
    s = re.sub(r"^title\s*:\s*", "", s, flags=re.I)
    s = s.strip(_QUOTES + " ").rstrip(_TRAIL).strip(_QUOTES + " ")
    return truncate(s, width) if s else ""


_PATH_RE = re.compile(r"^(~|\.{1,2})?/?[\w.\-~+@]*(/[\w.\-~+@]*)+/?$|^~$")
_USERHOST_RE = re.compile(r"^[\w.\-]+@[\w.\-]+(:|$)")


def agent_title(raw: str | None, agent: str | None) -> str | None:
    """Agent-specific cleanup before normalize_title."""
    if raw and agent == "codex":
        # Codex: "<task> | <dir>"
        raw = re.sub(r"\s+\|\s+[^|]*$", "", raw)
    return raw


def is_meaningful(title: str, cwd: str | None = None, ws_label: str | None = None) -> bool:
    if not title:
        return False
    low = title.lower().rstrip("…").strip()
    if not low or low in PLACEHOLDERS or low in GENERIC:
        return False
    if low.isdigit():
        return False
    if _PATH_RE.match(title) or _USERHOST_RE.match(title):
        return False
    if cwd:
        base = os.path.basename(cwd.rstrip("/"))
        if base and low == base.lower():
            return False
    if ws_label and low == ws_label.strip().lower():
        return False
    return True


def compose(pos: int, title: str | None) -> str:
    return f"{pos}{SEP}{title}" if title else str(pos)


def owns_label(label: str, tab_state: dict | None) -> bool:
    if label.isdigit():
        return True
    return bool(tab_state) and label == tab_state.get("label")


# --------------------------------------------------------------------------
# Prompt extraction / title generation


def _text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if not isinstance(item, dict):
                continue
            kind = item.get("type")
            if kind == "text":
                parts.append(item.get("text") or "")
            elif kind == "tool_result":
                return ""  # tool output, not a prompt
            # images/documents: ignore, keep the accompanying text
        return "\n".join(parts)
    return ""


_CMD_RE = re.compile(r"<command-name>\s*/?([^<\s]+)\s*</command-name>")
_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)


def prompt_from_text(text: str) -> str | None:
    text = text.strip()
    if not text:
        return None
    m = _CMD_RE.search(text)
    if m:
        cmd = m.group(1)
        a = _ARGS_RE.search(text)
        args = a.group(1).strip() if a else ""
        if cmd in BUILTIN_COMMANDS or not args:
            return None
        return f"/{cmd} {args}"
    if text.startswith(NOISE_PREFIXES):
        return None
    text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text, flags=re.S)
    text = re.sub(r"\[Image #\d+\]", "", text).strip()
    return text or None


def extract_prompt(records) -> str | None:
    for rec in records:
        if not isinstance(rec, dict) or rec.get("type") != "user":
            continue
        if rec.get("isMeta") or rec.get("isSidechain") or rec.get("isCompactSummary"):
            continue
        msg = rec.get("message") or {}
        p = prompt_from_text(_text_of(msg.get("content")))
        if p:
            return p
    return None


_SESSION_RE = re.compile(r"^[\w-]+$")


def transcript_path(session: str) -> str | None:
    if not session or not _SESSION_RE.match(session):
        return None
    base = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    hits = glob.glob(os.path.join(base, "projects", "*", f"{session}.jsonl"))
    if not hits:
        return None
    return max(hits, key=lambda p: os.path.getmtime(p))


def _iter_jsonl(path: str, limit: int = 5000):
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= limit:
                return
            try:
                yield json.loads(line)
            except ValueError:
                continue


def read_first_prompt(session: str) -> str | None:
    path = transcript_path(session)
    if not path:
        return None
    try:
        return extract_prompt(_iter_jsonl(path))
    except OSError:
        return None


_GH_RE = re.compile(r"https?://github\.com/[^/\s]+/([^/\s]+)/(?:issues|pull)/(\d+)\S*")


def heuristic_title(prompt: str, width: int = 40) -> str:
    line = next((ln for ln in prompt.splitlines() if ln.strip()), "")
    line = _GH_RE.sub(r"\1#\2", line)
    line = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", line)  # md links
    line = re.sub(r"^\s*(#+|>|[-*+]|\d+[.)])\s+", "", line)
    line = re.sub(r"[*_`~]+", "", line)
    words = line.split()[:6]
    s = " ".join(words)
    if s:
        s = s[0].upper() + s[1:]
    return normalize_title(s, width)


def clean_generated(stdout: str, width: int = 40) -> str | None:
    lines = [ln for ln in (stdout or "").splitlines() if ln.strip()]
    if not lines:
        return None
    t = normalize_title(lines[-1], 10_000)
    if not t or len(t.split()) > 8 or display_width(t) > width:
        return None
    return t if is_meaningful(t) else None


def child_env() -> dict:
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(STRIP_ENV_PREFIXES) and k not in STRIP_ENV
    }


def title_request(prompt: str) -> str:
    return (
        "Write a 2-5 word title (sentence case, no quotes, no trailing "
        "punctuation) naming the task in the request below. Reply with the "
        "title only.\n\n"
        f"<request>{prompt[:2000]}</request>"
    )


def resolve_cmd(cmd: list[str]) -> list[str]:
    exe = cmd[0]
    if os.sep not in exe and not shutil.which(exe):
        local = os.path.expanduser(f"~/.local/bin/{exe}")
        if os.access(local, os.X_OK):
            return [local, *cmd[1:]]
    return cmd


def generate_title(prompt: str, cfg: dict) -> tuple[str | None, bool]:
    """Return (title, retry). retry=True means heuristic fallback."""
    width = int(cfg["max_width"])
    if cfg["title_source"] == "claude":
        cmd = resolve_cmd(list(cfg["claude_command"])) + [
            "-p", "--model", str(cfg["claude_model"]),
            "--no-session-persistence", "--strict-mcp-config",
            "--disable-slash-commands", "--setting-sources", "",
            "--tools", "",
        ]  # prompt via stdin: variadic --tools would swallow a positional
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = subprocess.run(
                    cmd, cwd=tmp, env=child_env(), capture_output=True,
                    text=True, timeout=int(cfg["generate_timeout"]),
                    input=title_request(prompt),
                )
            if p.returncode == 0:
                t = clean_generated(p.stdout, width)
                if t:
                    return t, False
            else:
                log(f"claude exited {p.returncode}: {p.stderr.strip()[-200:]}")
        except (OSError, subprocess.TimeoutExpired) as e:
            log(f"claude failed: {e}")
        h = heuristic_title(prompt, width)
        return (h or None), True
    if cfg["title_source"] == "prompt":
        return (heuristic_title(prompt, width) or None), False
    return None, False


# --------------------------------------------------------------------------
# Herdr CLI


class HerdrError(Exception):
    def __init__(self, code: str, message: str = ""):
        super().__init__(f"{code}: {message}")
        self.code = code

    @property
    def not_found(self) -> bool:
        return self.code.endswith("not_found")


def _parse_json(text: str | None):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        # tolerate a trailing JSON line after other output
        try:
            return json.loads(text.splitlines()[-1])
        except ValueError:
            return None


def herdr(*args: str) -> dict:
    exe = os.environ.get("HERDR_BIN_PATH") or "herdr"
    try:
        p = subprocess.run(
            [exe, *args], capture_output=True, text=True, timeout=HERDR_TIMEOUT,
            stdin=subprocess.DEVNULL,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise HerdrError("unavailable", str(e)) from e
    data = _parse_json(p.stdout)
    # herdr prints error JSON on stderr (stdout checked too, to be safe)
    for d in (data, _parse_json(p.stderr)):
        if isinstance(d, dict) and d.get("error"):
            err = d["error"] if isinstance(d["error"], dict) else {}
            raise HerdrError(str(err.get("code") or "error"), str(err.get("message") or ""))
    if p.returncode != 0:
        raise HerdrError("failed", p.stderr.strip()[-200:])
    if isinstance(data, dict):
        return data.get("result") or {}
    return {}


def get_pane(pane_id: str) -> dict | None:
    """None = gone. Raises HerdrError when herdr couldn't answer."""
    try:
        return herdr("pane", "get", pane_id).get("pane")
    except HerdrError as e:
        if e.not_found:
            return None
        raise


def list_tabs(workspace: str | None = None) -> list[dict]:
    args = ["tab", "list"] + (["--workspace", workspace] if workspace else [])
    return herdr(*args).get("tabs") or []


def list_panes() -> list[dict]:
    return herdr("pane", "list").get("panes") or []


def workspace_label(ws: str) -> str | None:
    try:
        return (herdr("workspace", "get", ws).get("workspace") or {}).get("label")
    except HerdrError:
        return None


def rename_tab(tab_id: str, label: str) -> None:
    herdr("tab", "rename", tab_id, label)


def rename_if_label(tab_id: str, ws: str | None, expected: str, label: str) -> bool:
    """Rename only if the tab still carries `expected`.

    Herdr has no compare-and-set rename; re-reading right before renaming
    shrinks the window in which a manual rename could be overwritten.
    Returns False if the label changed under us (treat as manual).
    """
    _pos, current = position(list_tabs(ws), tab_id)
    if current is None or current != expected:
        return False
    rename_tab(tab_id, label)
    return True


def report_token(pane_id: str, name: str, value: str | None) -> None:
    source = os.environ.get("HERDR_PLUGIN_ID") or "lkk.auto-tab-title"
    if value:
        herdr("pane", "report-metadata", pane_id, "--source", source, "--token", f"{name}={value}")
    else:
        herdr("pane", "report-metadata", pane_id, "--source", source, "--clear-token", name)


def session_of(pane: dict) -> str | None:
    return (pane.get("agent_session") or {}).get("value") or None


def position(tabs: list[dict], tab_id: str) -> tuple[int | None, str | None]:
    for i, t in enumerate(tabs):
        if t.get("tab_id") == tab_id:
            return i + 1, str(t.get("label") or "")
    return None, None


# --------------------------------------------------------------------------
# State


def state_dir() -> str:
    d = os.environ.get("HERDR_PLUGIN_STATE_DIR") or os.path.join(
        tempfile.gettempdir(), "herdr-auto-tab-title"
    )
    os.makedirs(d, exist_ok=True)
    return d


def empty_state() -> dict:
    # stale: {pane_id: {session, title}} previous session's title, ignored
    # while still on the terminal so /clear can't restore the old task.
    return {"tabs": {}, "generated": {}, "pending": {}, "reported": {}, "stale": {}}


@contextlib.contextmanager
def locked_state():
    d = state_dir()
    path = os.path.join(d, "state.json")
    with open(os.path.join(d, "state.lock"), "a+") as lockf:
        fcntl.flock(lockf, fcntl.LOCK_EX)
        try:
            st = empty_state()
            try:
                with open(path, encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    for k in st:
                        if isinstance(loaded.get(k), dict):
                            st[k] = loaded[k]
            except (OSError, ValueError):
                pass
            try:
                yield st
            finally:
                # Save even on error: state must match renames already done,
                # or our own label would later look like a manual name.
                cap_generated(st)
                fd, tmp = tempfile.mkstemp(dir=d, prefix=".state.", suffix=".json")
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(st, f, indent=1, ensure_ascii=False)
                os.replace(tmp, path)
        finally:
            fcntl.flock(lockf, fcntl.LOCK_UN)


def cap_generated(st: dict) -> None:
    gen = st["generated"]
    if len(gen) > GENERATED_CAP:
        for k in sorted(gen, key=lambda k: gen[k].get("ts", 0))[: len(gen) - GENERATED_CAP]:
            del gen[k]


def reported_entry(st: dict, pane_id: str) -> dict | None:
    v = st["reported"].get(pane_id)
    if v is None:
        return None
    if isinstance(v, str):  # legacy: plain title
        return {"title": v, "session": None}
    return v if isinstance(v, dict) else None


def should_generate(st: dict, session: str | None, cfg: dict, now: float | None = None) -> bool:
    if not session or cfg["title_source"] == "off":
        return False
    now = time.time() if now is None else now
    pend = st["pending"].get(session)
    if pend and now - pend < PENDING_TTL:
        return False
    gen = st["generated"].get(session)
    if not gen:
        return True
    return bool(gen.get("retry")) and int(gen.get("attempts", 0)) < MAX_ATTEMPTS


# --------------------------------------------------------------------------
# Core


@dataclass
class Decision:
    action: str  # skip | rename | adopt | generate
    base: str | None  # session title when known
    label: str | None = None
    reason: str = ""


def decide(label: str, pos: int, tab_state: dict | None, pane_id: str,
           title: str | None, owner_alive) -> Decision:
    if not owns_label(label, tab_state):
        return Decision("skip", title, reason="manual")
    owner = (tab_state or {}).get("pane")
    if owner and owner != pane_id and owner_alive(owner):
        return Decision("skip", title, reason="other-owner")
    if not title:
        return Decision("generate", None)
    wanted = compose(pos, title)
    if label == wanted:
        return Decision("adopt", title, wanted)
    return Decision("rename", title, wanted)


def owner_alive_fn(tab_id: str, agents: list[str]):
    def alive(owner: str) -> bool:
        try:
            p = get_pane(owner)
        except HerdrError:
            return True  # couldn't ask: keep current owner
        return bool(p) and p.get("tab_id") == tab_id and p.get("agent") in agents
    return alive


def report_task_token(st: dict, cfg: dict, pane_id: str, title: str | None, session: str | None) -> None:
    name = cfg.get("metadata_token") or ""
    if not name:
        return
    rep = reported_entry(st, pane_id)
    if not title:
        if rep and rep.get("title"):
            report_token(pane_id, name, None)
        st["reported"].pop(pane_id, None)
        return
    if rep and rep.get("title") == title and rep.get("session") == session:
        return
    report_token(pane_id, name, title)
    st["reported"][pane_id] = {"title": title, "session": session}


def apply(st: dict, cfg: dict, pane_id: str) -> tuple[str, str | None]:
    """Returns (status, session_to_generate). status: ok|gone|not-agent."""
    pane = get_pane(pane_id)
    if pane is None:
        return "gone", None
    if pane.get("agent") not in cfg["agents"]:
        return "not-agent", None
    session = session_of(pane)
    tab_id, ws = pane.get("tab_id"), pane.get("workspace_id")
    if not tab_id:
        return "gone", None
    tabs = list_tabs(ws)
    pos, label = position(tabs, tab_id)
    if pos is None or label is None:
        return "gone", None
    ws_label = workspace_label(ws) if ws else None
    token = cfg.get("metadata_token") or ""

    agent = pane.get("agent")
    term = normalize_title(
        agent_title(pane.get("terminal_title_stripped"), agent), int(cfg["max_width"])
    )
    switched = False
    old_title = None

    rep = reported_entry(st, pane_id)
    if rep and rep.get("session") != session:
        switched = rep.get("session") is not None
        old_title = rep.get("title")
        if token:
            report_token(pane_id, token, None)
        st["reported"].pop(pane_id, None)

    ts = st["tabs"].get(tab_id)
    if ts and ts.get("pane") == pane_id and ts.get("session") != session:
        switched = switched or ts.get("session") is not None
        old_title = old_title or ts.get("title")
        if token and pane_id in st["reported"]:
            report_token(pane_id, token, None)
        st["reported"].pop(pane_id, None)
        if owns_label(label, ts):
            ok = label == str(pos) or rename_if_label(tab_id, ws, label, str(pos))
            if ok:
                label = str(pos)
                ts = {"label": label, "title": None, "pane": pane_id, "session": session}
                st["tabs"][tab_id] = ts
            else:
                st["tabs"].pop(tab_id, None)
                ts = None
        else:
            st["tabs"].pop(tab_id, None)
            ts = None

    # The old session's title may still be on the terminal when the new
    # session is reported (/clear): ignore it until the terminal changes.
    if switched and old_title:
        st["stale"][pane_id] = {"session": session, "title": old_title}
    stale = st["stale"].get(pane_id)
    stale_title = False
    if stale:
        if stale.get("session") == session and stale.get("title") == term:
            stale_title = True
        else:
            st["stale"].pop(pane_id, None)

    cwd = pane.get("foreground_cwd") or pane.get("cwd")
    term_ok = term if not stale_title and is_meaningful(term, cwd, ws_label) else None
    gen = st["generated"].get(session) if session else None
    title = term_ok or (gen or {}).get("title") or None

    d = decide(label, pos, ts, pane_id, title, owner_alive_fn(tab_id, cfg["agents"]))
    if d.reason == "manual":
        st["tabs"].pop(tab_id, None)
    elif d.action in ("rename", "adopt"):
        if d.action == "adopt" or rename_if_label(tab_id, ws, label, d.label):
            st["tabs"][tab_id] = {"label": d.label, "title": d.base, "pane": pane_id, "session": session}
        else:
            st["tabs"].pop(tab_id, None)  # renamed by hand meanwhile

    report_task_token(st, cfg, pane_id, d.base, session)

    need = (
        term_ok is None
        and agent in cfg["generate_agents"]
        and should_generate(st, session, cfg)
    )
    return "ok", (session if need else None)


def pane_known(st: dict, pane_id: str) -> bool:
    return (
        pane_id in st["reported"]
        or pane_id in st["stale"]
        or any(t.get("pane") == pane_id for t in st["tabs"].values())
    )


def handle_pane(pane_id: str, cfg: dict, renumber: bool = True) -> None:
    with locked_state() as st:
        status, session = apply(st, cfg, pane_id)
        known = pane_known(st, pane_id)
    if status in ("gone", "not-agent"):
        # pane.updated fires for every shell pane: only renumber when the
        # agent we tracked there went away.
        if renumber and known:
            renumber_all(cfg)
        return
    if not session:
        return
    prompt = read_first_prompt(session)
    if not prompt:
        return
    with locked_state() as st:
        if not should_generate(st, session, cfg):
            return
        st["pending"][session] = time.time()
    title, retry = None, True
    try:
        title, retry = generate_title(prompt, cfg)
    finally:
        with locked_state() as st:
            st["pending"].pop(session, None)
            prev = st["generated"].get(session) or {}
            attempts = int(prev.get("attempts", 0)) + 1
            if title or not prev.get("title"):
                st["generated"][session] = {
                    "title": title or prev.get("title"),
                    "ts": time.time(),
                    "retry": retry or not title,
                    "attempts": attempts,
                }
            else:  # keep earlier heuristic, count the attempt
                prev.update(attempts=attempts, ts=time.time())
                st["generated"][session] = prev
            apply(st, cfg, pane_id)


def plan_workspace(wtabs: list[dict], st_tabs: dict, agent_panes: dict) -> tuple[list, list, list]:
    """Pure renumber plan for one workspace's tabs (in position order).

    Returns (renames [(tab_id, current, wanted)], released [tab_id],
    orphaned [tab_id]). Mutates st_tabs for released/orphaned tabs; new
    labels are recorded by the caller only after the rename succeeds.
    """
    renames, released, orphaned = [], [], []
    for i, t in enumerate(wtabs):
        tid, pos, label = t["tab_id"], i + 1, str(t.get("label") or "")
        ts = st_tabs.get(tid)
        if not ts:
            continue
        if not owns_label(label, ts):
            released.append(tid)
            st_tabs.pop(tid, None)
            continue
        owner = ts.get("pane")
        op = agent_panes.get(owner) if owner else None
        if owner and not (op and op.get("tab_id") == tid):
            ts.update(title=None, pane=None, session=None)
        if not ts.get("pane"):
            orphaned.append(tid)
        wanted = compose(pos, ts.get("title"))
        if label != wanted:
            renames.append((tid, label, wanted))  # label committed on success
        else:
            ts["label"] = wanted
    return renames, released, orphaned


def renumber_all(cfg: dict) -> None:
    retry: list[str] = []
    with locked_state() as st:
        try:
            tabs = list_tabs()
            panes = list_panes()
        except HerdrError as e:
            log(f"renumber skipped: {e}")
            return
        live = {t["tab_id"] for t in tabs}
        for tid in list(st["tabs"]):
            if tid not in live:
                del st["tabs"][tid]
        pane_ids = {p["pane_id"] for p in panes}
        agent_panes = {p["pane_id"]: p for p in panes if p.get("agent") in cfg["agents"]}
        by_ws: dict[str, list[dict]] = {}
        for t in tabs:
            by_ws.setdefault(t.get("workspace_id"), []).append(t)
        orphaned: set[str] = set()
        for ws, wtabs in by_ws.items():
            renames, _released, orph = plan_workspace(wtabs, st["tabs"], agent_panes)
            orphaned.update(orph)
            for tid, current, wanted in renames:
                try:
                    if rename_if_label(tid, ws, current, wanted):
                        st["tabs"][tid]["label"] = wanted
                    else:
                        st["tabs"].pop(tid, None)  # renamed by hand meanwhile
                except HerdrError as e:
                    log(f"rename {tid} failed: {e}")  # keep old label: still ours
        name = cfg.get("metadata_token") or ""
        for pid in list(st["reported"]):
            if pid in agent_panes:
                continue
            if pid in pane_ids and name:
                try:
                    report_token(pid, name, None)
                except HerdrError as e:
                    if not e.not_found:
                        continue  # retry next time
            st["reported"].pop(pid, None)
        for pid in list(st["stale"]):
            if pid not in agent_panes:
                st["stale"].pop(pid, None)
        retry = [pid for pid, p in agent_panes.items() if p.get("tab_id") in orphaned]
    for pid in retry:
        safe(handle_pane, pid, cfg, False)


def handle_all_panes(cfg: dict) -> None:
    try:
        panes = list_panes()
    except HerdrError as e:
        log(f"pane list failed: {e}")
        return
    for p in panes:
        if p.get("agent") in cfg["agents"]:
            safe(handle_pane, p["pane_id"], cfg, False)


def prune(cfg: dict) -> None:
    with locked_state() as st:
        st["pending"] = {}
        st["reported"] = {}
        st["stale"] = {}
    renumber_all(cfg)
    handle_all_panes(cfg)


def find_pane_id(obj) -> str | None:
    if isinstance(obj, dict):
        v = obj.get("pane_id")
        if isinstance(v, str) and v:
            return v
        for x in obj.values():
            r = find_pane_id(x)
            if r:
                return r
    elif isinstance(obj, list):
        for x in obj:
            r = find_pane_id(x)
            if r:
                return r
    return None


def event_pane_id() -> str | None:
    raw = os.environ.get("HERDR_PLUGIN_EVENT_JSON")
    if raw:
        try:
            pid = find_pane_id(json.loads(raw))
            if pid:
                return pid
        except ValueError:
            pass
    return os.environ.get("HERDR_PANE_ID") or None


def safe(fn, *args) -> None:
    try:
        fn(*args)
    except HerdrError as e:
        log(f"{fn.__name__}: herdr {e}")


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "pane"
    cfg = load_config()
    if mode == "pane":
        pid = event_pane_id()
        if pid:
            safe(handle_pane, pid, cfg)
    elif mode == "pane-moved":
        # source tab loses its owner, destination tab may gain one
        safe(renumber_all, cfg)
        pid = event_pane_id()
        if pid:
            safe(handle_pane, pid, cfg, False)
    elif mode == "tabs-changed":
        safe(renumber_all, cfg)
    elif mode == "prune":
        safe(prune, cfg)
    elif mode == "all":
        safe(handle_all_panes, cfg)
    else:
        log(f"unknown mode {mode!r}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
