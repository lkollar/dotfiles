import { View, div } from "gpui-kit";
import { exec, focused, spaces, theme, layout, run } from "herdr";

// Recolours the focused-pane border of the shown layout by host.
// Sits in a 1px block (id "host-sync"). Colour follows the machine of the
// focused space; local = this computer's hostname. Unlisted hosts get a
// stable pick. layout.set rewrites the layout file: keep it untracked.
const HOSTS = {
  mbp: "ansi4",
  tower: "ansi3",
};
const FALLBACK = ["ansi1", "ansi2", "ansi5", "ansi6", "ansi9", "ansi10", "ansi13", "ansi14"];

const pick = (name) => {
  if (HOSTS[name]) return HOSTS[name];
  let h = 0;
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return FALLBACK[h % FALLBACK.length];
};

// Finds the block that shows the active tab (it holds the pane frame look).
const findMain = (n) => {
  if (!n || typeof n !== "object") return null;
  if (n.content?.tab && n.content.pane) return n;
  for (const c of n.children ?? []) {
    const r = findMain(c);
    if (r) return r;
  }
  return null;
};

export default class HostFrame extends View {
  init(_props, cx) {
    this.local = "local";
    cx.spawn(async (cx) => {
      try {
        const r = await exec("hostname", ["-s"]);
        this.local = r.stdout.trim() || "local";
      } catch {}
      cx.notify();
    });
  }

  render() {
    const t = theme();
    const f = focused();
    const sp = f && spaces().find((s) => s.id === f.space);
    const color = t[pick(sp?.machine ?? this.local)];
    const tree = layout();
    const main = findMain(tree);
    if (color && main && main.content.pane.focus?.color !== color) {
      main.content.pane.focus = { ...(main.content.pane.focus ?? { width: 1 }), color };
      run("layout.set", { layout: tree });
    }
    return div().size_full();
  }
}
