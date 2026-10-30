/* Voucher Programme Overview: figures, two breakdowns and the redemptions waiting for review. */
ZAS.screen('dashboard', function (c) {
  var S = ZAS.store, h = ZAS.h, I = ZAS.I, fmt = ZAS.fmt, E = CFG.entities;
  var camps = S.list('campaign'), vouchers = S.list('voucher'), reds = S.list('redemption');
  var redeemed = reds.filter(function (r) { return r.status === 'approved' || r.status === 'settled'; }).reduce(function (s, r) { return s + (r.benefit_amount || 0); }, 0);
  var flagged = reds.filter(function (r) { return r.status === 'flagged'; });
  var kpis = [
    ['Active campaigns', camps.filter(function (x) { return x.status === 'live'; }).length, 'megaphone', 'purple', 'campaigns'],
    ['Vouchers issued', vouchers.length, 'ticket', 'indigo', 'vouchers'],
    ['Redeemed value', fmt.money(redeemed), 'indian-rupee', 'teal', 'redemptions'],
    ['Flagged for fraud', flagged.length, 'shield-alert', 'red', 'redemptions']
  ].map(function (k) {
    return '<a href="#" class="kpi" data-act="go" data-go="' + k[4] + '"><div class="ki ki-' + k[3] + '">' + I(k[2], 18) + '</div><div><div class="kl">' + h(k[0]) + '</div><div class="kv">' + h(k[1]) + '</div></div></a>';
  }).join('');
  function bars(title, groups) {
    var max = Math.max.apply(null, groups.map(function (g) { return g[1]; }).concat([1]));
    return '<div class="card pad"><h3>' + h(title) + '</h3>' + groups.map(function (g) {
      return '<div class="bar"><span>' + h(g[0]) + '</span><div class="bt"><div class="bf bf-' + h(g[2] || 'blue') + '" style="width:' + Math.round(g[1] / max * 100) + '%"></div></div><b>' + g[1] + '</b></div>';
    }).join('') + '</div>';
  }
  var vs = E.voucher.statuses.map(function (s) { return [s.label, vouchers.filter(function (v) { return v.status === s.code; }).length, s.color]; });
  var cities = E.pharmacy.fields.city && CFG.choices.city.map(function (ci) {
    return [ci.label, reds.filter(function (r) { var ph = S.get('pharmacy', r.pharmacy); return ph && ph.city === ci.id; }).length, 'indigo'];
  });
  var waiting = flagged.slice(0, 8).map(function (r) {
    return '<div class="li" data-act="go" data-go="redemptions"><div><div class="lp">' + h(r.redemption_no) + '</div><div class="ls">' + h(P.name('pharmacy', r.pharmacy)) + '</div></div><span class="sp"></span><span class="lm">' + fmt.money(r.benefit_amount) + '</span>' + P.status('redemption', r) + '</div>';
  }).join('') || '<div class="empty">No redemption is waiting for review.</div>';
  return '<div class="ph"><div><h1>Voucher Programme Overview</h1></div></div><div class="kpis">' + kpis + '</div><div class="grid2">' + bars('Vouchers by status', vs) + bars('Redemptions by pharmacy city', cities) +
    '</div><div class="card pad"><h3>Redemptions waiting for review</h3>' + waiting + '</div>';
});
