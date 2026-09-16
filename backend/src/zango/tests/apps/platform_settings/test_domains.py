"""Automatic subdomain allocation.

The failure modes worth pinning down are the quiet ones: a base domain that
looks fine but produces unreachable hostnames, a collision that loses an app
its domain, and an allocation error that takes the whole app launch down with
it.
"""

import unittest

from zango.apps.shared.platform_settings.domains import (
    ADJECTIVES,
    NOUNS,
    candidate_domains,
    is_valid_base_domain,
    normalise_base_domain,
    random_label,
)


class BaseDomainTests(unittest.TestCase):
    def test_normalises_what_people_actually_paste(self):
        for raw, expected in [
            ("zelthy.com", "zelthy.com"),
            ("  ZELTHY.com  ", "zelthy.com"),
            ("https://zelthy.com", "zelthy.com"),
            ("http://zelthy.com/", "zelthy.com"),
            ("https://zelthy.com/apps/x", "zelthy.com"),
            (".zelthy.com.", "zelthy.com"),
        ]:
            self.assertEqual(normalise_base_domain(raw), expected, raw)

    def test_accepts_real_domains(self):
        for good in ("zelthy.com", "apps.zelthy.com", "zango.io", "a-b.co.uk"):
            self.assertTrue(is_valid_base_domain(good), good)

    def test_rejects_things_that_would_not_resolve(self):
        for bad in ("", "   ", "localhost", "zelthy", "-bad.com", "bad-.com",
                    "spaces here.com", "zelthy..com", None):
            self.assertFalse(is_valid_base_domain(bad), repr(bad))

    def test_scheme_is_stripped_before_validation(self):
        self.assertTrue(is_valid_base_domain("https://zelthy.com"))


class LabelTests(unittest.TestCase):
    def test_label_is_two_words(self):
        label = random_label()
        self.assertRegex(label, r"^[a-z]+-[a-z]+$")

    def test_widened_label_adds_entropy(self):
        self.assertRegex(random_label(widen=True), r"^[a-z]+-[a-z]+-[0-9a-f]{4}$")

    def test_word_lists_are_clean_hostname_labels(self):
        """A word with an apostrophe or capital would produce a dead host."""
        for word in list(ADJECTIVES) + list(NOUNS):
            self.assertRegex(word, r"^[a-z]+$", word)

    def test_word_lists_have_no_duplicates(self):
        self.assertEqual(len(ADJECTIVES), len(set(ADJECTIVES)))
        self.assertEqual(len(NOUNS), len(set(NOUNS)))

    def test_namespace_is_big_enough_to_be_worth_retrying(self):
        self.assertGreater(len(ADJECTIVES) * len(NOUNS), 2000)


class CandidateTests(unittest.TestCase):
    def test_candidates_are_under_the_base_domain(self):
        for host in candidate_domains("zelthy.com", attempts=5):
            self.assertTrue(host.endswith(".zelthy.com"), host)
            self.assertRegex(host, r"^[a-z0-9-]+\.zelthy\.com$")

    def test_candidates_vary(self):
        """A generator that returned the same name every time would make the
        retry-on-collision loop useless."""
        hosts = list(candidate_domains("zelthy.com", attempts=12))
        self.assertGreater(len(set(hosts)), 6)

    def test_base_domain_is_normalised_in_candidates(self):
        host = next(iter(candidate_domains("https://Zelthy.com/", attempts=1)))
        self.assertTrue(host.endswith(".zelthy.com"), host)

    def test_widening_kicks_in_for_later_attempts(self):
        hosts = list(candidate_domains("zelthy.com", attempts=12))
        widened = [h for h in hosts if h.count("-") >= 2]
        self.assertTrue(widened, "later attempts should widen the namespace")
