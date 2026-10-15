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
// Evaluated as an expression: (root) => [{ kit, title?, items?, children? }]. Stack and grid are
// layout: their blocks are listed in place.
(root) => {
  const LAYOUT = new Set(["stack", "grid"]);
  const blocks = (el) => {
    const out = [];
    for (const c of el.children) {
      const kit = c.getAttribute("data-zas-kit");
      if (!kit || LAYOUT.has(kit)) {
        out.push(...blocks(c));
        continue;
      }
      const node = { kit };
      const title = c.getAttribute("data-zas-title");
      if (title) node.title = title;
      const items = [...c.querySelectorAll("[data-zas-item]")]
        .filter((x) => x.parentElement && x.parentElement.closest("[data-zas-kit]:not([data-zas-kit=stack]):not([data-zas-kit=grid])") === c)
        .map((x) => x.getAttribute("data-zas-item"));
      if (items.length) node.items = items;
      const children = blocks(c);
      if (children.length) node.children = children;
      out.push(node);
    }
    return out;
  };
  return root ? blocks(root) : [];
}
