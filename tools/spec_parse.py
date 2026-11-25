"""Parse H156 learning outcomes from the spec's left column (pdftotext -bbox-layout)."""
import re, sys, json, subprocess, html

pdf, out = sys.argv[1], sys.argv[2]
s = subprocess.run(["pdftotext", "-bbox-layout", pdf, "-"], capture_output=True, text=True).stdout
LINE = re.compile(r'<line xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</line>', re.S)
WORD = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')

SEC = re.compile(r"^([1-4]\.\d(?:\.\d)?)\s+(.+)$")
sections = {}      # code -> title
outcomes = []      # {code, section, letter, roman, text}
cur_sec = None; cur = None; sub_letter = None
started = False

def flush():
    global cur
    if cur:
        cur["text"] = re.sub(r"\s+", " ", cur["text"]).strip().rstrip(".")
        cur["text"] = re.sub(r"\bs election\b", "selection", cur["text"])
        outcomes.append(cur)
    cur = None

for pg in re.findall(r"<page.*?</page>", s, re.S):
    W = float(re.search(r'<page width="([\d.]+)"', pg).group(1))
    lines = []
    for l in LINE.findall(pg):
        ws = [(float(a), float(b), float(c), float(d), html.unescape(t)) for a, b, c, d, t in WORD.findall(l[4])]
        lines.append(ws)
    # guidance column starts at the x of 'Additional guidance' header, else ~ mid page
    split = None
    for ws in lines:
        t = " ".join(w[4] for w in ws)
        if "Additional guidance" in t:
            split = [w for w in ws if w[4] == "Additional"][0][0] - 4
    if split is None:
        split = W * 0.5
    rows = {}
    for ws in lines:
        for w in ws:
            if w[0] < split:
                rows.setdefault(round(w[1]), []).append(w)
    for y in sorted(rows):
        ws = sorted(rows[y], key=lambda w: w[0])
        t = " ".join(w[4] for w in ws).strip()
        # drop the stray page-edge digit
        t = re.sub(r"^\d\s+(?=\()", "", t)
        m = SEC.match(t)
        if m and len(m.group(2)) < 70 and not m.group(2)[0].isdigit():
            code, title = m.group(1), m.group(2).strip()
            if code.count(".") == 2 or code.count(".") == 1:
                if code == "1.1" or started:
                    started = True
                    flush()
                    sections.setdefault(code, title)
                    if code.count(".") == 2:
                        cur_sec = code; sub_letter = None
                    continue
        if not started or not cur_sec:
            continue
        if re.match(r"^(Learning outcomes|Learners should be able|apply their knowledge|Version \d|Cambridge OCR|©)", t):
            continue
        if re.match(r"^\d+$", t):
            continue
        m = re.match(r"^\(([a-z])\)\s*(?:\(([ivx]+)\)\s*)?(.*)$", t)
        m2 = re.match(r"^\(([ivx]+)\)\s*(.*)$", t)
        if m and not (m.group(1) in "iv" and sub_letter and m.group(1) == "i" and False):
            letter = m.group(1)
            if letter in ("i", "v", "x") and sub_letter and not cur_is_letter_seq(letter) if False else False:
                pass
            # roman numeral "(i)" alone is ambiguous with letter i; treat (i) as roman when a parent letter is open
            if letter == "i" and sub_letter is not None and outcomes and cur and cur.get("letter") != "h":
                flush(); cur = {"code": f"{cur_sec}({sub_letter})(i)", "section": cur_sec, "text": m.group(3) or ""}
                continue
            flush(); sub_letter = letter
            if m.group(2):
                cur = {"code": f"{cur_sec}({letter})({m.group(2)})", "section": cur_sec, "letter": letter, "text": m.group(3)}
                parent_text = ""
            else:
                cur = {"code": f"{cur_sec}({letter})", "section": cur_sec, "letter": letter, "text": m.group(3)}
            continue
        if m2 and sub_letter:
            flush(); cur = {"code": f"{cur_sec}({sub_letter})({m2.group(1)})", "section": cur_sec, "text": m2.group(2)}
            continue
        if cur and t:
            cur["text"] += " " + t
flush()

# merge: a letter outcome immediately followed by its roman children keeps its stem text
clean = []
for o in outcomes:
    o.pop("letter", None)
    if not o["text"]:
        continue
    clean.append(o)
json.dump({"sections": sections, "outcomes": clean}, open(out, "w"), indent=1, ensure_ascii=False)
print(len(sections), "sections,", len(clean), "outcomes")
