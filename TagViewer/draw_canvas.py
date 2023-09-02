"""
This is solely for the purpose of testing the TagViewer canvas

Shout out to https://dummyimage.com/2000x2200/8864f4/000000&text=+ for the background image,
actually so useful.
"""

from PIL import Image, ImageDraw, ImageFont

with Image.open("base.png").copy() as image:
    size = image.size
    font = ImageFont.truetype("font.ttf", 175)
    CANVAS_OFFSET = 150
    ratio = size[0] / size[1]
    canvas_first_dims = (CANVAS_OFFSET, CANVAS_OFFSET * ratio)
    canvas_second_dims = (size[0] - CANVAS_OFFSET, size[1] - (CANVAS_OFFSET * ratio))

    canvas = ImageDraw.Draw(image)

    NAME_OFFSET = 100
    NAME_UPSET = 1600
    name_first_dims = (CANVAS_OFFSET + NAME_OFFSET, (CANVAS_OFFSET * ratio) + NAME_OFFSET)
    name_second_dims = (size[0] - CANVAS_OFFSET - NAME_OFFSET, size[1] - (CANVAS_OFFSET * ratio) - NAME_UPSET)

    PREFIX_OFFSET = 1350
    prefix_first_dims = (CANVAS_OFFSET + NAME_OFFSET, (CANVAS_OFFSET * ratio) + NAME_OFFSET)
    prefix_second_dims = (size[0] - CANVAS_OFFSET - PREFIX_OFFSET, size[1] - (CANVAS_OFFSET * ratio) - NAME_UPSET)

    # Background
    canvas.rounded_rectangle((canvas_first_dims, canvas_second_dims), radius=100, fill="#40444c")

    # Name field
    canvas.rounded_rectangle((name_first_dims, name_second_dims), radius=100, fill="#585c64", outline="#23282c")

    # Prefix field
    canvas.rounded_rectangle((prefix_first_dims, prefix_second_dims), radius=100, fill="#383c44", outline="#23282c")

    # Prefix Text
    canvas.text((prefix_first_dims[0] + 100, prefix_first_dims[1] + 30), "!", fill="#ffffff", font=font)
    
    # Tag Name
    canvas.text((name_first_dims[0] + 280, name_first_dims[1] + 30), text="Tag Name", font=font, fill="#ffffff")
    
    image.save("beta_canvas.png")