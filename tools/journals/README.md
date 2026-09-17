# Journal reading content

The live `/journals/data/manifest.json` is served from R2 and is newer than the
manifest checked into this repository. Do not replace it with the repository
copy. The independent `/journals/reading/catalog.json` adds curated journal
records and locally hosted reading pages without touching the R2 archive.

## Coverage (2026-09-17)

All 17 planned Chinese education journals now have real bibliographic records
(269 records in total). This is an initial curated import, **not five complete
years**. Coverage is stated individually in the catalog. Most sources are 2026
current issues. Curriculum, Teaching Material and Method contains the official
2023 issue 6 contents and one selected issue 5 article. E-Education Research,
China Higher Education Research and Fudan Education Forum each have three
selected records, because their complete publisher archives were unavailable.
Do not describe those journals as completely backfilled.

The 21 reading pages contain 18 independently written Chinese abstract guides
and 3 PLOS papers with the complete English abstract, complete Chinese abstract
translation and an English prose edition of the article body. Chinese guides
are not copies of publisher abstracts. Prose editions omit figures, tables,
reference lists and supplementary materials and are labeled accordingly.
PLOS attribution and CC BY 4.0 license links are present on each page.

Every catalog row keeps a source URL. Specific publisher article links are used
where available; some selected bibliographic records cite a publisher contents
page or the author's institution. Do not infer abstracts from titles.

## Editing

1. Verify the article against its publisher or author institution. Confirm the
   actual publication period, author names and DOI. An issue number is not
   automatically a calendar month; online publication and issue dates differ.
2. Edit `reading-content.json` for reviewed content. Do not add unlicensed full
   abstracts/translations or full papers. Record content type and attribution.
3. Update `public/journals/reading/catalog.json` records, article cards, counts
   and coverage together. `n` equals rows and the sum of `years` counts;
   `readingCount` counts rows having a local `read` link.
4. Run `python tools/journals/build_reading.py` to regenerate static pages.
5. Validate loading behavior using `test_loading.cjs` with jsdom on NODE_PATH.
   The tests cover unavailable/invalid manifests, independent readable content,
   retry, all 17 journal tiles, stale success/failure responses, and navigation.

Readers and the reading index are static HTML and work without JavaScript.
The large archive and small reading catalog load independently. This keeps
available reading content usable when the archive is unavailable.
