# Configuration-driven publication units

This isolated runtime adds reading, chapter-specific learning and model dialogue without changing legacy book-agent JavaScript. It uses `/api/wds/read` and sends `bookagent:1`, the exact `bookNo`, and `sourceMode:'selected-original'`. The worker must recognize those book numbers in its scoped-original branch. No model request occurs on page load, navigation, or opening a starter question.

## Page shell

```html
<link rel="stylesheet" href="/books/unit-runtime/unit.css?v=20261011">
<main id="publication-unit"></main>
<script>window.PUBLICATION_UNIT={manifest:'/books/m/123/unit/learning.json',view:'learning'};</script>
<script src="/books/unit-runtime/core.js?v=20261011" defer></script>
<script src="/books/unit-runtime/app.js?v=20261011" defer></script>
```

`view` accepts `learning`, `dialogue`, or `agent`. Agent defaults to the free-reading mode; others default to a hint. Query parameters `lesson` and `chapter` select a task. Page title, canonical URL, description, and a useful `noscript` link should be included in each static shell.

## Manifest

`unit/learning.json` uses `schemaVersion:'1.0'`, `unitId:'m-123'`, integer `number`, `title`, `authors`, `isbn`, `sourceEdition`, `revision`, `readingUrl`, `agentUrl`, and `agent:{name,epithet,intro,principles,starts}`. Keep principles under 7,000 characters. `starts` maps `read`, `apply`, `cut`, `clash`, and `write` to arrays of starter questions. A starter prefills a question and never sends it.

Optional presentation fields: `overview`, `downloads:[{label,url}]`, `readingRoutes:[{title,aim,lessons:[1,2]}]`, `capstone:{title,steps:[],rubric:[]}`, `parts:[{id:1,title:'…'}]`.

Each `tasks` entry has sequential integer `lesson` starting at 1, `problemId`, `part`, `title`, `chapterTitle`, `question`, `checkpoint`, `sourceUrl`, `sourceData`, and `sourceSha256`. Optional fields are `objectives:[]`, `practice`, `pitfall`, and `answerGuide` (string or array). There is no fixed chapter or part count.

Each source JSON has `{title,url,text,sha256}`. SHA256 is computed on exact UTF-8 `text`. Both the manifest identity hash and the loaded text hash must match before model submission is enabled. Source URLs must belong to the current book.

Tasks may include `collisions:[{title,bookNo,url,text,sha256}]`, with exact excerpt hashes. These are explicitly labeled as editorial comparison selections, not independent proof. The reader must opt in; a mismatch disables inclusion; more than 12,000 serialized characters is rejected rather than truncated.

## Reader records and submission

IndexedDB is isolated per book at `sde-publication-m-123-unit-v1`. Events append without overwriting; only drafts update. Initial answers are sealed, revisions require explicit reader confirmation, and observations are marked as reader self-reports. Conflicting imports fail atomically; other drafts and rescue records are preserved. Exports do not contain API keys. Import size above 25 MB is explicitly rejected, never cropped.

Before every model submission, the reader previews the exact request, provides a Key for that request, and confirms. The Key is forwarded through the existing site API to the selected provider (`ds` or `glm`); it is cleared from the input and never saved in a request event or learning archive. A consumed preview cannot be sent twice.

Current-task personal drafts, same-task dialogue history, and cross-book excerpts are three separate opt-ins. History requires identical source hashes. Requests are rejected above 4,000 question characters, 110,000 source/personal characters, 100 dialogue turns, 12,000 characters per history entry, or 55,000 history characters. Nothing is silently trimmed by this client. Model suggestions never automatically confirm reader revisions.

SSE parsing preserves interrupted/error/cancelled output. A complete site transport is recorded as `received-unverified` because the API does not expose independently verifiable upstream completion. This runtime does not certify model correctness or learning outcomes.

## Validation boundary

JavaScript syntax checks and Node VM + linkedom + fake-indexeddb contract tests were performed. Tests cover source hashes, dynamic task navigation, five agent modes, sealed initial answers, confirmed revisions, preview/opt-ins, request shape and mocked SSE, credential exclusion, book isolation, import conflicts, interrupted output and draft recovery. No real paid model request or real browser rendering test is claimed.
