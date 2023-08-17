from django.core.exceptions import FieldError

from workspaces.Tenant3.null_fk.models import NullChoice, NullInner, NullOuterA, NullOuterB, NullPoll
from zelthy.test.base import BaseTestCase

class NullQueriesTests(BaseTestCase):

    def test_none_as_null(self):
        """
        Regression test for the use of None as a query value.

        None is interpreted as an SQL NULL, but only in __exact and __iexact
        queries.
        Set up some initial polls and choices
        """
        p1 = NullPoll(question="Why?")
        p1.save()
        c1 = NullChoice(poll=p1, choice="Because.")
        c1.save()
        c2 = NullChoice(poll=p1, choice="Why Not?")
        c2.save()

        # Exact query with value None returns nothing ("is NULL" in sql,
        # but every 'id' field has a value).
        self.assertSequenceEqual(NullChoice.objects.filter(choice__exact=None), [])

        # The same behavior for iexact query.
        self.assertSequenceEqual(NullChoice.objects.filter(choice__iexact=None), [])

        # Excluding the previous result returns everything.
        self.assertSequenceEqual(
            NullChoice.objects.exclude(choice=None).order_by("id"), [c1, c2]
        )


    def test_unsaved(self):
        poll = NullPoll(question="How?")
        msg = (
            "'NullPoll' instance needs to have a primary key value before this "
            "relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            poll.nullchoice_set.all()

    def test_reverse_relations(self):
        """
        Querying across reverse relations and then another relation should
        insert outer joins correctly so as not to exclude results.
        """
        obj = NullOuterA.objects.create()
        self.assertSequenceEqual(NullOuterA.objects.filter(nullinner__third=None), [obj])
        self.assertSequenceEqual(NullOuterA.objects.filter(nullinner__third__data=None), [obj])

        inner = NullInner.objects.create(first=obj)
        self.assertSequenceEqual(
            NullInner.objects.filter(first__nullinner__third=None), [inner]
        )

        # Ticket #13815: check if <reverse>_isnull=False does not produce
        # faulty empty lists
        outerb = NullOuterB.objects.create(data="reverse")
        self.assertSequenceEqual(NullOuterB.objects.filter(nullinner__isnull=False), [])
        NullInner.objects.create(first=obj)
        self.assertSequenceEqual(NullOuterB.objects.exclude(nullinner__isnull=False), [outerb])