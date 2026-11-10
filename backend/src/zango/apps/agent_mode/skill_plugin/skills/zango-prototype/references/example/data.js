const day = 864e5, ago = d => new Date(Date.now() - d * day).toISOString(), ahead = d => new Date(Date.now() + d * day).toISOString();
const STAGES = ['Received', 'In prep', 'On instrument', 'Review', 'Released'];
ZAS.seed({
  samples: [
    {id: 'LS-24-0418', label: 'Batch 7731 — tablet assay', matrix: 'Tablet', batch: 'B-7731', received: ago(6), due: ago(1), stage: 'On instrument', assignee: 'Priya Raman', method: 'HPLC-UV assay', instrument: 'Agilent 1290 #2', urgent: true},
    {id: 'LS-24-0421', label: 'Batch 7733 — dissolution', matrix: 'Tablet', batch: 'B-7733', received: ago(5), due: ahead(2), stage: 'In prep', assignee: 'Priya Raman', method: 'USP II dissolution', instrument: 'Distek 2500'},
    {id: 'LS-24-0422', label: 'Raw material — lactose', matrix: 'Powder', batch: 'RM-0912', received: ago(4), due: ahead(1), stage: 'Review', assignee: 'Jonas Weber', method: 'KF moisture', instrument: 'Metrohm 917'},
    {id: 'LS-24-0425', label: 'Stability T6M 25°C', matrix: 'Capsule', batch: 'B-7602', received: ago(3), due: ahead(4), stage: 'Received', assignee: 'Priya Raman', method: 'Related substances', instrument: ''},
    {id: 'LS-24-0427', label: 'Cleaning swab — line 3', matrix: 'Swab', batch: 'CL-0331', received: ago(2), due: ahead(0), stage: 'On instrument', assignee: 'Jonas Weber', method: 'TOC', instrument: 'Sievers M9', urgent: true},
    {id: 'LS-24-0429', label: 'Batch 7740 — content uniformity', matrix: 'Tablet', batch: 'B-7740', received: ago(1), due: ahead(5), stage: 'Received', assignee: 'Amara Okafor', method: 'HPLC-UV CU', instrument: ''},
    {id: 'LS-24-0410', label: 'Batch 7718 — tablet assay', matrix: 'Tablet', batch: 'B-7718', received: ago(11), due: ago(4), stage: 'Released', assignee: 'Priya Raman', method: 'HPLC-UV assay', instrument: 'Agilent 1290 #1'}
  ],
  events: [
    {id: 1, sample: 'LS-24-0418', at: ago(1.2), who: 'Priya Raman', stage: 'On instrument', text: 'Sequence started on Agilent 1290 #2'},
    {id: 2, sample: 'LS-24-0418', at: ago(3), who: 'Priya Raman', stage: 'In prep', text: 'Standards and samples prepared'},
    {id: 3, sample: 'LS-24-0418', at: ago(6), who: 'Sample receipt', stage: 'Received', text: 'Received, 2 × 30 tablets, chain of custody complete'}
  ]
});
// Shared helpers: one tone per stage (the badge classes in app.css), one avatar colour per person.
const TONE = {Received: 't-blue', 'In prep': 't-gray', 'On instrument': 't-amber', Review: 't-purple', Released: 't-green'};
const AV = ['var(--brand)', '#0D9488', '#D97706', '#DB2777', '#2563EB', '#7C3AED', '#059669'];
window.LAB = {
  STAGES,
  late: s => s.stage !== 'Released' && new Date(s.due) < Date.now(),
  badge: stage => `<span class="z-badge ${TONE[stage] || 't-gray'}"><i></i>${ZAS.h(stage)}</span>`,
  av: name => `<span class="z-av" style="--av:${AV[[...String(name)].reduce((a, ch) => a + ch.charCodeAt(0), 0) % AV.length]}">${ZAS.initials(name)}</span>`,
  person: name => name ? `<span class="c-person">${LAB.av(name)}${ZAS.h(name)}</span>` : '<span class="z-nil">—</span>'
};
