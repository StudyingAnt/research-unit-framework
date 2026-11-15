import unittest

from research_program_framework.merge import merge_text


class MergeTests(unittest.TestCase):
    def test_unchanged_and_identical_choices(self):
        for base, local, new, expected in [(b'a', b'a', b'b', b'b'), (b'a', b'b', b'a', b'b'),
                                           (b'a', b'b', b'b', b'b'), (b'\0', b'\0', b'\1', b'\1')]:
            with self.subTest(base=base, local=local, new=new):
                self.assertEqual(merge_text(base, local, new).content, expected)

    def test_disjoint_edits_preserve_bytes(self):
        self.assertEqual(merge_text(b'a\r\nb\r\nc', b'A\r\nb\r\nc', b'a\r\nb\r\nC').content,
                         b'A\r\nb\r\nC')
        self.assertEqual(merge_text('가\n나\n다\n'.encode(), '가\n나\n라\n'.encode(),
                                   '마\n나\n다\n'.encode()).content, '마\n나\n라\n'.encode())

    def test_overlap_insert_delete_conflicts(self):
        for base, local, new in [(b'a\n', b'b\n', b'c\n'), (b'a\n', b'x\na\n', b'y\na\n'),
                                 (b'a\nb\n', b'b\n', b'A\nb\n'), (b'\0a', b'\0b', b'\0c')]:
            with self.subTest(base=base):
                self.assertIsNone(merge_text(base, local, new).content)

    def test_conflict_markers_refused(self):
        self.assertIsNone(merge_text(b'old', b'old', b'<<<<<<< local\nx\n=======\ny\n>>>>>>> upstream\n').content)

    def test_resource_bound_requires_resolution(self):
        self.assertIsNone(merge_text(b'a\n' * 10001, b'b\n' * 10001, b'c\n' * 10001).content)
