"""Free design: every hero or transactional entity with a list page needs a record page."""

import unittest

from zango.apps.agent_mode.spec_tools import SpecWorkbench


def _doc(detail_views):
    return {
        "modules": [
            {
                "entities": [
                    {"code": "purchase_request", "kind": "transactional"},
                    {"code": "supplier", "kind": "master"},
                ]
            }
        ],
        "pages": [
            {"code": "requests", "type": "crud", "entity": "purchase_request"},
            {"code": "suppliers", "type": "crud", "entity": "supplier"},
        ],
        "detail_views": detail_views,
    }


class RecordPageRuleTests(unittest.TestCase):
    def test_transactional_entity_without_detail_view_is_listed(self):
        self.assertEqual(
            SpecWorkbench._entities_without_record_page(_doc([])), ["purchase_request"]
        )

    def test_detail_view_satisfies_it(self):
        doc = _doc([{"code": "request_360", "hero": "purchase_request"}])
        self.assertEqual(SpecWorkbench._entities_without_record_page(doc), [])


if __name__ == "__main__":
    unittest.main()
