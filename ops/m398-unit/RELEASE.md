# Book398 publication unit — 20261008-m398-unit-v1

Authorized by the book owner: update book398 on the production site, adopting the Happiness book's reading/learning/dialogue pattern. Authors 王德生、张琼; ISBN 979-8-90690-868-1; US$20. Existing agent 判生 remains; 回甘 belongs to Happiness and is not reused.

## Scope

Only book398 public assets, book398's catalog record and book398's card on the three existing shelves are changed. Old downloads and original agent remain. Main text is preserved; companion tasks are explicitly separate. Forty chapter-bound tasks, a 41-page workbook and same-node dialogue with append-only local learning records are added. A minimally lettered knife/winter-melon cover replaces the earlier mockup. No reindex, daily schedule modification, shared agent or service rewrite, cross-book migration or public learner records.

## Evidence levels

`acceptance/engineering-report.json` describes browser and synthetic protocol tests. Six task routes and failure scenarios use clearly synthetic responses, not a real paid model. `acceptance/rollback-rehearsal.json` is isolated reconstruction, not production rollback. The separate live workflow verifies deployed asset fingerprints, author text, entry links and real browser storage/navigation/preview behavior. It intentionally prevents model calls. Provider performance, upstream finish_reason and human learning effects have NOT been validated. The current site's streaming interface exposes no upstream finish_reason; an apparently ended stream is labeled received-unverified, not certified complete.

Reader-supplied keys travel through the site's existing API to the chosen provider only after explicit per-request confirmation. Keys are never written to the learning archive. Personal material is unchecked by default. No real user archives or credentials are used in tests.

## Targeted rollback

Preserve the merge commit, the manifest's before/after fingerprints and the baseline revision recorded by the rollback rehearsal. Work on a rollback branch; never reset or force-push main. For each file in `acceptance/m398-build-report.json`, first compare the current SHA256 with its published `after` hash. A mismatch is a later edit: stop and reconcile, do not overwrite it. Restore a preexisting file only from a git version whose hash equals `before`; delete a newly introduced file only while its current hash still equals `after`.

For the shared catalog and three shelf pages, prefer removing only book398's added fields/card block. If the full-file hash has changed, merge the book398 reversal into the current file; never restore an entire old shelf over somebody else's changes. Restore the old reader link/cover, remove scoped unit navigation, and verify old read/learning/agent entries. Keep private IndexedDB records in the reader's browser and retain export availability; a website rollback does not authorize erasing learning history. A later complete unit decommission needs an explicit export/migration plan.

Build scripts and branch-only staging assets are not public learner data. They may be retained for reproducibility. Production status is not inferred from a Git commit or HTTP200 alone; consult the live workflow evidence. No automatic public manuscript writeback is provided.
