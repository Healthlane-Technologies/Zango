"""
zas_core - the Zango App Studio runtime.

Copied verbatim into every app at backend/zas_core/ (Phase 2). Do not edit it in
an app: change the skill's copy and re-copy. Generated modules import from here;
hand-written logic lives in each module's hooks.py, never in this package.

    spec.py      the resolved spec (spec.json) + model / hook / workflow lookup
    expr.py      expression grammar -> Q / evaluate
    access.py    role, row scoping, parent filter, action checks
    records.py   sequences, computed fields, display values
    dupes.py     duplicate detection (exact / normalised / fuzzy)
    app_user.py  login provisioning for records that own a login
    mixins.py    ZasTableMixin, ZasFormMixin, ZasActionFormMixin, ZasWorkflowMixin, ZasCrudViewMixin
    detail.py    ZasDetail: the 360 payload on fetch_item_details
    notify.py    the single notification seam
    models.py    ZasSequence
"""

ZAS_CORE_VERSION = "0.1.0"
