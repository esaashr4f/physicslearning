"""Locate every question part in OCR A AS physics QPs and MSs.
Output per session: {qp:{w,h,units:[{label,segs:[[page,y0,y1],...]}]}, ms:{...}}
Coordinates are PDF points, y measured from the top.
"""
import re, sys, json, subprocess, os, glob, html

ROMAN = {"i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"}
LINE_RE = re.compile(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', re.S)
WORD_RE = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')


def pages_of(pdf):
    s = subprocess.run(["pdftotext", "-bbox-layout", pdf, "-"], capture_output=True, text=True).stdout
    out = []
    for pg in re.findall(r"<page.*?</page>", s, re.S):
        m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', pg)
        W, H = float(m.group(1)), float(m.group(2))
        words = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD_RE.findall(pg)]
        lines = []
        for l in LINE_RE.findall(pg):
            ws = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD_RE.findall(l[4])]
            lines.append((float(l[0]), float(l[1]), float(l[2]), float(l[3]), ws))
        out.append({"W": W, "H": H, "words": words, "lines": lines})
    return out


def is_noise(w, H):
    x0, y0, x1, y1, t = w
    if y0 < 22 and t in ("PMT",):
        return True
    return False


def content_bounds(pg):
    """top/bottom of the real content on a page (excludes running header/footer)."""
    H = pg["H"]; top, bot = None, None
    ys = []
    for (x0, y0, x1, y1, ws) in pg["lines"]:
        txt = " ".join(w[4] for w in ws).strip()
        if y0 < 24 and txt == "PMT":
            continue
        if re.fullmatch(r"\d{1,2}", txt) and y0 < 60:  # page number header
            continue
        if y0 > H - 75 and re.search(r"©\s*OCR|Turn over|^\d+$|OCR \d{4}|^PMT$", txt):
            continue
        if y0 < 50 and re.search(r"H156/0[12]|Mark Scheme|June|November|October|Specimen|SAM", txt):
            continue
        ys.append((y0, y1))
    if not ys:
        return None
    return min(a for a, b in ys), max(b for a, b in ys)


def lab(t):
    t = t.strip()
    m = re.fullmatch(r"\(([a-z])\)", t)
    if m and m.group(1) not in ROMAN - {"i", "v", "x"} | set():
        pass
    m = re.fullmatch(r"\(([ivx]+|[a-h])\)", t)
    return m.group(1) if m else None


def kind(x):
    return "roman" if x in ROMAN and x not in ("a", "b", "c", "d", "e", "f", "g", "h") else "letter"


# ---------------- Question paper ----------------
def qp_units(pdf):
    pages = pages_of(pdf)
    markers = []  # (page, y, label-tuple)
    ended = False
    cur_q, cur_l, cur_r = None, None, None
    usable = []
    for pi, pg in enumerate(pages):
        if pi == 0 or ended:
            usable.append(False); continue
        alltxt = " ".join(w[4] for w in pg["words"])
        if re.search(r"BLANK PAGE", alltxt) and len(pg["words"]) < 30:
            usable.append(False); continue
        if re.search(r"ADDITIONAL ANSWER SPACE|EXTRA ANSWER SPACE", alltxt) and not markers:
            usable.append(False); continue
        if re.search(r"ADDITIONAL ANSWER SPACE|EXTRA ANSWER SPACE", alltxt):
            usable.append(False); ended = True; continue
        usable.append(True)
        for (x0, y0, x1, y1, ws) in sorted(pg["lines"], key=lambda l: l[1]):
            txt = " ".join(w[4] for w in ws)
            if "END OF QUESTION PAPER" in txt:
                markers.append((pi, y0, None)); ended = True; break
            if x0 > 100 or not ws:
                continue
            toks = [w for w in ws if w[0] < 120]
            i = 0; found = []
            # question number
            if toks and re.fullmatch(r"\d{1,2}\*?", toks[0][4]) and toks[0][0] < 62:
                n = int(toks[0][4].rstrip("*"))
                if cur_q is None or n == cur_q + 1:
                    found.append(("q", n)); i = 1
            while i < len(toks) and lab(toks[i][4]) and toks[i][0] < 100:
                found.append(("p", lab(toks[i][4]))); i += 1
            if not found:
                continue
            q, l, r = cur_q, cur_l, cur_r
            ok = True
            for k, v in found:
                if k == "q":
                    q, l, r = v, None, None
                else:
                    if v in ROMAN and (l is not None) and (r is None and v == "i" or r is not None):
                        # roman sub-part
                        order = ["i", "ii", "iii", "iv", "v", "vi"]
                        exp = "i" if r is None else (order[order.index(r) + 1] if r in order[:-1] else None)
                        if v != exp:
                            ok = False; break
                        r = v
                    elif len(v) == 1 and v in "abcdefgh":
                        exp = "a" if l is None else chr(ord(l) + 1)
                        if v != exp:
                            ok = False; break
                        l, r = v, None
                    else:
                        ok = False; break
            if not ok or q is None:
                continue
            cur_q, cur_l, cur_r = q, l, r
            markers.append((pi, y0, (q, l, r)))
    return pages, usable, markers


def label_str(t):
    q, l, r = t
    return f"{q}" + (f"({l})" if l else "") + (f"({r})" if r else "")


def build_segments(pages, usable, markers, pad_top=5):
    """Each marker owns content until the next marker (across pages)."""
    units = []
    bounds = [content_bounds(pg) if u else None for pg, u in zip(pages, usable)]
    for k, (pi, y, t) in enumerate(markers):
        if t is None:
            continue
        nxt = markers[k + 1] if k + 1 < len(markers) else (len(pages), 0, None)
        segs = []
        p = pi
        while p < len(pages):
            if p > nxt[0] or (p == nxt[0] and False):
                break
            b = bounds[p]
            if b is None:
                p += 1
                if p > nxt[0]:
                    break
                continue
            y0 = y - pad_top if p == pi else b[0] - 4
            y1 = (nxt[1] - pad_top) if p == nxt[0] else b[1] + 6
            if p == nxt[0] and nxt[2] is None and nxt[1] == 0:
                break
            # trim to actual content inside the band
            inside = [l for l in pages[p]["lines"] if l[1] >= y0 - 1 and l[3] <= y1 + 1 and b[0] - 1 <= l[1] <= b[1] + 1]
            if inside:
                y1 = min(y1, max(l[3] for l in inside) + 8)
                if y1 - y0 > 6:
                    segs.append([p + 1, round(y0, 1), round(y1, 1)])
            if p == nxt[0]:
                break
            p += 1
        units.append({"label": label_str(t), "segs": segs})
    return units


# ---------------- Mark scheme ----------------
def ms_units(pdf):
    pages = pages_of(pdf)
    usable = []
    started = False; ended = False
    markers = []
    cur_q, cur_l, cur_r = None, None, None
    for pi, pg in enumerate(pages):
        txt = " ".join(w[4] for w in pg["words"])
        if not started and pi > 0:
            hdr = [w for w in pg["words"] if w[4] == "Question" and w[0] < 130]
            if any(any(w[4] in ("Answer", "Answers", "Marks", "Mark") and abs(w[1] - h[1]) < 6 for w in pg["words"]) for h in hdr):
                started = True
        if started and re.search(r"Assessment Objectives? (Grid|grid)|AO1\s+AO2\s+AO3", txt):
            ended = True
        usable.append(started and not ended)
        if not (started and not ended):
            continue
        # group label words by y
        cand = [w for w in pg["words"] if w[0] < 160]
        rows = {}
        for w in cand:
            key = round(w[1] / 3)
            rows.setdefault(key, []).append(w)
        for key in sorted(rows):
            ws = sorted(rows[key], key=lambda w: w[0])
            # merge near keys
            toks = [w for w in ws if re.fullmatch(r"\d{1,2}\*?|\(([a-h]|[ivx]+)\)|[a-h]|[ivx]+", w[4])]
            if not toks or ws[0] is not toks[0]:
                continue
            q, l, r = cur_q, cur_l, cur_r
            first = toks[0]
            found = []
            for w in toks:
                t = w[4]
                if re.fullmatch(r"\d{1,2}\*?", t) and not found:
                    found.append(("q", int(t.rstrip("*"))))
                else:
                    m = re.fullmatch(r"\(?([a-h]|[ivx]+)\)?", t)
                    if m:
                        found.append(("p", m.group(1)))
            if not found:
                continue
            ok = True
            for k, v in found:
                if k == "q":
                    if q is not None and v not in (q, q + 1, q + 2):
                        ok = False; break
                    if v != q:
                        l, r = None, None
                    q = v
                else:
                    if v in ROMAN and v not in "abcdefgh":
                        r = v
                    elif v in ROMAN and l is not None and r is None and v == "i":
                        r = v
                    else:
                        if v == l and r is not None:
                            continue
                        l, r = v, None
            if not ok or q is None:
                continue
            t = (q, l, r)
            if markers and markers[-1][2] == t:
                continue  # repeated label on continuation page
            cur_q, cur_l, cur_r = t
            markers.append((pi, ws[0][1], t))
    markers.append((len(pages), 0, None))
    return pages, usable, markers


def table_top(pg):
    """y below a repeated 'Question Answer Marks Guidance' header row."""
    for (x0, y0, x1, y1, ws) in pg["lines"]:
        if ws and ws[0][4] == "Question":
            return y1 + 2
    for w in pg["words"]:
        if w[4] in ("Question", "Answer") and w[1] < 140:
            return w[3] + 4
    return None


def run(paper, slug, base):
    qp = f"{base}/p{paper}-{slug}-qp.pdf"; ms = f"{base}/p{paper}-{slug}-ms.pdf"
    pages, usable, mk = qp_units(qp)
    qunits = build_segments(pages, usable, mk)
    W, H = pages[1]["W"], pages[1]["H"]
    mpages, musable, mmk = ms_units(ms)
    # for MS, on continuation pages start below table header
    munits = []
    bounds = [content_bounds(pg) if u else None for pg, u in zip(mpages, musable)]
    for k, (pi, y, t) in enumerate(mmk):
        if t is None:
            continue
        nxt = mmk[k + 1]
        segs = []
        p = pi
        while p < len(mpages) and p <= nxt[0]:
            b = bounds[p]
            if b is None:
                p += 1; continue
            if p == pi:
                y0 = y - 4
            else:
                tt = table_top(mpages[p]); y0 = (tt if tt else b[0]) - 2
            y1 = (nxt[1] - 4) if p == nxt[0] else b[1] + 4
            if y1 - y0 > 8:
                ws = [w for w in mpages[p]["words"] if w[3] > y0 and w[1] < y1 and not (w[1] < 24 and w[4] == "PMT")]
                if ws:
                    W_ = mpages[p]["W"]
                    xa = max(20, min(w[0] for w in ws) - 10); xb = min(W_ - 20, max(w[2] for w in ws) + 12)
                    segs.append([p + 1, round(y0, 1), round(y1, 1), round(xa, 1), round(xb, 1)])
                else:
                    segs.append([p + 1, round(y0, 1), round(y1, 1)])
            if p == nxt[0]:
                break
            p += 1
        munits.append({"label": label_str(t), "segs": segs})
    MW, MH = mpages[0]["W"], mpages[0]["H"]
    qs = [[round(pg["W"], 1), round(pg["H"], 1)] for pg in pages]
    ms = [[round(pg["W"], 1), round(pg["H"], 1)] for pg in mpages]
    return {"qp": {"w": W, "h": H, "sizes": qs, "units": qunits}, "ms": {"w": MW, "h": MH, "sizes": ms, "units": munits}}


if __name__ == "__main__":
    base, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for f in sorted(glob.glob(f"{base}/p*-qp.pdf")):
        m = re.match(r"p(\d)-(\w+)-qp\.pdf", os.path.basename(f)); paper, slug = m.group(1), m.group(2)
        try:
            r = run(paper, slug, base)
        except Exception as e:
            print("FAIL", paper, slug, e); continue
        json.dump(r, open(f"{outdir}/p{paper}-{slug}.json", "w"))
        print(f"p{paper}-{slug}: qp {len(r['qp']['units'])} units, ms {len(r['ms']['units'])} units")
