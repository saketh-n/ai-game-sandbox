"""Tests for sprite-sheet extraction: overlap-merge and column-gap fallbacks."""

import numpy as np
import pytest
from PIL import Image

from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer


@pytest.fixture
def analyzer():
    return SpriteSheetAnalyzer(api_key="test-key-no-network-calls")


def make_strip(width: int, height: int, blocks: list) -> Image.Image:
    """Build a transparent RGBA strip with opaque colored blocks.

    blocks: list of (left, top, right, bottom, (r, g, b)) rectangles.
    """
    data = np.zeros((height, width, 4), dtype=np.uint8)
    for left, top, right, bottom, color in blocks:
        data[top:bottom, left:right] = [*color, 255]
    return Image.fromarray(data, 'RGBA')


RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)
YELLOW = (200, 200, 0)


def test_clean_strip_extracts_expected_frames(analyzer):
    strip = make_strip(200, 50, [
        (10, 10, 40, 45, RED),
        (80, 10, 110, 45, GREEN),
        (150, 10, 180, 45, BLUE),
    ])
    frames, w, h = analyzer._extract_horizontal_with_gaps(strip, expected_frames=3)

    assert len(frames) == 3
    assert (w, h) == (30, 35)
    assert all(f.size == (w, h) for f in frames)


def test_detached_tail_merged(analyzer):
    # Sprite 2 is a body plus a detached blob 2px above it, sharing its x-range.
    # Old behavior: 4 components != 3 expected -> grid fallback. New: merge -> 3.
    strip = make_strip(220, 60, [
        (10, 20, 40, 55, RED),
        (80, 20, 110, 55, GREEN),   # body
        (85, 10, 105, 18, GREEN),   # detached "hair" overlapping body's x-range
        (160, 20, 190, 55, BLUE),
    ])
    frames, w, h = analyzer._extract_horizontal_with_gaps(strip, expected_frames=3)

    assert len(frames) == 3
    # Merged frame 2 spans hair top (y=10) to body bottom (y=55) -> height 45,
    # so the shared canvas is 45 tall (others are 35).
    assert h == 45


def test_merge_boxes_unit(analyzer):
    def box(left, right, top=0, bottom=10):
        return {'left': left, 'right': right, 'top': top, 'bottom': bottom,
                'area': (bottom - top) * (right - left)}

    # Overlapping pair merges
    merged = analyzer._merge_overlapping_boxes([box(0, 20), box(15, 30)])
    assert len(merged) == 1
    assert (merged[0]['left'], merged[0]['right']) == (0, 30)

    # Near pair (gap 3 <= 4) merges
    merged = analyzer._merge_overlapping_boxes([box(0, 20), box(23, 40)])
    assert len(merged) == 1

    # Far pair (gap 10) stays separate
    merged = analyzer._merge_overlapping_boxes([box(0, 20), box(30, 50)])
    assert len(merged) == 2

    # Union bbox covers both inputs vertically
    merged = analyzer._merge_overlapping_boxes(
        [box(0, 20, top=10, bottom=30), box(5, 25, top=0, bottom=15)]
    )
    assert len(merged) == 1
    assert (merged[0]['top'], merged[0]['bottom']) == (0, 30)
    assert merged[0]['area'] == 30 * 25


def test_column_gap_slicing_uneven_spacing(analyzer):
    # Four blocks with irregular widths and spacing
    strip = make_strip(300, 40, [
        (5, 5, 30, 35, RED),
        (42, 5, 90, 35, GREEN),
        (170, 5, 185, 35, BLUE),
        (250, 5, 295, 35, YELLOW),
    ])
    frames = analyzer._extract_by_column_gaps(strip)

    assert frames is not None
    assert len(frames) == 4
    # Tight-cropped to content
    assert [f.width for f in frames] == [25, 48, 15, 45]
    assert all(f.height == 30 for f in frames)
    # Each frame contains its own block's color
    for frame, color in zip(frames, [RED, GREEN, BLUE, YELLOW]):
        assert tuple(np.array(frame)[0, 0][:3]) == color


def test_gap_fallback_used_on_count_mismatch(analyzer):
    # 4 clearly gapped sprites but caller expects 3: column-gap slicing should
    # win and return the actual 4 frames, not 3 equal grid slices.
    strip = make_strip(280, 40, [
        (10, 5, 40, 35, RED),
        (80, 5, 110, 35, GREEN),
        (150, 5, 180, 35, BLUE),
        (220, 5, 250, 35, YELLOW),
    ])
    frames, w, h = analyzer._extract_horizontal_with_gaps(strip, expected_frames=3)

    assert len(frames) == 4
    assert (w, h) == (30, 30)


def test_grid_last_resort(analyzer):
    # Fully opaque sheet: one component, no transparent column gaps ->
    # grid slicing is the only remaining option.
    data = np.zeros((40, 200, 4), dtype=np.uint8)
    data[:, :] = [128, 128, 128, 255]
    sheet = Image.fromarray(data, 'RGBA')

    frames, w, h = analyzer._extract_horizontal_with_gaps(sheet, expected_frames=4)

    assert len(frames) == 4
    assert w == 50  # 200 / 4 equal slices
