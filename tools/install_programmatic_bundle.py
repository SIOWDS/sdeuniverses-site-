#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import base64, io, tarfile

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / '.programmatic-staging'
parts = sorted(STAGING.glob('part_*'))
if not parts:
    raise SystemExit('No programmatic bundle parts found')
encoded = ''.join(p.read_text(encoding='ascii').strip() for p in parts)
data = base64.b64decode(encoded, validate=True)
with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as tf:
    for m in tf.getmembers():
        dest = (ROOT / m.name).resolve()
        if ROOT.resolve() not in dest.parents and dest != ROOT.resolve():
            raise SystemExit(f'Unsafe tar member: {m.name}')
    tf.extractall(ROOT)
print(f'Installed {len(tf.getmembers())} entries from {len(parts)} parts')
