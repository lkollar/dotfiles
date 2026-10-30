import { View, div } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { exec, theme, props, openOverlay, closeOverlay } from "herdr";

// Data: `codexbar usage --provider both --format json` (one call, both providers).
// Status bar: compact bars. Click: opens the same mod as a popup card (props().overlay set).
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const p2 = (n) => String(n).padStart(2, "0");

const fmtLeft = (secs) => {
  if (secs <= 0) return "";
  const m = Math.round(secs / 60);
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h${p2(m % 60)}`;
  return `${Math.floor(h / 24)}d${h % 24}h`;
};

const fmtReset = (epoch) => {
  if (!epoch) return "";
  const d = new Date(epoch * 1000), n = new Date();
  const hm = `${p2(d.getHours())}:${p2(d.getMinutes())}`;
  return d.toDateString() === n.toDateString() ? hm : `${d.getDate()} ${MONTHS[d.getMonth()]} at ${hm}`;
};

const fmtAgo = (epoch) => {
  if (!epoch) return "";
  const m = Math.max(0, Math.round((Date.now() / 1000 - epoch) / 60));
  return m < 1 ? "Updated just now" : m < 60 ? `Updated ${m} min ago` : `Updated ${Math.floor(m / 60)}h ago`;
};

// codexbar window + pace -> { left, resets, secs, pace }; an expired window is full again
const norm = (w, pace) => {
  if (w?.usedPercent == null) return null;
  const resets = w.resetsAt ? Date.parse(w.resetsAt) / 1000 : null;
  const secs = resets ? resets - Date.now() / 1000 : null;
  if (secs != null && secs <= 0) return { left: 100, resets: null, secs: 0, pace: null };
  return { left: Math.max(0, Math.min(100, 100 - w.usedPercent)), resets, secs, pace: pace?.summary ?? null };
};

const cap = (x) => (x ? x[0].toUpperCase() + x.slice(1) : null);

export default class Limits extends View {
  init(_props, cx) {
    this.claude = { h5: null, d7: null, updated: null, plan: null };
    this.codex = { h5: null, d7: null, updated: null, plan: null };
    cx.timer.every(60000, (cx) => this.refresh(cx));
    this.refresh(cx);
  }

  refresh(cx) {
    cx.spawn(async (cx) => {
      try {
        const r = await exec("codexbar", ["usage", "--provider", "both", "--format", "json"]);
        for (const e of JSON.parse(r.stdout)) {
          const target = e.provider === "claude" ? "claude" : e.provider === "codex" ? "codex" : null;
          if (!target || !e.usage) continue; // errors keep the last known values
          const u = e.usage;
          this[target] = {
            h5: norm(u.primary, e.pace?.primary),
            d7: norm(u.secondary, e.pace?.secondary),
            updated: u.updatedAt ? Date.parse(u.updatedAt) / 1000 : null,
            plan: cap((u.loginMethod ?? "").replace(/^Claude /, "")) || null,
          };
        }
      } catch (e) { console.log("codexbar", String(e)); }
      cx.notify();
    });
  }

  render() {
    return props()?.overlay ? this.card() : this.bar();
  }

  color(left, t) { return left <= 10 ? t.blocked : left <= 30 ? t.working : t.accent; }

  bar() {
    const t = theme();
    const win = (id, label, w) => {
      const el = h_flex().id(id).gap(6).items_center();
      el.child(div().text_color(t.muted).child(label));
      if (!w) return el.child(div().text_color(t.muted).child("–"));
      const c = this.color(w.left, t);
      const tip = `${label}: ${Math.round(w.left)}% left` + (w.resets ? `, resets ${fmtReset(w.resets)} (in ${fmtLeft(w.secs)})` : "");
      return el.tooltip(tip)
        .child(div().w(40).h(6).rounded(3).bg(t.input).child(div().h(6).rounded(3).bg(c).w(Math.max(3, Math.round(40 * w.left / 100)))))
        .child(div().text_color(w.left <= 30 ? c : t.foreground).font_semibold().child(`${Math.round(w.left)}%`));
    };
    const group = (name, g, key) => h_flex().gap(10).items_center()
      .child(div().text_color(t.foreground).font_semibold().child(name))
      .child(win(`${key}-5h`, "5h", g.h5))
      .child(win(`${key}-7d`, "7d", g.d7));
    return h_flex().id("limits-bar").size_full().px(14).gap(20).items_center().justify_end().bg(t.chrome).border_t(1).border_color(t.border).text_size(13)
      .on_click(() => openOverlay({ mod: "limits", kind: "popup", width: 400, height: 470 }))
      .child(group("Claude", this.claude, "cl"))
      .child(group("Codex", this.codex, "cx"))
      .child(div().text_color(t.dim).child("left"));
  }

  card() {
    const t = theme();
    const row = (title, w) => {
      const c = w ? this.color(w.left, t) : t.dim;
      return v_flex().gap(8)
        .child(h_flex().items_baseline().justify_between()
          .child(div().text_size(17).font_semibold().text_color(t.foreground).child(w ? `${title} ${Math.round(w.left)}% left` : `${title} –`))
          .child(div().text_size(12.5).text_color(t.muted).child(w?.resets ? `Resets ${fmtReset(w.resets)}` : "")))
        .child(div().w_full().h(8).rounded(4).bg(t.input).child(div().h(8).rounded(4).bg(c).w(`${w ? Math.max(1, w.left) : 0}%`)))
        .child(div().text_size(12.5).text_color(t.muted).child(w?.pace ? w.pace.split(" | ").filter((x) => !x.startsWith("Expected")).join(" · ") : ""));
    };
    const section = (name, g) => v_flex().gap(14)
      .child(h_flex().items_baseline().justify_between()
        .child(div().text_size(15).font_semibold().text_color(t.foreground).child(name))
        .child(div().text_size(12.5).text_color(t.muted).child(g.plan ?? "")))
      .child(div().text_size(12.5).text_color(t.muted).child(fmtAgo(g.updated)))
      .child(row("Session", g.h5))
      .child(row("Weekly", g.d7));
    return v_flex().id("limits-card").size_full().p(18).gap(16).bg(t.popover)
      .on_click(() => closeOverlay(props().overlay))
      .child(section("Claude", this.claude))
      .child(div().w_full().h(1).bg(t.border))
      .child(section("Codex", this.codex));
  }
}
