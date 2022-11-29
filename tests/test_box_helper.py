import unittest

from box import box


class BoxHelperTest(unittest.TestCase):
    def test_box_none(self) -> None:
        self.assertEqual(0, len(box()))
        self.assertEqual(0, len(box(None)))
