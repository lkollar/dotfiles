// Spaces and agents in one block. Combined (the default): tabs for Spaces, with
// each space's tabs and agents under it, and Agents. With `combined: false` in the settings: the
// two lists one above the other, as two blocks of this mod would draw them.
import { v_flex, h_flex } from "gpui-base";
import { focused, theme, setAgentOrder, agents, run, nextCommand, checking } from "herdr";
import { Spaces } from "./spaces.js";
import { Agents } from "./agents.js";
import { TEXT, Badge, Rail } from "./ui.js";

const TABS = ["spaces", "agents"];

export class Lists {
  init(props, cx) {
    this.spaces = new Spaces();
    this.spaces.init(props, cx);
    this.agents = new Agents();
    this.agents.init(props, cx);
    const saved = localStorage.getItem("lists.tab");
    this.tab = TABS.includes(saved) ? saved : "spaces";
    // The Spaces tab's rows in drawn order, for next-row / prev-row; null when not drawn.
    this.walk = null;
    if (checking()) return;
    cx.spawn(async (cx) => {
      for (;;) {
        const command = await nextCommand();
        if (command === "next-row") this.step(1);
        else if (command === "prev-row") this.step(-1);
      }
    });
  }

  // Moves to the next or previous row the Spaces tab draws, from the focused pane's
  // row, else its tab's, else its space's place. Without the Spaces tab: Herdr's agents.
  step(dir) {
    const walk = this.walk;
    const targets = walk?.filter((r) => !r.mark) ?? [];
    if (!targets.length) return run(dir > 0 ? "agent.next" : "agent.prev");
    const f = focused();
    let at = f?.pane ? walk.findIndex((r) => !r.mark && r.pane === f.pane) : -1;
    if (at === -1 && f?.tab) at = walk.findIndex((r) => !r.mark && r.tab === f.tab && !r.pane);
    if (at === -1 && f?.tab) at = walk.findIndex((r) => !r.mark && r.tab === f.tab);
    // Off any row: start just before the space's first row, so next lands on it.
    let from = at;
    if (at === -1) {
      from = walk.findIndex((r) => r.mark && r.space === f?.space);
      if (from !== -1 && dir < 0) from += 1;
    }
    const n = walk.length;
    for (let i = 1; i <= n; i++) {
      const r = walk[(((from === -1 ? (dir > 0 ? -1 : 0) : from) + dir * i) % n + n) % n];
      if (r.mark) continue;
      if (r.pane) run("pane.focus", { pane: r.pane });
      else {
        run("space.select", { id: r.space });
        run("tab.select", { id: r.tab });
      }
      return;
    }
  }

  pick(tab, cx) {
    this.tab = tab;
    localStorage.setItem("lists.tab", tab);
    cx.notify();
  }

  render() {
    const t = theme();
    const collapsed = this.spaces.collapsed();
    const root = v_flex()
      .id("better-sidebar-lists")
      .size_full()
      .min_h(0)
      .bg(t.chrome)
      .text_size(TEXT.body)
      .on_size_change((size, cx) => this.spaces.resized(size, cx));
    this.spaces.under = null;
    this.spaces.quiet = null;
    this.spaces.above = null;
    // The rail has no room for tabs: both lists, as numbers.
    this.walk = null;
    if (!this.spaces.settings.combined || collapsed)
      return root
        .child(
          v_flex()
            .flex_1()
            .min_h(0)
            .child(this.spaces.header(t, collapsed))
            .child(this.spaces.body(t, collapsed)),
        )
        .child(v_flex().flex_1().min_h(0).child(this.agents.render()));

    const view = this.agents.readView();
    root.child(this.tabBar(t, view));
    if (this.tab !== "spaces") return root.child(this.agents.render({ view, heading: false }));

    // Spaces, each with its tabs and agents beneath in tab order, so rows don't move as
    // their state changes; next-agent keys follow that order.
    const nested = { ...view, sort: { id: "grouped" }, byPriority: false, nested: true };
    const order = [];
    // The agents as they are listed: a kept sub-agent is under its parent, so
    // it is not drawn again under its space.
    const all = view.model;
    // Pinned agents go above every space, in the Agents tab's Pinned group.
    const pinned = view.groups.find((g) => g.id === "pinned");
    const pins = pinned?.members.map((a) => a.address) ?? [];
    order.push(...pins);
    const live = new Map(agents().map((a) => [a.address, a]));
    // Rows as drawn: an agent, its unfolded sub-agents that have a pane, a tab.
    const agentRows = (a) => [
      { pane: a.pane, tab: a.tab, space: a.space },
      ...(this.agents.folded.has(a.address) ? [] : this.agents.tree(view.all, a.address))
        .map((s) => live.get(s.t.address))
        .filter(Boolean)
        .map((k) => ({ pane: k.pane, tab: k.tab, space: k.space })),
    ];
    const walk = pinned && !this.agents.folded.has("pinned") ? pinned.members.flatMap(agentRows) : [];
    this.spaces.above = () => (pinned ? this.agents.groupRows(pinned, 0, view, t) : []);
    const nest = (lines, row) => h_flex().children(lines.map((l) => Rail(l))).child(row.flex_1().min_w(0));
    // A space's agents hang from its line; a main space's worktrees come after them,
    // so its line carries on, and a worktree's own agents sit one step further in.
    // Every tab shows: a tab with agents as its agents, any other as itself.
    const shownTab = focused()?.tab;
    const plain = (tab) => !all.some((a) => a.tab === tab.id);
    this.spaces.under = ({ w, tree, kids }) => {
      const items = w.tabs.flatMap((tab) =>
        plain(tab)
          ? tab.settled ? [] : [{ tab }]
          : all.filter((a) => a.tab === tab.id && !pins.includes(a.address)).map((a) => ({ a })),
      );
      order.push(...items.filter((x) => x.a).map((x) => x.a.address));
      walk.push({ mark: true, space: w.id });
      for (const x of items) walk.push(...(x.a ? agentRows(x.a) : [{ tab: x.tab.id, space: w.id }]));
      const before = tree ? [tree.startsWith("└") ? "" : "│"] : [];
      return items.flatMap((x, i) => {
        const last = i === items.length - 1 && !kids;
        const [row, ...subs] = x.a
          ? this.agents.agentWithSubs(x.a, i, nested, t)
          : [this.agents.tabRow(w, x.tab, x.tab.id === shownTab, t)];
        return [nest([...before, last ? "└" : "├"], row), ...subs.map((s) => nest([...before, last ? "" : "│"], s))];
      });
    };
    // One row lit: a space whose focused agent or tab shows beneath it leaves it to that row.
    this.spaces.quiet = (w) =>
      all.some((a) => a.space === w.id && a.focused) || w.tabs.some((tab) => tab.id === shownTab && plain(tab));
    const body = this.spaces.body(t, false);
    this.walk = walk;
    setAgentOrder(order);
    return root.child(body);
  }

  // Tabs side by side from the left, the picked one filled.
  tabBar(t, view) {
    const tab = (id, label, count) =>
      h_flex()
        .id(`lists-tab-${id}`)
        .px(10)
        .h(24)
        .gap(5)
        .justify_center()
        .items_center()
        .rounded(6)
        .cursor_pointer()
        .text_size(TEXT.label)
        .font_medium()
        .text_color(this.tab === id ? t.foreground : t.dim)
        .when(this.tab === id, (el) => el.bg(t.selected))
        .when(this.tab !== id, (el) => el.hover((s) => s.bg(t.hover).text_color(t.foreground)))
        .on_click((_e, cx) => this.pick(id, cx))
        .child(label)
        // The count badge the group headers use.
        .when(count !== null, (el) => el.child(Badge(count)));
    return h_flex()
      .px(8)
      .pt(6)
      .pb(6)
      .mb(4)
      .border_b(1)
      .border_color(t.border)
      .flex_none()
      .gap(6)
      .items_center()
      .child(
        h_flex()
          .flex_1()
          .gap(2)
          .child(tab("spaces", "Spaces", null))
          .child(tab("agents", "Agents", view.count)),
      )
      .child(this.tab === "spaces" ? this.spaces.headerButtons() : this.agents.sortMenu());
  }
}
