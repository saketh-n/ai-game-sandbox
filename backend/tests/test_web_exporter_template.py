"""Tests for the game HTML template: load-time collectible placement."""

import inspect
import json
import re
import shutil
import subprocess

import pytest

from scene_builder.web_exporter import WebGameExporter


MINIMAL_CONFIG = {
    'name': 'TestGame',
    'background': {'path': 'bg.png', 'width': 1280, 'height': 720},
    'physics': {
        'platforms': [{'x': 0, 'y': 500, 'width': 800, 'height': 40}],
        'bounds': {'width': 1280, 'height': 720},
        'gravity': 800,
    },
    'character': {
        'sprite_path': 'sprite.png',
        'frame_width': 64,
        'frame_height': 64,
        'num_frames': 4,
        'spawn_x': 100,
        'spawn_y': 400,
    },
    'player': {'walk_speed': 180, 'jump_velocity': -380, 'max_jumps': 2},
}


def render_html(**kwargs):
    return WebGameExporter()._generate_html(
        MINIMAL_CONFIG, 'bg.png', 'sprite.png', **kwargs
    )


def test_html_contains_placement_function():
    # Rendering itself guards against f-string brace mistakes in the template:
    # an unescaped brace raises at format time.
    html = render_html(collectible_sprites=['data:image/png;base64,x'],
                       collectible_metadata=[{'name': 'Gem'}])

    assert 'function generateCollectiblePositions' in html
    assert 'generateCollectiblePositions(' in html.split('create()', 1)[1]
    # No baked-in positions array anymore
    assert 'const collectiblePositions = [' not in html


def test_signature_no_longer_accepts_positions():
    params = inspect.signature(WebGameExporter._generate_html).parameters
    assert 'collectible_positions' not in params
    assert 'collectible_sprites' in params
    assert 'collectible_metadata' in params


@pytest.mark.skipif(shutil.which('node') is None, reason='node not available')
def test_placement_algorithm_in_node():
    html = render_html()
    match = re.search(
        r'function generateCollectiblePositions.*?\n        \}\}?\n', html, re.DOTALL
    )
    assert match, 'placement function not found in template'
    js_fn = match.group(0)

    platforms = [
        {'x': 0, 'y': 500, 'width': 800, 'height': 40},
        {'x': 900, 'y': 350, 'width': 200, 'height': 30},
        {'x': 300, 'y': 250, 'width': 50, 'height': 30},  # too narrow, skipped
    ]
    script = (
        js_fn
        + f"\nconst platforms = {json.dumps(platforms)};"
        + "\nconsole.log(JSON.stringify(generateCollectiblePositions(platforms, 5)));"
    )
    out = subprocess.run(['node', '-e', script], capture_output=True, text=True, check=True)
    positions = json.loads(out.stdout)

    assert 8 <= len(positions) <= 15
    platform_tops = {p['y'] - 20 for p in platforms}
    for pos in positions:
        assert pos['y'] in platform_tops
        assert pos['y'] != 250 - 20  # narrow platform never used
        assert 0 <= pos['sprite_index'] < 5
    for i, a in enumerate(positions):
        for b in positions[i + 1:]:
            dist = ((a['x'] - b['x']) ** 2 + (a['y'] - b['y']) ** 2) ** 0.5
            assert dist >= 80
