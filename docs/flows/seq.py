"""Tiny sequence-diagram and box-diagram renderer (plain SVG) for the flows document."""
from html import escape

INK, MUTE, LINE = "#1B1F1D", "#6B726E", "#D9D6CC"
TONES = {  # fill, stroke, text
    "ink": ("#1B1F1D", "#1B1F1D", "#FFFFFF"),
    "app": ("#EDE9DD", "#B9B3A0", "#1B1F1D"),
    "api": ("#DCEBE3", "#2F6B57", "#173F33"),
    "stock": ("#F6E6C8", "#B7791F", "#6B4710"),
    "health": ("#DCE8F3", "#2B5F8A", "#1D4468"),
    "warn": ("#FBE9E4", "#B4412D", "#7A2A1C"),
    "note": ("#FAF7EE", "#CFC9B6", "#3A403D"),
}
CHAR = 5.35  # average glyph width at 10.5px


def wrap(text, width_px):
    limit = max(8, int(width_px / CHAR))
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            if cur and len(cur) + 1 + len(word) > limit:
                lines.append(cur)
                cur = word
            else:
                cur = f"{cur} {word}".strip()
        lines.append(cur)
    return lines


def tspans(lines, x, y0, lh=12.5, anchor="middle", weight=None, fill=INK, size=10.5, family=None):
    out = []
    for i, ln in enumerate(lines):
        w = f' font-weight="{weight}"' if weight else ""
        f = f' font-family="{family}"' if family else ""
        out.append(f'<text x="{x:.1f}" y="{y0 + i * lh:.1f}" text-anchor="{anchor}" font-size="{size}" fill="{fill}"{w}{f}>{escape(ln)}</text>')
    return "".join(out)


def sequence(lanes, steps, width=720):
    """lanes: [(id, title, subtitle, tone)]. steps: ('m', a, b, text[, kind]) | ('n', lane|(l1,l2), text[, tone]) | ('f', 'start', label) | ('f','end') | ('s', label)."""
    n = len(lanes)
    left, right = 62, width - 62
    xs = {l[0]: left + i * (right - left) / (n - 1) for i, l in enumerate(lanes)}
    head_h, y = 46, 62
    body, frames, stack, num = [], [], [], 0

    def badge(x, yy):
        nonlocal num
        num += 1
        return (f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="7.5" fill="{INK}"/>'
                f'<text x="{x:.1f}" y="{yy + 3.4:.1f}" text-anchor="middle" font-size="9" font-weight="700" fill="#fff">{num}</text>')

    for st in steps:
        kind = st[0]
        if kind == "m":
            _, a, b, text = st[:4]
            style = st[4] if len(st) > 4 else "call"
            xa, xb = xs[a], xs[b]
            span = abs(xb - xa) - 18
            lines = wrap(text, max(span, 90) if a != b else 150)
            lh = 12.5
            h = len(lines) * lh + 14
            ay = y + len(lines) * lh + 4
            mid = (xa + xb) / 2
            if a == b:  # message to itself: small loop
                x0 = xa
                body.append(f'<path d="M{x0:.1f} {ay - 6:.1f} h26 v14 h-26" fill="none" stroke="{INK}" stroke-width="1.1" marker-end="url(#ah)"/>')
                body.append(tspans(lines, x0 + 32, y + 9, anchor="start"))
                body.append(badge(x0 - 12, y + 6))
                h = max(h, len(lines) * lh + 20)
            else:
                dash = ' stroke-dasharray="4 3"' if style == "ret" else ""
                col = MUTE if style == "ret" else INK
                body.append(f'<line x1="{xa:.1f}" y1="{ay:.1f}" x2="{xb + (-6 if xb > xa else 6):.1f}" y2="{ay:.1f}" stroke="{col}" stroke-width="1.2"{dash} marker-end="url(#{"ah" if style != "ret" else "ahr"})"/>')
                body.append(tspans(lines, mid + (6 if style != "ret" else 0), y + 9, fill=col if style == "ret" else INK))
                if style != "ret":
                    tw = max(len(l) for l in lines) * CHAR
                    body.append(badge(max(min(xa, xb) + 12, mid - tw / 2 - 8), y + 6))
            y += h + 4
        elif kind == "n":
            _, over, text = st[:3]
            tone = st[3] if len(st) > 3 else "note"
            ls = over if isinstance(over, tuple) else (over, over)
            x1, x2 = xs[ls[0]], xs[ls[1]]
            if x1 == x2:
                w = 196
                x = min(max(x1 - w / 2, 4), width - w - 4)
            else:
                x = min(x1, x2) - 48
                w = abs(x2 - x1) + 96
            lines = wrap(text, w - 26)
            h = len(lines) * 12.5 + 12
            fill, stroke, tcol = TONES[tone]
            body.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
            body.append(tspans(lines, x + 22, y + 15, anchor="start", fill=tcol))
            body.append(badge(x + 11, y + 12))
            y += h + 8
        elif kind == "f":
            if st[1] == "start":
                stack.append((st[2], y))
                y += 16
            else:
                label, y0 = stack.pop()
                frames.append((label, y0 - 2, y + 2))
                y += 8
        elif kind == "s":
            body.append(f'<line x1="14" y1="{y + 8:.1f}" x2="{width - 14}" y2="{y + 8:.1f}" stroke="{LINE}" stroke-dasharray="2 3"/>')
            tw = len(st[1]) * 5.6 + 20
            body.append(f'<rect x="{width / 2 - tw / 2:.1f}" y="{y:.1f}" width="{tw:.1f}" height="17" rx="8.5" fill="#fff" stroke="{LINE}"/>')
            body.append(tspans([st[1]], width / 2, y + 12, weight=600, fill=MUTE, size=9.5))
            y += 26
    total = y + 14
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {total:.0f}" width="100%" font-family="Figtree, sans-serif">',
           '<defs>'
           f'<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{INK}"/></marker>'
           f'<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="{MUTE}"/></marker></defs>']
    for label, y0, y1 in frames:
        out.append(f'<rect x="8" y="{y0:.1f}" width="{width - 16}" height="{y1 - y0:.1f}" rx="8" fill="none" stroke="#B9B3A0" stroke-dasharray="5 4"/>')
        tw = len(label) * 5.4 + 16
        out.append(f'<rect x="14" y="{y0 - 8:.1f}" width="{tw:.1f}" height="15" rx="7.5" fill="#fff" stroke="#B9B3A0"/>')
        out.append(tspans([label], 14 + tw / 2, y0 + 3, weight=600, fill=MUTE, size=9.2))
    for lid, title, sub, tone in lanes:
        x = xs[lid]
        fill, stroke, tcol = TONES[tone]
        out.append(f'<line x1="{x:.1f}" y1="{head_h}" x2="{x:.1f}" y2="{total - 8:.0f}" stroke="{LINE}" stroke-width="1" stroke-dasharray="3 4"/>')
        out.append(f'<rect x="{x - 56:.1f}" y="6" width="112" height="{head_h - 8}" rx="9" fill="{fill}" stroke="{stroke}"/>')
        out.append(tspans([title], x, 22, weight=700, fill=tcol, size=11))
        if sub:
            out.append(tspans([sub], x, 35, fill=tcol, size=8.6))
    out.extend(body)
    out.append("</svg>")
    return "".join(out)


# ---------------------------------------------------------------- box diagrams

def box(x, y, w, h, title, sub="", tone="app", mono=False):
    fill, stroke, tcol = TONES[tone]
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1.1"/>'
    if sub:
        sl = wrap(sub, w - 14)
        s += tspans([title], x + w / 2, y + 17, weight=700, fill=tcol, size=10.5)
        s += tspans(sl, x + w / 2, y + 30, fill=tcol, size=8.6, lh=10.5)
    else:
        s += tspans([title], x + w / 2, y + h / 2 + 3.5, weight=700, fill=tcol, size=10.5)
    return s


def arrow(x1, y1, x2, y2, label="", dash=False, both=False, lx=None, ly=None, anchor="middle"):
    d = ' stroke-dasharray="4 3"' if dash else ""
    ms = ' marker-start="url(#bh)"' if both else ""
    s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="1.2"{d}{ms} marker-end="url(#bh)"/>'
    if label:
        mx = lx if lx is not None else (x1 + x2) / 2
        my = ly if ly is not None else (y1 + y2) / 2 - 5
        lines = label.split("\n")
        s += (f'<rect x="{mx - max(len(l) for l in lines) * 2.55 - 3:.1f}" y="{my - 9:.1f}" width="{max(len(l) for l in lines) * 5.1 + 6:.1f}" '
              f'height="{len(lines) * 10.5 + 2:.1f}" fill="#fff" opacity=".92"/>')
        s += tspans(lines, mx, my, size=8.6, lh=10.5, fill=MUTE, anchor=anchor)
    return s


def diagram(width, height, parts):
    defs = (f'<defs><marker id="bh" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0 L10 5 L0 10 z" fill="{INK}"/></marker></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" font-family="Figtree, sans-serif">{defs}'
            + "".join(parts) + "</svg>")


def container(x, y, w, h, title, tone):
    fill, stroke, tcol = TONES[tone]
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" fill-opacity=".38" stroke="{stroke}" stroke-width="1.2" stroke-dasharray="6 4"/>'
            + tspans([title], x + 16, y + 22, anchor="start", weight=700, fill=tcol, size=12))
