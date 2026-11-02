"""
Generates the inkJam brand logo and favicon using Pillow (PIL).
"""
import os
from PIL import Image, ImageDraw, ImageFont

def generate_logo(output_path="img/logo.png", size=512):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create image with transparent background
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Outer circle with soft shadow or gradient
    padding = 20
    draw.ellipse(
        [padding, padding, size - padding, size - padding],
        fill=(56, 88, 233, 255)  # inkJam royal blue #3858e9
    )
    
    # Inner decorative accent ring
    draw.ellipse(
        [padding + 16, padding + 16, size - padding - 16, size - padding - 16],
        outline=(255, 255, 255, 60),
        width=4
    )
    
    # Draw ink pen nib / stylized monogram
    center_x, center_y = size // 2, size // 2
    
    # Elegant pen nib coordinates
    nib_top = (center_x, center_y - 120)
    nib_left = (center_x - 70, center_y + 40)
    nib_right = (center_x + 70, center_y + 40)
    nib_bottom_left = (center_x - 45, center_y + 110)
    nib_bottom_right = (center_x + 45, center_y + 110)
    
    # Pen nib polygon
    nib_points = [
        nib_top,
        (center_x + 55, center_y - 40),
        nib_right,
        nib_bottom_right,
        (center_x + 20, center_y + 100),
        (center_x - 20, center_y + 100),
        nib_bottom_left,
        nib_left,
        (center_x - 55, center_y - 40)
    ]
    draw.polygon(nib_points, fill=(255, 255, 255, 255))
    
    # Central ink slit line
    draw.line([(center_x, center_y - 110), (center_x, center_y + 50)], fill=(56, 88, 233, 255), width=8)
    
    # Breather hole in pen nib
    hole_radius = 16
    draw.ellipse(
        [center_x - hole_radius, center_y - 10 - hole_radius, 
         center_x + hole_radius, center_y - 10 + hole_radius],
        fill=(56, 88, 233, 255)
    )
    
    # Save the logo
    img.save(output_path, "PNG")
    print(f"Generated logo at: {output_path}")

if __name__ == "__main__":
    generate_logo("img/logo.png")
    generate_logo("inkJam/img/logo.png")
