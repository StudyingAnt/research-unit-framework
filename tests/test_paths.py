from dataclasses import replace
import os
import socket
import stat
from unittest import mock

from research_program_framework import paths
from research_program_framework.paths import (ValidationError, fingerprint_file,
    read_payload_file, validate_path_set, validate_payload, validate_relative_path)
from support import PayloadCase


class PathTests(PayloadCase):
    def test_canonical_names(self):
        for value in ['AGENTS.md', '.research-framework/runtime.pyz', 'data/.gitkeep',
                      'templates/report.ko.md', 'a-b_c.1/x']:
            with self.subTest(value=value):
                self.assertEqual(validate_relative_path(value), value)

    def test_unsafe_names(self):
        for value in ['', '.', '..', '/escape', 'a/../b', 'a/./b', 'a//b', 'a/',
                      r'a\b', 'X:/escape', r'X:\escape', '//server/share', 'a:b',
                      'a\x00b', 'a\nb', 'a\tb', 'a%2fb', 'file ', 'file.',
                      '.git/config', 'a/.GIT/config', '.hg/x', '.svn/x',
                      'DEVELOPMENT_CONTEXT.local.md', 'CON', 'nul.txt', 'AUX', 'com1.py',
                      'LPT9.log', '\u202eabc', 'caf\u00e9.md', '\ud800', 'a' * 256,
                      '/'.join(['a'] * 129), 'a/' * 2049 + 'x', None, 7]:
            with self.subTest(value=repr(value)), self.assertRaises(ValidationError):
                validate_relative_path(value)

    def test_collision_and_prefix_conflicts(self):
        for values in [('x', 'x'), ('x', 'X'), ('x', 'x/y'), ('X', 'x/y'),
                       ('A/one', 'a/two'), ('x/Dir/one', 'x/dir/two')]:
            with self.subTest(values=values), self.assertRaises(ValidationError):
                validate_path_set(values)
        self.assertEqual(validate_path_set(['a/x', 'a/y']), ('a/x', 'a/y'))

    def test_hash_size_mode_and_no_content_changes(self):
        item = self.write()
        before = {p.relative_to(self.payload): (p.stat().st_mode, p.stat().st_size,
                  p.stat().st_mtime_ns, p.stat().st_ctime_ns) for p in self.payload.rglob('*')}
        self.assertEqual(fingerprint_file(self.payload, item.path), item)
        self.assertEqual(validate_payload(self.payload, [item]), (item,))
        self.assertEqual(read_payload_file(self.payload, item.path), b'Synthetic template\n')
        after = {p.relative_to(self.payload): (p.stat().st_mode, p.stat().st_size,
                 p.stat().st_mtime_ns, p.stat().st_ctime_ns) for p in self.payload.rglob('*')}
        self.assertEqual(before, after)

    def test_empty_and_executable_files(self):
        first = self.write('empty', b'')
        second = self.write('tools/helper.py', b'# synthetic\n', 0o755)
        self.assertEqual(validate_payload(self.payload, [first, second]), (first, second))

    def test_content_size_and_mode_mismatches(self):
        item = self.write()
        for bad in [replace(item, sha256='0' * 64), replace(item, size=item.size + 1),
                    replace(item, size=item.size - 1), replace(item, mode='0755')]:
            with self.subTest(bad=bad), self.assertRaises(ValidationError):
                validate_payload(self.payload, [bad])

    def test_unlisted_and_missing_files(self):
        item = self.write()
        extra = self.payload / 'extra'
        extra.write_bytes(b'not listed')
        with self.assertRaises(ValidationError):
            validate_payload(self.payload, [item])
        extra.unlink()
        (self.payload / item.path).unlink()
        with self.assertRaises(ValidationError):
            validate_payload(self.payload, [item])

    def test_extra_empty_directory(self):
        item = self.write()
        (self.payload / 'extra').mkdir()
        with self.assertRaises(ValidationError):
            validate_payload(self.payload, [item])

    def test_symlink_file_and_dangling_link(self):
        item = self.write('entry')
        target = self.payload / 'entry'
        target.rename(self.root / 'outside')
        for destination in [self.root / 'outside', self.root / 'missing']:
            target.symlink_to(destination)
            with self.subTest(destination=destination.name), self.assertRaises(ValidationError):
                fingerprint_file(self.payload, 'entry')
            with self.assertRaises(ValidationError):
                validate_payload(self.payload, [item])
            target.unlink()
        self.assertEqual((self.root / 'outside').read_bytes(), b'Synthetic template\n')

    def test_symlink_parent_and_root(self):
        item = self.write()
        (self.payload / 'templates').rename(self.root / 'outside')
        (self.payload / 'templates').symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaises(ValidationError):
            fingerprint_file(self.payload, item.path)
        alias = self.root / 'alias'
        alias.symlink_to(self.payload, target_is_directory=True)
        with self.assertRaises(ValidationError):
            validate_payload(alias, [item])
        with self.assertRaises(ValidationError):
            fingerprint_file(alias / 'templates', 'report.en.md')

    def test_root_parent_traversal(self):
        self.write('entry')
        with self.assertRaises(ValidationError):
            fingerprint_file(self.payload / '..' / 'payload', 'entry')

    def test_hard_link(self):
        item = self.write('entry')
        os.link(self.payload / 'entry', self.root / 'alias')
        with self.assertRaises(ValidationError):
            validate_payload(self.payload, [item])
        with self.assertRaises(ValidationError):
            fingerprint_file(self.payload, 'entry')

    def test_fifo(self):
        item = self.write()
        fifo = self.payload / 'pipe'
        os.mkfifo(fifo)
        with self.assertRaises(ValidationError):
            validate_payload(self.payload, [item])
        with self.assertRaises(ValidationError):
            fingerprint_file(self.payload, 'pipe')

    def test_socket_metadata_rejected(self):
        item = self.write()
        self.write('socket', b'')
        original = paths.os.stat
        def inspect(name, *args, **kwargs):
            info = original(name, *args, **kwargs)
            if name == 'socket':
                values = list(info)
                values[0] = stat.S_IFSOCK | 0o644
                return os.stat_result(values)
            return info
        with mock.patch.object(paths.os, 'stat', side_effect=inspect):
            # Preserve capability detection while instrumenting metadata reads.
            with mock.patch.object(paths.os, 'supports_dir_fd', {paths.os.open, paths.os.stat}):
                with self.assertRaisesRegex(ValidationError, 'single-link regular'):
                    fingerprint_file(self.payload, 'socket')

    def test_real_socket_when_permitted(self):
        item = self.write()
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        try:
            sock.bind(str(self.payload / 'socket'))
        except PermissionError:
            self.skipTest('Sandbox disallows AF_UNIX bind; socket metadata rejection is tested separately')
        with self.assertRaisesRegex(ValidationError, 'single-link regular'):
            fingerprint_file(self.payload, 'socket')

    def test_file_swapped_for_symlink_before_open(self):
        self.write('entry')
        outside = self.root / 'outside'
        outside.write_bytes(b'private synthetic bytes')
        original = paths.os.open
        def open_file(name, flags, *args, **kwargs):
            if name == 'entry':
                (self.payload / 'entry').unlink()
                (self.payload / 'entry').symlink_to(outside)
            return original(name, flags, *args, **kwargs)
        with mock.patch.object(paths.os, 'open', side_effect=open_file):
            with mock.patch.object(paths.os, 'supports_dir_fd', {paths.os.open, paths.os.stat}):
                with self.assertRaises(ValidationError):
                    fingerprint_file(self.payload, 'entry')
        self.assertEqual(outside.read_bytes(), b'private synthetic bytes')

    def test_parent_swapped_for_symlink_before_open(self):
        item = self.write()
        original = paths.os.open
        def open_directory(name, flags, *args, **kwargs):
            if name == 'templates':
                (self.payload / 'templates').rename(self.root / 'outside')
                (self.payload / 'templates').symlink_to(self.root / 'outside', target_is_directory=True)
            return original(name, flags, *args, **kwargs)
        with mock.patch.object(paths.os, 'open', side_effect=open_directory):
            with mock.patch.object(paths.os, 'supports_dir_fd', {paths.os.open, paths.os.stat}):
                with self.assertRaises(ValidationError):
                    fingerprint_file(self.payload, item.path)

    def test_unsafe_permissions(self):
        item = self.write('entry')
        for mode in [0o600, 0o666, 0o4755, 0o2755, 0o1644]:
            (self.payload / 'entry').chmod(mode)
            with self.subTest(mode=mode), self.assertRaises(ValidationError):
                validate_payload(self.payload, [item])

    def test_byte_limits(self):
        item = self.write('entry', b'12345')
        with self.assertRaises(ValidationError):
            read_payload_file(self.payload, 'entry', 4)
        for options in [{'max_file_bytes': 4}, {'max_total_bytes': 4},
                        {'max_file_bytes': -1}, {'max_total_bytes': True}]:
            with self.subTest(options=options), self.assertRaises(ValidationError):
                validate_payload(self.payload, [item], **options)

    def test_invalid_fingerprint_records(self):
        item = self.write()
        for bad in [replace(item, size=True), replace(item, size=-1),
                    replace(item, sha256='bad'), replace(item, mode='0777'), object()]:
            with self.subTest(bad=repr(bad)), self.assertRaises(ValidationError):
                validate_payload(self.payload, [bad])

    def test_file_growth_during_read(self):
        item = self.write('entry')
        original = paths.os.read
        changed = False
        def read(fd, size):
            nonlocal changed
            data = original(fd, size)
            if not changed:
                changed = True
                with (self.payload / 'entry').open('ab') as stream:
                    stream.write(b'changed')
            return data
        with mock.patch.object(paths.os, 'read', side_effect=read), self.assertRaises(ValidationError):
            fingerprint_file(self.payload, item.path)

    def test_name_replacement_during_read(self):
        item = self.write('entry')
        replacement = self.root / 'replacement'
        replacement.write_bytes(b'Synthetic template\n')
        original = paths.os.read
        changed = False
        def read(fd, size):
            nonlocal changed
            data = original(fd, size)
            if not changed:
                changed = True
                os.replace(replacement, self.payload / 'entry')
            return data
        with mock.patch.object(paths.os, 'read', side_effect=read), self.assertRaises(ValidationError):
            fingerprint_file(self.payload, item.path)

    def test_earlier_file_changed_after_its_hash(self):
        first = self.write('a', b'first')
        second = self.write('b', b'second')
        original = paths._read_file
        def read(fd, relative, *args, **kwargs):
            if relative == 'b':
                (self.payload / 'a').write_bytes(b'other')
            return original(fd, relative, *args, **kwargs)
        with mock.patch.object(paths, '_read_file', side_effect=read), self.assertRaises(ValidationError):
            validate_payload(self.payload, [first, second])

    def test_unavailable_secure_platform(self):
        self.write('entry')
        with mock.patch.object(paths.os, 'supports_dir_fd', set()), self.assertRaises(ValidationError):
            fingerprint_file(self.payload, 'entry')
