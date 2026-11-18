#!/usr/bin/env python3
"""
Deterministic joint-event configuration IDs and printable reference cards.
"""

import csv
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path

CT_MIN_B = 0.20
# The last three positions are fixed: R<n>_<three digits>_A<n>B<n>O<n>.
CT_PATTERN = re.compile(
    r"^(?P<task>[A-Za-z][A-Za-z0-9_-]*)_R(?P<n>[1-9])_"
    r"(?P<index>\d{3})_A(?P<a>\d)B(?P<b>\d)O(?P<o>\d)$"
)


@dataclass(frozen=True)
class TaskConfig:
    task: str
    resolution: int  # denominator; R6 means probabilities in sixths
    index: int       # 1-based, sorted lexicographically by (overlap, A, B)
    a: int           # number out of resolution with A
    b: int           # number out of resolution with B
    overlap: int     # number out of resolution with both

    @property
    def name(self) -> str:
        return f"{self.task}_R{self.resolution}_{self.index:03d}_A{self.a}B{self.b}O{self.overlap}"

    @property
    def cell_counts(self) -> tuple[int, int, int, int]:
        """Counts for (both, A-only, B-only, neither)."""
        return (self.overlap, self.a - self.overlap,
                self.b - self.overlap, self.resolution - self.a - self.b + self.overlap)

    @property
    def joint_probabilities(self) -> tuple[float, float, float, float]:
        return tuple(c / self.resolution for c in self.cell_counts)


def configurations(task: str, resolution: int) -> list[TaskConfig]:
    """All valid configs at resolution n, in O-A-B lexicographic order."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", task):
        raise ValueError("task must start with a letter and contain only letters, digits, '_' or '-'")
    if not 1 <= resolution <= 9:
        raise ValueError("R must be 1..9 because the requested ID format has one digit")
    n = resolution
    triples = (
        (o, a, b)
        for a in range(n + 1)
        for b in range(n + 1)
        if b / CT_MIN_B >= n  # minimal P(B) >= CT_MIN_B; avoids floating-point errors
        for o in range(max(0, a + b - n), min(a, b) + 1)
    )
    return [TaskConfig(task, n, index, a, b, o)
            for index, (o, a, b) in enumerate(sorted(triples), start=1)]


def encode(task: str, resolution: int, a: int, b: int, overlap: int) -> TaskConfig:
    for item in configurations(task, resolution):
        if (item.a, item.b, item.overlap) == (a, b, overlap):
            return item
    raise ValueError(f"Not a valid grid configuration with P(B) >= {CT_MIN_B}")


def parse(name: str) -> TaskConfig:
    match = CT_PATTERN.fullmatch(name)
    if not match:
        raise ValueError("Invalid format; expected TASK_Rn_###_AaBbOo (one-digit counts)")
    fields = match.groupdict()
    actual = encode(fields['task'], int(fields['n']), int(fields['a']),
                    int(fields['b']), int(fields['o']))
    given_index = int(fields['index'])
    if given_index != actual.index:
        raise ValueError(f"Index mismatch: got {given_index:03d}, "
                         f"but O-A-B sorting requires {actual.index:03d}: {actual.name}")
    return actual



# Visualization


CT_PALETTE = {
    'Both': '#3E6FA8',
    'A only': '#E6A04C',
    'B only': '#42A485',
    'Neither': '#A6ADB8',
}

def export_csv(items: list[TaskConfig], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    columns = ['id', 'index', 'resolution', 'a', 'b', 'overlap',
               'p_a', 'p_b', 'p_overlap', 'p_ab', 'p_a_only', 'p_b_only', 'p_neither']
    with dest.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for c in items:
            ab, ao, bo, neither = c.joint_probabilities
            writer.writerow(dict(id=c.name, index=c.index, resolution=c.resolution,
                                 a=c.a, b=c.b, overlap=c.overlap,
                                 p_a=c.a / c.resolution, p_b=c.b / c.resolution,
                                 p_overlap=c.overlap / c.resolution,
                                 p_ab=ab, p_a_only=ao, p_b_only=bo, p_neither=neither))

def visualize_resolution(items: list[TaskConfig], dest: Path) -> None:
    """Print up to 20 configuration cards per US-letter page."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.pagesizes import letter

    if not items:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    width, height = letter
    pdf = canvas.Canvas(str(dest), pagesize=letter)
    pdf.setTitle(f"{items[0].task}: R{items[0].resolution} probability configurations")
    margin = 24
    cols, rows = 4, 5
    gutter_x, gutter_y = 8, 8
    top_y = height - 84
    bottom_y = 39
    card_w = (width - 2*margin - gutter_x*(cols-1)) / cols
    card_h = (top_y - bottom_y - gutter_y*(rows-1)) / rows
    card_padding = 9
    content_w = card_w - 2*card_padding
    preferred_name_size = 9
    per_page = cols*rows
    total_pages = math.ceil(len(items)/per_page)
    n = items[0].resolution

    tile_gap = 2
    tile_w = min(30, (content_w - (n-1)*tile_gap) / n)
    tile_h = 21
    tile_labels = {'Both': 'AB', 'A only': 'A', 'B only': 'B', 'Neither': '-'}

    for start in range(0, len(items), per_page):
        page_no = start//per_page + 1
        pdf.setFillColor(HexColor('#182536'))
        pdf.setFont('Helvetica-Bold', 17)
        pdf.drawString(margin, height-33, f'{items[0].task}  |  R{n}  |  {len(items)} configurations')
        pdf.setFont('Helvetica', 9)
        pdf.setFillColor(HexColor('#526171'))
        pdf.drawString(margin, height-49, 'Grid: 1/%d  |  P(B) >= 20%%  |  Reference order: overlap, A, B' % n)
        pdf.drawString(margin, height-62, 'Each tile = 1/%d; blue=both, orange=A only, green=B only, gray=neither' % n)
        pdf.setStrokeColor(HexColor('#D6DEE5'))
        pdf.line(margin, height-70, width-margin, height-70)
        for local, c in enumerate(items[start:start+per_page]):
            col, row = local%cols, local//cols
            x = margin + col*(card_w + gutter_x)
            y = top_y - (row+1)*card_h - row*gutter_y
            pdf.setStrokeColor(HexColor('#D1D9E0'))
            pdf.roundRect(x, y, card_w, card_h, 6, fill=0, stroke=1)
            text_x = x + card_padding
            pdf.setFillColor(HexColor('#142A42'))
            pdf.setFont('Helvetica-Bold', 11)
            pdf.drawString(text_x, y+card_h-22, f'#{c.index:03d}  A{c.a} B{c.b} O{c.overlap}')
            pdf.setFillColor(HexColor('#5A6472'))
            pdf.setFont('Helvetica', 8)
            pdf.drawString(text_x, y+card_h-42, f'P(A)={c.a}/{n}  P(B)={c.b}/{n}  P(AB)={c.overlap}/{n}')
            kinds = (['Both']*c.overlap + ['A only']*(c.a-c.overlap)
                     + ['B only']*(c.b-c.overlap)
                     + ['Neither']*(n-c.a-c.b+c.overlap))
            # Tile strip at a glance; tile counts sum to n exactly.
            tile_y = y + 39
            for t, kind in enumerate(kinds):
                tile_x = text_x + t*(tile_w + tile_gap)
                pdf.setFillColor(HexColor(CT_PALETTE[kind]))
                pdf.roundRect(tile_x, tile_y, tile_w, tile_h, 3, fill=1, stroke=0)
                pdf.setFillColor(white)
                pdf.setFont('Helvetica-Bold', 7)
                pdf.drawCentredString(tile_x + tile_w/2, tile_y + 8, tile_labels[kind])
            name = c.name
            name_width = pdf.stringWidth(name, 'Helvetica-Bold', preferred_name_size)
            name_size = preferred_name_size * min(1, content_w / name_width)
            pdf.setFillColor(HexColor("#000000"))
            pdf.setFont('Helvetica-Bold', name_size)
            pdf.drawString(text_x, y+16, name)
        pdf.setFillColor(HexColor('#647181'))
        pdf.setFont('Helvetica', 8)
        pdf.drawRightString(width-margin, 27, f'Page {page_no} / {total_pages}')
        pdf.showPage()
    pdf.save()


def main():
    output_dir = Path(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    for n in (3, 4, 5, 6, 7, 8):
        items = configurations('Default', n)        
        stem = f'Default_R{n}'
        export_csv(items, output_dir/f'{stem}_reference.csv')
        visualize_resolution(items, output_dir/f'{stem}_R{n}.pdf')

    
if __name__ == '__main__':
    main()
