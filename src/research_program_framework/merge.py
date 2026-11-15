"""Conservative in-memory, byte-preserving three-way text merging."""

from dataclasses import dataclass
from difflib import SequenceMatcher, unified_diff
import re
from typing import Optional


def is_text(value: bytes) -> bool:
    if b'\0' in value:
        return False
    try:
        value.decode('utf-8')
        return True
    except UnicodeError:
        return False


def has_markers(value: bytes) -> bool:
    return bool(re.search(rb'(?m)^(?:<{7}|>{7}|\|{7})(?: |\r?$)', value))


@dataclass(frozen=True)
class MergeResult:
    content: Optional[bytes]
    reason: str


def _edits(base, changed):
    return [(i, j, changed[a:b]) for op, i, j, a, b in
            SequenceMatcher(None, base, changed, autojunk=False).get_opcodes() if op != 'equal']


def merge_text(base: bytes, local: bytes, incoming: bytes) -> MergeResult:
    """Merge disjoint line edits; ambiguous overlaps require explicit resolution.

    An insertion at a changed range boundary is deliberately conservative.
    No temporary files, subprocesses, newline normalization, or markers are used.
    """
    if local == incoming:
        result = local
    elif local == base:
        result = incoming
    elif incoming == base:
        result = local
    else:
        if not all(is_text(value) for value in (base, local, incoming)):
            return MergeResult(None, 'Both sides changed binary or non-UTF-8 content')
        if any(len(value) > 1024 * 1024 or value.count(b'\n') > 10000 for value in (base, local, incoming)):
            return MergeResult(None, 'Text merge resource bound; explicit resolution required')
        lines = base.splitlines(keepends=True)
        left, right = _edits(lines, local.splitlines(keepends=True)), _edits(lines, incoming.splitlines(keepends=True))
        for start, end, content in left:
            for other_start, other_end, other_content in right:
                overlap = (max(start, other_start) < min(end, other_end)
                           or start == end and other_start <= start <= other_end
                           or other_start == other_end and start <= other_start <= end)
                if overlap and (start, end, content) != (other_start, other_end, other_content):
                    return MergeResult(None, 'Overlapping or ambiguous text edits')
        edits = list(left)
        edits.extend(edit for edit in right if edit not in edits)
        output, cursor = [], 0
        for start, end, content in sorted(edits, key=lambda edit: (edit[0], edit[1])):
            output.extend(lines[cursor:start])
            output.extend(content)
            cursor = end
        output.extend(lines[cursor:])
        result = b''.join(output)
    if has_markers(result):
        return MergeResult(None, 'Unresolved conflict markers')
    return MergeResult(result, 'Byte-identical choice or disjoint text merge')


def diff_text(before: Optional[bytes], after: Optional[bytes]) -> str:
    old, new = before or b'', after or b''
    if not is_text(old) or not is_text(new):
        return 'Binary content; inspect the recorded fingerprints'
    return ''.join(unified_diff(old.decode().splitlines(keepends=True), new.decode().splitlines(keepends=True),
                                fromfile='local', tofile='planned'))
