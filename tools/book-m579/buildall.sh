#!/bin/bash
cd /home/claude/books/jie
(python3 book.py pdf > out/log_pdf.txt 2>&1) &
(python3 book.py reader > out/log_reader.txt 2>&1) &
(python3 book.py word > out/log_word.txt 2>&1) &
wait
tail -1 out/log_pdf.txt out/log_reader.txt out/log_word.txt
python3 finalize.py
ls -la dist | cut -c20-
