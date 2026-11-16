"""Run: uv run --no-project python -m unittest test_auto_tab_title"""

import os
import tempfile
import unittest
from unittest import mock

import auto_tab_title as m

WJ = m.WJ


class FakeHerdr:
    """In-memory herdr: tabs/panes keyed by id, records calls."""

    def __init__(self):
        self.tabs = []  # ordered dicts {tab_id, workspace_id, label}
        self.panes = {}
        self.renames = []
        self.tokens = {}
        self.token_calls = 0
        self.fail_get = set()
        self.fail_rename = False
        self.list_calls = 0
        self.on_list = None  # callback(call_no) to mutate between reads

    def add_tab(self, tid, label=None, ws="w1"):
        n = sum(1 for t in self.tabs if t["workspace_id"] == ws) + 1
        self.tabs.append({"tab_id": tid, "workspace_id": ws, "label": label or str(n)})

    def add_pane(self, pid, tid, title="", session="s1", agent="claude", ws="w1"):
        self.panes[pid] = {
            "pane_id": pid, "tab_id": tid, "workspace_id": ws, "agent": agent,
            "agent_session": {"value": session} if session else None,
            "terminal_title_stripped": title, "cwd": "/home/u/proj",
        }

    def label(self, tid):
        return next(t["label"] for t in self.tabs if t["tab_id"] == tid)

    def set_label(self, tid, label):
        next(t for t in self.tabs if t["tab_id"] == tid)["label"] = label

    # patched API
    def get_pane(self, pid):
        if pid in self.fail_get:
            raise m.HerdrError("timeout")
        p = self.panes.get(pid)
        return dict(p) if p else None

    def list_tabs(self, ws=None):
        self.list_calls += 1
        if self.on_list:
            self.on_list(self.list_calls)
        return [dict(t) for t in self.tabs if ws is None or t["workspace_id"] == ws]

    def list_panes(self):
        return [dict(p) for p in self.panes.values()]

    def workspace_label(self, ws):
        return "proj-ws"

    def rename_tab(self, tid, label):
        if self.fail_rename:
            raise m.HerdrError("timeout")
        self.renames.append((tid, label))
        self.set_label(tid, label)

    def report_token(self, pid, name, value):
        self.token_calls += 1
        if value:
            self.tokens[pid] = value
        else:
            self.tokens.pop(pid, None)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = mock.patch.dict(os.environ, {"HERDR_PLUGIN_STATE_DIR": self.tmp.name})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("HERDR_PLUGIN_CONFIG_DIR", None)
        self.h = FakeHerdr()
        for name in ("get_pane", "list_tabs", "list_panes", "workspace_label",
                     "rename_tab", "report_token"):
            p = mock.patch.object(m, name, getattr(self.h, name))
            p.start()
            self.addCleanup(p.stop)
        self.gen = mock.patch.object(m, "generate_title", return_value=(None, True))
        self.gen_mock = self.gen.start()
        self.addCleanup(self.gen.stop)
        self.prompt = mock.patch.object(m, "read_first_prompt", return_value=None)
        self.prompt_mock = self.prompt.start()
        self.addCleanup(self.prompt.stop)
        self.cfg = dict(m.DEFAULTS)

    def handle(self, pid):
        m.handle_pane(pid, self.cfg)

    def state(self):
        with m.locked_state() as st:
            return st


class TestTabs(Base):
    def test_numeric_tab_renamed(self):
        self.h.add_tab("t1")
        self.h.add_tab("t2")
        self.h.add_pane("p1", "t2", "Fix S3 fetch race")
        self.handle("p1")
        self.assertEqual(self.h.label("t2"), f"2{WJ}·Fix S3 fetch race")
        self.assertEqual(self.h.tokens["p1"], "Fix S3 fetch race")

    def test_manual_name_never_overwritten(self):
        self.h.add_tab("t1", "my work")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "my work")
        self.assertEqual(self.h.renames, [])
        self.assertEqual(self.h.tokens["p1"], "Fix bug")  # $task still reported

    def test_manual_rename_after_auto_wins(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.set_label("t1", "mine")
        self.h.panes["p1"]["terminal_title_stripped"] = "Other thing"
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "mine")
        self.assertNotIn("t1", self.state()["tabs"])

    def test_owned_tab_follows_title(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.panes["p1"]["terminal_title_stripped"] = "Write tests"
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Write tests")

    def test_adopt_when_label_correct(self):
        self.h.add_tab("t1", f"1{WJ}·Fix bug")
        with m.locked_state() as st:
            st["tabs"]["t1"] = {"label": f"1{WJ}·Fix bug", "title": "Fix bug", "pane": None, "session": None}
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.assertEqual(self.h.renames, [])
        self.assertEqual(self.state()["tabs"]["t1"]["pane"], "p1")

    def test_token_not_resent_when_unchanged(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.handle("p1")
        self.assertEqual(self.h.token_calls, 1)

    def test_session_switch_reverts_and_clears(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug", session="s1")
        self.handle("p1")
        self.h.panes["p1"].update(agent_session={"value": "s2"}, terminal_title_stripped="Claude Code")
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "1")
        self.assertNotIn("p1", self.h.tokens)

    def test_session_switch_in_manual_tab_clears_token(self):
        self.h.add_tab("t1", "mine")
        self.h.add_pane("p1", "t1", "Fix bug", session="s1")
        self.handle("p1")
        self.h.panes["p1"].update(agent_session={"value": "s2"}, terminal_title_stripped="claude")
        self.handle("p1")
        self.assertNotIn("p1", self.h.tokens)
        self.assertEqual(self.h.label("t1"), "mine")

    def test_orphan_reverts_on_agent_exit(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.panes["p1"]["agent"] = None
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "1")
        self.assertNotIn("p1", self.h.tokens)

    def test_renumber_after_move(self):
        self.h.add_tab("t1")
        self.h.add_tab("t2")
        self.h.add_pane("p2", "t2", "Fix bug")
        self.handle("p2")
        self.h.tabs.reverse()  # t2 now first
        m.renumber_all(self.cfg)
        self.assertEqual(self.h.label("t2"), f"1{WJ}·Fix bug")

    def test_second_agent_takes_orphaned_tab(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "First task", session="s1")
        self.h.add_pane("p2", "t1", "Second task", session="s2")
        self.handle("p1")
        self.handle("p2")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·First task")
        self.h.panes["p1"]["agent"] = None
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Second task")

    def test_failed_liveness_keeps_owner(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "First task", session="s1")
        self.h.add_pane("p2", "t1", "Second task", session="s2")
        self.handle("p1")
        self.h.fail_get.add("p1")
        self.handle("p2")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·First task")

    def test_closed_tab_dropped(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.tabs.clear()
        del self.h.panes["p1"]
        m.renumber_all(self.cfg)
        st = self.state()
        self.assertEqual(st["tabs"], {})
        self.assertEqual(st["reported"], {})


class TestSyncPoints(Base):
    def test_claude_quit_clears_title_and_token(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.panes["p1"].update(agent=None, agent_session=None, terminal_title_stripped=None)
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "1")
        self.assertEqual(self.h.tokens, {})
        self.assertIsNone(self.state()["tabs"]["t1"]["pane"])

    def test_untracked_shell_pane_skips_renumber(self):
        self.h.add_tab("t1")
        self.h.add_pane("p9", "t1", "zsh", agent=None)
        with mock.patch.object(m, "renumber_all") as rn:
            self.handle("p9")
        rn.assert_not_called()

    def test_clear_keeps_stale_title_off(self):
        # SessionStart reported before Claude updated its terminal title
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug", session="s1")
        self.handle("p1")
        self.h.panes["p1"]["agent_session"] = {"value": "s2"}
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "1")
        self.assertNotIn("p1", self.h.tokens)
        self.handle("p1")  # title still stale
        self.assertEqual(self.h.label("t1"), "1")
        self.h.panes["p1"]["terminal_title_stripped"] = "New work"
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·New work")
        self.assertEqual(self.h.tokens["p1"], "New work")

    def test_resume_applies_new_title(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug", session="s1")
        self.handle("p1")
        self.h.panes["p1"].update(agent_session={"value": "s0"}, terminal_title_stripped="Old task")
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Old task")

    def test_pane_moved_between_tabs(self):
        self.h.add_tab("t1")
        self.h.add_tab("t2")
        self.h.add_pane("p1", "t1", "Fix bug")
        self.handle("p1")
        self.h.panes["p1"]["tab_id"] = "t2"
        env = {"HERDR_PLUGIN_EVENT_JSON": '{"pane_id": "p1"}'}
        with mock.patch.dict(os.environ, env):
            m.main(["x", "pane-moved"])
        self.assertEqual(self.h.label("t1"), "1")
        self.assertEqual(self.h.label("t2"), f"2{WJ}·Fix bug")

    def test_manual_rename_race_not_overwritten(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug")
        # user renames between apply()'s read and the rename
        self.h.on_list = lambda n: n == 2 and self.h.set_label("t1", "mine")
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "mine")
        self.assertNotIn("t1", self.state()["tabs"])
        self.assertEqual(self.h.tokens["p1"], "Fix bug")

    def test_renumber_race_not_overwritten(self):
        self.h.add_tab("t1")
        self.h.add_tab("t2")
        self.h.add_pane("p2", "t2", "Fix bug")
        self.handle("p2")
        self.h.tabs.reverse()
        n0 = self.h.list_calls
        self.h.on_list = lambda n: n == n0 + 2 and self.h.set_label("t2", "mine")
        m.renumber_all(self.cfg)
        self.assertEqual(self.h.label("t2"), "mine")
        self.assertNotIn("t2", self.state()["tabs"])

    def test_failed_renumber_keeps_ownership(self):
        self.h.add_tab("t1")
        self.h.add_tab("t2")
        self.h.add_pane("p2", "t2", "Fix bug")
        self.handle("p2")
        self.h.tabs.reverse()
        self.h.fail_rename = True
        m.renumber_all(self.cfg)
        self.assertEqual(self.state()["tabs"]["t2"]["label"], f"2{WJ}·Fix bug")
        self.h.fail_rename = False
        m.renumber_all(self.cfg)
        self.assertEqual(self.h.label("t2"), f"1{WJ}·Fix bug")


class TestCodex(Base):
    def test_codex_title_suffix_stripped(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Commit changes | proj", agent="codex", session=None)
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Commit changes")

    def test_codex_dir_only_title_ignored(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "proj", agent="codex", session="c1")
        self.prompt_mock.return_value = "do things"
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "1")
        self.gen_mock.assert_not_called()  # no transcript-based titles for codex

    def test_agent_title_only_touches_codex(self):
        self.assertEqual(m.agent_title("a | b", "claude"), "a | b")
        self.assertEqual(m.agent_title("a | b", "codex"), "a")


class TestRefreshAction(Base):
    def test_all_mode_resets_after_idle_clear(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Fix bug", session="s1")
        self.handle("p1")
        self.h.panes["p1"].update(agent_session={"value": "s2"}, terminal_title_stripped="Claude Code")
        m.main(["x", "all"])
        self.assertEqual(self.h.label("t1"), "1")
        self.assertNotIn("p1", self.h.tokens)


class TestHerdrWrapper(unittest.TestCase):
    def run_with(self, rc, out, err):
        res = mock.Mock(returncode=rc, stdout=out, stderr=err)
        with mock.patch.object(m.subprocess, "run", return_value=res):
            return m.herdr("pane", "get", "x")

    def test_not_found_on_stderr(self):
        err = '{"error":{"code":"pane_not_found","message":"gone"},"id":"cli:pane:get"}\n'
        with self.assertRaises(m.HerdrError) as cm:
            self.run_with(1, "", err)
        self.assertTrue(cm.exception.not_found)

    def test_other_error_not_gone(self):
        with self.assertRaises(m.HerdrError) as cm:
            self.run_with(1, "", "connection refused")
        self.assertFalse(cm.exception.not_found)

    def test_get_pane_gone_returns_none(self):
        err = '{"error":{"code":"pane_not_found","message":"gone"}}'
        res = mock.Mock(returncode=1, stdout="", stderr=err)
        with mock.patch.object(m.subprocess, "run", return_value=res):
            self.assertIsNone(m.get_pane("x"))

    def test_result_unwrapped(self):
        self.assertEqual(self.run_with(0, '{"result":{"pane":{"a":1}}}', ""), {"pane": {"a": 1}})


class TestGeneration(Base):
    def test_manual_tab_gets_generated_task(self):
        self.h.add_tab("t1", "mine")
        self.h.add_pane("p1", "t1", "Claude Code")
        self.prompt_mock.return_value = "please fix the login bug"
        self.gen_mock.return_value = ("Fix login bug", False)
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), "mine")
        self.assertEqual(self.h.tokens["p1"], "Fix login bug")

    def test_generated_title_renames(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Claude Code")
        self.prompt_mock.return_value = "please fix the login bug"
        self.gen_mock.return_value = ("Fix login bug", False)
        self.handle("p1")
        self.handle("p1")
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Fix login bug")
        self.assertEqual(self.gen_mock.call_count, 1)

    def test_heuristic_retry_limited(self):
        self.h.add_tab("t1")
        self.h.add_pane("p1", "t1", "Claude Code")
        self.prompt_mock.return_value = "please fix the login bug"
        self.gen_mock.return_value = ("Please fix the login bug", True)
        for _ in range(5):
            self.handle("p1")
        self.assertEqual(self.gen_mock.call_count, 3)
        self.assertEqual(self.h.label("t1"), f"1{WJ}·Please fix the login bug")

    def test_pending_blocks_concurrent(self):
        with m.locked_state() as st:
            st["pending"]["s1"] = __import__("time").time()
        self.assertFalse(m.should_generate(self.state(), "s1", self.cfg))

    def test_off_disables(self):
        cfg = dict(self.cfg, title_source="off")
        self.assertFalse(m.should_generate(m.empty_state(), "s1", cfg))


class TestPure(unittest.TestCase):
    def test_compose_marker(self):
        self.assertEqual(m.compose(2, "Fix"), f"2{WJ}·Fix")
        self.assertEqual(m.compose(2, None), "2")

    def test_user_dot_not_owned(self):
        self.assertFalse(m.owns_label("2·Mine", None))
        self.assertTrue(m.owns_label("7", None))

    def test_normalize(self):
        self.assertEqual(m.normalize_title('  ✳ "Title: Fix  the\tbug."  '), "Fix the bug")
        long = m.normalize_title("word " * 20, 20)
        self.assertEqual(m.display_width(long), 20)
        self.assertTrue(long.endswith("…"))
        self.assertLessEqual(m.display_width(m.normalize_title("漢" * 30, 10)), 10)

    def test_meaningful(self):
        bad = ["Claude Code", "claude", "zsh", "main", "~", "123", "/usr/local",
               "~/src/x", "src/foo.py", "user@host:~/x", "proj", "proj-ws", ""]
        for t in bad:
            self.assertFalse(m.is_meaningful(t, "/home/u/proj", "proj-ws"), t)
        self.assertTrue(m.is_meaningful("Fix S3 fetch race", "/home/u/proj", "proj-ws"))

    def test_extract_prompt_noise(self):
        recs = [
            {"type": "summary"},
            {"type": "user", "isMeta": True, "message": {"content": "meta"}},
            {"type": "user", "message": {"content": "<local-command-stdout>x</local-command-stdout>"}},
            {"type": "user", "message": {"content": "Caveat: blah"}},
            {"type": "user", "message": {"content": "<command-name>/clear</command-name><command-args></command-args>"}},
            {"type": "user", "message": {"content": "<command-name>/model</command-name><command-args>opus</command-args>"}},
            {"type": "user", "message": {"content": "<command-name>/review-pr</command-name><command-args></command-args>"}},
            {"type": "user", "isSidechain": True, "message": {"content": "side"}},
            {"type": "user", "isCompactSummary": True, "message": {"content": "summary"}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]}},
            {"type": "user", "message": {"content": "[Request interrupted by user]"}},
            {"type": "user", "message": {"content": [{"type": "text", "text": "[Image #1] fix this layout"}]}},
        ]
        self.assertEqual(m.extract_prompt(recs), "fix this layout")

    def test_image_with_text_kept(self):
        recs = [{"type": "user", "message": {"content": [
            {"type": "image", "source": {}}, {"type": "text", "text": "Fix this layout"}]}}]
        self.assertEqual(m.extract_prompt(recs), "Fix this layout")

    def test_extract_slash_with_args(self):
        recs = [{"type": "user", "message": {"content":
                 "<command-message>fix</command-message><command-name>/fix-issue</command-name><command-args>123</command-args>"}}]
        self.assertEqual(m.extract_prompt(recs), "/fix-issue 123")

    def test_heuristic(self):
        self.assertEqual(
            m.heuristic_title("## look at https://github.com/o/repo/pull/12 and **fix** it please now ok"),
            "Look at repo#12 and fix it",
        )

    def test_clean_generated(self):
        self.assertEqual(m.clean_generated("noise\n\nFix S3 fetch race\n"), "Fix S3 fetch race")
        self.assertIsNone(m.clean_generated("one two three four five six seven eight nine"))
        self.assertIsNone(m.clean_generated("x" * 60))
        self.assertIsNone(m.clean_generated(""))

    def test_reported_legacy_string(self):
        st = m.empty_state()
        st["reported"]["p1"] = "Old"
        self.assertEqual(m.reported_entry(st, "p1"), {"title": "Old", "session": None})

    def test_child_env_strips(self):
        with mock.patch.dict(os.environ, {"HERDR_X": "1", "CLAUDECODE": "1",
                                          "CLAUDE_CODE_SESSION_ID": "x", "KEEP": "1"}):
            env = m.child_env()
        self.assertNotIn("HERDR_X", env)
        self.assertNotIn("CLAUDECODE", env)
        self.assertNotIn("CLAUDE_CODE_SESSION_ID", env)
        self.assertIn("KEEP", env)

    def test_find_pane_id(self):
        self.assertEqual(m.find_pane_id({"event": {"data": [{"pane_id": "w1:p3"}]}}), "w1:p3")


if __name__ == "__main__":
    unittest.main()
