import unittest

from scripts.resolve_conflict_markers import resolve_text


class ConflictResolverTests(unittest.TestCase):
    def setUp(self):
        self.sample = (
            "a\n"
            "<<<<<<< branch-a\n"
            "ours1\n"
            "ours2\n"
            "=======\n"
            "theirs1\n"
            ">>>>>>> main\n"
            "z\n"
        )

    def test_ours(self):
        self.assertEqual(resolve_text(self.sample, "ours"), "a\nours1\nours2\nz\n")

    def test_theirs(self):
        self.assertEqual(resolve_text(self.sample, "theirs"), "a\ntheirs1\nz\n")

    def test_both(self):
        self.assertEqual(resolve_text(self.sample, "both"), "a\nours1\nours2\ntheirs1\nz\n")


if __name__ == "__main__":
    unittest.main()
