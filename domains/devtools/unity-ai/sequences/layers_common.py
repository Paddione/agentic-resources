"""What the layer scripts of the skill's sequences share (image_layers.py, portrait_layers.py): reading the picture
and the model's outputs at its exact size, growing and softening masks, connected pieces, and the PSB writer for
Unity's PSD Importer. Pillow and NumPy only; imported from next to those scripts, never run on its own."""

import sys

import numpy as np
from PIL import Image, ImageFilter


def same_size(path, im, size):
    if im.size != size:
        sys.exit(
            f"{path} is {im.size[0]}x{im.size[1]}, it must be {size[0]}x{size[1]}: scaling it would move every "
            f"outline. Redo that generation with --param width={size[0]} --param height={size[1]}."
        )


def load_rgba(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size:
        same_size(path, im, size)
    return np.asarray(im).astype(np.float32)


def grow(mask, px):
    """`mask` dilated by `px` pixels (a square window): a sliding count along rows, then columns, in NumPy."""
    if px <= 0:
        return mask
    out = mask.astype(bool)
    for axis in (0, 1):
        n = out.shape[axis]
        c = np.cumsum(out, axis=axis, dtype=np.int32)
        c = np.concatenate([np.zeros_like(c.take([0], axis=axis)), c], axis=axis)
        hi = np.minimum(np.arange(n) + px + 1, n)
        lo = np.maximum(np.arange(n) - px, 0)
        out = (c.take(hi, axis=axis) - c.take(lo, axis=axis)) > 0
    return out


def soften(mask, r=0.8):
    """A label edge softened a little, so a moved part has no stair-step outline."""
    im = Image.fromarray((mask * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(r)
    )
    return np.asarray(im).astype(np.float32) / 255


def components(mask):
    """The 4-connected parts of `mask`, each as an array of flat pixel indices."""
    H, W = mask.shape
    flat = mask.ravel().copy()
    parts = []
    for start in np.flatnonzero(flat):
        if not flat[start]:
            continue
        flat[start] = False
        stack, part = [start], []
        while stack:
            i = stack.pop()
            part.append(i)
            y, x = divmod(i, W)
            for j, ok in (
                (i - W, y > 0),
                (i + W, y < H - 1),
                (i - 1, x > 0),
                (i + 1, x < W - 1),
            ):
                if ok and flat[j]:
                    flat[j] = False
                    stack.append(j)
        parts.append(np.array(part))
    return parts


def write_psb(path, W, H, layers, composite):
    """A layered PSB (Photoshop large document, version 2, 8-bit RGB with transparency, raw channel data): `layers`
    bottom to top as (name, RGBA uint8 array the canvas's size, visible), and the flattened `composite`. What the 2D
    PSD Importer reads: one sprite per layer at its place, hidden layers imported when asked.
    """
    import struct
    import zlib

    def pascal(name):
        b = name.encode("ascii", "replace")[:255]
        s = bytes([len(b)]) + b
        return s + b"\0" * ((-len(s)) % 4)

    # Each layer's id comes from its name, not its place: a PSB written again with states added keeps every other
    # layer's id, so the PSD Importer maps each layer back to the same sprite (and its references in scenes).
    layer_ids, used = [], set()
    for name, _, _ in layers:
        lid = zlib.crc32(name.encode("utf-8")) & 0x7FFFFFFF or 1
        while lid in used:
            lid = lid % 0x7FFFFFFF + 1
        used.add(lid)
        layer_ids.append(lid)
    records, channel_data = b"", b""
    for index, (name, rgba, visible) in enumerate(layers):
        box = Image.fromarray(rgba, "RGBA").getbbox() or (0, 0, 1, 1)
        x0, y0, x1, y1 = box
        crop = rgba[y0:y1, x0:x1]
        planes = [
            crop[:, :, 3],
            crop[:, :, 0],
            crop[:, :, 1],
            crop[:, :, 2],
        ]  # -1 transparency, then R, G, B
        ids = [-1, 0, 1, 2]
        channels = b""
        for cid, plane in zip(ids, planes):
            data = struct.pack(">H", 0) + plane.astype(np.uint8).tobytes()
            channels += struct.pack(">hQ", cid, len(data))
            channel_data += data
        # The Unicode name (`luni`): a character count, then UTF-16. Its length is the data's, padded to 4 bytes,
        # never counting the signature, the key or the length field itself.
        uname = name.encode("utf-16-be")
        luni_data = struct.pack(">I", len(uname) // 2) + uname
        luni_data += b"\0" * ((-len(luni_data)) % 4)
        luni = b"8BIMluni" + struct.pack(">I", len(luni_data)) + luni_data
        # A unique layer id (`lyid`): the PSD Importer maps a reimported layer to its sprite (and so its rig) by id.
        luni += b"8BIMlyid" + struct.pack(">II", 4, layer_ids[index])
        extra = struct.pack(">I", 0) + struct.pack(">I", 0) + pascal(name) + luni
        flags = 0 if visible else 2  # bit 1: hidden
        records += struct.pack(">iiiiH", y0, x0, y1, x1, 4) + channels
        records += (
            b"8BIMnorm"
            + struct.pack(">BBBB", 255, 0, flags, 0)
            + struct.pack(">I", len(extra))
            + extra
        )
    layer_info = struct.pack(">h", -len(layers)) + records + channel_data
    layer_info += b"\0" * ((-len(layer_info)) % 2)
    layer_section = (
        struct.pack(">Q", len(layer_info)) + layer_info + struct.pack(">I", 0)
    )
    with open(path, "wb") as f:
        f.write(
            b"8BPS"
            + struct.pack(">H", 2)
            + b"\0" * 6
            + struct.pack(">HIIHH", 4, H, W, 8, 3)
        )
        f.write(
            struct.pack(">I", 0) + struct.pack(">I", 0)
        )  # colour mode data, image resources
        f.write(struct.pack(">Q", len(layer_section)) + layer_section)
        f.write(struct.pack(">H", 0))  # the composite, raw: R, G, B, A planes
        for c in (0, 1, 2, 3):
            f.write(composite[:, :, c].astype(np.uint8).tobytes())
