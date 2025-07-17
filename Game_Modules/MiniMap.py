"""
MiniMap utility for cropping the map image to center on the player and overlaying a fixed marker.
Requires Pillow: pip install pillow
"""

from PIL import Image, ImageDraw
import os

MINIMAP_PATH = os.path.join(os.path.dirname(__file__), '../Textures/mini-map.png')

def generate_minimap(player_x, player_y, view_width=1500, view_height=1000, marker_radius=5, output_path=None):
    """
    Crops the mini-map so the player is centered, overlays a marker at the center, and saves/returns the image.
    Args:
        player_x, player_y: Player's position on the map image (in pixels)
        view_width, view_height: Size of the cropped view (in pixels)
        marker_radius: Radius of the marker dot
        output_path: If provided, saves the image to this path
    Returns:
        Cropped PIL Image object
    """
    # Load the mini-map image
    minimap = Image.open(MINIMAP_PATH).convert('RGBA')
    map_w, map_h = minimap.size

    # Calculate crop box so player is centered
    left = int(player_x - view_width // 2)
    upper = int(player_y - view_height // 2)
    right = left + view_width
    lower = upper + view_height

    # Clamp crop box to image boundaries
    left = max(0, min(left, map_w - view_width))
    upper = max(0, min(upper, map_h - view_height))
    right = left + view_width
    lower = upper + view_height

    cropped = minimap.crop((left, upper, right, lower))

    # Draw marker at center
    draw = ImageDraw.Draw(cropped)
    center_x = view_width // 2
    center_y = view_height // 2
    draw.ellipse([
        (center_x - marker_radius, center_y - marker_radius),
        (center_x + marker_radius, center_y + marker_radius)
    ], fill='red', outline='black')

    if output_path:
        cropped.save(output_path)
    return cropped
