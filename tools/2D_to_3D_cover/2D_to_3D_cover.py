"""This program creates a 3D cover from a 500x500 base image.

  Interactive mode (no arguments):
  - Select the source base image (tab to autocomplete).
  - Choose one of the available cover overlays (tab to autocomplete).
  - The generated 3D cover will be at the output directory.

  Automated mode:
  - Pass --base and --overlay to skip the prompts entirely, e.g.:
      python 2D_to_3D_cover.py --base SLUS-00001.jpg --overlay SIDE_LOGO
  - Passing only one of the two still prompts for the other.

  Be sure to review the generated images to ensure no problems occurred.

  Depends on:
    opencv-python >=5,<6
    prompt_toolkit >=3,<4
"""

__author__ = "RenanMsV"
__version__ = "1.0.0"

from pathlib import Path
from typing import Optional

import argparse
import sys

try:
    import cv2
except ImportError:
    print("Error: OpenCV is not installed.")
    print("Install it with:")
    print("    pip install opencv-python")
    sys.exit(1)

try:
    from prompt_toolkit import prompt
    from prompt_toolkit.completion import PathCompleter, WordCompleter
except ImportError:
    print("Error: prompt_toolkit is not installed.")
    print("Install it with:")
    print("    pip install prompt-toolkit")
    sys.exit(1)

import numpy as np

OUTPUT_DIR = Path("output")
OVERLAYS = {
    "DEFAULT": Path("overlays") / "default.png",
    "SIDE_LOGO": Path("overlays") / "side_logo.png",
    "GREATEST_HITS": Path("overlays") / "greatest_hits.png",
    "GREATEST_HITS_NO_COLUMN": Path("overlays") / "greatest_hits_no_column.png"
}

# Extensions suggested by tab-completion when picking a base image.
# Add more (e.g. ".png", ".jpeg", ".webp") to expand what's suggested.
IMAGE_COMPLETER_EXTENSIONS = (".jpg",)

_image_completer = PathCompleter(
    only_directories=False,
    file_filter=lambda filename:
        Path(filename).suffix.lower() in IMAGE_COMPLETER_EXTENSIONS,
)

_overlay_completer = WordCompleter(
    list(OVERLAYS.keys()),
    ignore_case=True,
    sentence=True,  # match/replace the whole line, not just the last word
)


def resolve_overlay(raw: str) -> Path:
    """Turn a raw overlay value (number, name, or path) into a Path.

    Does not check whether the resulting Path actually exists -
    callers decide how to handle a missing file (re-prompt vs. hard error).
    """
    names = list(OVERLAYS.keys())
    raw = raw.strip()

    if not raw:
        return OVERLAYS["DEFAULT"]
    if raw.isdigit() and 1 <= int(raw) <= len(names):
        return OVERLAYS[names[int(raw) - 1]]
    if raw.upper() in OVERLAYS:
        return OVERLAYS[raw.upper()]
    return Path(raw)


def prompt_base_image() -> Path:
    """Ask the user for the base image and return a valid Path to it."""
    while True:
        raw = prompt(
            "• Base image path (e.g. SLUS-00001.jpg) "
            "or press Tab to autocomplete: ",
            completer=_image_completer
        ).strip()
        path = Path(raw)
        if path.is_file():
            return path
        print(f"  -> File not found: {path}")


def prompt_overlay() -> Path:
    """Ask the user which overlay to use.

    Shows a numbered list of the known overlays in the OVERLAYS dict. The user
    can type the number, press Tab to cycle through the overlay names, or type
    a path to a custom overlay file. Leaving it blank falls back to DEFAULT.
    """
    names = list(OVERLAYS.keys())

    print("\nAvailable overlays:")
    for i, name in enumerate(names, start=1):
        print(f"  {i}. {name}")

    while True:
        raw = prompt(
            "• Choose an overlay by its number/name (Tab to cycle) "
            "or a path to a .png image: ",
            completer=_overlay_completer,
        )
        path = resolve_overlay(raw)

        if path.is_file():
            return path
        print(f"  -> File not found: {path}")


def load_images(base_path: Path, overlay_path: Path):
    """Load the base and overlay images,
    ensuring the base has an alpha channel."""
    base = cv2.imread(str(base_path), cv2.IMREAD_UNCHANGED)
    if base is None:
        raise ValueError(f"Could not read base image: {base_path}")

    overlay = cv2.imread(str(overlay_path), cv2.IMREAD_UNCHANGED)
    if overlay is None:
        raise ValueError(f"Could not read overlay image: {overlay_path}")

    if base.shape[2] == 3:
        base = cv2.cvtColor(base, cv2.COLOR_BGR2BGRA)

    return base, overlay


def build_cover(base: np.ndarray, overlay: np.ndarray) -> np.ndarray:
    """Warp the base image into the 3D cover
    perspective and blend the overlay on top."""
    # -----------------------------
    # Source corners (500x500 image)
    # -----------------------------
    src = np.float32([
        [0, 0],
        [499, 0],
        [499, 499],
        [0, 499]
    ])

    # -----------------------------
    # Destination corners for the warp
    # -----------------------------
    # estimated based on a 500x500 resolution
    dst_500 = np.float32([
        [69, 20],     # Top Left
        [493, 28],    # Top Right
        [493, 451],   # Bottom Right
        [69, 484]     # Bottom Left
    ])

    # -----------------------------
    # Perspective transform
    # -----------------------------
    matrix = cv2.getPerspectiveTransform(src, dst_500)

    warped_500 = cv2.warpPerspective(
        base,
        matrix,
        (500, 500),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)
    )

    resized_226 = cv2.resize(
        warped_500,
        (226, 226),
        interpolation=cv2.INTER_AREA
    )

    # -----------------------------
    # Alpha blend overlay on top
    # -----------------------------
    result = resized_226.copy()

    alpha = overlay[:, :, 3:4] / 255.0

    result[:, :, :3] = (
        overlay[:, :, :3] * alpha +
        result[:, :, :3] * (1 - alpha)
    ).astype(np.uint8)

    result[:, :, 3] = np.maximum(result[:, :, 3], overlay[:, :, 3])

    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a 3D cover from a 500x500 base image. "
                    "Run with no arguments for the interactive prompts, "
                    "or pass --base/--overlay to skip them."
    )
    parser.add_argument(
        "-b", "--base",
        help="Path to the base image. Skips the interactive prompt.",
    )
    parser.add_argument(
        "-o", "--overlay",
        help="Overlay number, name (e.g. SIDE_LOGO), or path to a .png. "
             "Skips the interactive prompt.",
    )
    return parser.parse_args()


def get_base_image(cli_value: Optional[str]) -> Path:
    """Resolve the base image from a CLI value, or fall back to prompting."""
    if cli_value is None:
        return prompt_base_image()

    path = Path(cli_value)
    if not path.is_file():
        print(f"Error: base image not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def get_overlay(cli_value: Optional[str]) -> Path:
    """Resolve the overlay from a CLI value, or fall back to prompting."""
    if cli_value is None:
        return prompt_overlay()

    path = resolve_overlay(cli_value)
    if not path.is_file():
        print(f"Error: overlay not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path


def main():
    """Executes the program"""
    args = parse_args()
    automated = args.base is not None and args.overlay is not None

    if not automated:
        print("Welcome » 2D to 3D cover tool.\n")

    base_path = get_base_image(args.base)
    overlay_path = get_overlay(args.overlay)

    base, overlay = load_images(base_path, overlay_path)
    result = build_cover(base, overlay)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{base_path.stem}.png"
    cv2.imwrite(str(output_path), result)

    print(f"Saved 3D cover to: {output_path}")


if __name__ == "__main__":
    main()
