import os
import tempfile

from PIL import Image


def transform_image(
    path: str,
    rotation: int = 0,
    flip_h: bool = False,
    flip_v: bool = False,
    output_path: str | None = None,
) -> str:
    with Image.open(path) as img:
        img = img.convert("RGB")

        if flip_h:
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if flip_v:
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if rotation:
            img = img.rotate(rotation, expand=True, fillcolor=(255, 255, 255))

        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            output_path = tmp.name
            tmp.close()

        img.save(output_path)

    return output_path


def merge_side_by_side(
    path1: str,
    path2: str,
    output_path: str = "merged_image.jpg",
) -> str:
    with Image.open(path1) as raw1, Image.open(path2) as raw2:
        left = raw1.convert("RGB")
        right = raw2.convert("RGB")

        merged = Image.new(
            "RGB",
            (left.width + right.width, max(left.height, right.height)),
            (255, 255, 255),
        )
        merged.paste(left, (0, 0))
        merged.paste(right, (left.width, 0))

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        merged.save(output_path)

    return output_path
