"""Every \\hyperlink in the deck must resolve to a \\hypertarget in a frame the
deck inputs. A dangling button still compiles -- it just goes nowhere."""
import re
import sys
from pathlib import Path

PRES = Path(__file__).resolve().parent
BS = chr(92)
INPUT = re.compile(re.escape(BS + "input{frames/") + r"([^}]+)\.tex}")
HYPER = re.compile(re.escape(BS + "hypertarget{") + r"([^}]+)}")
LINK = re.compile(re.escape(BS + "hyperlink{") + r"([^}]+)}")

deck = "slides_report.tex"
drv = (PRES / deck).read_text(encoding="utf-8-sig")
frames = INPUT.findall(drv)
targets, links = set(), {}
for f in frames:
    txt = (PRES / "frames" / f"{f}.tex").read_text(encoding="utf-8")
    targets |= set(HYPER.findall(txt))
    for t in LINK.findall(txt):
        links.setdefault(t, []).append(f)
dangling = {t: v for t, v in links.items() if t not in targets}
print(f"{deck}: {len(frames)} frames, {len(targets)} targets, "
      f"{len(links)} distinct link targets, {len(dangling)} dangling")
for t, v in sorted(dangling.items()):
    print(f"   DANGLING {t}  <- {', '.join(sorted(set(v)))}")

# A frame file the driver never inputs is dead weight in the library.
unused = sorted(p.stem for p in (PRES / "frames").glob("*.tex") if p.stem not in frames)
for u in unused:
    print(f"   UNUSED frames/{u}.tex")
sys.exit(1 if dangling or unused else 0)
