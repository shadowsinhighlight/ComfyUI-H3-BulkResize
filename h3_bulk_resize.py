"""
H3 Bulk Reference Resize
------------------------
Nine independent image slots, each with its own resize rule.
Aspect ratio is preserved, nothing is ever cropped, and both output
dimensions are snapped to a chosen multiple (32 by default).

Bortevekk Studio
"""

import math

import comfy.utils

MAX_RESOLUTION = 16384
NUM_SLOTS = 9

UPSCALE_METHODS = ["lanczos", "bicubic", "bilinear", "area", "nearest-exact"]
MODES = ["passthrough", "longest_edge", "max_width_height"]


def snap(value, multiple, rounding):
    """Snap a float dimension to a multiple, never returning less than one step."""
    if multiple <= 1:
        return max(1, int(round(value)))

    q = value / float(multiple)
    if rounding == "down":
        n = math.floor(q)
    elif rounding == "up":
        n = math.ceil(q)
    else:  # nearest
        n = math.floor(q + 0.5)

    n = max(1, int(n))
    return min(n * multiple, MAX_RESOLUTION)


def scale_image(image, width, height, upscale_method):
    """image is [B, H, W, C] in 0-1 float. Returns the same layout, resized."""
    samples = image.movedim(-1, 1)
    try:
        out = comfy.utils.common_upscale(samples, width, height, upscale_method, "disabled")
    except Exception:
        # older ComfyUI builds may not expose every method (e.g. lanczos)
        out = comfy.utils.common_upscale(samples, width, height, "bicubic", "disabled")
    return out.movedim(1, -1)


class H3BulkReferenceResize:
    """
    Bulk resize for MiniMax H3 reference images.

    Per slot you choose:
      passthrough        - leave the image exactly as it is
      longest_edge       - scale so the longest side hits the target
      max_width_height   - scale to fit inside a width x height box

    Aspect ratio is always preserved and the image is never cropped.
    Both dimensions are then snapped to `multiple_of`, which can shift the
    ratio by at most half a step (8 px at 32) - unavoidable if you want both
    sides divisible by 32.
    """

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "multiple_of": ("INT", {"default": 32, "min": 1, "max": 256, "step": 1}),
            "rounding": (["nearest", "down", "up"], {"default": "nearest"}),
            "upscale_method": (UPSCALE_METHODS, {"default": "lanczos"}),
            "allow_upscale": ("BOOLEAN", {"default": False}),
        }
        optional = {}

        for i in range(1, NUM_SLOTS + 1):
            optional[f"image_{i}"] = ("IMAGE",)
            required[f"i{i}_mode"] = (MODES, {"default": "longest_edge"})
            required[f"i{i}_longest_edge"] = (
                "INT",
                {"default": 1024, "min": 32, "max": MAX_RESOLUTION, "step": 32},
            )
            required[f"i{i}_max_width"] = (
                "INT",
                {"default": 1024, "min": 32, "max": MAX_RESOLUTION, "step": 32},
            )
            required[f"i{i}_max_height"] = (
                "INT",
                {"default": 1024, "min": 32, "max": MAX_RESOLUTION, "step": 32},
            )

        return {"required": required, "optional": optional}

    RETURN_TYPES = tuple(["IMAGE"] * NUM_SLOTS + ["STRING"])
    RETURN_NAMES = tuple([f"image_{i}" for i in range(1, NUM_SLOTS + 1)] + ["report"])
    FUNCTION = "resize"
    CATEGORY = "Bortevekk/H3"
    DESCRIPTION = (
        "Resize up to 9 reference images independently. Keeps aspect ratio, "
        "never crops, snaps both sides to a multiple of 32 and reports the "
        "resulting resolutions."
    )

    def resize(self, multiple_of, rounding, upscale_method, allow_upscale, **kwargs):
        results = []
        lines = []
        any_input = False

        for i in range(1, NUM_SLOTS + 1):
            image = kwargs.get(f"image_{i}")

            if image is None:
                results.append(None)
                lines.append(f"{i}. (empty)")
                continue

            any_input = True
            batch, src_h, src_w = image.shape[0], image.shape[1], image.shape[2]

            mode = kwargs.get(f"i{i}_mode", "longest_edge")
            longest = kwargs.get(f"i{i}_longest_edge", 1024)
            max_w = kwargs.get(f"i{i}_max_width", 1024)
            max_h = kwargs.get(f"i{i}_max_height", 1024)

            if mode == "passthrough":
                results.append(image)
                lines.append(
                    f"{i}. {src_w}x{src_h} -> {src_w}x{src_h}  passthrough"
                    f"{'' if src_w % multiple_of == 0 and src_h % multiple_of == 0 else f'  [not /{multiple_of}]'}"
                )
                continue

            if mode == "longest_edge":
                scale = float(longest) / float(max(src_w, src_h))
            else:  # max_width_height
                scale = min(float(max_w) / float(src_w), float(max_h) / float(src_h))

            if not allow_upscale and scale > 1.0:
                scale = 1.0

            dst_w = snap(src_w * scale, multiple_of, rounding)
            dst_h = snap(src_h * scale, multiple_of, rounding)

            if dst_w == src_w and dst_h == src_h:
                out = image
            else:
                out = scale_image(image, dst_w, dst_h, upscale_method)

            results.append(out)

            src_ar = src_w / float(src_h)
            dst_ar = dst_w / float(dst_h)
            mp = (dst_w * dst_h) / 1_000_000.0
            drift = abs(dst_ar - src_ar) / src_ar * 100.0
            batch_tag = f" x{batch}" if batch > 1 else ""

            lines.append(
                f"{i}. {src_w}x{src_h} -> {dst_w}x{dst_h}{batch_tag}"
                f"  ({scale:.3f}x, {mp:.2f} MP)"
                f"  AR {src_ar:.4f} -> {dst_ar:.4f} ({drift:.2f}% off)"
            )

        header = (
            f"multiple of {multiple_of} / round {rounding} / {upscale_method}"
            f"{' / upscale on' if allow_upscale else ''}"
        )
        if not any_input:
            report = header + "\nno images connected"
        else:
            report = header + "\n" + "\n".join(lines)

        results.append(report)
        return {"ui": {"h3_resize_report": [report]}, "result": tuple(results)}


NODE_CLASS_MAPPINGS = {
    "H3BulkReferenceResize": H3BulkReferenceResize,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "H3BulkReferenceResize": "H3 Bulk Reference Resize (9x)",
}
