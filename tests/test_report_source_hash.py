import hashlib

import pytest

from scripts.audit_course_report import check_source


def test_historical_text_hash_requires_explicit_line_ending_reconstruction(tmp_path):
    source = tmp_path / "source.py"
    source.write_bytes(b"x = 1\ny = 2\n")
    expected = hashlib.sha256(b"x = 1\r\ny = 2\r\n").hexdigest()
    with pytest.raises(ValueError, match="source hash mismatch"):
        check_source(source, expected)
    assert check_source(source, expected, True) == "recorded_bytes_reconstructed_by_line_endings_only"
    source.write_bytes(b"x = 2\ny = 2\n")
    with pytest.raises(ValueError, match="source hash mismatch"):
        check_source(source, expected, True)
