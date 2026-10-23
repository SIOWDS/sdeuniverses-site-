"""Generate this unit from the shared runtime, preserving its hand-built reading pages."""
from pathlib import Path
base=Path('tools/book_unit/build_unit.py')
code=base.read_text().split('    # ---- wire into existing pages')[0]
exec(compile(code+'\nif __name__ == "__main__": main()\n',str(base),'exec'),{'__name__':'__main__','__file__':str(base)})
