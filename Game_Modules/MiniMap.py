"""
MiniMap utility for cropping the map image to center on the player and overlaying a fixed marker.
Requires Pillow: pip install pillow
"""

from PIL import Image, ImageDraw
import os
from . import temp_utils

MINIMAP_PATH = os.path.join(os.path.dirname(__file__), '../Textures/mini-map.png')

def generate_minimap(player_x, player_y, view_width=1500, view_height=1000,
                     marker_radius=5, output_path=None, return_coords=False,
                     full_map=False):
    """
    Crops the mini-map so the player is centered when possible, overlays a marker
    at the player's location within the cropped view, and saves/returns the image.
    Args:
        player_x, player_y: Player's position on the map image (in pixels)
        view_width, view_height: Size of the cropped view (in pixels)
        marker_radius: Radius of the marker dot
        output_path: If provided, saves the image to this path
    Returns:
        Cropped PIL Image object. If ``return_coords`` is True, also returns the
        player's coordinates within the cropped image as ``(x, y)``.
    """
    # Load the mini-map image
    minimap = Image.open(MINIMAP_PATH).convert('RGBA')
    map_w, map_h = minimap.size

    if full_map:
        draw = ImageDraw.Draw(minimap)
        draw.ellipse([
            (player_x - marker_radius, player_y - marker_radius),
            (player_x + marker_radius, player_y + marker_radius)
        ], fill='red', outline='black')
        resized = minimap.resize((view_width, view_height), Image.BILINEAR)
        if output_path is None:
            output_path = os.path.join(temp_utils.MAP_DIR, 'minimap.png')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        resized.save(output_path)
        if return_coords:
            scale_x = view_width / map_w
            scale_y = view_height / map_h
            return resized, player_x * scale_x, player_y * scale_y
        return resized

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

    # Draw marker at the player's coordinates relative to the crop
    draw = ImageDraw.Draw(cropped)
    draw_x = player_x - left
    draw_y = player_y - upper
    draw.ellipse([
        (draw_x - marker_radius, draw_y - marker_radius),
        (draw_x + marker_radius, draw_y + marker_radius)
    ], fill='red', outline='black')

    if output_path is None:
        output_path = os.path.join(temp_utils.MAP_DIR, 'minimap.png')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cropped.save(output_path)

    return (cropped, draw_x, draw_y) if return_coords else cropped
