# 12 recent monographs: reading, learning and source-grounded dialogue

2026-10-11. This update adds 525 chapter-linked learning tasks, twelve PDF workbooks (585 pages), twelve individually named agents, and explicit cross-book excerpt selection. All original reading text and publication metadata are retained.

The reader can seal an initial answer, store versions, retain disagreement, preview model inputs, confirm their own revisions, and record planned versus observed practice. Personal text and prior turns are opt-in, with append-only local IndexedDB records and import/export.

Validation: source hashes and anchors, exact preservation of original HTML after removal of injected navigation, all task coverage, PDF embedded fonts and all-page visual review, Node simulated DOM/IndexedDB/SSE interaction and failure paths. No real browser or paid upstream-model test was performed. The existing BYOK API is used only after explicit reader submission. Learning effects are not certified.

Only the twelve source-scoped books use the new backend prompt branch and declared comparison excerpts. Unselected book retrieval is disabled for source-scoped requests to keep the preview accurate. Other books keep their existing interface.

Rollback: revert this publication commit; browser learning data is kept under a distinct per-book database name and is never migrated or erased by deployment.
