/* Voucher & Coupon Management: the demo data and what the screens are made of.
   CFG.entities describes each record type (fields, table, forms, workflow); the engine in shell.js
   draws every list, form, status change and the 360 from it. Change a label, a column, a status or
   a form here and every screen follows. The rows below are the starting demo data. */
(function () {
  var TODAY = '2026-10-29';

  var choices = {
    voucher_type: [
      { id: 'copay', label: 'Copay assistance', color: 'purple' },
      { id: 'free_trial', label: 'Free trial', color: 'teal' },
      { id: 'discount', label: 'Discount coupon', color: 'blue' },
      { id: 'bogo', label: 'Buy one get one', color: 'pink' }
    ],
    benefit_kind: [
      { id: 'percent', label: 'Percent off' },
      { id: 'amount', label: 'Fixed amount off' },
      { id: 'free', label: 'Free pack' }
    ],
    channel: [
      { id: 'hcp', label: 'Issued by HCP', color: 'indigo' },
      { id: 'hub', label: 'Patient hub', color: 'teal' },
      { id: 'web', label: 'Self sign-up', color: 'blue' },
      { id: 'field', label: 'Field rep', color: 'purple' }
    ],
    fraud_rule: [
      { id: 'velocity', label: 'Same patient redeemed twice in 24 hours' },
      { id: 'pharmacy_spike', label: 'Pharmacy redemptions 3x its 30-day average' },
      { id: 'amount_cap', label: 'Benefit above the campaign cap' },
      { id: 'wrong_product', label: 'Product not on the campaign' },
      { id: 'expired', label: 'Voucher expired on the bill date' }
    ],
    reject_reason: [
      { id: 'fraud', label: 'Confirmed fraud' },
      { id: 'ineligible', label: 'Patient not eligible' },
      { id: 'wrong_product', label: 'Product not covered' },
      { id: 'no_invoice', label: 'Bill not attached' },
      { id: 'duplicate', label: 'Duplicate redemption' }
    ],
    city: [
      { id: 'mumbai', label: 'Mumbai' }, { id: 'delhi', label: 'Delhi' }, { id: 'bengaluru', label: 'Bengaluru' },
      { id: 'chennai', label: 'Chennai' }, { id: 'hyderabad', label: 'Hyderabad' }, { id: 'pune', label: 'Pune' }
    ]
  };

  var PM = 'program_manager', SA = 'support_agent', PH = 'pharmacy', PT = 'patient';

  var entities = {
    product: {
      name: 'Product', plural: 'Products', display: 'name', sort: 'name', collection: 'product',
      fields: {
        name: { label: 'Name', type: 'text', req: true },
        sku: { label: 'SKU', type: 'text', req: true },
        pack_size: { label: 'Pack size', type: 'text', ph: '10 tablets' },
        mrp: { label: 'MRP', type: 'money', req: true, help: 'Maximum retail price per pack.' },
        is_active: { label: 'Is active', type: 'bool', def: true }
      },
      columns: [
        { k: 'name', label: 'Product', search: true, sort: true }, { k: 'sku', label: 'SKU', search: true },
        { k: 'pack_size', label: 'Pack' }, { k: 'mrp', label: 'MRP', sort: true }, { k: 'is_active', label: 'Active', filter: true }
      ],
      access: { program_manager: ['add', 'edit', 'export'] },
      add: { label: 'Add Product', title: 'Add Product', sections: [{ fields: ['name', 'sku', 'pack_size', 'mrp', 'is_active'] }] },
      codePrefix: ''
    },
    pharmacy: {
      name: 'Pharmacy', plural: 'Pharmacies', display: 'name', sort: 'name', collection: 'pharmacy',
      fields: {
        pharmacy_code: { label: 'Code', type: 'text', auto: true },
        name: { label: 'Name', type: 'text', req: true },
        city: { label: 'City', type: 'choice', choices: 'city', req: true },
        drug_licence: { label: 'Drug licence no.', type: 'text', req: true },
        contact_name: { label: 'Contact', type: 'text', req: true },
        email: { label: 'Email', type: 'email', req: true },
        phone: { label: 'Phone', type: 'text' },
        is_active: { label: 'Partner access', type: 'bool', def: true }
      },
      columns: [
        { k: 'pharmacy_code', label: 'Code', search: true }, { k: 'name', label: 'Pharmacy', search: true, sort: true },
        { k: 'city', label: 'City', filter: true }, { k: 'drug_licence', label: 'Licence' },
        { k: 'contact_name', label: 'Contact' }, { k: 'is_active', label: 'Partner', filter: true }
      ],
      access: { program_manager: ['add', 'edit', 'export'], support_agent: [] },
      add: { label: 'Add Pharmacy', title: 'Add Pharmacy', sections: [{ fields: ['name', 'city', 'drug_licence', 'contact_name', 'email', 'phone', 'is_active'] }] },
      unique: [{ keys: ['drug_licence'], msg: 'A pharmacy with this drug licence already exists.' }]
    },
    campaign: {
      name: 'Campaign', plural: 'Campaigns', display: 'title', sort: '-start_date', collection: 'campaign',
      fields: {
        campaign_code: { label: 'Code', type: 'text', auto: true },
        title: { label: 'Campaign name', type: 'text', req: true },
        voucher_type: { label: 'Type', type: 'choice', choices: 'voucher_type', req: true },
        product: { label: 'Product', type: 'link', to: 'product', req: true },
        benefit_kind: { label: 'Benefit', type: 'choice', choices: 'benefit_kind', req: true },
        benefit_value: { label: 'Benefit value', type: 'number', req: true, help: 'Percent off, amount off, or packs given free.' },
        max_benefit: { label: 'Cap per redemption', type: 'money', help: 'Redemptions above this cap are flagged.' },
        budget: { label: 'Budget', type: 'money', req: true },
        spent: { label: 'Spent', type: 'money', auto: true },
        voucher_limit: { label: 'Vouchers to issue', type: 'number', req: true },
        uses_per_voucher: { label: 'Uses per voucher', type: 'number', def: 1 },
        start_date: { label: 'Start date', type: 'date', req: true },
        end_date: { label: 'End date', type: 'date', req: true },
        terms: { label: 'Terms shown to patients', type: 'long' }
      },
      columns: [
        { k: 'campaign_code', label: 'Code', search: true, link: true }, { k: 'title', label: 'Campaign', search: true, sort: true },
        { k: 'voucher_type', label: 'Type', filter: true }, { k: 'product', label: 'Product', filter: true },
        { k: 'budget', label: 'Budget' }, { k: 'spent', label: 'Spent' }, { k: 'end_date', label: 'Ends', sort: true },
        { k: 'status', label: 'Status', filter: true }
      ],
      quick: [
        { label: 'Live', test: function (r) { return r.status === 'live'; }, def: true },
        { label: 'Budget low', test: function (r) { return r.budget && (r.budget - (r.spent || 0)) / r.budget < 0.1; } }
      ],
      access: { program_manager: ['add', 'edit', 'export', 'detail'], support_agent: ['detail'] },
      add: {
        label: 'New Campaign', title: 'New Campaign', roles: [PM],
        sections: [
          { title: 'Offer', fields: ['title', 'voucher_type', 'product', 'benefit_kind', 'benefit_value', 'max_benefit'] },
          { title: 'Limits', fields: ['budget', 'voucher_limit', 'uses_per_voucher', 'start_date', 'end_date'] },
          { title: 'Patient terms', fields: ['terms'] }
        ]
      },
      editable: ['draft'],
      rowClick: 'campaign_360',
      statuses: [
        { code: 'draft', label: 'Draft', color: 'gray' }, { code: 'in_review', label: 'In Review', color: 'amber' },
        { code: 'live', label: 'Live', color: 'green' }, { code: 'paused', label: 'Paused', color: 'blue' },
        { code: 'closed', label: 'Closed', color: 'gray' }
      ],
      initial: 'draft',
      transitions: [
        { name: 'submit', label: 'Submit for Review', from: ['draft'], to: 'in_review', roles: [PM], primary: true,
          check: function (r) { return r.terms && r.budget >= r.voucher_limit * (r.benefit_value || 0) ? '' : 'Write the patient terms and check the budget first.'; } },
        { name: 'go_live', label: 'Go Live', from: ['in_review'], to: 'live', roles: [PM], primary: true },
        { name: 'send_back', label: 'Send Back', from: ['in_review'], to: 'draft', roles: [PM], form: { note: { label: 'Note', type: 'long', req: true } } },
        { name: 'pause', label: 'Pause', from: ['live'], to: 'paused', roles: [PM], form: { reason: { label: 'Reason', type: 'long', req: true } },
          note: 'Stop issuing and redeeming vouchers on this campaign.' },
        { name: 'resume', label: 'Resume', from: ['paused'], to: 'live', roles: [PM], primary: true },
        { name: 'close', label: 'Close', from: ['live', 'paused'], to: 'closed', roles: [PM], tone: 'danger',
          confirm: 'Close this campaign? Unused vouchers stop working today.' }
      ]
    },
    patient: {
      name: 'Patient', plural: 'Patients', display: 'full_name', sort: 'full_name', collection: 'patient',
      fields: {
        patient_id: { label: 'Patient ID', type: 'text', auto: true },
        full_name: { label: 'Name', type: 'text', req: true },
        mobile: { label: 'Mobile', type: 'text', req: true },
        email: { label: 'Email', type: 'email' },
        city: { label: 'City', type: 'choice', choices: 'city', req: true },
        whatsapp_opt_in: { label: 'WhatsApp opt-in', type: 'bool', def: false },
        consent: { label: 'Consent given', type: 'bool', req: true },
        has_login: { label: 'Portal login', type: 'bool', def: false }
      },
      columns: [
        { k: 'patient_id', label: 'Patient ID', search: true }, { k: 'full_name', label: 'Name', search: true, sort: true },
        { k: 'mobile', label: 'Mobile', search: true }, { k: 'city', label: 'City', filter: true }, { k: 'consent', label: 'Consent', filter: true }
      ],
      access: { support_agent: ['add', 'edit', 'export'], program_manager: ['export'] },
      add: { label: 'Enroll Patient', title: 'Enroll Patient', sections: [{ fields: ['full_name', 'mobile', 'email', 'city', 'whatsapp_opt_in', 'consent', 'has_login'] }] },
      unique: [{ keys: ['mobile'], msg: 'A patient with this mobile number is already enrolled.' }]
    },
    voucher: {
      name: 'Voucher', plural: 'Vouchers', display: 'code', sort: '-issued_on', collection: 'voucher',
      fields: {
        code: { label: 'Voucher code', type: 'text', auto: true },
        campaign: { label: 'Campaign', type: 'link', to: 'campaign', req: true, only: function (r) { return r.status === 'live'; } },
        patient: { label: 'Patient', type: 'link', to: 'patient', req: true },
        channel: { label: 'Issued via', type: 'choice', choices: 'channel', req: true },
        issued_on: { label: 'Issued on', type: 'date', auto: true },
        expires_on: { label: 'Expires', type: 'date', req: true },
        uses_left: { label: 'Uses left', type: 'number', auto: true }
      },
      columns: [
        { k: 'code', label: 'Code', search: true, sort: true }, { k: 'patient', label: 'Patient', search: true },
        { k: 'campaign', label: 'Campaign', filter: true }, { k: 'channel', label: 'Issued via', filter: true },
        { k: 'expires_on', label: 'Expires', sort: true }, { k: 'uses_left', label: 'Uses left' }, { k: 'status', label: 'Status', filter: true }
      ],
      quick: [
        { label: 'Active', test: function (r) { return r.status === 'issued'; }, def: true },
        { label: 'Expiring soon', test: function (r) { return r.status === 'issued' && r.expires_on <= '2026-11-30'; } }
      ],
      scope: { patient: 'patient' },
      access: { support_agent: ['add', 'export'], program_manager: ['export'] },
      add: { label: 'Issue Voucher', title: 'Issue Voucher', roles: [SA], sections: [{ fields: ['campaign', 'patient', 'channel', 'expires_on'] }] },
      unique: [{ keys: ['campaign', 'patient'], msg: 'This patient already has a voucher on this campaign.' }],
      statuses: [
        { code: 'issued', label: 'Issued', color: 'blue' }, { code: 'redeemed', label: 'Redeemed', color: 'green' },
        { code: 'expired', label: 'Expired', color: 'gray' }, { code: 'cancelled', label: 'Cancelled', color: 'red' }
      ],
      initial: 'issued',
      transitions: [
        { name: 'resend', label: 'Resend Code', from: ['issued'], to: 'issued', roles: [SA], note: 'The code was sent to the patient again by SMS.' },
        { name: 'cancel', label: 'Cancel', from: ['issued'], to: 'cancelled', roles: [SA, PM], tone: 'danger',
          confirm: 'Cancel this voucher? The patient can no longer redeem it.', form: { reason: { label: 'Reason', type: 'long', req: true } } }
      ]
    },
    redemption: {
      name: 'Redemption', plural: 'Redemptions', display: 'redemption_no', sort: '-created_at', collection: 'redemption',
      fields: {
        redemption_no: { label: 'Redemption', type: 'text', auto: true },
        voucher: { label: 'Voucher', type: 'link', to: 'voucher', req: true, only: function (r) { return r.status === 'issued'; } },
        pharmacy: { label: 'Pharmacy', type: 'link', to: 'pharmacy', auto: true },
        bill_no: { label: 'Bill no.', type: 'text', req: true },
        bill_date: { label: 'Bill date', type: 'date', req: true },
        packs: { label: 'Packs', type: 'number', req: true },
        bill_amount: { label: 'Bill amount', type: 'money', req: true },
        benefit_amount: { label: 'Benefit', type: 'money', auto: true },
        bill_file: { label: 'Bill photo', type: 'file', req: true },
        fraud_hits: { label: 'Fraud rules', type: 'multi', choices: 'fraud_rule', auto: true }
      },
      columns: [
        { k: 'redemption_no', label: 'Redemption', search: true, sort: true }, { k: 'voucher', label: 'Voucher', search: true },
        { k: 'pharmacy', label: 'Pharmacy', filter: true }, { k: 'bill_date', label: 'Bill date', sort: true },
        { k: 'bill_amount', label: 'Bill' }, { k: 'benefit_amount', label: 'Benefit', sort: true },
        { k: 'fraud_hits', label: 'Fraud rules' }, { k: 'status', label: 'Status', filter: true }
      ],
      quick: [
        { label: 'Flagged', test: function (r) { return r.status === 'flagged'; }, def: true, roles: [PM] },
        { label: 'To settle', test: function (r) { return r.status === 'approved'; } }
      ],
      totals: ['bill_amount', 'benefit_amount'],
      scope: { pharmacy: 'pharmacy' },
      access: { pharmacy: ['add'], program_manager: ['export'] },
      add: { label: 'Redeem Voucher', title: 'Redeem Voucher', roles: [PH], sections: [{ fields: ['voucher', 'bill_no', 'bill_date', 'packs', 'bill_amount', 'bill_file'] }] },
      unique: [{ keys: ['pharmacy', 'bill_no'], msg: 'This bill was already redeemed at this pharmacy.' }],
      statuses: [
        { code: 'submitted', label: 'Submitted', color: 'blue' }, { code: 'flagged', label: 'Flagged', color: 'amber' },
        { code: 'approved', label: 'Approved', color: 'teal' }, { code: 'settled', label: 'Settled', color: 'green' },
        { code: 'rejected', label: 'Rejected', color: 'red' }
      ],
      initial: 'submitted',
      transitions: [
        { name: 'clear', label: 'Clear & Approve', from: ['flagged'], to: 'approved', roles: [PM], primary: true,
          form: { review_note: { label: 'Review note', type: 'long', req: true } }, hook: 'approve' },
        { name: 'reject', label: 'Reject', from: ['submitted', 'flagged'], to: 'rejected', roles: [PM], tone: 'danger',
          form: { reason: { label: 'Reason', type: 'choice', choices: 'reject_reason', req: true }, note: { label: 'Note', type: 'long' } },
          note: 'The pharmacy was emailed the rejection reason.' }
      ]
    },
    settlement: {
      name: 'Settlement', plural: 'Settlements', display: 'settlement_no', sort: '-month', collection: 'settlement',
      fields: {
        settlement_no: { label: 'Settlement', type: 'text', auto: true },
        pharmacy: { label: 'Pharmacy', type: 'link', to: 'pharmacy', req: true },
        month: { label: 'Month end', type: 'date', req: true },
        lines: { label: 'Redemptions', type: 'number', auto: true },
        amount: { label: 'Amount', type: 'money', auto: true },
        payment_ref: { label: 'Payment ref', type: 'text', auto: true }
      },
      columns: [
        { k: 'settlement_no', label: 'Settlement', search: true }, { k: 'pharmacy', label: 'Pharmacy', filter: true },
        { k: 'month', label: 'Month end', sort: true }, { k: 'lines', label: 'Redemptions' },
        { k: 'amount', label: 'Amount', sort: true }, { k: 'payment_ref', label: 'Payment ref' }, { k: 'status', label: 'Status', filter: true }
      ],
      quick: [
        { label: 'To approve', test: function (r) { return r.status === 'draft'; }, def: true, roles: [PM] },
        { label: 'Disputed', test: function (r) { return r.status === 'disputed'; } }
      ],
      totals: ['amount'],
      scope: { pharmacy: 'pharmacy' },
      access: { program_manager: ['add', 'export'] },
      add: { label: 'New Settlement', title: 'New Settlement', roles: [PM], sections: [{ fields: ['pharmacy', 'month'] }] },
      unique: [{ keys: ['pharmacy', 'month'], msg: 'A settlement for this pharmacy and month already exists.' }],
      statuses: [
        { code: 'draft', label: 'Draft', color: 'gray' }, { code: 'approved', label: 'Approved', color: 'teal' },
        { code: 'paid', label: 'Paid', color: 'green' }, { code: 'disputed', label: 'Disputed', color: 'amber' }
      ],
      initial: 'draft',
      transitions: [
        { name: 'approve', label: 'Approve', from: ['draft'], to: 'approved', roles: [PM], primary: true, note: 'The payment file was exported for Finance.' },
        { name: 'dispute', label: 'Dispute', from: ['draft', 'approved'], to: 'disputed', roles: [PH],
          form: { note: { label: 'Note', type: 'long', req: true } }, note: 'The Program Manager was notified.' },
        { name: 'resolve', label: 'Resolve', from: ['disputed'], to: 'draft', roles: [PM], primary: true,
          form: { resolution: { label: 'Resolution', type: 'long', req: true } } }
      ]
    }
  };

  // Who is signed in for each persona when a screen only shows its own rows.
  var personas = {
    program_manager: { name: 'Isha Menon', title: 'Program Manager' },
    support_agent: { name: 'Rahul Verma', title: 'Support Agent' },
    pharmacy: { name: 'Nova Pharma Pvt Ltd', title: 'Pharmacy', pharmacy: 'ph1' },
    patient: { name: 'Karan Joshi', title: 'Patient', patient: 'pt1' }
  };

  var menus = {
    program_manager: [
      { screen: 'dashboard', icon: 'layout-dashboard' }, { screen: 'campaigns', icon: 'megaphone' },
      { screen: 'vouchers', icon: 'ticket' }, { screen: 'redemptions', icon: 'scan-line' },
      { screen: 'settlements', icon: 'landmark' },
      { group: 'Master Data', items: [{ screen: 'pharmacies', icon: 'store' }, { screen: 'products', icon: 'package' }] }
    ],
    support_agent: [
      { screen: 'vouchers', icon: 'ticket' }, { screen: 'patients', icon: 'users' }, { screen: 'redemptions', icon: 'scan-line' }
    ],
    pharmacy: [
      { screen: 'redemptions', label: 'Redeem & History', icon: 'scan-line' }, { screen: 'settlements', label: 'My Settlements', icon: 'landmark' }
    ],
    patient: [{ screen: 'vouchers', label: 'My Vouchers', icon: 'ticket' }]
  };

  window.CFG = { today: TODAY, choices: choices, entities: entities, personas: personas, menus: menus };

  /* ---------- demo data ---------- */
  ZAS.seed({
    product: [
      { id: 'pr1', name: 'Cardiva 5 mg', sku: 'CRD-005', pack_size: '30 tablets', mrp: 420, is_active: true },
      { id: 'pr2', name: 'Glucomet 500', sku: 'GLU-500', pack_size: '60 tablets', mrp: 310, is_active: true },
      { id: 'pr3', name: 'Respira Inhaler', sku: 'RSP-120', pack_size: '1 inhaler', mrp: 780, is_active: true },
      { id: 'pr4', name: 'Neurolin 75', sku: 'NRL-075', pack_size: '10 capsules', mrp: 265, is_active: true },
      { id: 'pr5', name: 'Onco-Tab 20', sku: 'ONC-020', pack_size: '14 tablets', mrp: 1850, is_active: false }
    ],
    pharmacy: [
      { id: 'ph1', pharmacy_code: 'PH-0001', name: 'Nova Pharma Pvt Ltd', city: 'mumbai', drug_licence: 'MH-20-118842', contact_name: 'Anita Rao', email: 'anita@novapharma.example', phone: '+91 98200 11001', is_active: true },
      { id: 'ph2', pharmacy_code: 'PH-0002', name: 'Vertex Healthcare Pvt Ltd', city: 'delhi', drug_licence: 'DL-20-440217', contact_name: 'Sameer Khanna', email: 'sameer@vertex.example', phone: '+91 98100 22002', is_active: true },
      { id: 'ph3', pharmacy_code: 'PH-0003', name: 'Silverline Labs', city: 'bengaluru', drug_licence: 'KA-20-775301', contact_name: 'Divya Nair', email: 'divya@silverline.example', phone: '+91 98450 33003', is_active: true },
      { id: 'ph4', pharmacy_code: 'PH-0004', name: 'Orbit Healthcare Pvt Ltd', city: 'chennai', drug_licence: 'TN-20-309954', contact_name: 'Suresh Iyer', email: 'suresh@orbit.example', phone: '+91 98400 44004', is_active: true },
      { id: 'ph5', pharmacy_code: 'PH-0005', name: 'Medico Plus', city: 'hyderabad', drug_licence: 'TS-20-662018', contact_name: 'Farah Syed', email: 'farah@medicoplus.example', phone: '+91 98480 55005', is_active: true },
      { id: 'ph6', pharmacy_code: 'PH-0006', name: 'CarePoint Pharmacy', city: 'pune', drug_licence: 'MH-20-228871', contact_name: 'Nikhil Joshi', email: 'nikhil@carepoint.example', phone: '+91 98220 66006', is_active: false }
    ],
    patient: [
      { id: 'pt1', patient_id: 'PT-000001', full_name: 'Karan Joshi', mobile: '+91 98200 10001', email: 'karan@example.com', city: 'mumbai', whatsapp_opt_in: true, consent: true, has_login: true },
      { id: 'pt2', patient_id: 'PT-000002', full_name: 'Sana Bose', mobile: '+91 98300 10002', email: 'sana@example.com', city: 'delhi', whatsapp_opt_in: false, consent: true, has_login: false },
      { id: 'pt3', patient_id: 'PT-000003', full_name: 'Vikram Bose', mobile: '+91 98450 10003', email: '', city: 'bengaluru', whatsapp_opt_in: true, consent: true, has_login: false },
      { id: 'pt4', patient_id: 'PT-000004', full_name: 'Meera Pillai', mobile: '+91 98400 10004', email: 'meera@example.com', city: 'chennai', whatsapp_opt_in: true, consent: true, has_login: true },
      { id: 'pt5', patient_id: 'PT-000005', full_name: 'Arjun Reddy', mobile: '+91 98480 10005', email: '', city: 'hyderabad', whatsapp_opt_in: false, consent: true, has_login: false },
      { id: 'pt6', patient_id: 'PT-000006', full_name: 'Neha Kulkarni', mobile: '+91 98220 10006', email: 'neha@example.com', city: 'pune', whatsapp_opt_in: true, consent: false, has_login: false },
      { id: 'pt7', patient_id: 'PT-000007', full_name: 'Imran Shaikh', mobile: '+91 98190 10007', email: '', city: 'mumbai', whatsapp_opt_in: false, consent: true, has_login: false },
      { id: 'pt8', patient_id: 'PT-000008', full_name: 'Latha Menon', mobile: '+91 98860 10008', email: 'latha@example.com', city: 'bengaluru', whatsapp_opt_in: true, consent: true, has_login: false }
    ],
    campaign: [
      { id: 'cm1', campaign_code: 'VC-26-001', title: 'Annual supply agreement', voucher_type: 'copay', product: 'pr1', benefit_kind: 'percent', benefit_value: 20, max_benefit: 4000, budget: 1460000, spent: 1400000, voucher_limit: 800, uses_per_voucher: 2, start_date: '2026-08-19', end_date: '2027-01-09', terms: 'Valid on Cardiva 5 mg at partner pharmacies. One redemption per bill.', status: 'live' },
      { id: 'cm2', campaign_code: 'VC-26-002', title: 'Diabetes starter trial', voucher_type: 'free_trial', product: 'pr2', benefit_kind: 'free', benefit_value: 1, max_benefit: 310, budget: 220000, spent: 98000, voucher_limit: 600, uses_per_voucher: 1, start_date: '2026-09-01', end_date: '2027-02-19', terms: 'First pack free for newly diagnosed patients.', status: 'live' },
      { id: 'cm3', campaign_code: 'VC-26-003', title: 'Respiratory season offer', voucher_type: 'discount', product: 'pr3', benefit_kind: 'amount', benefit_value: 150, max_benefit: 150, budget: 450000, spent: 0, voucher_limit: 1500, uses_per_voucher: 1, start_date: '2026-11-15', end_date: '2027-03-31', terms: '', status: 'draft' },
      { id: 'cm4', campaign_code: 'VC-26-004', title: 'Neuro buy one get one', voucher_type: 'bogo', product: 'pr4', benefit_kind: 'free', benefit_value: 1, max_benefit: 265, budget: 300000, spent: 0, voucher_limit: 900, uses_per_voucher: 1, start_date: '2026-11-01', end_date: '2027-01-31', terms: 'Buy one pack, get one pack free.', status: 'in_review' },
      { id: 'cm5', campaign_code: 'VC-25-011', title: 'Monsoon copay support', voucher_type: 'copay', product: 'pr2', benefit_kind: 'percent', benefit_value: 15, max_benefit: 2500, budget: 500000, spent: 468000, voucher_limit: 700, uses_per_voucher: 1, start_date: '2026-06-01', end_date: '2026-09-30', terms: 'Closed after the monsoon quarter.', status: 'closed' }
    ],
    voucher: [
      { id: 'v1', code: 'VCH-26-000001', campaign: 'cm1', patient: 'pt1', channel: 'web', issued_on: '2026-09-02', expires_on: '2026-11-11', uses_left: 1, status: 'issued' },
      { id: 'v2', code: 'VCH-26-000002', campaign: 'cm1', patient: 'pt2', channel: 'hub', issued_on: '2026-09-05', expires_on: '2027-02-19', uses_left: 2, status: 'issued' },
      { id: 'v3', code: 'VCH-26-000003', campaign: 'cm1', patient: 'pt3', channel: 'hcp', issued_on: '2026-09-09', expires_on: '2027-01-09', uses_left: 0, status: 'redeemed' },
      { id: 'v4', code: 'VCH-26-000004', campaign: 'cm1', patient: 'pt4', channel: 'field', issued_on: '2026-09-12', expires_on: '2026-11-20', uses_left: 2, status: 'issued' },
      { id: 'v5', code: 'VCH-26-000005', campaign: 'cm1', patient: 'pt5', channel: 'hcp', issued_on: '2026-09-14', expires_on: '2027-03-04', uses_left: 1, status: 'issued' },
      { id: 'v6', code: 'VCH-26-000006', campaign: 'cm2', patient: 'pt6', channel: 'web', issued_on: '2026-09-18', expires_on: '2026-10-20', uses_left: 1, status: 'expired' },
      { id: 'v7', code: 'VCH-26-000007', campaign: 'cm2', patient: 'pt7', channel: 'hub', issued_on: '2026-09-21', expires_on: '2027-01-21', uses_left: 0, status: 'redeemed' },
      { id: 'v8', code: 'VCH-26-000008', campaign: 'cm2', patient: 'pt8', channel: 'hcp', issued_on: '2026-09-24', expires_on: '2027-01-30', uses_left: 1, status: 'issued' },
      { id: 'v9', code: 'VCH-26-000009', campaign: 'cm1', patient: 'pt6', channel: 'web', issued_on: '2026-09-27', expires_on: '2026-11-28', uses_left: 2, status: 'issued' },
      { id: 'v10', code: 'VCH-26-000010', campaign: 'cm2', patient: 'pt1', channel: 'hub', issued_on: '2026-10-01', expires_on: '2027-02-10', uses_left: 1, status: 'issued' },
      { id: 'v11', code: 'VCH-26-000011', campaign: 'cm1', patient: 'pt7', channel: 'field', issued_on: '2026-10-03', expires_on: '2027-01-09', uses_left: 0, status: 'cancelled' },
      { id: 'v12', code: 'VCH-26-000012', campaign: 'cm5', patient: 'pt2', channel: 'web', issued_on: '2026-06-12', expires_on: '2026-09-30', uses_left: 0, status: 'redeemed' }
    ],
    redemption: [
      { id: 'r1', redemption_no: 'RD-26-000001', voucher: 'v3', pharmacy: 'ph1', bill_no: 'NP-4471', bill_date: '2026-10-02', packs: 2, bill_amount: 840, benefit_amount: 168, fraud_hits: [], status: 'settled', created_at: '2026-10-02' },
      { id: 'r2', redemption_no: 'RD-26-000002', voucher: 'v7', pharmacy: 'ph2', bill_no: 'VH-9120', bill_date: '2026-10-05', packs: 1, bill_amount: 310, benefit_amount: 310, fraud_hits: [], status: 'approved', created_at: '2026-10-05' },
      { id: 'r3', redemption_no: 'RD-26-000003', voucher: 'v1', pharmacy: 'ph1', bill_no: 'NP-4502', bill_date: '2026-10-09', packs: 2, bill_amount: 840, benefit_amount: 168, fraud_hits: [], status: 'approved', created_at: '2026-10-09' },
      { id: 'r4', redemption_no: 'RD-26-000004', voucher: 'v4', pharmacy: 'ph1', bill_no: 'NP-4533', bill_date: '2026-10-14', packs: 6, bill_amount: 85000, benefit_amount: 4000, fraud_hits: ['amount_cap'], status: 'flagged', created_at: '2026-10-14' },
      { id: 'r5', redemption_no: 'RD-26-000005', voucher: 'v2', pharmacy: 'ph3', bill_no: 'SL-2210', bill_date: '2026-10-16', packs: 1, bill_amount: 420, benefit_amount: 84, fraud_hits: [], status: 'approved', created_at: '2026-10-16' },
      { id: 'r6', redemption_no: 'RD-26-000006', voucher: 'v5', pharmacy: 'ph1', bill_no: 'NP-4561', bill_date: '2026-10-19', packs: 3, bill_amount: 3000, benefit_amount: 600, fraud_hits: ['velocity', 'pharmacy_spike'], status: 'flagged', created_at: '2026-10-19' },
      { id: 'r7', redemption_no: 'RD-26-000007', voucher: 'v8', pharmacy: 'ph4', bill_no: 'OH-7781', bill_date: '2026-10-21', packs: 1, bill_amount: 310, benefit_amount: 310, fraud_hits: [], status: 'approved', created_at: '2026-10-21' },
      { id: 'r8', redemption_no: 'RD-26-000008', voucher: 'v10', pharmacy: 'ph5', bill_no: 'MP-3305', bill_date: '2026-10-23', packs: 4, bill_amount: 1240, benefit_amount: 310, fraud_hits: [], status: 'submitted', created_at: '2026-10-23' },
      { id: 'r9', redemption_no: 'RD-26-000009', voucher: 'v9', pharmacy: 'ph2', bill_no: 'VH-9188', bill_date: '2026-10-25', packs: 1, bill_amount: 151000, benefit_amount: 4000, fraud_hits: ['amount_cap', 'wrong_product'], status: 'flagged', created_at: '2026-10-25' },
      { id: 'r10', redemption_no: 'RD-26-000010', voucher: 'v12', pharmacy: 'ph1', bill_no: 'NP-4101', bill_date: '2026-09-08', packs: 2, bill_amount: 620, benefit_amount: 93, fraud_hits: [], status: 'settled', created_at: '2026-09-08' },
      { id: 'r11', redemption_no: 'RD-26-000011', voucher: 'v11', pharmacy: 'ph3', bill_no: 'SL-2154', bill_date: '2026-10-01', packs: 1, bill_amount: 420, benefit_amount: 84, fraud_hits: ['expired'], status: 'rejected', created_at: '2026-10-01' }
    ],
    settlement: [
      { id: 's1', settlement_no: 'ST-26-0001', pharmacy: 'ph1', month: '2026-09-30', lines: 1, amount: 93, payment_ref: 'UTR-5582104', status: 'paid' },
      { id: 's2', settlement_no: 'ST-26-0002', pharmacy: 'ph1', month: '2026-10-31', lines: 2, amount: 336, payment_ref: '', status: 'draft' },
      { id: 's3', settlement_no: 'ST-26-0003', pharmacy: 'ph2', month: '2026-10-31', lines: 1, amount: 310, payment_ref: '', status: 'approved' },
      { id: 's4', settlement_no: 'ST-26-0004', pharmacy: 'ph3', month: '2026-10-31', lines: 1, amount: 84, payment_ref: '', status: 'disputed' }
    ],
    activity: [
      { id: 'a1', entity: 'campaign', ref: 'cm1', ts: '2026-08-12', text: 'Campaign created by Isha Menon' },
      { id: 'a2', entity: 'campaign', ref: 'cm1', ts: '2026-08-14', text: 'Submitted for review' },
      { id: 'a3', entity: 'campaign', ref: 'cm1', ts: '2026-08-19', text: 'Went live' },
      { id: 'a4', entity: 'voucher', ref: 'cm1', ts: '2026-09-02', text: 'Voucher VCH-26-000001 issued' },
      { id: 'a5', entity: 'voucher', ref: 'cm1', ts: '2026-09-09', text: 'Voucher VCH-26-000003 issued' }
    ]
  });
})();
