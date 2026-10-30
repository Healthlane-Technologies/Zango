/* A campaign: header with its status actions, figures, the offer and budget, and tabs for its vouchers,
   redemptions and activity. */
ZAS.screen('campaign_360', function (c) {
  var S = ZAS.store, h = ZAS.h, I = ZAS.I, fmt = ZAS.fmt, E = CFG.entities;
  var r = P.get('campaign', c.record);
  if (!r) return '<div class="empty"><h2>Campaign not found</h2><a href="#" class="btn" data-act="go" data-go="campaigns">Back to Campaigns</a></div>';
  var tab = (c.params && c.params.tab) || 'vouchers';
  var vouchers = S.list('voucher', function (v) { return v.campaign === r.id; });
  var vids = vouchers.map(function (v) { return v.id; });
  var reds = S.list('redemption', function (x) { return vids.indexOf(x.voucher) >= 0; });
  var low = r.budget && (r.budget - (r.spent || 0)) / r.budget < 0.1;
  var acts = P.transitionsFor('campaign', r).map(function (t) {
    return '<button class="btn' + (t.primary ? ' pri' : '') + (t.tone === 'danger' ? ' dng' : '') + '" data-act="rowact" data-ek="campaign" data-id="' + h(r.id) + '" data-name="' + h(t.name) + '">' + h(t.label) + '</button>';
  }).join('') + (P.can('campaign', 'edit') && r.status === 'draft' ? '<button class="btn" data-act="rowact" data-ek="campaign" data-id="' + h(r.id) + '" data-name="_edit">' + I('pencil', 15) + 'Edit</button>' : '');
  function fact(label, v) { return '<div class="fact"><span>' + h(label) + '</span><b>' + v + '</b></div>'; }
  function stat(label, v, tone, to) { return '<a href="#" class="stat st-' + tone + '" data-act="tab360" data-id="' + h(r.id) + '" data-tab="' + to + '"><span>' + h(label) + '</span><b>' + v + '</b></a>'; }
  var benefitPaid = reds.filter(function (x) { return x.status === 'approved' || x.status === 'settled'; }).reduce(function (s, x) { return s + (x.benefit_amount || 0); }, 0);
  function dl(title, keys) {
    return '<div class="card pad"><h3>' + h(title) + '</h3><dl class="dl">' + keys.map(function (k) { return '<dt>' + h(E.campaign.fields[k].label) + '</dt><dd>' + P.cell('campaign', k, r) + '</dd>'; }).join('') + '</dl></div>';
  }
  var tabs = [['vouchers', 'Vouchers', vouchers.length], ['redemptions', 'Redemptions', reds.length], ['activity', 'Activity', null]].map(function (t) {
    return '<button role="tab" class="tab' + (tab === t[0] ? ' on' : '') + '" aria-selected="' + (tab === t[0]) + '" data-act="tab360" data-id="' + h(r.id) + '" data-tab="' + t[0] + '">' + h(t[1]) + (t[2] != null ? ' <span class="cnt">' + t[2] + '</span>' : '') + '</button>';
  }).join('');
  var panel;
  if (tab === 'vouchers') {
    var issue = P.can('voucher', 'add') ? '<button class="btn pri sm" data-act="newfor" data-id="' + h(r.id) + '">' + I('plus', 15) + 'Issue Voucher</button>' : '';
    panel = '<div class="tbh"><span></span>' + issue + '</div>' + P.table('voucher', '360v', vouchers, { columns: ['code', 'patient', 'channel', 'expires_on', 'uses_left', 'status'], all: true });
  } else if (tab === 'redemptions') {
    panel = P.table('redemption', '360r', reds, { columns: ['redemption_no', 'voucher', 'pharmacy', 'bill_date', 'benefit_amount', 'status'], all: true });
  } else {
    var ev = S.list('activity', function (a) { return a.ref === r.id; }).sort(function (a, b) { return String(b.ts).localeCompare(String(a.ts)); });
    panel = '<ul class="tl">' + (ev.map(function (a) { return '<li><i></i><div><div>' + h(a.text) + '</div><small>' + fmt.date(a.ts) + '</small></div></li>'; }).join('') || '<li class="empty">No activity yet.</li>') + '</ul>';
  }
  return '<div class="crumb"><a href="#" data-act="go" data-go="campaigns">Campaigns</a> / <span>' + h(r.title) + '</span></div>' +
    '<div class="hero card"><div class="hero-t"><div class="hav">' + h(ZAS.initials(r.title)) + '</div><div class="grow"><h1>' + h(r.title) + '</h1><div class="hs">' + h(r.campaign_code) + ' · ' + h(P.name('product', r.product)) + '</div><div class="hb">' + P.status('campaign', r) + (low ? P.badge('Budget Low', 'amber') : '') + '</div></div><div class="hact">' + acts + '</div></div>' +
    '<div class="facts">' + fact('Type', P.cell('campaign', 'voucher_type', r)) + fact('Benefit', P.cell('campaign', 'benefit_kind', r)) + fact('Starts', fmt.date(r.start_date)) + fact('Ends', fmt.date(r.end_date)) + '</div>' +
    (low ? '<div class="ban">' + I('alert-triangle', 16) + "Less than 10% of this campaign's budget is left.</div>" : '') + '</div>' +
    '<div class="stats">' + stat('Vouchers issued', vouchers.length, 'indigo', 'vouchers') + stat('Redeemed', vouchers.filter(function (v) { return v.status === 'redeemed'; }).length, 'teal', 'vouchers') + stat('Benefit paid', fmt.money(benefitPaid), 'purple', 'redemptions') + stat('Flagged', reds.filter(function (x) { return x.status === 'flagged'; }).length, 'red', 'redemptions') + '</div>' +
    '<div class="cols"><div class="card"><div class="tabs" role="tablist">' + tabs + '</div>' + panel + '</div><div class="side2">' + dl('Offer', ['product', 'benefit_kind', 'benefit_value', 'max_benefit', 'uses_per_voucher']) + dl('Budget', ['budget', 'spent', 'voucher_limit']) + '</div></div>';
});
ZAS.on('tab360', function (d) { ZAS.go('campaign_360', { record: d.id, params: { tab: d.tab }, replace: true }); });
ZAS.on('newfor', function (d) { P.form('voucher', '', { campaign: d.id }); });
