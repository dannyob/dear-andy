import pytest
from src.pdf_tools.extract_svg import optimize_svg_precision


def test_optimize_svg_precision_basic():
    """Test basic coordinate rounding."""
    svg_input = '<path d="M0.123456789 1.987654321L2.5 3.0"/>'
    result = optimize_svg_precision(svg_input, precision=2)
    assert 'M0.12 1.99L2.5 3' in result
    assert '0.123456789' not in result


def test_optimize_svg_precision_matrix():
    """Test matrix transformation rounding."""
    svg_input = '<g transform="matrix(1,0,0,-.99999997,37.5427,127.518009)"/>'
    result = optimize_svg_precision(svg_input, precision=2)
    assert 'matrix(1,0,0,-1,37.54,127.52)' in result
    assert '.99999997' not in result
    assert '127.518009' not in result


def test_optimize_svg_precision_preserves_integers():
    """Test that integers are preserved without decimals."""
    svg_input = '<rect x="10" y="20" width="100.0" height="200.0"/>'
    result = optimize_svg_precision(svg_input, precision=2)
    assert 'x="10"' in result
    assert 'y="20"' in result
    assert 'width="100"' in result
    assert 'height="200"' in result


def test_optimize_svg_precision_negative_numbers():
    """Test negative number handling."""
    svg_input = '<path d="M-12.3456 -7.8901"/>'
    result = optimize_svg_precision(svg_input, precision=2)
    assert 'M-12.35 -7.89' in result
    assert '-12.3456' not in result


def test_optimize_svg_precision_custom_precision():
    """Test with different precision values."""
    svg_input = '<path d="M1.23456789 2.98765432"/>'

    result_1 = optimize_svg_precision(svg_input, precision=1)
    assert 'M1.2 3' in result_1
    assert '1.23456789' not in result_1

    result_3 = optimize_svg_precision(svg_input, precision=3)
    assert 'M1.235 2.988' in result_3


def test_optimize_svg_precision_preserves_ids():
    """Test that IDs and other non-coordinate text are preserved."""
    svg_input = '<clipPath id="clip_123"><path d="M1.123456 2.987654"/></clipPath>'
    result = optimize_svg_precision(svg_input, precision=2)
    assert 'id="clip_123"' in result
    assert 'M1.12 2.99' in result
    assert '1.123456' not in result
