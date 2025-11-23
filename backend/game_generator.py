#!/usr/bin/env python3
"""
Unified Game Generator
Creates playable HTML5 platformer games from character sprites and background images
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
from PIL import Image
import anthropic
import os
from dotenv import load_dotenv

from sprite_processing.background_remover import BackgroundRemover
from sprite_processing.sprite_sheet_builder import SpriteSheetBuilder
from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer
from scene_builder.background_analyzer import BackgroundAnalyzer
from scene_builder.scene_generator import SceneGenerator
from scene_builder.web_exporter import WebGameExporter

load_dotenv()


class GameGenerator:
    """
    Orchestrates the complete pipeline from assets to playable game
    """

    def __init__(self, output_dir: str = "generated_game"):
        """
        Initialize game generator

        Args:
            output_dir: Directory where game files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize processing modules
        self.bg_remover = BackgroundRemover()
        self.sprite_builder = SpriteSheetBuilder()
        self.bg_analyzer = BackgroundAnalyzer()
        self.scene_gen = SceneGenerator()
        self.web_exporter = WebGameExporter()

        # Initialize Anthropic client for VLM analysis (required)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required for platform detection. Set it in your .env file.")
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)

        # Initialize sprite sheet analyzer
        self.sprite_analyzer = SpriteSheetAnalyzer(api_key=api_key)

    def analyze_walkable_platforms(self, background_path: Path) -> Dict[str, Any]:
        """
        Use VLM (Claude Sonnet 4.5) with extended thinking to identify walkable platforms.

        Features:
        - Extended thinking mode for complex reasoning about platform detection
        - Detailed prompting for reliable JSON responses
        - Comprehensive validation and error handling

        Args:
            background_path: Path to background image

        Returns:
            Dictionary with platform data, gaps, and spawn point
        """
        print(f"\n🔍 Analyzing walkable platforms with Claude Vision API...")
        print(f"  Features: Extended Thinking + JSON Prompting")
        print(f"  Background: {background_path.name}")

        # Load and encode image
        img = Image.open(background_path)
        width, height = img.size
        print(f"  Dimensions: {width}x{height}px")

        # Convert image to base64 for Claude API
        import base64
        import io

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

        # Create vision analysis prompt
        prompt = f"""You are analyzing a 2D platformer game background ({width}x{height}px) to identify WALKABLE PLATFORMS where a player character can stand and move.

CRITICAL: Your bounding boxes must be PRECISE. Players will fall through platforms if your coordinates are wrong!

═══════════════════════════════════════════════════════════
WHAT IS A WALKABLE PLATFORM?
═══════════════════════════════════════════════════════════

A platform MUST have these characteristics:
1. **Flat or nearly-flat TOP SURFACE** - The player stands on top
2. **Solid and continuous** - Not transparent, not broken, spans horizontally
3. **Visible ground/terrain** - Grass, dirt, stone, wood planks, etc.
4. **Contrasts with background** - Clearly distinguishable from sky/air
5. **Wide enough for character** - Minimum 50px width for playability

═══════════════════════════════════════════════════════════
WHAT TO EXCLUDE (NOT walkable):
═══════════════════════════════════════════════════════════

❌ **Trees**: Vertical objects with trunks - they SIT ON platforms, not ARE platforms
❌ **Plants/Vegetation**: Grass tufts, flowers, mushrooms - decorations ON platforms
❌ **Clouds**: In the sky, ethereal, not solid
❌ **Water**: Lakes, ponds - typically at bottom, blue/transparent
❌ **Fences/Barriers**: Vertical obstacles that block movement
❌ **Collectibles**: Coins, gems, power-ups - small decorative items
❌ **Sky/Background**: Air, distant mountains, clouds

═══════════════════════════════════════════════════════════
BOUNDING BOX PRECISION RULES:
═══════════════════════════════════════════════════════════

For EACH platform you detect:

1. **X (left edge)**: Start where the solid ground BEGINS (left-most walkable pixel)
2. **Y (top edge)**: The EXACT top surface where character feet would touch
3. **Width**: Full horizontal extent of continuous walkable surface
4. **Height**: Thin walkable surface layer ONLY (10-20px) - we only need the TOP, not the full platform depth

CRITICAL ACCURACY TIPS:
- **FOCUS ON PLATFORM TOPS ONLY** - We don't need the full platform body, just the walkable surface
- Look for the EXACT top surface line of platforms
- Height should be MINIMAL (10-20px) - just enough for collision detection
- Ignore decorations sitting ON TOP of platforms when measuring Y
- If a tree sits on a platform, the platform Y is at the tree's BASE, not tree top
- Measure the platform UNDERNEATH decorations, not the decorations themselves
- Ensure bounding boxes capture ONLY the thin walkable surface layer

═══════════════════════════════════════════════════════════
SPAWN POINT SELECTION:
═══════════════════════════════════════════════════════════

Choose a spawn point that is:
- ON a large, stable platform (not a tiny ledge)
- Near the left or center of the level
- ABOVE the platform surface (not inside it!)
  → If platform top is at Y=740, spawn should be Y=700 (40px above)
- Not near level edges or dangerous gaps

═══════════════════════════════════════════════════════════
ACCESSIBILITY VALIDATION:
═══════════════════════════════════════════════════════════

CRITICAL: Only include platforms that are ACCESSIBLE from the spawn point!

For each platform, verify:
- Can the player REACH this platform from spawn by walking or jumping?
- If a platform is floating with no way to reach it → EXCLUDE IT
- If a platform requires impossible jumps (>300px vertical) → EXCLUDE IT
- If a platform is isolated with no path to it → EXCLUDE IT

Only include platforms in a connected traversal graph from spawn.

═══════════════════════════════════════════════════════════
GAP IDENTIFICATION:
═══════════════════════════════════════════════════════════

Identify horizontal gaps where:
- There is empty space between two platforms
- Player must JUMP to cross
- Gap is significant (> 30px wide)

For each gap, provide:
- Description (e.g., "Gap between left ground and first floating platform")
- From/to platform names
- Approximate width in pixels
- X, Y, width, height for visual representation

═══════════════════════════════════════════════════════════
OUTPUT FORMAT:
═══════════════════════════════════════════════════════════

Return ONLY valid JSON (no markdown, no explanation):

{{
  "platforms": [
    {{
      "name": "Descriptive name (e.g., 'Bottom Ground Platform', 'Upper Left Ledge')",
      "x": 0,
      "y": 740,
      "width": 1024,
      "height": 28,
      "walkable": true
    }}
  ],
  "gaps": [
    {{
      "description": "Gap between platforms",
      "from_platform": "Platform A name",
      "to_platform": "Platform B name",
      "width": 80,
      "x": 400,
      "y": 700,
      "height": 20
    }}
  ],
  "spawn": {{
    "x": 100,
    "y": 700
  }},
  "notes": [
    "Important observations about the level layout",
    "Any ambiguities or challenges in detection"
  ]
}}

Now analyze the image and return your analysis in the structured format."""

        # Define tool for structured platform detection
        tools = [
            {
                "name": "report_platform_analysis",
                "description": "Report the detected walkable platforms, gaps, spawn point, and analysis notes",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "platforms": {
                            "type": "array",
                            "description": "List of detected walkable platforms",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Descriptive name for the platform"},
                                    "x": {"type": "integer", "description": "Top-left X coordinate in pixels"},
                                    "y": {"type": "integer", "description": "Top-left Y coordinate in pixels"},
                                    "width": {"type": "integer", "description": "Width in pixels"},
                                    "height": {"type": "integer", "description": "Height in pixels (10-20px for thin walkable surface)"},
                                    "walkable": {"type": "boolean", "description": "Whether this platform is walkable"}
                                },
                                "required": ["name", "x", "y", "width", "height", "walkable"]
                            }
                        },
                        "gaps": {
                            "type": "array",
                            "description": "Gaps between platforms requiring jumps",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "from_platform": {"type": "string"},
                                    "to_platform": {"type": "string"},
                                    "width": {"type": "integer"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "height": {"type": "integer"}
                                },
                                "required": ["description", "from_platform", "to_platform", "width"]
                            }
                        },
                        "spawn": {
                            "type": "object",
                            "description": "Player spawn point (should be above a platform)",
                            "properties": {
                                "x": {"type": "integer", "description": "Spawn X coordinate"},
                                "y": {"type": "integer", "description": "Spawn Y coordinate"}
                            },
                            "required": ["x", "y"]
                        },
                        "notes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Important observations about the level"
                        }
                    },
                    "required": ["platforms", "gaps", "spawn", "notes"]
                }
            }
        ]

        # Call Claude Vision API with extended thinking (no forced tool choice)
        print(f"  Calling Claude Sonnet 4.5 with extended thinking...")

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=16000,  # Increased for thinking + response
            thinking={
                "type": "enabled",
                "budget_tokens": 10000  # Allow substantial reasoning
            },
            tools=tools,
            # NO tool_choice with thinking mode - can't force tool calls
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Extract thinking blocks and tool use
        thinking_content = []
        tool_input = None

        for block in response.content:
            if block.type == "thinking":
                thinking_content.append(block.thinking)
                print(f"  🧠 Claude's reasoning: {block.thinking[:200]}...")  # Show first 200 chars
            elif block.type == "tool_use":
                tool_input = block.input
                print(f"  ✓ Tool called: {block.name}")

        # Log full thinking to file for analysis
        if thinking_content:
            thinking_log_path = self.output_dir / "platform_detection_thinking.txt"
            with open(thinking_log_path, 'w') as f:
                f.write("=== CLAUDE'S REASONING FOR PLATFORM DETECTION ===\n\n")
                f.write('\n\n'.join(thinking_content))
            print(f"  ✓ Reasoning saved to: {thinking_log_path.name}")

        # If no tool call was made (can happen with thinking mode), re-prompt without thinking
        if tool_input is None:
            print(f"  ⚠️  No tool call detected, re-prompting without thinking mode...")

            retry_response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=16000,
                tools=tools,
                tool_choice={"type": "tool", "name": "report_platform_analysis"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt + "\n\nPlease make a tool call with your analysis."
                            }
                        ]
                    }
                ]
            )

            # Extract tool use from retry
            for block in retry_response.content:
                if block.type == "tool_use":
                    tool_input = block.input
                    print(f"  ✓ Tool called on retry: {block.name}")
                    break

            if tool_input is None:
                raise ValueError("Failed to get tool call even after retry")

        # Extract structured data from tool use
        analysis_data = tool_input

        # Add image dimensions
        analysis_data["width"] = width
        analysis_data["height"] = height

        print(f"  ✓ Found {len(analysis_data['platforms'])} walkable platforms")
        print(f"  ✓ Identified {len(analysis_data['gaps'])} gaps requiring jumps")
        print(f"  ✓ Spawn point: ({analysis_data['spawn']['x']}, {analysis_data['spawn']['y']})")

        # Validate and fix spawn point to ensure it's on a platform
        analysis_data = self._validate_spawn_point(analysis_data)

        # Self-reflection: Have Claude review its own detections
        print(f"\n🔄 Self-reflection: Claude reviewing its detections...")
        analysis_data = self._self_reflect_on_detections(
            background_path,
            analysis_data,
            width,
            height
        )

        return analysis_data

    def verify_platform_detections(
        self,
        background_path: Path,
        initial_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Verify platform detections by showing Claude an overlay of its initial detections
        and asking it to correct them, focusing only on walkable surfaces.

        Args:
            background_path: Path to background image
            initial_analysis: Initial platform analysis from Claude

        Returns:
            Verified/corrected platform analysis
        """
        import base64
        import io
        from PIL import ImageDraw

        # Load background
        img = Image.open(background_path).convert('RGBA')
        width, height = img.size

        # Create overlay with detected platforms
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw initial platform detections
        for i, platform in enumerate(initial_analysis['platforms']):
            x = platform['x']
            y = platform['y']
            w = platform['width']
            h = platform['height']

            # Draw semi-transparent green rectangles
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=(0, 255, 0, 80),  # Green with alpha
                outline=(0, 255, 0, 255),  # Solid green outline
                width=3
            )

            # Add platform number
            label = f"P{i+1}"
            draw.text((x + 5, y + 5), label, fill=(255, 255, 255, 255))

        # Draw gaps
        for gap in initial_analysis.get('gaps', []):
            x = gap.get('x', 0)
            y = gap.get('y', 0)
            w = gap.get('width', 0)
            h = gap.get('height', 0)
            if w > 0 and h > 0:
                draw.rectangle(
                    [x, y, x + w, y + h],
                    fill=(255, 0, 0, 60),  # Red with alpha
                    outline=(255, 0, 0, 200),
                    width=2
                )

        # Draw spawn point
        spawn_x = initial_analysis['spawn']['x']
        spawn_y = initial_analysis['spawn']['y']
        spawn_radius = 12
        draw.ellipse(
            [spawn_x - spawn_radius, spawn_y - spawn_radius,
             spawn_x + spawn_radius, spawn_y + spawn_radius],
            fill=(255, 255, 0, 200),
            outline=(255, 255, 0, 255),
            width=3
        )

        # Composite overlay onto background
        overlay_img = Image.alpha_composite(img, overlay)

        # Convert to base64
        buffer = io.BytesIO()
        overlay_img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

        # Create verification prompt
        verification_prompt = f"""You previously analyzed this 2D platformer background ({width}x{height}px) and detected platforms.

I've overlaid your detections on the image:
- GREEN rectangles = platforms you detected (labeled P1, P2, etc.)
- RED rectangles = gaps you detected
- YELLOW circle = spawn point you chose

Please review your detections and provide CORRECTED platform data following these CRITICAL rules:

ONLY DETECT ACTUAL WALKABLE SURFACES:
- ONLY solid horizontal grass/ground platforms where a character can walk
- IGNORE all decorative elements (trees, mushrooms, crystals, plants, etc.)
- Trees and vegetation are NOT platforms - they sit ON platforms
- Focus on the solid ground/terrain underneath decorations
- A platform should be a continuous walkable surface (can span full width if ground is continuous)

PLATFORM REQUIREMENTS:
- Must be wide enough for a character to stand on (minimum ~50px wide)
- Should capture the full horizontal extent of walkable ground
- Include ONLY the grass/ground surface layer, not decorations on top
- If ground is continuous across the bottom, it should be ONE platform

ENSURE FULL LEVEL TRAVERSAL:
- Player must be able to walk or jump between all platforms
- Check that platforms allow movement from left edge to right edge of the scene
- Verify no unreachable areas or impossible gaps

Review the image carefully and return CORRECTED analysis as JSON:
{{
  "platforms": [
    {{"name": "Platform Name", "x": 0, "y": 740, "width": 1024, "height": 28, "walkable": true}},
    ...
  ],
  "gaps": [
    {{"description": "Gap description", "from_platform": "Platform A", "to_platform": "Platform B", "width": 50, "x": 100, "y": 700, "height": 20}},
    ...
  ],
  "spawn": {{"x": 512, "y": 640}},
  "corrections_made": ["List any corrections you made from the initial detection"],
  "notes": ["Important observations about the level layout"]
}}

Only return the JSON, no other text."""

        # Call Claude Vision with overlay
        print(f"  Sending overlay to Claude for verification...")

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": verification_prompt
                        }
                    ]
                }
            ]
        )

        # Parse verified response
        response_text = response.content[0].text.strip()

        # Remove markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()

        verified_data = json.loads(response_text)

        # Add image dimensions
        verified_data["width"] = width
        verified_data["height"] = height

        print(f"  ✓ Verified: {len(verified_data['platforms'])} platforms (was {len(initial_analysis['platforms'])})")
        if verified_data.get('corrections_made'):
            print(f"  ✓ Corrections made:")
            for correction in verified_data['corrections_made']:
                print(f"    - {correction}")

        return verified_data

    def _self_reflect_on_detections(
        self,
        background_path: Path,
        initial_analysis: Dict[str, Any],
        width: int,
        height: int
    ) -> Dict[str, Any]:
        """
        Have Claude review its own platform detections and decide if refinements are needed.

        Creates a visualization of detected platforms, shows it to Claude, and asks:
        1. Are all accessible platforms detected?
        2. Are any inaccessible platforms included?
        3. Do platform tops accurately represent walkable surfaces?
        4. Should any detections be refined?

        Args:
            background_path: Path to background image
            initial_analysis: Initial platform detection from Claude
            width: Image width
            height: Image height

        Returns:
            Refined analysis if changes needed, otherwise original analysis
        """
        import base64
        import io
        from PIL import ImageDraw, ImageFont

        # Create visualization of detections
        img = Image.open(background_path).convert('RGBA')
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw detected platforms
        for i, platform in enumerate(initial_analysis['platforms']):
            x, y, w, h = platform['x'], platform['y'], platform['width'], platform['height']

            # Draw platform as thin horizontal line (representing top surface)
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=(0, 255, 0, 120),  # Semi-transparent green
                outline=(0, 255, 0, 255),  # Solid green outline
                width=2
            )

            # Label platform
            label = f"P{i+1}: {platform['name'][:20]}"
            draw.text((x + 5, y - 15), label, fill=(255, 255, 255, 255))

        # Draw spawn point
        spawn_x, spawn_y = initial_analysis['spawn']['x'], initial_analysis['spawn']['y']
        draw.ellipse(
            [spawn_x - 15, spawn_y - 15, spawn_x + 15, spawn_y + 15],
            fill=(255, 255, 0, 200),
            outline=(255, 200, 0, 255),
            width=3
        )
        draw.text((spawn_x + 20, spawn_y - 10), "SPAWN", fill=(255, 255, 255, 255))

        # Composite and encode
        composite_img = Image.alpha_composite(img, overlay)
        buffer = io.BytesIO()
        composite_img.save(buffer, format='PNG')
        img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

        # Save visualization for debugging
        viz_path = self.output_dir / "platform_detections_visualization.png"
        composite_img.save(viz_path)
        print(f"  ✓ Visualization saved: {viz_path.name}")

        # Self-reflection prompt
        reflection_prompt = f"""You previously analyzed this platformer background and detected {len(initial_analysis['platforms'])} platforms.

I've visualized your detections:
- GREEN boxes = platforms you detected (labeled P1, P2, etc.)
- YELLOW circle = spawn point

CRITICAL REVIEW QUESTIONS:

1. **Platform Tops**: Do the green boxes represent just the THIN WALKABLE TOPS of platforms (10-20px high)?
   - If any platforms show full bodies instead of just tops, they need refinement

2. **Accessibility**: Can the player REACH all detected platforms from spawn by walking/jumping?
   - Check each platform: Is it reachable via a connected path?
   - Exclude any floating platforms with no access
   - Maximum jump height: ~300px vertical

3. **Completeness**: Are there any ACCESSIBLE walkable surfaces you missed?
   - Look for platforms the player can reach but weren't detected

4. **Accuracy**: Are all coordinates precise?
   - Check that Y values match the actual top surface
   - Verify widths span the full walkable extent

Based on your review, choose ONE of these actions:

A) **DETECTIONS ARE GOOD** - No changes needed, current detections are accurate and complete
B) **REFINEMENTS NEEDED** - Provide updated platform data with corrections

Return your response as JSON:
{{
  "reflection": {{
    "decision": "GOOD" or "REFINE",
    "reasoning": "Explain your decision in 2-3 sentences",
    "issues_found": ["List specific issues if any", "..."],
    "changes_made": ["List changes if refining", "..."]
  }},
  "platforms": [...],  // Updated platforms if REFINE, otherwise same as before
  "gaps": [...],
  "spawn": {{"x": ..., "y": ...}},
  "notes": [...]
}}

Be critical and thorough. If detections aren't perfect, refine them!"""

        # Define tool for reflection
        tools = [
            {
                "name": "report_reflection_result",
                "description": "Report the reflection decision and refined platform detections",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "reflection": {
                            "type": "object",
                            "properties": {
                                "decision": {"type": "string", "enum": ["GOOD", "REFINE"], "description": "Whether detections are good or need refinement"},
                                "reasoning": {"type": "string", "description": "Explanation of the decision"},
                                "issues_found": {"type": "array", "items": {"type": "string"}, "description": "List of issues found"},
                                "changes_made": {"type": "array", "items": {"type": "string"}, "description": "List of changes made if refining"}
                            },
                            "required": ["decision", "reasoning", "issues_found", "changes_made"]
                        },
                        "platforms": {
                            "type": "array",
                            "description": "Updated or confirmed platform list",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "x": {"type": "integer"},
                                    "y": {"type": "integer"},
                                    "width": {"type": "integer"},
                                    "height": {"type": "integer"},
                                    "walkable": {"type": "boolean"}
                                },
                                "required": ["name", "x", "y", "width", "height", "walkable"]
                            }
                        },
                        "gaps": {"type": "array", "items": {"type": "object"}},
                        "spawn": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "integer"},
                                "y": {"type": "integer"}
                            },
                            "required": ["x", "y"]
                        },
                        "notes": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["reflection", "platforms", "gaps", "spawn", "notes"]
                }
            }
        ]

        # Call Claude for self-reflection with extended thinking (no forced tool choice)
        print(f"  Asking Claude to review its detections...")

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 8000
            },
            tools=tools,
            # NO tool_choice with thinking mode - can't force tool calls
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": reflection_prompt
                        }
                    ]
                }
            ]
        )

        # Extract reflection thinking and tool use
        thinking_content = []
        tool_input = None

        for block in response.content:
            if block.type == "thinking":
                thinking_content.append(block.thinking)
                print(f"  🧠 Reflection: {block.thinking[:150]}...")
            elif block.type == "tool_use":
                tool_input = block.input
                print(f"  ✓ Reflection tool called: {block.name}")

        # Save reflection thinking
        if thinking_content:
            reflection_log_path = self.output_dir / "platform_reflection_thinking.txt"
            with open(reflection_log_path, 'w') as f:
                f.write("=== CLAUDE'S SELF-REFLECTION ON DETECTIONS ===\n\n")
                f.write('\n\n'.join(thinking_content))
            print(f"  ✓ Reflection thinking saved: {reflection_log_path.name}")

        # If no tool call was made (can happen with thinking mode), re-prompt without thinking
        if tool_input is None:
            print(f"  ⚠️  No tool call detected in reflection, re-prompting without thinking mode...")

            retry_response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=16000,
                tools=tools,
                tool_choice={"type": "tool", "name": "report_reflection_result"},
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": img_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": reflection_prompt + "\n\nPlease make a tool call with your reflection results."
                            }
                        ]
                    }
                ]
            )

            # Extract tool use from retry
            for block in retry_response.content:
                if block.type == "tool_use":
                    tool_input = block.input
                    print(f"  ✓ Reflection tool called on retry: {block.name}")
                    break

            if tool_input is None:
                raise ValueError("Failed to get reflection tool call even after retry")

        # Extract structured data from tool use
        reflection_result = tool_input

        decision = reflection_result['reflection']['decision']
        reasoning = reflection_result['reflection']['reasoning']
        issues = reflection_result['reflection']['issues_found']
        changes = reflection_result['reflection']['changes_made']

        print(f"\n  Decision: {decision}")
        print(f"  Reasoning: {reasoning}")

        if issues:
            print(f"  Issues found:")
            for issue in issues:
                print(f"    - {issue}")

        if decision == "REFINE":
            print(f"  ✓ Applying refinements:")
            for change in changes:
                print(f"    - {change}")

            # Use refined detections
            refined_data = {
                "platforms": reflection_result['platforms'],
                "gaps": reflection_result['gaps'],
                "spawn": reflection_result['spawn'],
                "notes": reflection_result['notes'],
                "width": width,
                "height": height
            }

            print(f"  ✓ Refined: {len(refined_data['platforms'])} platforms (was {len(initial_analysis['platforms'])})")
            return refined_data
        else:
            print(f"  ✓ Detections confirmed as accurate")
            return initial_analysis

    def _validate_spawn_point(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that the spawn point is on a platform and adjust if necessary.

        Ensures players always start on solid ground, not in mid-air.

        Args:
            analysis_data: Platform analysis data with spawn point

        Returns:
            Updated analysis data with validated spawn point
        """
        platforms = analysis_data['platforms']
        spawn_x = analysis_data['spawn']['x']
        spawn_y = analysis_data['spawn']['y']

        if not platforms:
            print(f"  ⚠️  WARNING: No platforms detected! Using original spawn point.")
            return analysis_data

        # Check if spawn point is on a platform
        def is_on_platform(x, y, platform, tolerance=50):
            """Check if point (x, y) is on the platform surface"""
            # X must be within platform horizontal bounds
            on_platform_x = platform['x'] <= x <= platform['x'] + platform['width']

            # Y should be ABOVE the platform (character stands on top)
            # Allow some tolerance (player should spawn 40-100px above platform top)
            on_platform_y = (platform['y'] - 100) <= y <= platform['y']

            return on_platform_x and on_platform_y

        # Find which platform the spawn point is on
        spawn_platform = None
        for platform in platforms:
            if is_on_platform(spawn_x, spawn_y, platform):
                spawn_platform = platform
                break

        if spawn_platform:
            print(f"  ✓ Spawn point validated: on '{spawn_platform['name']}'")
            return analysis_data

        # Spawn point is NOT on a platform - need to fix it!
        print(f"  ⚠️  WARNING: Spawn point ({spawn_x}, {spawn_y}) is NOT on any platform!")

        # Find the largest, most stable platform (prefer bottom platforms)
        # Sort by: 1) Y position (bottom first), 2) Width (larger first)
        sorted_platforms = sorted(
            platforms,
            key=lambda p: (-p['y'], -p['width'])  # Negative for descending order
        )

        best_platform = sorted_platforms[0]

        # Place spawn point in the center-left of the best platform, above the surface
        new_spawn_x = best_platform['x'] + best_platform['width'] // 3
        new_spawn_y = best_platform['y'] - 60  # 60px above platform top

        print(f"  ✓ Corrected spawn point: ({spawn_x}, {spawn_y}) → ({new_spawn_x}, {new_spawn_y})")
        print(f"    Now on platform: '{best_platform['name']}'")

        analysis_data['spawn']['x'] = new_spawn_x
        analysis_data['spawn']['y'] = new_spawn_y

        return analysis_data

    def process_character_sprite(
        self,
        sprite_path: Path,
        num_frames: int = 8,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Process character sprite sheet - removes background and detects frame dimensions

        Args:
            sprite_path: Path to sprite sheet image
            num_frames: Number of animation frames
            frame_width: Width of each frame (auto-detected if None)
            frame_height: Height of each frame (auto-detected if None)

        Returns:
            Tuple of (processed_sprite_path, sprite_config)
        """
        print(f"\n🎨 Processing character sprite {sprite_path.name}...")

        # NEW FLOW: Clean FIRST, then extract based on actual content edges

        # STEP 1: Analyze sprite sheet layout
        import sys
        print(f"  📊 Analyzing sprite sheet layout...")
        sys.stdout.flush()
        layout_info = self.sprite_analyzer.analyze_sprite_sheet_layout(sprite_path)

        print(f"  Layout: {layout_info['layout_type']} ({layout_info['rows']}×{layout_info['columns']})")
        print(f"  Total frames: {layout_info['total_frames']}")
        sys.stdout.flush()

        # ALWAYS use the detected frame count from Claude Vision
        detected_frames = layout_info['total_frames']
        if detected_frames != num_frames:
            print(f"\n⚠️  FRAME COUNT MISMATCH ⚠️")
            print(f"  Requested: {num_frames}, Detected: {detected_frames}")
            num_frames = detected_frames  # Override!
            print(f"  Using detected count: {num_frames}\n")
            sys.stdout.flush()
        else:
            print(f"  ✓ Frame counts match: {num_frames}")
            sys.stdout.flush()

        # STEP 2: Remove background from ORIGINAL sprite sheet FIRST
        print(f"  🧹 Removing background from original sprite sheet...")
        sys.stdout.flush()
        original_img = Image.open(sprite_path)
        if original_img.mode != 'RGBA':
            original_img = original_img.convert('RGBA')

        cleaned_img = self.bg_remover.remove_background(
            original_img,
            background_color=(255, 255, 255),  # White background
            tolerance=40
        )

        # Auto-crop to remove excess transparent space
        cleaned_img = self.bg_remover.auto_crop(cleaned_img, padding=5)
        print(f"  ✓ Background removed and cropped: {cleaned_img.size[0]}x{cleaned_img.size[1]}px")
        sys.stdout.flush()

        # Save the cleaned sprite sheet temporarily
        cleaned_sprite_path = self.output_dir / "assets" / f"cleaned_{sprite_path.name}"
        cleaned_sprite_path.parent.mkdir(parents=True, exist_ok=True)
        cleaned_img.save(cleaned_sprite_path)

        # STEP 3: NOW do smart extraction on the CLEANED image
        # This ensures frame boundaries are based on actual content edges, not pre-removal pixels
        print(f"  ✂️  Extracting frames using content-edge detection on cleaned image...")
        sys.stdout.flush()
        temp_sprite_path = self.output_dir / "assets" / f"rearranged_{sprite_path.name}"
        temp_sprite_path.parent.mkdir(parents=True, exist_ok=True)

        sprite_path, rearranged_info = self.sprite_analyzer.rearrange_to_horizontal(
            cleaned_sprite_path,  # Use cleaned image!
            temp_sprite_path,
            layout_info=layout_info
        )

        # Update num_frames with actual extracted frame count
        num_frames = rearranged_info['total_frames']
        frame_width = rearranged_info['frame_width']
        frame_height = rearranged_info['frame_height']

        print(f"  ✓ Extracted {num_frames} frames at {frame_width}x{frame_height}px each")
        sys.stdout.flush()

        # STEP 4: Load the final processed sprite sheet
        processed_img = Image.open(sprite_path)
        cropped_width, cropped_height = processed_img.size
        print(f"  ✓ Final sprite sheet: {cropped_width}x{cropped_height}px")

        print(f"  ✓ Frame size: {frame_width}x{frame_height}px")
        print(f"  ✓ Number of frames: {num_frames}")
        print(f"  ✓ Expected sprite sheet width: {frame_width * num_frames}px (actual: {cropped_width}px)")

        # The sprite_path is already the final processed horizontal strip from smart extraction
        # Just rename it for clarity
        processed_path = sprite_path
        print(f"  ✓ Final sprite sheet saved: {processed_path.name}")

        print(f"\n📦 Creating sprite_config with num_frames={num_frames}")
        import sys
        sys.stdout.flush()

        sprite_config = {
            "sprite_path": str(processed_path),
            "frame_width": frame_width,
            "frame_height": frame_height,
            "num_frames": num_frames
        }

        print(f"  sprite_config created: frame_width={frame_width}, frame_height={frame_height}, num_frames={num_frames}")
        sys.stdout.flush()

        return processed_path, sprite_config

    def generate_game(
        self,
        character_sprite: str,
        background_image: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate complete playable game from assets

        Args:
            character_sprite: Path to character sprite sheet
            background_image: Path to background image
            num_frames: Number of animation frames in sprite sheet
            game_name: Name for the generated game
            player_config: Optional player physics configuration

        Returns:
            Path to generated game.html
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name}")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite)
        bg_path = Path(background_image)

        # Validate inputs
        if not char_path.exists():
            raise FileNotFoundError(f"Character sprite not found: {char_path}")
        if not bg_path.exists():
            raise FileNotFoundError(f"Background image not found: {bg_path}")

        # Process assets
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Create scene configuration
        scene_config = {
            "name": game_name,
            "background": {
                "path": str(bg_path),
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": str(processed_sprite_path),
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }

        # Save configuration
        print(f"\n💾 Saving game configuration...")
        config_path = self.output_dir / "scene_config.json"
        self.scene_gen.save_scene_config(scene_config, config_path)
        print(f"  ✓ Config saved to {config_path}")

        # Copy background to output directory
        print(f"\n📦 Copying background...")
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        bg_dest = assets_dir / bg_path.name
        Image.open(bg_path).save(bg_dest)
        print(f"  ✓ Background: {bg_dest.name}")
        print(f"  ✓ Character sprite already processed and saved")

        # Export game
        print(f"\n🔨 Generating game files...")
        game_path = self.output_dir / "game.html"
        self.web_exporter.export_game(scene_config, game_path, embed_assets=False)
        print(f"  ✓ Game HTML: {game_path}")

        # Create run script
        run_script = self.output_dir / "run_game.py"
        self._create_run_script(run_script)
        print(f"  ✓ Run script: {run_script}")

        # Summary
        print("\n" + "=" * 70)
        print(f"✅ {game_name} Generated Successfully!")
        print("=" * 70)

        print(f"\n🎯 Game Features:")
        print(f"  ✓ {len(platform_analysis['platforms'])} walkable platforms")
        print(f"  ✓ {len(platform_analysis['gaps'])} gaps requiring jumps")
        print(f"  ✓ Double jump mechanics")
        print(f"  ✓ Responsive canvas sizing")
        print(f"  ✓ {num_frames}-frame character animation")

        print(f"\n🎮 To Play:")
        print(f"    cd {self.output_dir} && python3 run_game.py")
        print(f"    OR open http://localhost:8080/game.html")

        print("\n💡 Controls:")
        print("  ← → : Move left/right")
        print("  SPACE : Jump (double jump!)")
        print("  R : Reset position")

        print("=" * 70)

        return game_path

    def generate_game_html_with_embedded_assets(
        self,
        character_sprite: str,
        background_image: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate game HTML with base64-embedded assets for iframe embedding

        Args:
            character_sprite: Path to character sprite sheet
            background_image: Path to background image
            num_frames: Number of animation frames
            game_name: Name for the generated game
            player_config: Optional player physics configuration

        Returns:
            Tuple of (game_html_string, scene_config_dict)
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name} with embedded assets")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite)
        bg_path = Path(background_image)

        # Validate inputs
        if not char_path.exists():
            raise FileNotFoundError(f"Character sprite not found: {char_path}")
        if not bg_path.exists():
            raise FileNotFoundError(f"Background image not found: {bg_path}")

        # Process assets
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Convert images to base64
        import base64

        print(f"\n📦 Encoding assets as base64...")
        with open(bg_path, 'rb') as f:
            bg_base64 = base64.b64encode(f.read()).decode('utf-8')
        bg_data_url = f"data:image/png;base64,{bg_base64}"
        print(f"  ✓ Background encoded")

        with open(processed_sprite_path, 'rb') as f:
            sprite_base64 = base64.b64encode(f.read()).decode('utf-8')
        sprite_data_url = f"data:image/png;base64,{sprite_base64}"
        print(f"  ✓ Character sprite encoded")

        # Create scene configuration with data URLs
        scene_config = {
            "name": game_name,
            "background": {
                "path": bg_data_url,  # Use data URL instead of file path
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": sprite_data_url,  # Use data URL instead of file path
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }

        # Generate HTML with embedded assets
        print(f"\n🔨 Generating HTML with embedded assets...")
        game_html = self.web_exporter._generate_html(
            scene_config,
            bg_data_url,  # Pass data URL
            sprite_data_url  # Pass data URL
        )

        print(f"  ✓ Game HTML generated: {len(game_html)} characters")
        print("=" * 70)

        return game_html, scene_config

    def generate_game_html_with_urls(
        self,
        character_sprite_path: str,
        character_sprite_url: str,
        background_image_path: str,
        background_image_url: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None,
        collectible_sprites: list = None,
        collectible_positions: list = None,
        collectible_metadata: list = None,
        mob_sprite_path: str = None,
        mob_sprite_url: str = None
    ) -> tuple[str, Dict[str, Any], list[str]]:
        """
        Generate game HTML using original image URLs (for Phaser compatibility)

        Downloads images for analysis/processing, but uses original URLs in HTML
        since Phaser doesn't support data URIs.

        Args:
            character_sprite_path: Local path to downloaded character sprite
            character_sprite_url: Original URL to character sprite
            background_image_path: Local path to downloaded background
            background_image_url: Original URL to background
            num_frames: Number of animation frames
            game_name: Name for the generated game
            player_config: Optional player physics configuration
            collectible_sprites: List of collectible sprite data URLs
            collectible_positions: List of collectible positions
            collectible_metadata: List of collectible metadata
            mob_sprite_path: Local path to downloaded mob sprite
            mob_sprite_url: Original URL to mob sprite

        Returns:
            Tuple of (game_html_string, scene_config_dict, debug_frames_base64_list)
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name} with URL references")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite_path)
        bg_path = Path(background_image_path)

        # Process character sprite locally (remove background, get dimensions)
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        # Analyze background locally with Claude Vision
        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Convert processed sprite to base64 for embedding
        import base64
        print(f"\n📦 Encoding processed sprite as base64...")
        with open(processed_sprite_path, 'rb') as f:
            sprite_base64 = base64.b64encode(f.read()).decode('utf-8')
        processed_sprite_data_url = f"data:image/png;base64,{sprite_base64}"
        print(f"  ✓ Processed sprite encoded ({len(sprite_base64)} bytes)")

        # Process mob sprite if provided
        processed_mob_data_url = None
        mob_config = None
        if mob_sprite_path and mob_sprite_url:
            print(f"\n👾 Processing mob sprite...")
            mob_path = Path(mob_sprite_path)
            processed_mob_path, mob_config = self.process_character_sprite(
                mob_path,
                num_frames=num_frames
            )
            with open(processed_mob_path, 'rb') as f:
                mob_base64 = base64.b64encode(f.read()).decode('utf-8')
            processed_mob_data_url = f"data:image/png;base64,{mob_base64}"
            print(f"  ✓ Mob sprite processed ({len(mob_base64)} bytes)")

        # Create scene configuration
        scene_config = {
            "name": game_name,
            "background": {
                "path": background_image_url,  # Use original URL for background
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": processed_sprite_data_url,  # Use data URL for processed sprite
                "sprite_path_original": character_sprite_url,  # Keep original for reference
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }
        
        # Add mob configuration if mob was processed
        if mob_config and processed_mob_data_url:
            scene_config["mob"] = {
                "sprite_path": processed_mob_data_url,
                "frame_width": mob_config["frame_width"],
                "frame_height": mob_config["frame_height"],
                "num_frames": mob_config["num_frames"]
            }

        # Generate HTML with URLs (background URL + sprite data URI + collectibles + mob)
        print(f"\n🔨 Generating HTML with URL references...")
        game_html = self.web_exporter._generate_html(
            scene_config,
            background_image_url,  # Pass original URL for background
            processed_sprite_data_url,  # Pass data URL for processed sprite
            collectible_sprites,  # Pass collectible sprite data URLs
            collectible_positions,  # Pass collectible positions
            collectible_metadata,  # Pass collectible metadata
            processed_mob_data_url,  # Pass mob sprite data URL
            mob_config  # Pass mob sprite configuration
        )

        print(f"  ✓ Game HTML generated: {len(game_html)} characters")
        print(f"  ✓ Using original image URLs (Phaser compatible)")

        # Extract debug frames for visualization
        print(f"\n🔍 Extracting debug frames for visualization...")
        debug_frames = self._extract_debug_frames(processed_sprite_path, sprite_config)
        print(f"  ✓ Extracted {len(debug_frames)} debug frames")

        print("=" * 70)

        return game_html, scene_config, debug_frames

    def _extract_debug_frames(self, sprite_sheet_path: Path, sprite_config: Dict[str, Any]) -> list[str]:
        """
        Extract individual frames from the processed sprite sheet for debug visualization

        Args:
            sprite_sheet_path: Path to the processed horizontal sprite sheet
            sprite_config: Configuration dict with frame dimensions

        Returns:
            List of base64-encoded PNG frames as data URLs
        """
        import base64
        import io

        sprite_sheet = Image.open(sprite_sheet_path)
        frame_width = sprite_config["frame_width"]
        frame_height = sprite_config["frame_height"]
        num_frames = sprite_config["num_frames"]

        print(f"\n  🔍 Debug frame extraction:")
        print(f"     Sprite sheet size: {sprite_sheet.size}")
        print(f"     Frame dimensions: {frame_width}x{frame_height}px")
        print(f"     Number of frames: {num_frames}")
        print(f"     Extracting positions:")

        debug_frames = []

        for i in range(num_frames):
            # Extract frame
            x = i * frame_width
            x_end = x + frame_width
            print(f"       Frame {i}: x={x} to {x_end} (width={frame_width})")
            frame = sprite_sheet.crop((x, 0, x_end, frame_height))

            # Convert to base64 data URL
            buffer = io.BytesIO()
            frame.save(buffer, format='PNG')
            frame_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            data_url = f"data:image/png;base64,{frame_base64}"

            debug_frames.append(data_url)

        return debug_frames

    def _create_run_script(self, output_path: Path):
        """Create a simple HTTP server script to run the game"""
        script_content = '''#!/usr/bin/env python3
"""
Simple HTTP server to run the game
This avoids CORS issues when loading local files
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8080

# Change to the directory containing this script
os.chdir(Path(__file__).parent)

Handler = http.server.SimpleHTTPRequestHandler

print("=" * 70)
print("🎮 Platformer Game")
print("=" * 70)
print(f"\\n🌐 Starting server at http://localhost:{PORT}")
print(f"📁 Serving files from: {Path.cwd()}")
print(f"\\n🎯 Opening game in your browser...")
print(f"\\n⚠️  Press Ctrl+C to stop the server when you're done")
print("=" * 70 + "\\n")

# Open browser after a short delay
import threading
def open_browser():
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/game.html')

threading.Thread(target=open_browser, daemon=True).start()

# Start server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n\\n✅ Server stopped. Thanks for playing!")
'''
        output_path.write_text(script_content)
        output_path.chmod(0o755)  # Make executable


def main():
    """CLI entry point for game generation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate playable HTML5 platformer game from assets"
    )
    parser.add_argument(
        "--character",
        "-c",
        required=True,
        help="Path to character sprite sheet"
    )
    parser.add_argument(
        "--background",
        "-b",
        required=True,
        help="Path to background image"
    )
    parser.add_argument(
        "--frames",
        "-f",
        type=int,
        default=8,
        help="Number of animation frames (default: 8)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="generated_game",
        help="Output directory (default: generated_game)"
    )
    parser.add_argument(
        "--name",
        "-n",
        default="PlatformerGame",
        help="Game name (default: PlatformerGame)"
    )

    args = parser.parse_args()

    # Generate game
    generator = GameGenerator(output_dir=args.output)
    game_path = generator.generate_game(
        character_sprite=args.character,
        background_image=args.background,
        num_frames=args.frames,
        game_name=args.name
    )

    print(f"\n✨ Game ready at: {game_path}")


if __name__ == "__main__":
    main()
