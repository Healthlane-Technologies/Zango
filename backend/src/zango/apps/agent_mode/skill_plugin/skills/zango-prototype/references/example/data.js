const day = 864e5, ago = d => new Date(Date.now() - d * day).toISOString(), ahead = d => new Date(Date.now() + d * day).toISOString();
const STAGES = ['Received', 'In prep', 'On instrument', 'Review', 'Released'];
ZAS.seed({
  samples: [
    {id: 'LS-24-0418', label: 'Batch 7731 — tablet assay', matrix: 'Tablet', batch: 'B-7731', received: ago(6), due: ago(1), stage: 'On instrument', assignee: 'Priya Raman', method: 'HPLC-UV assay', instrument: 'Agilent 1290 #2'},
    {id: 'LS-24-0421', label: 'Batch 7733 — dissolution', matrix: 'Tablet', batch: 'B-7733', received: ago(5), due: ahead(2), stage: 'In prep', assignee: 'Priya Raman', method: 'USP II dissolution', instrument: 'Distek 2500'},
    {id: 'LS-24-0422', label: 'Raw material — lactose', matrix: 'Powder', batch: 'RM-0912', received: ago(4), due: ahead(1), stage: 'Review', assignee: 'Jonas Weber', method: 'KF moisture', instrument: 'Metrohm 917'},
    {id: 'LS-24-0425', label: 'Stability T6M 25°C', matrix: 'Capsule', batch: 'B-7602', received: ago(3), due: ahead(4), stage: 'Received', assignee: 'Priya Raman', method: 'Related substances', instrument: '—'},
    {id: 'LS-24-0427', label: 'Cleaning swab — line 3', matrix: 'Swab', batch: 'CL-0331', received: ago(2), due: ahead(0), stage: 'On instrument', assignee: 'Jonas Weber', method: 'TOC', instrument: 'Sievers M9'},
    {id: 'LS-24-0429', label: 'Batch 7740 — content uniformity', matrix: 'Tablet', batch: 'B-7740', received: ago(1), due: ahead(5), stage: 'Received', assignee: 'Amara Okafor', method: 'HPLC-UV CU', instrument: '—'},
    {id: 'LS-24-0410', label: 'Batch 7718 — tablet assay', matrix: 'Tablet', batch: 'B-7718', received: ago(11), due: ago(4), stage: 'Released', assignee: 'Priya Raman', method: 'HPLC-UV assay', instrument: 'Agilent 1290 #1'}
  ],
  events: [
    {id: 1, sample: 'LS-24-0418', at: ago(1.2), who: 'Priya Raman', text: 'Sequence started on Agilent 1290 #2'},
    {id: 2, sample: 'LS-24-0418', at: ago(3), who: 'Priya Raman', text: 'Standards and samples prepared'},
    {id: 3, sample: 'LS-24-0418', at: ago(6), who: 'Sample receipt', text: 'Received, 2 × 30 tablets, chain of custody complete'}
  ]
});
window.LAB = {STAGES, late: s => s.stage !== 'Released' && new Date(s.due) < Date.now(),
  tone: st => ({Received: 'info', 'In prep': '', 'On instrument': 'warn', Review: 'warn', Released: 'ok'}[st] || '')};
