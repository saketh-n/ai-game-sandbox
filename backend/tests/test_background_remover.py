"""Tests for flood-fill background removal."""

import numpy as np
from PIL import Image

from sprite_processing.background_remover import BackgroundRemover


def make_image(data: np.ndarray) -> Image.Image:
    return Image.fromarray(data.astype(np.uint8), 'RGB')


def white_canvas(height: int, width: int) -> np.ndarray:
    return np.full((height, width, 3), 255, dtype=np.uint8)


def test_border_background_removed():
    data = white_canvas(40, 40)
    data[10:30, 10:30] = [200, 0, 0]  # red square in the middle
    result = BackgroundRemover().remove_background(make_image(data))
    alpha = np.array(result)[:, :, 3]

    assert alpha[0, 0] == 0
    assert alpha[39, 39] == 0
    assert (alpha[10:30, 10:30] == 255).all()


def test_enclosed_background_preserved():
    data = white_canvas(40, 40)
    data[8:32, 8:32] = [200, 0, 0]
    data[16:20, 16:20] = [255, 255, 255]  # white "eye" enclosed by the sprite
    result = BackgroundRemover().remove_background(make_image(data))
    alpha = np.array(result)[:, :, 3]

    assert alpha[0, 0] == 0  # outer background removed
    assert (alpha[16:20, 16:20] == 255).all()  # enclosed white stays opaque


def test_specific_color_with_tolerance():
    # Production call: background_color=(255,255,255), tolerance=40, near-white bg
    data = np.full((40, 40, 3), 250, dtype=np.uint8)
    data[8:32, 8:32] = [0, 120, 0]
    data[15:18, 15:18] = [255, 255, 255]  # enclosed pure-white patch
    result = BackgroundRemover().remove_background(
        make_image(data), background_color=(255, 255, 255), tolerance=40
    )
    alpha = np.array(result)[:, :, 3]

    assert alpha[0, 0] == 0
    assert (alpha[8:32, 8:32] == 255).all()


def test_sprite_touching_edge():
    data = white_canvas(40, 40)
    data[10:30, 0:20] = [200, 0, 0]  # sprite flush against the left edge
    result = BackgroundRemover().remove_background(make_image(data))
    alpha = np.array(result)[:, :, 3]

    assert (alpha[10:30, 0:20] == 255).all()
    assert alpha[0, 0] == 0
    assert alpha[35, 35] == 0


def test_all_background_image():
    result = BackgroundRemover().remove_background(make_image(white_canvas(20, 20)))
    alpha = np.array(result)[:, :, 3]

    assert (alpha == 0).all()


def test_returns_rgba_and_does_not_mutate_input():
    data = white_canvas(20, 20)
    data[5:15, 5:15] = [0, 0, 200]
    img = make_image(data)
    result = BackgroundRemover().remove_background(img)

    assert result.mode == 'RGBA'
    assert img.mode == 'RGB'
    assert np.array_equal(np.array(img), data)
