# Agent principles repair: 12 real manifests

The generator added an editorial string to a Python rule list, expanding it into individual characters. All twelve learning manifests, agent specs and instructions now contain the original full rule paragraphs followed by the unchanged editorial summary. The generator normalizes the original rule list before appending; runtime validation rejects malformed non-string principles. Publication-unit metadata contains no principles field and required no edit.

Validation used the actual repository manifests and runtime in Node VM + linkedom + fake-indexeddb. For every book, the first and last task opened the real UI preview. Its actual `bookPoints` matched every rule and editorial paragraph exactly; `bookNo`, `sourceMode: selected-original`, and selected-source text/hash matched. No live API call was made. This is simulated DOM QA, not browser or paid model QA.

| Volume | Full rules | Editorial paragraphs | Actual bookPoints characters |
| --- | ---: | ---: | ---: |
| 266 | 5 | 10 | 2456 |
| 330 | 6 | 10 | 2562 |
| 347 | 4 | 9 | 2206 |
| 401 | 4 | 9 | 2222 |
| 272 | 4 | 9 | 2255 |
| 276 | 5 | 10 | 2445 |
| 278 | 5 | 10 | 2393 |
| 281 | 6 | 10 | 2545 |
| 282 | 6 | 10 | 2549 |
| 386 | 4 | 10 | 2322 |
| 399 | 5 | 8 | 2001 |
| 400 | 5 | 10 | 2355 |

All 24 previews passed; every prompt remains below the 7,500-character bound. The existing 25 runtime mock checks also passed. Source content and authored rule/summary text were preserved verbatim; only representation was repaired.

Reproduce from this directory (dependencies listed in `package.json`):

```sh
npm install --ignore-scripts
node manifest_smoke.cjs
node runtime_mock_qa.cjs
```

Detailed results: `manifest-smoke-result.json`, `principles-repair.json`, `runtime-qa-result.json`. The local generator passed Python AST compilation and a normalization check confirming its input rule list is not mutated.
