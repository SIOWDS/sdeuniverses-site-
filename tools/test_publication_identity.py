"""Regression tests for imported memory; never mutate the working publication."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegisterMemoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for rel in ['tools/book-m459/register_agent.py', 'tools/book-m459/content.json',
                    'public/books/agents.json', 'public/books/m/459/publication-unit.json',
                    'public/books/m/459/keypoints.json']:
            dst = self.root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dst)
        self.memory = self.root / 'public/books/m/459/keypoints.json'
        self.agents = self.root / 'public/books/agents.json'

    def run_import(self, data, ok):
        source = self.root / 'incoming.json'
        source.write_text(json.dumps(data, ensure_ascii=False))
        before = [p.read_bytes() for p in [self.memory, self.agents]]
        result = subprocess.run([sys.executable, str(self.root / 'tools/book-m459/register_agent.py'), str(source)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        if not ok:
            self.assertEqual(before, [p.read_bytes() for p in [self.memory, self.agents]],
                             'Rejected import must not partially update the registry')
        else:
            self.assertEqual(json.loads(self.memory.read_text()), data)
            self.assertEqual(json.loads(before[1])['agents']['414'],
                             json.loads(self.agents.read_text())['agents']['414'])

    def test_old_volume_rejected_before_write(self):
        d = json.loads(self.memory.read_text()); d['no'] = 414
        self.run_import(d, False)

    def test_wrong_book_title_rejected_before_write(self):
        d = json.loads(self.memory.read_text()); d['title'] = 'SDE智能体到底能做什么？'
        self.run_import(d, False)

    def test_missing_items_rejected_before_write(self):
        d = json.loads(self.memory.read_text()); d['items'] = []
        self.run_import(d, False)

    def test_matching_memory_accepted(self):
        self.run_import(json.loads(self.memory.read_text()), True)

    def test_published_memory_matches_both_units(self):
        for n in [414, 459]:
            p = ROOT / f'public/books/m/{n}'
            k = json.loads((p / 'keypoints.json').read_text())
            u = json.loads((p / 'publication-unit.json').read_text())
            self.assertEqual(k['no'], u['number'])
            self.assertEqual(k['title'], u['title'])


if __name__ == '__main__':
    unittest.main()
