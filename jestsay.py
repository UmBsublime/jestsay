#!/usr/bin/env python3
"""
jestsay - cowsay with a twist

Overlays witty quips onto ANSI art images with 
proper color handling when possible.
"""

import argparse
import os
import random
import sys
import textwrap
from dataclasses import dataclass
from typing import List, Tuple, Optional


DEFAULT_XDG_DATA = os.path.join(os.path.expanduser("~/.local"), "share")
DEFAULT_XDG_DATA_HOME = os.environ.get("XDG_DATA_HOME", DEFAULT_XDG_DATA)
DEFAULT_JESTER = os.path.join(DEFAULT_XDG_DATA_HOME, "jestsay", "pixpop_bubble_short.ans")
DEFAULT_QUIPS = os.path.join(DEFAULT_XDG_DATA_HOME, "jestsay", "quips.txt")

DEFAULT_X_OFFSET = 23
DEFAULT_Y_OFFSET = 8
DEFAULT_WIDTH = 33
DEFAULT_HEIGHT = 3
DEFAULT_ALIGN = "center"
DEFAULT_COLOR = "#775A95"


@dataclass
class Cell:
    """Represents a single character cell with color information."""

    char: str
    fg_color: Optional[Tuple[int, int, int]] = None
    bg_color: Optional[Tuple[int, int, int]] = None
    bold: bool = False


class AnsiImage:
    """Represents an ANSI art image as a grid of cells."""

    def __init__(self):
        self.grid: List[List[Cell]] = []
        self.width = 0
        self.height = 0
        self.original_lines: List[str] = []
        self.modified_rows: set = set()

    def parse_ansi_file(self, filepath: str) -> None:
        """Parse an ANSI art file into a grid of cells."""
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        lines = content.split("\n")
        self.original_lines = lines
        self.grid = []

        for line in lines:
            row = self._parse_line(line)
            if row:
                self.grid.append(row)

        self.height = len(self.grid)
        self.width = max(len(row) for row in self.grid) if self.grid else 0

    def _parse_line(self, line: str) -> List[Cell]:
        """Parse a single line of ANSI content into cells."""
        row = []
        i = 0
        current_fg: Optional[Tuple[int, int, int]] = None
        current_bg: Optional[Tuple[int, int, int]] = None
        current_bold: bool = False

        while i < len(line):
            if line[i] == "\x1b" and i + 1 < len(line) and line[i + 1] == "[":
                seq_end = line.find("m", i)
                if seq_end == -1:
                    seq_end = len(line)
                else:
                    seq_end += 1

                seq = line[i:seq_end]
                fg, bg, bold, fg_explicit, bg_explicit = self._parse_escape_sequence(seq)

                if fg_explicit:
                    current_fg = fg
                if bg_explicit:
                    current_bg = bg
                if fg_explicit or bg_explicit:
                    current_bold = bold

                i = seq_end
            else:
                row.append(Cell(line[i], current_fg, current_bg, current_bold))
                i += 1

        return row

    def _parse_escape_sequence(
        self, seq: str
    ) -> Tuple[Optional[Tuple[int, int, int]], Optional[Tuple[int, int, int]], bool, bool, bool]:
        """Parse an ANSI escape sequence for colors.
        
        Returns: (fg_color, bg_color, bold, fg_explicitly_set, bg_explicitly_set)
        """
        fg = None
        bg = None
        bold = False
        fg_explicit = False
        bg_explicit = False

        if seq.startswith("\x1b[") and seq.endswith("m"):
            content = seq[2:-1]
        else:
            return fg, bg, bold, fg_explicit, bg_explicit

        codes = content.split(";")
        i = 0
        while i < len(codes):
            code = codes[i]

            if code == "0":
                fg = None
                bg = None
                bold = False
                fg_explicit = True
                bg_explicit = True
            elif code == "1":
                bold = True
            elif code == "22":
                bold = False
            elif code == "38" and i + 4 < len(codes) and codes[i + 1] == "2":
                try:
                    r = int(codes[i + 2])
                    g = int(codes[i + 3])
                    b = int(codes[i + 4])
                    fg = (r, g, b)
                    fg_explicit = True
                    i += 4
                except (ValueError, IndexError):
                    pass
            elif code == "48" and i + 4 < len(codes) and codes[i + 1] == "2":
                try:
                    r = int(codes[i + 2])
                    g = int(codes[i + 3])
                    b = int(codes[i + 4])
                    bg = (r, g, b)
                    bg_explicit = True
                    i += 4
                except (ValueError, IndexError):
                    pass
            elif code == "39":
                fg = None
                fg_explicit = True
            elif code == "49":
                bg = None
                bg_explicit = True

            i += 1

        return fg, bg, bold, fg_explicit, bg_explicit

    def render(self) -> str:
        """Render the image back to ANSI escape sequences."""
        result = []

        for row_idx, row in enumerate(self.grid):
            if row_idx not in self.modified_rows:
                result.append(self.original_lines[row_idx])
                continue

            last_fg: Optional[Tuple[int, int, int]] = None
            last_bg: Optional[Tuple[int, int, int]] = None
            last_bold: bool = False
            line_parts = []

            for cell in row:
                if (
                    cell.fg_color != last_fg
                    or cell.bg_color != last_bg
                    or cell.bold != last_bold
                ):
                    codes = []

                    if (
                        cell.fg_color is None
                        and cell.bg_color is None
                        and not cell.bold
                    ):
                        codes.append("0")
                    else:
                        if cell.bold:
                            codes.append("1")
                        if cell.fg_color is not None:
                            codes.append(
                                f"38;2;{cell.fg_color[0]};{cell.fg_color[1]};{cell.fg_color[2]}"
                            )
                        else:
                            codes.append("39")
                        if cell.bg_color is not None:
                            codes.append(
                                f"48;2;{cell.bg_color[0]};{cell.bg_color[1]};{cell.bg_color[2]}"
                            )
                        else:
                            codes.append("49")

                    if codes:
                        line_parts.append(f"\x1b[{';'.join(codes)}m")

                line_parts.append(cell.char)
                last_fg = cell.fg_color
                last_bg = cell.bg_color
                last_bold = cell.bold

            line_parts.append("\x1b[0m")
            result.append("".join(line_parts))

        return "\n".join(result)


def parse_color(hex_color: str) -> Tuple[int, int, int]:
    """Parse hex color code to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) not in (3, 6):
        raise ValueError(f"Invalid hex color length: {len(hex_color)} (expected 3 or 6)")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    try:
        return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
    except ValueError as e:
        raise ValueError(f"Invalid hex color '{hex_color}': {e}")


def load_quips(filepath: str) -> List[str]:
    """Load quips from file, one per line."""
    with open(filepath, "r", encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.strip().startswith("#")
        ]


def format_quip(quip: str, width: int, height: int, align: str) -> List[str]:
    """Format a quip for display within the given dimensions."""
    wrapped = textwrap.wrap(
        quip, width=width, break_long_words=False, replace_whitespace=False
    )

    wrapped = wrapped[:height]

    while len(wrapped) < height:
        wrapped.append("")

    result = []
    for line in wrapped:
        if align == "center":
            line = line.center(width)
        elif align == "right":
            line = line.rjust(width)
        else:
            line = line.ljust(width)
        result.append(line[:width])

    return result


def overlay_text(
    image: AnsiImage,
    text_lines: List[str],
    x_offset: int,
    y_offset: int,
    text_color: Tuple[int, int, int],
    bold: bool = True,
):
    """Overlay text onto the image, preserving original background colors."""
    for row_idx, line in enumerate(text_lines):
        y = y_offset + row_idx
        if y >= image.height:
            break

        image.modified_rows.add(y)

        for col_idx, char in enumerate(line):
            x = x_offset + col_idx
            if x >= image.width:
                break

            if char != " ":
                existing = image.grid[y][x]
                image.grid[y][x] = Cell(char, text_color, existing.bg_color, bold)


def main():
    parser = argparse.ArgumentParser(
        description="Overlay witty quips onto ANSI art images.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Use defaults
  %(prog)s --align left --color #FF5733
  %(prog)s --x-offset 20 --y-offset 5 --width 40
""",
    )

    parser.add_argument(
        "--jester",
        default=DEFAULT_JESTER,
        help=f"Path to ANSI art file (default: {DEFAULT_JESTER})",
    )
    parser.add_argument(
        "--quips", default=DEFAULT_QUIPS, help=f"Path to quips file (default: {DEFAULT_QUIPS})"
    )
    parser.add_argument(
        "--x-offset",
        type=int,
        default=DEFAULT_X_OFFSET,
        help=f"Horizontal position for text start (default: {DEFAULT_X_OFFSET})",
    )
    parser.add_argument(
        "--y-offset",
        type=int,
        default=DEFAULT_Y_OFFSET,
        help=f"Vertical position for text start (default: {DEFAULT_Y_OFFSET})",
    )
    parser.add_argument(
        "--width", type=int, default=DEFAULT_WIDTH, help=f"Width of text area (default: {DEFAULT_WIDTH})"
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT, help=f"Number of text lines (default: {DEFAULT_HEIGHT})"
    )
    parser.add_argument(
        "--align",
        choices=["left", "center", "right"],
        default=DEFAULT_ALIGN,
        help=f"Text alignment: left|center|right (default: {DEFAULT_ALIGN})",
    )
    parser.add_argument(
        "--color",
        default=DEFAULT_COLOR,
        help=f"Text color as hex code (default: {DEFAULT_COLOR})",
    )
    parser.add_argument(
        "--no-bold",
        action="store_true",
        help="Disable bold text (default: bold enabled)",
    )

    args = parser.parse_args()

    try:
        text_color = parse_color(args.color)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    image = AnsiImage()
    try:
        image.parse_ansi_file(args.jester)
    except FileNotFoundError:
        print(f"Error: ANSI art file not found: {args.jester}", file=sys.stderr)
        sys.exit(1)

    try:
        quips = load_quips(args.quips)
    except FileNotFoundError:
        print(f"Error: Quips file not found: {args.quips}", file=sys.stderr)
        sys.exit(1)

    if not quips:
        print("Error: No quips found in file", file=sys.stderr)
        sys.exit(1)

    quip = random.choice(quips)

    text_lines = format_quip(quip, args.width, args.height, args.align)

    text_height = len(text_lines)
    text_width = max((len(line) for line in text_lines), default=0)

    x_offset = max(0, min(args.x_offset, image.width - text_width))
    y_offset = max(0, min(args.y_offset, image.height - text_height))

    overlay_text(
        image, text_lines, x_offset, y_offset, text_color, not args.no_bold
    )

    print(image.render())


if __name__ == "__main__":
    main()
