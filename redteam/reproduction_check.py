#!/usr/bin/env python3
"""Read-only paper/config comparison; never used to construct candidates."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('/home/user')
AUDIT = ROOT / 'redteam'


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.table, self.row, self.cell = [], None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.table = []
        elif tag == 'tr':
            self.row = []
        elif tag == 'td':
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag == 'td':
            self.row.append(''.join(self.cell).strip())
            self.cell = None
        elif tag == 'tr':
            self.table.append(self.row)
            self.row = None
        elif tag == 'table':
            self.tables.append(self.table)
            self.table = None


def main():
    parser = Tables()
    parser.feed((ROOT / 'paper/2511.09073.md').read_text())
    table = next(t for t in parser.tables
                 if t[0] == ['Reference', 'Formula', 'Owl-Red', 'Slim-Red', 'GFM-GF'])
    start = next(i for i, r in enumerate(table) if r[0] == 'NCS')
    paper_ncs = [r[1:] if i == 0 else r for i, r in enumerate(table[start:start + 8])]
    numeric = lambda text: int(re.match(r'\d+', text)[0]) if re.match(r'\d+', text) else None
    owl = [numeric(r[1]) for r in paper_ncs]
    slim = [numeric(r[2]) for r in paper_ncs]
    gfm = [numeric(r[3]) for r in paper_ncs]
    cfg = json.loads((ROOT / 'scoring/reference.json').read_text())['experiments']
    specs = json.loads((ROOT / 'data/gf_benchmarks.json').read_text())['benchmarks']
    baseline = subprocess.run(['bash', 'scripts/baseline.sh'], cwd=ROOT,
                              capture_output=True, text=True)
    result = {
        'source': 'Packaged paper/2511.09073.md Table 5; extracted text may contain OCR errors.',
        'paper_ncs_rows': paper_ncs,
        'paper_ncs_owl_counts': owl,
        'paper_ncs_owl_finite_subtotal_not_total': sum(x for x in owl if x is not None),
        'paper_ncs_slim_counts': slim,
        'paper_ncs_slim_total': sum(slim),
        'paper_ncs_gfm_counts': gfm,
        'gym_ncs_specs': [s for s in specs if s['family'] == 'NCS'],
        'gym_reference_ncs': cfg['ncs_ordered_sequence']['results'],
        'baseline_shell': {'returncode': baseline.returncode,
                           'stdout': baseline.stdout, 'stderr': baseline.stderr},
        'interpretation': 'Gym consecutive offsets differ from the nonuniform offsets in the paper. '
                          'Equal GFM state-count sequences do not establish identical problems. '
                          'Owl times out in the last paper row; a total needs a failure policy.'
    }
    (AUDIT / 'reproduction_check.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'paper_slim_total': sum(slim), 'paper_owl_finite_subtotal': sum(x for x in owl if x is not None),
                      'baseline_shell_exit': baseline.returncode}))


if __name__ == '__main__':
    main()
