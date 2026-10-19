// The sketch-kit tree of a custom screen: the blocks it draws, in order, with their titles and
// their fixed labels (KPI labels, table columns). The same function reads the Studio preview
// (approval bundle, agent_mode/approval_bundle.py) and the built app (zas_test parity), so the two
// trees compare as data. Values are left out on purpose: the preview drew demo rows, the app has
// real ones.
//
// Markers (zas/ui.tsx and the preview's ctx.ui draw the same ones):
//   data-zas-kit="kpis|bars|list|table|board|panel|progress|stack|grid"
//   data-zas-title="<block title>"   data-zas-item="<KPI label | table column>"
//
// Each block also carries its `look`: visual features that do not depend on the data (a gradient,
// a coloured fill, a chart, avatar circles, coloured accent borders), so a flattened port of the
// approved screen fails parity. Hand-drawn markup outside any kit block (a banner drawn as raw
// HTML) is listed as { kit: "markup", text, look }; its text (digits dropped) pairs it with the
// built block.
//
// Evaluated as an expression: (root) => [{ kit, title?, items?, children?, look, text? }]. Stack and
// grid are layout: their blocks are listed in place.
(root) => {
  const LAYOUT = new Set(["stack", "grid"]);
  const rgb = (c) => {
    const m = /rgba?\(([^)]+)\)/.exec(c || "");
    if (!m) return null;
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  // coloured, not white, grey or black
  const vivid = (c) => {
    const x = rgb(c);
    return !!x && x.a > 0.5 && Math.max(x.r, x.g, x.b) - Math.min(x.r, x.g, x.b) >= 40;
  };
  const look = (el) => {
    const box = el.getBoundingClientRect();
    const area = Math.max(1, box.width * box.height);
    const f = new Set();
    for (const x of [el, ...el.querySelectorAll("*")]) {
      const r = x.getBoundingClientRect();
      if (r.width < 1 || r.height < 1) continue;
      const cs = getComputedStyle(x);
      const big = r.width * r.height >= 0.4 * area;
      const bgi = cs.backgroundImage || "";
      const tag = x.tagName.toLowerCase();
      if (/conic-gradient/.test(bgi)) f.add("chart");
      else if (/(linear|radial)-gradient/.test(bgi) && big && !x.closest(".zas-skel")) f.add("gradient").add("filled");
      if ((tag === "svg" || tag === "canvas") && r.width >= 64 && r.height >= 64) f.add("chart");
      if (big && vivid(cs.backgroundColor)) f.add("filled");
      const text = (x.textContent || "").trim();
      if (Math.abs(r.width - r.height) <= 2 && r.width >= 20 && r.width <= 72
          && parseFloat(cs.borderTopLeftRadius) >= r.width / 2 - 1
          && vivid(cs.backgroundColor) && text && text.length <= 3) f.add("avatar");
      for (const side of ["Top", "Left"]) {
        if (parseFloat(cs[`border${side}Width`]) >= 3 && cs[`border${side}Style`] !== "none"
            && vivid(cs[`border${side}Color`]) && r.width >= 40) f.add("accent");
      }
    }
    return [...f].sort();
  };
  const hasKit = (el) => !!el.querySelector("[data-zas-kit]");
  const blocks = (el) => {
    const out = [];
    for (const c of el.children) {
      const kit = c.getAttribute("data-zas-kit");
      if (!kit || LAYOUT.has(kit)) {
        if (kit || hasKit(c)) {
          out.push(...blocks(c));
          continue;
        }
        const r = c.getBoundingClientRect();
        const text = (c.textContent || "").replace(/\s+/g, " ").trim();
        if (r.width >= 8 && r.height >= 8 && (text || c.querySelector("svg, canvas"))) {
          out.push({ kit: "markup", text: text.slice(0, 120), look: look(c) });
        }
        continue;
      }
      const node = { kit };
      const title = c.getAttribute("data-zas-title");
      if (title) node.title = title;
      const items = [...c.querySelectorAll("[data-zas-item]")]
        .filter((x) => x.parentElement && x.parentElement.closest("[data-zas-kit]:not([data-zas-kit=stack]):not([data-zas-kit=grid])") === c)
        .map((x) => x.getAttribute("data-zas-item"));
      if (items.length) node.items = items;
      node.look = look(c);
      const children = blocks(c).filter((n) => n.kit !== "markup");
      if (children.length) node.children = children;
      out.push(node);
    }
    return out;
  };
  return root ? blocks(root) : [];
}
