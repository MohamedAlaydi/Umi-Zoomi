#!/usr/bin/env python3
"""Build PITCH_PRECLINICAL_DRAFT.pptx from SLIDE_SPEC.md.

Visual identity is taken from deck B (review/panel18plus2/PITCH_18_PLUS_2.pptx):
13.333 x 7.5 in (16:9), DejaVu Sans, background F9FAF5, teal 00776C eyebrow,
navy 142B36 headline, slate 415E65 secondary text, mint DEF1EB / white / peach
F7E7DA tiles, a grey hairline at y=6.75 and an 12 pt source strip at y=6.94.
No images: every element is a native shape, text box or table.

python-pptx is not installed in this environment; it is imported from the uv
wheel cache (override with PPTX_PATHS, colon-separated).

Run:  python3 build_draft.py
"""
from __future__ import annotations

import os
import sys

_DEFAULT_PATHS = [
    "/home/hackathon/.cache/uv/archive-v0/EMGm8sepJkikMlVS",  # python-pptx 1.0.2
    "/home/hackathon/.cache/uv/archive-v0/Fr71oWU9ck0teCrK",  # lxml
    "/home/hackathon/.cache/uv/archive-v0/fH_0v4UYp_PS_0Q4",  # Pillow (text metrics)
    "/home/hackathon/.cache/uv/archive-v0/nDT0ISByfnNQA-ig",  # XlsxWriter
]
for _p in os.environ.get("PPTX_PATHS", ":".join(_DEFAULT_PATHS)).split(":"):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.enum.shapes import MSO_SHAPE  # noqa: E402
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN  # noqa: E402
from pptx.util import Emu, Inches, Pt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "PITCH_PRECLINICAL_DRAFT.pptx")

# ---------------------------------------------------------------- palette ----
BG = RGBColor(0xF9, 0xFA, 0xF5)
TEAL = RGBColor(0x00, 0x77, 0x6C)
NAVY = RGBColor(0x14, 0x2B, 0x36)
SLATE = RGBColor(0x41, 0x5E, 0x65)
MINT = RGBColor(0xDE, 0xF1, 0xEB)
GREY = RGBColor(0xE4, 0xE9, 0xE5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PEACH = RGBColor(0xF7, 0xE7, 0xDA)
RED = RGBColor(0xC6, 0x28, 0x28)  # only for the [VERIFY] / [TEAM TO CONFIRM] tags

FONT = "DejaVu Sans"
L = 0.62          # left margin, as deck B
W = 12.08         # content width, as deck B
RULE_Y = 6.75
SRC_Y = 6.94
LINE = 1.21       # line height multiplier used for fit checks
TLINE = 1.02      # tighter line spacing inside table cells

# ------------------------------------------------------------ text metrics ----
_TTF = {
    False: "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    True: "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
}
_FONTS: dict[tuple[bool, int], object] = {}


def _font(bold: bool, px: int = 200):
    from PIL import ImageFont

    key = (bold, px)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(_TTF[bold], px)
    return _FONTS[key]


def measure(text: str, size: float, bold: bool) -> float:
    """Width of `text` in inches at `size` pt."""
    if not text:
        return 0.0
    f = _font(bold)
    return f.getlength(text) / 200.0 * size / 72.0


def wrap(text: str, width_in: float, size: float, bold: bool) -> list[str]:
    """Greedy word wrap; mirrors how PowerPoint breaks on spaces."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if measure(trial, size, bold) <= width_in or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


ISSUES: list[str] = []


def _check(tag: str, text: str, width_in: float, height_in: float, size: float, bold: bool,
           line: float = LINE) -> int:
    lines = wrap(text, width_in, size, bold)
    need = len(lines) * size * line / 72.0
    if need > height_in + 0.005:
        ISSUES.append(
            f"{tag}: needs {need:.2f}in for {len(lines)} line(s) at {size}pt, box is {height_in:.2f}in"
        )
    longest = max(measure(x, size, bold) for x in lines)
    if longest > width_in + 0.005:
        ISSUES.append(f"{tag}: unbreakable line {longest:.2f}in wide, box is {width_in:.2f}in")
    return len(lines)


# ------------------------------------------------------------- primitives ----
class Deck:
    def __init__(self) -> None:
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.3333)
        self.prs.slide_height = Inches(7.5)
        self.blank = self.prs.slide_masters[0].slide_layouts[6]
        self.sid = -1

    # -- shapes ------------------------------------------------------------
    def rect(self, slide, left, top, width, height, fill):
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
        sh.line.fill.background()
        sh.shadow.inherit = False
        sh.text_frame.word_wrap = True
        return sh

    def text(self, slide, left, top, width, height, runs, size, bold=False,
             color=NAVY, align=PP_ALIGN.LEFT, tag="", space=0.0):
        """runs: str, or list of (text, bold, color) / (text, bold, color, size)."""
        if isinstance(runs, str):
            runs = [(runs, bold, color)]
        box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = box.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.alignment = align
        p.line_spacing = LINE
        if space:
            p.space_after = Pt(space)
        flat = ""
        for item in runs:
            t, b, c = item[0], item[1], item[2]
            sz = item[3] if len(item) > 3 else size
            r = p.add_run()
            r.text = t
            r.font.name = FONT
            r.font.size = Pt(sz)
            r.font.bold = b
            r.font.color.rgb = c
            flat += t
        _check(f"s{self.sid} {tag or flat[:34]!r}", flat, width, height, size, bold or runs[0][1])
        return box

    def para_block(self, slide, left, top, width, lines, size, color=SLATE, bold=False, gap=0.06, tag=""):
        """Stack of independent one-paragraph text boxes; returns the bottom edge."""
        y = top
        for item in lines:
            runs = item if isinstance(item, list) else [(item, bold, color)]
            flat = "".join(r[0] for r in runs)
            n = len(wrap(flat, width, size, runs[0][1]))
            h = n * size * LINE / 72.0
            self.text(slide, left, y, width, h, runs, size, bold=bold, color=color, tag=tag)
            y += h + gap
        return y - gap

    # -- slide chrome ------------------------------------------------------
    def new(self, eyebrow, headline, source, head_top=0.79, head_size=32.0):
        self.sid += 1
        s = self.prs.slides.add_slide(self.blank)
        self.rect(s, 0, 0, 13.3333, 7.5, BG)
        self.text(s, L, 0.38, W, 0.31, eyebrow, 13, bold=True, color=TEAL, tag="eyebrow")
        # shrink the headline until it fits two lines of the content width
        size = head_size
        while size > 19 and len(wrap(headline, W, size, True)) > 2:
            size -= 1
        n = len(wrap(headline, W, size, True))
        h = n * size * LINE / 72.0
        self.text(s, L, head_top, W, h, headline, size, bold=True, color=NAVY, tag="headline")
        self.rect(s, L, RULE_Y, W, 0.012, GREY)
        if source:
            runs = source if isinstance(source, list) else [(source, False, SLATE)]
            flat = "".join(r[0] for r in runs)
            nsrc = len(wrap(flat, W, 12, False))
            self.text(s, L, SRC_Y, W, nsrc * 12 * LINE / 72.0 + 0.01, runs, 12, color=SLATE, tag="source")
        self.head_bottom = head_top + h
        return s

    def notes(self, slide, spoken, sources):
        slide.notes_slide.notes_text_frame.text = (
            f"SPOKEN: {spoken}\n\nSOURCES: {sources}"
        )

    # -- composites --------------------------------------------------------
    def row(self, slide, top, height, fill=WHITE, left=L, width=W):
        return self.rect(slide, left, top, width, height, fill)

    def stat_tile(self, slide, left, top, width, height, big, label, sub):
        self.rect(slide, left, top, width, height, MINT)
        self.text(slide, left + 0.21, top + 0.18, width - 0.42, 0.64, big, 38, bold=True, color=TEAL)
        self.text(slide, left + 0.21, top + 0.96, width - 0.42, 0.56, label, 17, bold=True, color=NAVY)
        self.text(slide, left + 0.21, top + 1.58, width - 0.42, 0.62, sub, 13, color=SLATE)

    def residue_tile(self, slide, left, top, size_in, letter, number, contact):
        self.rect(slide, left, top, size_in, size_in, TEAL if contact else GREY)
        self.text(slide, left, top + 0.07, size_in, size_in - 0.14,
                  letter, 20, bold=True, color=WHITE if contact else NAVY, align=PP_ALIGN.CENTER)
        self.text(slide, left, top + size_in + 0.06, size_in, 0.24,
                  number, 12, color=SLATE, align=PP_ALIGN.CENTER)

    def bar(self, slide, top, label, value, scale_max, colour):
        """Deck B slide 2 bar: label, grey track, filled bar, value."""
        track_l, track_w, track_h = 4.93, 5.42, 0.28
        self.text(slide, L, top, 4.26, 0.41, label, 17, bold=True, color=NAVY)
        self.rect(slide, track_l, top + 0.03, track_w, track_h, GREY)
        self.rect(slide, track_l, top + 0.03, track_w * value / scale_max, track_h, colour)
        self.text(slide, 10.72, top - 0.07, 1.98, 0.51, f"{value:.2f} / {scale_max:g}",
                  21, bold=True, color=colour)

    def table(self, slide, left, top, col_widths, rows, size=12.0, row_h=0.40, head_h=0.34):
        """Native pptx table, styled like deck B's row tiles (white rows, no grid)."""
        nrows, ncols = len(rows), len(col_widths)
        shp = slide.shapes.add_table(nrows, ncols, Inches(left), Inches(top),
                                     Inches(sum(col_widths)), Inches(head_h + (nrows - 1) * row_h))
        tbl = shp.table
        tbl.first_row = True
        tbl.horz_banding = False
        for i, cw in enumerate(col_widths):
            tbl.columns[i].width = Inches(cw)
        for r in range(nrows):
            tbl.rows[r].height = Inches(head_h if r == 0 else row_h)
        for r, rowdata in enumerate(rows):
            for c, cell_runs in enumerate(rowdata):
                cell = tbl.cell(r, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = GREY if r == 0 else WHITE
                cell.margin_left = cell.margin_right = Inches(0.07)
                cell.margin_top = cell.margin_bottom = Inches(0.03)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.line_spacing = TLINE
                runs = cell_runs if isinstance(cell_runs, list) else [(cell_runs, r == 0, SLATE if r == 0 else NAVY)]
                flat = ""
                for item in runs:
                    t, b, col = item[0], item[1], item[2]
                    sz = item[3] if len(item) > 3 else size
                    run = p.add_run()
                    run.text = t
                    run.font.name = FONT
                    run.font.size = Pt(sz)
                    run.font.bold = b
                    run.font.color.rgb = col
                    flat += t
                avail_w = col_widths[c] - 0.14
                avail_h = (head_h if r == 0 else row_h) - 0.06
                _check(f"s{self.sid} table r{r}c{c}", flat, avail_w, avail_h, size, runs[0][1],
                       line=TLINE)
        bottom = top + head_h + (nrows - 1) * row_h
        if bottom > RULE_Y - 0.05:
            ISSUES.append(f"s{self.sid} table: bottom at {bottom:.2f}in overruns the rule at {RULE_Y}")
        return tbl


def tag(text_: str):
    """The small visible red [VERIFY] / [TEAM TO CONFIRM] tag the spec requires."""
    return (f"  [{text_}]", True, RED, 11.0)


# ===================================================================== deck ==
def build() -> Presentation:
    d = Deck()

    # --------------------------------------------------------- slide 0 ------
    s = d.new("TEAM 14    /    PRE-CLINICAL PITCH  ·  DRAFT",
              "Testing better HER2 engagement, one decision at a time",
              "All numbers for our designs are predictions. Nothing has been measured yet.")
    d.text(s, L, 2.00, W, 0.42,
           "Team 14 · trastuzumab CDRH3 redesign · AI x Antibodies Hackathon Oslo",
           21, color=NAVY, tag="subtitle")
    d.stat_tile(s, L, 3.25, 3.81, 2.35, "20", "abguard-valid designs", "Fab panel, order frozen")
    d.stat_tile(s, 4.62, 3.25, 3.81, 2.35, "4", "Guaranteed lab slots", "One matched pair inside")
    d.stat_tile(s, 8.62, 3.25, 4.08, 2.35, "0", "Measured results", "Every value is predicted")
    d.notes(s, "Trastuzumab is a validated molecule. We spent our judgment on which four "
               "designs deserve a lab slot, and we have measured nothing ourselves yet.",
            "Panel size and slot counts: review/panel18plus2/TEAMBESLUTNING.md and "
            "RANKED_18_PLUS_2.csv (18 Fabs + 2 VHH = 20; four guaranteed slots). "
            "Zero measured results: PITCH_PRECLINICAL_PROPOSAL.md section 4.")

    # --------------------------------------------------------- slide 1 ------
    s = d.new("CLINICAL BACKGROUND    /    WHY ENGAGEMENT, NOT A NEW TARGET",
              "Trastuzumab transformed HER2+ breast cancer, but it still leaves patients behind",
              "Clinical figures are from memory and must be checked against the primary papers "
              "before this deck is shown.")
    lcol, lw = L, 5.06
    rcol, rw = 6.10, 6.60
    d.text(s, lcol, 1.98, lw, 0.34, "What it did", 15, bold=True, color=SLATE)
    d.para_block(s, lcol, 2.40, lw, [
        [("Binds HER2 domain IV near the membrane (Cho 2003, structure 1N8Z)", False, NAVY)],
        [("Approved 1998", False, NAVY), tag("VERIFY"),
         ("; with chemotherapy, longer survival (Slamon 2001)", False, NAVY), tag("VERIFY numbers")],
        [("Adjuvant use roughly halves recurrence", False, NAVY), tag("VERIFY HR")],
    ], 13, gap=0.20, tag="s1-left")

    d.text(s, rcol, 1.98, rw, 0.34, "Where it stops", 15, bold=True, color=SLATE)
    boxes = [
        ("1", [("Resistance: single-agent response only about 15-35 %", True, NAVY), tag("VERIFY")]),
        ("2", [("Epitope loss or masking: p95HER2 (shedding, or translation start at Met-611); MUC4", True, NAVY)]),
        ("3", [("Bypass signalling: PIK3CA / PTEN, HER3", True, NAVY)]),
        ("4", [("Low-density disease and the heart: HER2-low needs payload formats (T-DXd); "
                "cardiotoxicity follows HER2 signalling block", True, NAVY)]),
    ]
    y = 2.40
    for num, runs in boxes:
        d.row(s, y, 0.78, WHITE, left=rcol, width=rw)
        d.text(s, rcol + 0.18, y + 0.19, 0.30, 0.40, num, 15, bold=True, color=TEAL)
        d.text(s, rcol + 0.58, y + 0.13, rw - 0.80, 0.54, runs, 12, color=NAVY, tag=f"s1-box{num}")
        y += 0.86
    d.rect(s, L, 5.90, W, 0.70, MINT)
    d.text(s, L + 0.21, 6.09, W - 0.42, 0.34,
           "Our question: can we improve target engagement without leaving the validated epitope?",
           16, bold=True, color=NAVY, tag="s1-bar")
    d.notes(s, "Trastuzumab is validated; the open question is engagement, not a new target.",
            "Cho 2003 (1N8Z), Slamon 2001, Romond 2005, Cobleigh 1999, Vogel 2002, "
            "DESTINY-Breast04 - all to be checked. Narrative and the [VERIFY] flags: "
            "PITCH_PRECLINICAL_PROPOSAL.md section 2.")

    # --------------------------------------------------------- slide 2 ------
    s = d.new("EPITOPE MAP    /    19 CONTACTS, 4 REDESIGNABLE POSITIONS",
              "Keep the epitope, change the grip, measure three things",
              "Source: 1N8Z organiser crop (HER2 489-607, domain IV). Heavy-atom contacts within 4.5 A.")
    d.text(s, L, 1.95, 6.60, 0.32, "CDRH3 WGGDGFYAMD in the reference crystal", 14, bold=True, color=SLATE)
    cdr = [("W", "99", True), ("G", "100", False), ("G", "101", False), ("D", "102", False),
           ("G", "103", True), ("F", "104", True), ("Y", "105", True), ("A", "106", False),
           ("M", "107", False), ("D", "108", False)]
    x, tile, pitch = L, 0.56, 0.63
    for letter, number, contact in cdr:
        d.residue_tile(s, x, 2.40, tile, letter, number, contact)
        x += pitch
    d.text(s, L, 3.35, 6.60, 0.30, "Green = contacts HER2 (W99, G103, F104, Y105).  Grey = free.",
           12, color=SLATE, tag="s2-legend")
    d.text(s, L, 3.72, 6.60, 0.52,
           "19 HER2 contact residues; 4 of 10 redesignable CDRH3 positions touch HER2.",
           13, bold=True, color=NAVY, tag="s2-caption")

    d.rect(s, 7.30, 1.95, 5.40, 2.70, MINT)
    d.text(s, 7.52, 2.14, 4.96, 0.62,
           "Improved target engagement = three readouts vs same-run trastuzumab",
           15, bold=True, color=NAVY, tag="s2-right-head")
    ry = 2.92
    for name, detail in [("SPR binding", "KD against the control in the same run"),
                         ("Epitope preservation", "Competition with trastuzumab"),
                         ("Thermostability", "Tm not worse than the control")]:
        d.text(s, 7.52, ry, 4.96, 0.26, name, 13, bold=True, color=TEAL)
        d.text(s, 7.52, ry + 0.27, 4.96, 0.26, detail, 12, color=SLATE)
        ry += 0.58
    d.rect(s, L, 4.86, W, 1.52, PEACH)
    d.para_block(s, L + 0.23, 5.04, W - 0.46, [
        [("CDRH3 only: ten light-chain contacts stay out of reach.", True, NAVY)],
        [("Trastuzumab WT in our SPR data: 8 records 0.0285-0.178 nM, median 0.1345 nM.", False, SLATE)],
        [("Not “tighter is better”: tumour penetration and heart safety are tested at gate 3.",
          False, SLATE)],
    ], 13, gap=0.09, tag="s2-strip")
    d.notes(s, "We keep the validated epitope and redesign only the grip. The 489-607 crop is "
               "HER2 domain IV, which is where trastuzumab binds, so the crop is not a shortcut.",
            "Contact map and the four contacting CDRH3 positions: scripts/contacts.py, "
            "review/pitch_her2/HER2_pitch.pptx slide 1. WT SPR range 0.0285-0.178 nM, median "
            "0.1345 nM: review/panel18plus2/historical_binding.json (wt_observations_nM, "
            "thresholds_nM). Three readouts: PITCH_PRECLINICAL_PROPOSAL.md section 1.")

    # --------------------------------------------------------- slide 3 ------
    s = d.new("PIPELINE    /    SEVEN GATES, 64 MILLION TO FOUR",
              "Seven gates, each with a reason",
              [("Counts are reproducible from run 006. The seeds, the 5,000 / 40 cut sizes and "
                "p_high ≥ 0.95 are pragmatic, not tuned", False, SLATE),
               tag("TEAM TO CONFIRM wording")])
    gates = [
        ("64,000,000", "all fillings of the 6 free CDRH3 positions",
         [("free generation lost contacts or novelty (runs 004, 005)", False, SLATE)]),
        ("39,731,174", "pass organizer novelty rule",
         [("> 2 mutations, < 70 % CDRH3 identity", False, SLATE)]),
        ("25,208,628", "no Cys, both liabilities changed, identity ≤ 60 %",
         [("margin below the 70 % limit; remove D102/M107 flags", False, SLATE),
          tag("TEAM TO CONFIRM source file")]),
        ("5,000", "top by FACS-model score plus BLOSUM62 to parent",
         [("BLOSUM beat our own model retrospectively", False, SLATE)]),
        ("40", "refolded with Boltz-2 on the 1N8Z template",
         [("do the four anchor contacts survive?", False, SLATE)]),
        ("20", "abguard-validated Fab panel",
         [("legality receipts hashed", False, SLATE), tag("TEAM TO CONFIRM panel formation vs run 012")]),
        ("4", "guaranteed lab slots",
         [("matched pair answers a question even if all fail", False, SLATE)]),
    ]
    y = 1.70
    for count, gate, reason in gates:
        d.row(s, y, 0.60, WHITE)
        d.text(s, 0.83, y + 0.17, 1.60, 0.28, count, 14, bold=True, color=TEAL, tag=f"s3-n{count}")
        d.text(s, 2.50, y + 0.10, 4.30, 0.44, gate, 12, bold=True, color=NAVY, tag=f"s3-g{count}")
        d.text(s, 6.95, y + 0.10, 5.53, 0.44, reason, 12, color=SLATE, tag=f"s3-r{count}")
        y += 0.63
    d.rect(s, L, 6.14, W, 0.46, MINT)
    d.text(s, L + 0.21, 6.26, W - 0.42, 0.26,
           "Free loop: 0/10 kept all four contacts. Anchored: 10/10 kept contacts, 0/10 novel. "
           "So we enumerate.", 12, bold=True, color=NAVY, tag="s3-note")
    d.notes(s, "Each gate exists because the previous one failed in a specific way. The seeds, the "
               "5,000 and 40 cut sizes and the p_high >= 0.95 threshold are pragmatic choices, "
               "not tuned [TEAM TO CONFIRM wording].",
            "64,000,000 / 39,731,174 / 25,208,628: run 006 enumeration (pipeline_notes.md stage on "
            "people/anas/feasible.py + score_legal.py). Top 5,000 and top 40: legal-scored.csv, "
            "p_high 0.9965-0.9769. 20 abguard-valid: review/panel18plus2/VERIFICATION.json, "
            "validator-output.csv. Four slots: TEAMBESLUTNING.md. Run 004 0/10 and run 005 10/10: "
            "PITCH_PRECLINICAL_PROPOSAL.md section 3, decisions 3-5. The 25.2 M figure must be "
            "linked to the run-006 output file.")

    # --------------------------------------------------------- slide 4 ------
    s = d.new("RETROSPECTIVE CHECK    /    255 HISTORICAL VARIANTS",
              "The ranker beats chance on past data, but it cannot promise a better binder",
              "Lower KD means tighter binding. The 5,000 draws reuse one historical pool, and part "
              "of that series was itself BLOSUM-selected.")
    d.text(s, L, d.head_bottom + 0.10, W, 0.30,
           "Mean reportable-KD hits among four picks, over 5,000 draws of 40.",
           13, color=SLATE, tag="s4-lede")
    d.bar(s, 2.38, "Random selection", 1.28, 4, SLATE)
    d.bar(s, 3.14, "FACS-trained model", 2.11, 4, TEAL)
    d.bar(s, 3.90, "BLOSUM62 to parent", 2.38, 4, TEAL)
    d.rect(s, L, 4.54, W, 1.14, PEACH)
    d.text(s, L + 0.23, 4.72, W - 0.46, 0.78,
           "0 of 82 quantified historical variants beat the weakest trastuzumab record (0.185 nM).",
           19, bold=True, color=NAVY, tag="s4-null")
    d.text(s, L, 5.86, W, 0.56,
           "Assay transfer AUROC: BLOSUM 0.847 vs our classifier 0.751; paired difference +0.095 "
           "(95 % interval 0.061-0.132).", 14, color=SLATE, tag="s4-auroc")
    d.notes(s, "The bars are selection enrichment: how often a rule picks a variant that gave a "
               "reportable KD at all. They are not efficacy, and they do not say a design will "
               "beat trastuzumab.",
            "1.28 / 2.11 / 2.38 per four picks and the 82 quantified variants with best 0.185 nM: "
            "review/panel18plus2/historical_binding.json (methods.*.fits_per_four, "
            "quantified_constructs, lowest_quantified_kd_nM) and deck B slide 2. "
            "AUROC 0.847 / 0.751, paired +0.095 [0.061, 0.132]: review/evidence/assay_transfer.json "
            "via review/assay_transfer.py.")

    # --------------------------------------------------------- slide 5 ------
    s = d.new("MODEL DISAGREEMENT    /    OPENFOLD3, BOLTZ-2, MOL-1",
              "Where our models disagree, we treat it as uncertainty",
              [("One continuous 119-residue HER2 chain; heavy atoms within 4.5 A of the observed "
                "1N8Z footprint. Apheris OpenFold3 is in the pipeline", False, SLATE),
               tag("TEAM TO CONFIRM it is the Apheris build")])
    d.text(s, L, 1.88, 7.00, 0.52,
           "OpenFold3 crystal contacts recovered out of 19, seeds 42 / 7 / 101",
           13, bold=True, color=SLATE, tag="s5-tablehead")
    d.text(s, 0.76, 2.40, 2.30, 0.42, "Construct", 12, bold=True, color=SLATE)
    d.text(s, 3.16, 2.40, 2.10, 0.42, "Sequence only", 12, bold=True, color=SLATE)
    d.text(s, 5.34, 2.40, 2.24, 0.42, "With HER2 coordinates", 12, bold=True, color=SLATE)
    for i, (name, a, b) in enumerate([("Trastuzumab control", "7  /  8  /  11", "7  /  13  /  10"),
                                      ("anas_007", "0  /  3  /  3", "1  /  0  /  6")]):
        ry = 2.88 + i * 0.86
        d.row(s, ry, 0.76, WHITE, left=L, width=7.00)
        d.text(s, 0.76, ry + 0.22, 2.30, 0.32, name, 14, bold=True, color=NAVY)
        d.text(s, 3.16, ry + 0.18, 2.10, 0.40, a, 18, bold=True, color=TEAL)
        d.text(s, 5.34, ry + 0.18, 2.24, 0.40, b, 18, bold=True, color=TEAL)
    d.text(s, L, 4.68, 7.00, 0.56,
           "Three seeds per cell, in the same order. The control itself misses known contacts.",
           12, color=SLATE, tag="s5-caption")

    facts = [
        ("Trastuzumab control itself",
         "OpenFold3 recovers only 7-13 of 19 contacts (2/19 in the broader control test), "
         "so OpenFold3 is a weak judge of this epitope."),
        ("Boltz-2 six-seed spread",
         "SD 0.0147, minimum detectable difference about 0.054; 0 of 8 strict-pass designs "
         "stay top 8 by six-seed mean."),
        ("Mol-1 recovers 19/19",
         "All 18 Fabs reach 19/19, so Mol-1 cannot rank them."),
    ]
    fx, fw = 7.92, 4.78
    fy = 1.88
    for head, body in facts:
        n = len(wrap(body, fw - 0.44, 12, False))
        h = 0.32 + n * 12 * LINE / 72.0 + 0.30
        d.rect(s, fx, fy, fw, h, WHITE)
        d.text(s, fx + 0.22, fy + 0.15, fw - 0.44, 0.28, head, 13, bold=True, color=TEAL)
        d.text(s, fx + 0.22, fy + 0.47, fw - 0.44, n * 12 * LINE / 72.0, body, 12, color=NAVY,
               tag=f"s5-fact-{head[:12]}")
        fy += h + 0.14
    d.notes(s, "Our predictors disagree, so we report the disagreement instead of picking the "
               "predictor that flatters a candidate. We do not rank anas_007 first on OpenFold3 "
               "contact counts, because the control scores no better.",
            "7/8/11, 7/13/10, 0/3/3, 1/0/6: review/panel18plus2/OPENFOLD_RESULTS.csv "
            "(crystal_hits by condition no_template / HER2_only_template, seeds 42/7/101); "
            "same table in TEAMBESLUTNING.md. 2/19 control and Mol-1 18/19: run 011 "
            "(pipeline_notes.md stage 10). Seed SD 0.0147, MDD about 0.054, 0 of 8 PASS_STRICT: "
            "run 009. Mol-1 19/19 for all 18 Fabs: RANK_AND_EVIDENCE.csv (mol1_hits_of19).")

    # --------------------------------------------------------- slide 6 ------
    s = d.new("THE PANEL    /    FOUR GUARANTEED PLACES",
              "Twenty designs, four slots, one decidable question",
              "Order frozen before data. No tier claimed.")
    lw2 = 7.26
    ranks = [
        ("#1  anas_015", [("Contact-retaining hypothesis: all four loop positions touch HER2 in "
                           "6/6 predicted poses, BLOSUM 32.", False, NAVY)]),
        ("#2  anas_007", [("BLOSUM 36, four loop contacts in 6/6 predicted poses, 98.2 % "
                           "footprint overlap.", False, NAVY)]),
        ("#3  anas_028", [("BLOSUM 38, four loop contacts in 6/6 poses: the sequence-conservative "
                           "choice.", False, NAVY)]),
        ("#4  anas_009", [("Matched challenger: all four contacts in 0/6 poses, same BLOSUM 32.",
                           False, NAVY)]),
    ]
    y = 1.92
    for name, runs in ranks:
        d.row(s, y, 0.70, WHITE, left=L, width=lw2)
        d.text(s, 0.83, y + 0.23, 1.70, 0.26, name, 14, bold=True, color=TEAL)
        d.text(s, 2.62, y + 0.15, lw2 - 2.14, 0.42, runs, 12, color=NAVY, tag=f"s6-{name[:3]}")
        y += 0.76
    d.rect(s, L, 4.98, lw2, 0.84, MINT)
    d.para_block(s, L + 0.21, 5.12, lw2 - 0.42, [
        [("Matched pair: anas_015 (6/6) vs anas_009 (0/6), same BLOSUM 32.", True, NAVY)],
        [("If both bind, contact geometry did not matter; if only 015 does, it did.", False, SLATE)],
    ], 12, gap=0.06, tag="s6-pair")
    d.para_block(s, L, 5.94, lw2, [
        [("Four slots test four optimisations; six slots bring in the first de novo design",
          False, SLATE), tag("TEAM TO CONFIRM six vs eight")],
        [("Beyond the four: novel3 is #6 and novel1 is #12 in the same frozen order.", False, SLATE)],
    ], 12, gap=0.08, tag="s6-slots")

    rx, rwid = 8.10, 4.60
    d.text(s, rx, 1.92, rwid, 0.30, "Liabilities (predicted)", 15, bold=True, color=SLATE)
    liab = [
        "All 20 remove the Isom D102-G103 motif and the Met-107 flag.",
        "11/20 add one new flag; the top designs swap Met-107 for Trp, trading one oxidation flag for another.",
        "StaB-ddG, shown with standard error: anas_009 -0.228 ± 0.204 vs anas_015 +0.274 ± 0.204 kcal/mol.",
        "Only 11 of 20 designs have a ddG value at all.",
    ]
    total = 0.30
    blocks = []
    for t in liab:
        n = len(wrap(t, rwid - 0.44, 12, False))
        blocks.append((t, n))
        total += n * 12 * LINE / 72.0 + 0.16
    d.rect(s, rx, 2.30, rwid, total + 0.14, MINT)
    by = 2.48
    for t, n in blocks:
        h = n * 12 * LINE / 72.0
        d.text(s, rx + 0.22, by, rwid - 0.44, h, t, 12, color=NAVY, tag="s6-liab")
        by += h + 0.16
    d.notes(s, "The first two slots carry our hypothesis and our most replicated contact face; the "
               "pair at 015 and 009 is built so the lab answers a question even if nothing binds.",
            "Order anas_015, anas_007, anas_028, anas_009 with novel3 #6 and novel1 #12: "
            "review/panel18plus2/TEAMBESLUTNING.md (and RANKED_18_PLUS_2.csv). BLOSUM 32 / 36 / 38 "
            "and the 6/6 vs 0/6 Boltz-2 loop contacts: TEAMBESLUTNING.md 'Hvorfor disse fire'; "
            "98.2 % footprint overlap for anas_007: RANK_AND_EVIDENCE.csv. Slot arithmetic 4/0, 5/1, "
            "7/1 ... : TEAMBESLUTNING.md 'Etter fire' - six slots bring in the first de novo design. "
            "Liabilities and 11/20: run 013 liability control; StaB-ddG -0.228 +/- 0.204 and "
            "+0.274 +/- 0.204 with only 11/20 valued: RANK_AND_EVIDENCE.csv.")

    # --------------------------------------------------------- slide 7 ------
    s = d.new("PATH TO VALUE    /    GATES AND GO / NO-GO",
              "A pre-clinical path with go / no-go gates",
              [("Every threshold below is a proposal, team to agree", False, SLATE),
               tag("TEAM TO CONFIRM")])
    col_w, gap = 2.32, 0.12
    gates7 = [
        ("GATE 0", "In silico (done)", "Receipts and 20 abguard-valid designs."),
        ("GATE 1", "Adaptyv", "Expression, SPR, competition, Tm vs same-run WT. Go: binding at or "
                              "better than WT beyond 0.054-equivalent noise, competition kept, Tm not worse."),
        ("GATE 2", "Cells (IgG1 reformat)", "BT-474, SK-BR-3 (HER2 3+), MCF-7 (low), JIMT-1 "
                                            "(resistant), MDA-MB-468 (negative); binding, internalization, "
                                            "proliferation, ADCC."),
        ("GATE 3", "Safety and developability", "hiPSC-cardiomyocyte window, DSF/SEC/HIC, immunogenicity."),
        ("GATE 4", "In vivo", "BT-474 and JIMT-1 xenografts vs trastuzumab, PK."),
    ]
    tile_h = 2.74
    for i, (label, title, body) in enumerate(gates7):
        x = L + i * (col_w + gap)
        d.rect(s, x, 1.88, col_w, tile_h, WHITE if i else MINT)
        d.text(s, x + 0.16, 2.02, col_w - 0.32, 0.26, label, 12, bold=True, color=TEAL)
        n = len(wrap(title, col_w - 0.32, 13, True))
        d.text(s, x + 0.16, 2.34, col_w - 0.32, n * 13 * LINE / 72.0, title, 13, bold=True, color=NAVY,
               tag=f"s7-title{i}")
        bt = 2.34 + n * 13 * LINE / 72.0 + 0.12
        nb = len(wrap(body, col_w - 0.32, 12, False))
        d.text(s, x + 0.16, bt, col_w - 0.32, nb * 12 * LINE / 72.0, body, 12, color=SLATE,
               tag=f"s7-body{i}")
        if bt + nb * 12 * LINE / 72.0 > 1.88 + tile_h - 0.08:
            ISSUES.append(f"s7 gate {label}: text runs past the tile bottom")

    d.rect(s, L, 4.80, W, 1.08, MINT)
    d.para_block(s, L + 0.21, 4.96, W - 0.42, [
        [("User: HER2+ patients who relapse or have low-density / masked HER2, and teams who want "
          "a lower-liability CDRH3.", True, NAVY)],
        [("Value if gate 1 holds: the molecule; either way: the method.", False, SLATE)],
    ], 13, gap=0.08, tag="s7-value")
    d.text(s, L, 6.08, W, 0.42,
           "Three readouts, same-run control, frozen order, replication before any general claim.",
           16, bold=True, color=NAVY, tag="s7-close")
    d.notes(s, "Gate 1 is the only gate the hackathon can reach. Everything after it is a plan with "
               "stated decision rules, and the thresholds are a proposal the team still has to agree.",
            "Gate table, readouts and go/no-go wording: PITCH_PRECLINICAL_PROPOSAL.md section 4. "
            "The 0.054 noise-equivalent threshold: run 009 minimum detectable delta. "
            "Cell lines and the Fab-to-IgG1 reformat requirement: proposal section 4. "
            "Cardiotoxicity and binding-site-barrier caveat: proposal section 5.")

    # ------------------------------------------------------------ B1 -------
    s = d.new("BACKUP B1    /    DECISION LOG",
              "Twelve decisions, each with a reason, a rejected alternative and evidence",
              "Full wording: PITCH_PRECLINICAL_PROPOSAL.md section 3.",
              head_top=0.74, head_size=24.0)
    b1 = [
        ["Decision", "Reason", "Rejected alternative", "Evidence"],
        ["Template = trastuzumab / 1N8Z", "Only crystal structure of the clinical molecule on domain IV",
         "Pertuzumab or de novo only", "scripts/contacts.py: 19 contacts at 4.5 A"],
        ["Redesign CDRH3 only", "Organizer legality; framework and expression untouched",
         "Framework mutations", "abguard receipts; 20/20 valid"],
        ["Free-loop generation", "Unbiased baseline", "n/a", "Run 004: 0/10 kept all four contacts"],
        ["Anchor the four contacts", "Direct response to run 004", "Keep the loop free",
         "Run 005: 10/10 contacts, 0/10 novel"],
        ["Enumerate the six free positions", "Sampling cannot satisfy contact and novelty together",
         "More sampling", "Run 006: 64 M → 39,731,174 → 25,208,628"],
        ["Rank by BLOSUM62, tie-break with the FACS model", "Retrospective test on measured data",
         "FACS model alone; random", "AUROC 0.847 vs 0.751; +0.095 [0.061, 0.132]"],
        ["Multi-seed refold (6 seeds)", "Seed noise decides whether rankings mean anything",
         "Single seed 42", "SD 0.0147; ICC 0.567; MDD about 0.054"],
        ["Cross-check OpenFold3 / Mol-1 / OpenDDE", "Prize requirement; disagreement is information",
         "Single predictor", "OpenFold3 2/19 on WT; Mol-1 18/19"],
        ["Controls at every stage", "Prevents scoring artefacts", "none",
         "In-batch WT; 7,902 shuffled decoys; SPR calibration"],
        ["StaB-ddG plus liability scan", "Thermostability is judged and our worst-covered property",
         "Affinity only", "Only 11/20 have a ddG; SE reported"],
        ["Top four as a designed experiment", "A matched pair answers a question even if all four fail",
         "Four highest scores", "Ranks 1/4: same BLOSUM 32, 6/6 vs 0/6"],
        ["De novo VHH on hold", "No calibrated ranker; OpenFold3 misses the control epitope",
         "Ship the VHH", "Run 011"],
    ]
    d.table(s, L, 1.32, [2.66, 3.86, 2.30, 3.26], b1, size=12.0, row_h=0.41, head_h=0.30)
    d.notes(s, "This is the judgment table: every gate on slide 3 has a row here with what we "
               "rejected and the file that shows it.",
            "All twelve rows: PITCH_PRECLINICAL_PROPOSAL.md section 3 (which cites "
            "scripts/contacts.py, runs 004 / 005 / 006 / 009 / 011 / 012, "
            "review/assay_transfer.py and the abguard receipts).")

    # ------------------------------------------------------------ B2 -------
    s = d.new("BACKUP B2    /    OPEN ITEMS",
              "What we have not justified",
              "Listing these is cheaper than being asked about them.",
              head_top=0.74, head_size=24.0)
    d.text(s, L, 1.45, 6.10, 0.32, "Six decisions with no recorded rationale", 15, bold=True, color=SLATE)
    unjust = [
        "Boltz-2 seed 42 and the generation seeds",
        "N = 40 and TOPN",
        "Why six seeds",
        "The 5,000 and 40 cut sizes",
        "p_high ≥ 0.95",
        "Jaccard over recall",
    ]
    y = 1.90
    for t in unjust:
        d.row(s, y, 0.46, WHITE, left=L, width=6.10)
        d.text(s, L + 0.21, y + 0.13, 5.68, 0.26, t, 13, color=NAVY, tag="b2-left")
        y += 0.52
    d.text(s, 7.10, 1.45, 5.60, 0.32, "Three open items", 15, bold=True, color=SLATE)
    openitems = [
        "Run 006 NOTE.md is an empty template, although the submission draws on run 006",
        "notes/DECISIONS.md stops at 13:20; runs 009-014 have no entry",
        "The 25.2 M figure still needs to be linked to its run-006 output file",
    ]
    y = 1.90
    for t in openitems:
        n = len(wrap(t, 5.18, 13, False))
        h = max(0.46, n * 13 * LINE / 72.0 + 0.24)
        d.row(s, y, h, PEACH, left=7.10, width=5.60)
        d.text(s, 7.31, y + 0.12, 5.18, n * 13 * LINE / 72.0, t, 13, color=NAVY, tag="b2-right")
        y += h + 0.10
    d.text(s, L, 6.00, W, 0.56,
           "These are pragmatic choices, not tuned parameters. Labelling them is part of the "
           "decision log, not an apology for it.", 13, color=SLATE, tag="b2-foot")
    d.notes(s, "If a juror asks why six seeds or why 5,000, the honest answer is that the number "
               "was pragmatic and the noise floor, not the cut size, is what we measured.",
            "Six unjustified decisions and the three open items: "
            "PITCH_PRECLINICAL_PROPOSAL.md section 3, closing paragraphs.")

    # ------------------------------------------------------------ B3 -------
    s = d.new("BACKUP B3    /    CORRECTIONS",
              "Retractions and corrections we made",
              "All of them are kept in the repository, not removed.",
              head_top=0.74, head_size=24.0)
    corr = [
        ("Retracted", "Epitope-footprint erosion count: it was sub-angstrom relaxation of a "
                      "templated prediction, on light-chain contacts we never touched."),
        ("Corrected", "The M107 oxidation claim was reversed once and the sources still disagree, "
                      "so we now say the abguard scan flags it and literature support is mixed."),
        ("Corrected", "Novelty reference was incomplete: 525,063 local CDRH3 rows vs 610,109 in abguard."),
        ("Bug fixed", "A reporting fallback displayed another run's sequences; per-run path "
                      "isolation is now asserted."),
        ("Tool bug", "abguard novelty-report skipped its reference DB by default, so an unknown "
                     "novelty value must not be counted as a pass."),
        ("Withheld", "16 AntiFold variants held back at 70.9-73.1 % identity to a known antibody."),
    ]
    y = 1.45
    for label, body in corr:
        n = len(wrap(body, 10.00, 13, False))
        h = max(0.52, n * 13 * LINE / 72.0 + 0.26)
        d.row(s, y, h, WHITE)
        d.text(s, 0.83, y + 0.13, 1.60, 0.26, label, 13, bold=True, color=TEAL)
        d.text(s, 2.50, y + 0.13, 10.00, n * 13 * LINE / 72.0, body, 13, color=NAVY, tag="b3-row")
        y += h + 0.11
    d.notes(s, "A record of what we got wrong is the cheapest evidence that the rest was checked.",
            "Items 1-5: PITCH_PRECLINICAL_PROPOSAL.md section 7 limitations and the repository's "
            "failed / corrected / retracted list (pipeline_notes.md section 3). "
            "16 AntiFold variants at 70.9-73.1 % identity: CAMPAIGN_RESULTS.md. Note that the "
            "proposal (section 2) and the pipeline notes disagree on the direction of the M107 "
            "correction; the wording above states only what both agree on.")

    # ------------------------------------------------------------ B4 -------
    s = d.new("BACKUP B4    /    RUBRIC MAP",
              "Which slide answers which criterion",
              "Weights from the task PDF p.7 as recorded in the proposal.",
              head_top=0.74, head_size=24.0)
    crit = [
        ("Judgment", "40", "Slides 3, 4, 5, 6", "Reason per gate, the null result, model "
                                                "disagreement, the matched pair. Backups B1-B3."),
        ("Execution", "20", "Slides 3, 6", "Counts reproducible from run 006, abguard receipts, "
                                           "liabilities and ddG with SE. Backups B1, B3."),
        ("User fit", "20", "Slides 1, 7", "Who is left behind by trastuzumab today, and who uses "
                                          "the panel and the method."),
        ("Path to value", "20", "Slides 6, 7", "Frozen order before data, then gates 1-4 with "
                                               "stated go / no-go rules."),
    ]
    cw, cgap = 2.93, 0.12
    for i, (name, weight, slides_, body) in enumerate(crit):
        x = L + i * (cw + cgap)
        d.rect(s, x, 1.50, cw, 3.10, MINT)
        d.text(s, x + 0.20, 1.68, cw - 0.40, 0.62, weight, 34, bold=True, color=TEAL)
        d.text(s, x + 0.20, 2.40, cw - 0.40, 0.30, name, 15, bold=True, color=NAVY)
        d.text(s, x + 0.20, 2.78, cw - 0.40, 0.30, slides_, 13, bold=True, color=SLATE)
        n = len(wrap(body, cw - 0.40, 12, False))
        d.text(s, x + 0.20, 3.14, cw - 0.40, n * 12 * LINE / 72.0, body, 12, color=NAVY, tag=f"b4-{name}")
    d.text(s, L, 4.86, W, 0.56,
           "Novelty earns no points; it is a legality gate only. Model-based affinity claims are "
           "treated with suspicion, which is why slides 4 and 5 lead with the null result and the "
           "noise floor.", 13, color=SLATE, tag="b4-foot")
    d.notes(s, "Four criteria, four answers. If a juror only has one question, it is probably "
               "judgment, and that is slides 3 to 6.",
            "Criteria and weights (Judgment 40, Execution 20, User fit 20, Path to value 20) and "
            "the novelty / affinity caveats: PITCH_PRECLINICAL_PROPOSAL.md section 0.")

    return d


def main() -> int:
    d = build()
    d.prs.save(OUT)
    print(f"wrote {OUT}")
    print(f"slides: {len(d.prs.slides)}")
    notes_missing = [i for i, s in enumerate(d.prs.slides) if not s.has_notes_slide
                     or not s.notes_slide.notes_text_frame.text.strip()]
    print(f"slides without notes: {notes_missing or 'none'}")
    if ISSUES:
        print(f"\nLAYOUT ISSUES ({len(ISSUES)}):")
        for i in ISSUES:
            print("  -", i)
        return 1
    print("\nlayout audit: no overflow found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
