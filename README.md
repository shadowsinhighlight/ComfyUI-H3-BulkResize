# ComfyUI-H3-BulkResize

Nine image slots in, nine out, each resized independently. Built for feeding
MiniMax H3 reference images at different resolutions from a single node.

- Aspect ratio is always preserved, nothing is ever cropped
- Both output sides snap to a multiple of 32 (configurable)
- The resulting resolution of every slot is printed inside the node

## Install

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/shadowsinhighlight/ComfyUI-H3-BulkResize
```

Or install it with ComfyUI-Manager via **Install via Git URL**. Then restart
ComfyUI and hard-refresh the browser (Ctrl+Shift+R) so the frontend picks up
the report widget.

No extra dependencies.

Node lives under **Bortevekk/H3 → H3 Bulk Reference Resize (9x)**.

## Global settings

| Widget | What it does |
| --- | --- |
| `multiple_of` | Snap both output sides to this. 32 by default. |
| `rounding` | `nearest` / `down` / `up` when snapping. |
| `upscale_method` | `lanczos` is best for downscaling references. |
| `allow_upscale` | Off by default, so small images are never blown up. |

## Per-slot settings

Each slot `i1`–`i9` has:

- `mode`
  - `passthrough` – leave the image untouched
  - `longest_edge` – scale so the longest side hits `longest_edge`
  - `max_width_height` – scale to fit inside the `max_width` × `max_height` box
- `longest_edge` – target for longest-edge mode
- `max_width` / `max_height` – box for max-width/height mode

Unconnected slots output `None` and are marked `(empty)` in the report — leave
those outputs unwired.

## The report

After each run the node shows something like:

```
multiple of 32 / round nearest / lanczos
1. 1920x1080 -> 1024x576  (0.533x, 0.59 MP)  AR 1.7778 -> 1.7778 (0.00% off)
2. 2048x2048 -> 768x768  (0.375x, 0.59 MP)  AR 1.0000 -> 1.0000 (0.00% off)
3. (empty)
```

The same text is also available on the `report` string output if you'd rather
pipe it into a text/preview node.

## One caveat worth knowing

Forcing *both* sides to a multiple of 32 and keeping the aspect ratio exactly
are mutually exclusive in the general case. The node scales by the true ratio,
then snaps each side, so the ratio can drift by up to half a step — usually
well under 1%, and 0% for common ratios like 16:9 or 1:1.

`rounding` is where you control that trade-off. In `max_width_height` mode,
`nearest` or `up` can push a side slightly past your limit (3000×2000 into a
1280×720 box lands on 1088×736). Set `rounding` to `down` if the box is a hard
ceiling.

## Related

- [ComfyUI-H3-PromptBuilder](https://github.com/shadowsinhighlight/ComfyUI-H3-PromptBuilder) — structured prompts and automatic reference numbering for MiniMax H3
- [ComfyUI-ReferenceSheet](https://github.com/shadowsinhighlight/ComfyUI-ReferenceSheet) — pack several views of a subject into one reference slot

## License

MIT — see [LICENSE](LICENSE). Made by Bortevekk Studio.
