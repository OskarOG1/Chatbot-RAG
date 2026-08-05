# RAG Chatbot: answers drawn exclusively from a document base

[![CI](https://github.com/OskarOG1/Chatbot-RAG/actions/workflows/ci.yml/badge.svg)](https://github.com/OskarOG1/Chatbot-RAG/actions/workflows/ci.yml)

A chatbot that answers questions **only on the basis of the supplied articles**, never from the model's general knowledge. Every answer links to its sources. When the answer isn't in the base, the system refuses instead of making things up.

**Demo: [ogflow.pl](https://ogflow.pl)**

Test corpus: over 350 Allegro Help articles (buyer and seller sections), over 2,100 chunks. An educational project, not affiliated with Allegro.

---

## Results

| Metric | Result |
|---|---|
| Correct article in top 5 results | **0.918** (61 questions) |
| Correct article in top 5, typo set | 0.840 (50 questions) |
| False refusals (rejected questions the system could actually answer) | **0/61** |
| Off-topic questions correctly rejected | **7/8** |
| Median response time (production, Docker) | 6.31 s |

Cross-section over 100 questions in 6 categories: 76 answers, 24 refusals.

| Question category | Answered |
|---|---|
| plain | 25/26 |
| with typos | 19/21 |
| complex, three-part | 12/13 |
| complex, two-part | 12/16 |
| vague ("how do I change that") | 7/16 |
| off-topic | 1/8 *(rejection works)* |

---

## What this means in practice

**The problem it solves.** A chatbot wired straight to a language model isn't grounded in the client's knowledge and has no defined way of answering.

**How it's solved.** Before the model writes anything, the system retrieves the relevant document chunks and hands them over as the only admissible source. After the answer is generated, it checks whether the answer actually rests on them. If not, it refuses.

**Three independent refusal gates:**

1. **Before retrieval.** Filters reject empty, too short, and too long queries, plus basic prompt-injection attempts.

2. **Before generation.** If no chunk matches well enough, the model is never called at all (saving the most expensive step). Borderline questions are judged by a separate model call: "can this be answered from this context, YES/NO?"

3. **After generation.** A check of how many meaningful words of the answer actually occur in the sources. An answer detached from the context is rejected.

**Data need never leave the server.** Retrieval, embeddings and reranking all run locally. The generating model can be local too, though in my setup it isn't, due to hardware constraints.

---

## How it works

```
User question
      │
      ▼  input filters: empty / too short / too long / foreign alphabet / injection patterns
      ▼  typo corrector (Damerau-Levenshtein + word-frequency threshold)
      ▼  embedding (mmlw, prefix "zapytanie: ")
      │
      ▼
HYBRID RETRIEVAL, whole corpus
  lexical (BM25 with lemmatisation and trigrams) + semantic (FAISS)
  rankings fused by position (RRF), duplicates cut by URL → 20 candidates
      │
      ▼
RERANKER (cross-encoder scores the question–chunk pair, window of 20) → 5 links
      │
      ▼  GATE 1: reranker score < −4.3 → refusal without calling the model
      ▼  GATE 2: LLM judge (YES/NO) on borderline questions
      │
      ▼
GENERATION (system prompt + conversation history + context → apertus-v1.5-8b via API / Ollama locally)
      │
      ▼  URLs stripped from the text, citations [n] mapped to sources
      ▼  GATE 3: answer coverage by context < 0.20 → refusal
      │
      ▼
Answer + Sources
```

### Technology choices

| Component | Choice | Why |
|---|---|---|
| Embeddings | mmlw | Trained for Polish, captures meaning better than a multilingual model |
| Vector store | FAISS | Local, fast, sufficient at this scale |
| Lexical retrieval | BM25 + lemmatisation + trigrams | Embeddings alone missed questions built around specific words |
| Reranker | mmarco-mMiniLMv2 (118M) | 26× faster than bge-v2-m3 at the cost of one hit |
| Answering model | apertus-v1.5-8b | In a 25 PL + 25 EN question measurement it matches or beats Bielik-11B/Olmo-3-7B on quality (context coverage, no contradictions), with zero API errors and about 3.4x faster (see `Pomiary/jakosc_modeli.md`, `Pomiary/latencja.md`). Decision reconfirmed with a fresh measurement after hardening the prompt against duplicate sources: PL is a tie within noise, EN and latency still clearly favor apertus (3.5x fewer contradictions with the context, about 3x faster), see `Pomiary/POMIAR_APERTUS_VS_BIELIK.md` |

---

## Key decisions: problem → solution → result

### 1. Semantic retrieval alone isn't enough

**Problem.** "How do I change my password" landed on an article about changing currency. The embedding caught "change" and lost "password".

**Solution.** Added lexical retrieval (BM25), with both rankings fused via RRF. Then lemmatisation, so BM25 recognises inflected forms instead of demanding an exact match.

**Result.** On the first 20 questions: 10/20 → 12/20 after adding BM25, 16/20 after fixing blocking bugs. After lemmatisation, on 30 questions: 28/30.

### 2. Headings inside chunks

**Problem.** The first version cut articles into equal 500-token pieces. I assumed keeping headings would make a marginal difference at best.

**Solution.** Section-based chunking, with the heading appended to the chunk body (so it enters the embedding, BM25 and the reranker). Detected tables of contents are stripped. 641 chunks instead of 576, of which 236 carry a heading.

**Result.** I was wrong: the difference was clear.

| Set | top 3 before | top 3 after | top 5 before | top 5 after |
|---|---|---|---|---|
| clean questions | 0.867 | **0.933** | 0.900 | **0.967** |
| questions with typos | 0.800 | **0.867** | 0.867 | 0.867 |

### 3. Typos wrecked retrieval

**Problem.** The test set was written in correct Polish; real questions aren't. On misspelled questions accuracy dropped to 0.700, the system's weakest point.

**Solution.** Character trigrams in BM25 (matching on letter triples, tolerant of errors) + a Damerau-Levenshtein corrector over a dictionary built from the article text. Above the corrector sits a word-frequency threshold: a correct Polish word is left untouched.

**Result.** 0.700 → 0.800 (trigrams) → 0.867 (corrector). Trigrams also lifted clean questions from 0.967 to 1.000.

Current robustness measurement of the retrieval layer alone:

| Set | top 3 | top 5 | time/query |
|---|---|---|---|
| clean | **0.860** | **0.940** | 3.24 s |
| one typo per question | 0.720 | 0.840 | 4.44 s |

### 5. Splitting the base into sections hurt

**Problem.** Originally the base was split into three topical sections, with a separate router guessing which one to search. On 20–30 questions it looked fine. The split was originally built as practice for future, larger projects. I was aware it was unnecessary at this corpus size.

**Solution.** Expanded the test set to 61 questions and compared against searching the whole base.

**Result.** The router lost on every axis. Removed.

| Mode | top 5 (61 questions) | time/query | off-topic questions cut for free |
|---|---|---|---|
| router (two sections) | 0.852 | 4.41 s | 5/29 |
| **whole base** | **0.918** | **3.33 s** | **7/29** |

The router reranked 40 pairs (2×20 from the guessed sections). Searching everything yields 20 candidates, but better targeted ones.

### 6. No single threshold separates borderline questions

**Problem.** "What commission does Allegro take", "who owns Allegro", "how do I open a shop": questions close to the topic but outside the base. The score distributions for in-domain and out-of-domain questions overlap: 23 of 29 out-of-base questions score higher than the weakest in-domain question.

**Solution.** The reranker threshold stops pretending to be a classifier. Its only role is a cheap cut-off of extremes before the model is called. Distinguishing borderline questions is taken over by a separate LLM call ("YES/NO, can this be answered from this context?").

**Result.** Threshold loosened from −3.2 to −4.3:

| Threshold | False refusals | Cut for free | Judge calls |
|---|---|---|---|
| −3.2 | 2/61 | 11/29 | 77 |
| **−4.3** | **0/61** | 5/29 | 85 |

Zero false refusals at the cost of 8 extra calls. Cheap, since the judge caught those questions anyway.

Judge selection:

| Model | False refusals | Off-topic caught |
|---|---|---|
| **Bielik-11B** | **2/30** | **17/18** |
| EuroLLM-22B | 5/30 | 18/18 |

Bielik as the compromise. EuroLLM held in reserve for a client where "never answer off-topic" outweighs the occasional false refusal. The judge model is decoupled from the answering model; a YES/NO decision is lighter than generation, so a cheaper model can sit on it.

When the answering model was switched to apertus-v1.5-8b (see the technology choices table above), apertus was also tested in the judge role: false refusals were comparable (PL 1/50 vs 1/50, EN 0/50 vs 3/50 in apertus's favor), but caught OOD questions were clearly worse (22/29 vs 28/29 PL, 22/29 vs 27/29 EN), a real regression of the anti-hallucination gate. The judge stays on Bielik-11B (PL) and Olmo-3-7B (EN), independent of the answering model (see `Pomiary/sedzia_modele.md`).

### 7. The anti-hallucination gate threw out good answers

**Problem.** Of the 24 refusals in the 100-question simulation, 7 fired **after** generation (877 wasted tokens), two of them on fully valid questions. Retrieval put the right article first, the model answered correctly, and the answer was rejected. The cause: the model paraphrases with words outside the context ("verification", "identity" for a question about account recovery), so lexical coverage falls despite the answer being correct.

**Solution.** Recalibrated the coverage threshold from 0.40 to 0.20, on the distribution of 29 multi-part in-domain questions vs 29 out-of-domain.

|  | min | median | max |
|---|---|---|---|
| in-domain questions | 0.253 | 0.690 | 0.885 |
| out-of-domain questions | 0.042 | 0.228 | 0.651 |

**Result.**

| Threshold | False refusals |
|---|---|
| 0.40 | 4/29 |
| **0.20** | **0/29** |

0.20 chosen over 0.25: the lowest valid question sits at 0.253, and generation is slightly stochastic (spread 0.01–0.03). 0.25 would leave a margin of 0.003. 0.20 gives 0.05 and still reacts to text with no grounding in the sources.

### 8. A data bug diagnosed from the refusal latency

**Problem.** The question "The seller wants me to pay outside Allegro, is that safe?" was consistently rejected, despite being in-domain.

**Solution.** Refusal latency identifies the gate without reading any code: <1 s is the input filter, ~2.9 s is the reranker threshold, ~6.3 s is the judge. This question failed at ~6.3 s, so the judge was getting the wrong context.

**Result.** The right article was labelled `konto` (account) instead of `zakupy` (purchases), so it never entered the candidate pool. Fix: one line of mapping plus moving 3 articles. Regression check: accuracy unchanged (0.900/0.933).

### 9. Multi-turn rewriting via LLM, new complaint-email assistant

**Problem.** Follow-up turns were joined to the previous question by plain concatenation, which sometimes produced a worse search query than a standalone rephrasing would. The bot also always stopped at an answer, never proposing a concrete action, even though some situations (a complaint, an unresponsive seller) call for a ready-to-send draft.

**Solution.** Follow-ups detected by a cheap detector (`followup`) are now rewritten into a standalone question by an LLM (`przepisz_zapytanie`) instead of concatenated. Separately, a new mode drafts a complaint email to the seller, grounded in the Help Center article on opening a Discussion, with placeholders instead of invented order numbers and dates. Triggered by a hybrid: a cheap keyword regex gates a single LLM-judge call (`czy_oferowac_mail`) that decides whether to offer help, plus a cheap fallback for an explicit request.

**Result.** Multi-turn pairs: hit rate on the originating source went from 40% to 60% (n=10). The offer gate and judge: 6/6 correct decisions on a labelled set, 0/100 false positives for the explicit-request path on golden. Draft email quality (LLM judge, 1-5 rubric): average 4.5/5. End-to-end regression on 50 golden questions per language: unchanged beyond the known generation/judge noise floor (section 13 of the measurement log). Along the way, a pre-existing retrieval bug was found and fixed (the query "complaint" did not match the article, which uses the term "Discussion" instead), plus a Streamlit UI bug where the offer button never registered its click because it lived inside a conditionally executed block. Full log: `src/POMIAR_ROUTING.md`, section 19.

### 10. Testability: a unit test suite and cleaning up duplicate model loading

**Problem.** The input filter and typo corrector logic was covered only by end to end measurements on the golden set, with no tests for the underlying functions. Separately, running measurements in the same process as the pipeline loaded the mmlw embedding model twice, once in the measurement file and once again inside the pipeline.

**Solution.** Twenty two unit tests (pytest) for the input filters (too short, too long, foreign alphabet, prompt injection detection including leet variants) and for the typo corrector (language detection, matching against the corpus dictionary, edit distance). The measurement file no longer creates its own model instance and now reuses the one already loaded by the pipeline.

**Result.** 22/22 tests passing. Regression check: retrieval accuracy on the golden set unchanged (0.820, the same misses as before the change), and the model in the measurement file and in the pipeline are now a single object in memory instead of two.

### 11. Response cache, production observability, and judge prompt tightening

**Problem.** Frequent questions were regenerated from scratch every time (several to over ten seconds, plus API cost), even though the answer is deterministic for the same question and the same corpus state. Separately, there was no visibility into production traffic: refusal rate, latency distribution, which sections get asked. The end to end measurement (`measure_e2e`) also showed that some golden questions ended in a refusal despite the retriever finding good context, because the LLM judge was scoring context too strictly.

**Solution.** A response cache in `api.py`, keyed by the normalized question, language, and the corpus file's mtime stamp (rebuilding the knowledge base invalidates the cache automatically), only for successful answers and only for standalone questions with no conversation history. A structured JSONL log on every request (language, section, outcome, latency, cache hit), with PII redaction using the same mechanism as the existing `skazone_tokeny` filter. A Streamlit analytics page showing refusal rate, median latency, and top questions. The PL judge prompt was tightened with an explicit "you are not checking completeness" and "one matching source out of several is enough"; the same change was tried on EN too but measured worse across three runs, so it was reverted there.

**Result.** Cache: first request 10.4s, second request (cached) 0.28s, identical content. Judge: PL golden pass rate went from 46/50 to 50/50 end to end (zero refusals), that change stays. The same change measured on EN three times did not help (43 to 42 to 41 out of 50), so it was reverted, the remaining gap is a real problem in the corpus content or the EN embedder, not the prompt. OOD control (6 out of domain questions) showed no regression.

### 12. CI on GitHub Actions

**Problem.** Unit tests only existed locally, nothing enforced that they stayed green on every change. Three of the typo-corrector tests (`correct()`) read a dictionary from `RAG/`, a directory that doesn't exist in the repo, so those same tests would fail in CI despite passing locally.

**Solution.** An autouse fixture in `tests/conftest.py` injects a small dictionary instead of reading `RAG/`, making the `correct()` tests hermetic. The unit tests stopped being private (a deliberate convention change: they used to be gitignored, now they're committed, because GitHub Actions needs them in the checkout to run anything). The `.github/workflows/ci.yml` workflow runs `ruff check` and `pytest` on every push and pull request, without the heavy dependencies (`torch`/`faiss`/`sentence-transformers`).

**Result.** 22/22 tests green with the fixture, hermetically. `ruff check src tests` clean after fixing three ambiguous variable names (`l`, `I`) in `chunking.py`/`rankings.py`; regression check: retrieval accuracy on the golden set unchanged (0.820).

### 13. Four mail categories instead of one, a single router judge instead of YES/NO

**Problem.** The action assistant could only draft one kind of message: a complaint email to the seller, gated by a binary LLM judge (YES/NO, whether to offer help). Real buyer needs are broader: wanting a return with no defect involved, requesting an invoice, or reporting that the seller isn't responding at all.

**Solution.** The binary judge was replaced with a single router judge that picks one of five labels: `REKLAMACJA`/`ZWROT`/`FAKTURA`/`ESKALACJA`/`NONE`. Each category's data (grounding article, retrieval query, canonical offer text, cheap-gate words/phrases) lives centrally in the language config. A separate draft prompt per category, with the same rules as before (placeholders instead of invented data, process taken only from the source context).

**Result.** First measurement pass: 5/12 correct categories, because the cheap gate was too lenient on procedural questions, and the router's context retrieval in the free-text path sometimes pulled an unrelated article. After tightening the router prompt (an explicit boundary example for procedural-question-vs-own-situation) and widening the retrieval context (last conversation message instead of the instruction alone, `k` from 3 to 5): **12/12 correct categories, 12/12 correct gates**, draft quality across four categories (PL/EN) 8/8 correct category, average score 4.0-4.4/5 depending on the run (variance on the EN generation side, a known pre-existing weakness, not in the routing). Zero new false positives on the golden set (0/100), the same critical gate as with the single category.

### 14. Next.js frontend alongside Streamlit, streaming through a proxy Route Handler

**Problem.** Streamlit works well as a quick demo, but a portfolio piece and real deployment need a frontend with full UX control, without changing the backend, which stays the single source of truth.

**Solution.** A new `frontend-next/` directory (App Router, TypeScript, Tailwind, custom components, no shadcn), running alongside `frontend/app.py` until full parity is reached. The browser never talks to FastAPI directly: `app/api/chat/route.ts` does a server-side fetch to `FASTAPI_URL/chat/stream` and forwards the stream, so it's same-origin, zero CORS, and the backend address never reaches the browser. The SSE contract (`krok`/`token`/`wynik`/`blad`), the history rule (appended only on a successful reply), the retry-after-negation flow, and the categorized mail offer are mirrored 1:1 from `frontend/app.py`.

**Result.** End-to-end verification in the browser: a PL and EN RAG question streams tokens and finishes rendering from `wynik.dane.answer`, the offer button generates a correct draft with the category-specific header (e.g. "Draft complaint email"), a typo triggers the confirmation banner, and a correct "no" reverts to the original question without re-looping the correction. Parity measurement (`src/measure_frontend.py`, 8 PL/EN queries: RAG, offer, explicit mail request, typo, refusal) between the proxy and calling `/chat/stream` directly: **8/8 matching** on `agent`/`tryb`/`oferta`. Proxy-only overhead measured separately on a warmed cache (to isolate it from generation-time variance): median **21.7ms**, negligible.

### 15. Backend hardening: tests on critical paths, a bigger multi-turn sample, embedding cache, faithfulness measurement

**Problem.** The RAG core had a green measurement suite, but a review focused on hardening (not new features) found five weak spots: lexical coverage mistaken for answer faithfulness, multi-turn accuracy measured on too small a sample (10 pairs), no deliberate latency optimization loop, no unit tests on critical functions (citation mapping, the coverage gate, the mail router), and a single 507 line `agents.py` mixing generation, judges, and mail drafting.

**Solution.** Five independent points, each closed with a test or a measurement, tracked in `pomiary/PLAN_TWARDOSC_BACKEND.md`. Three new unit test files (`test_verify_answer.py`, `test_pokrycie.py`, `test_router_mail.py`), zero LLM calls. The multi-turn set grew from 10 to 30 pairs (proportional PL/EN, seven distinct intents). A query embedding cache (`functools.lru_cache`) for repeated queries, confirmation by measurement that the reranker warmup at server startup was already in place, and an honest test of the hypothesis that a smaller judge model would lower latency (rejected with numbers, not taken on faith). A new faithfulness measurement: an LLM judge checks each golden answer for claims that contradict the retrieved context, kept separate from the cheap lexical coverage gate. `agents.py` split into four modules (`agents_core`, `agents_generacja`, `agents_sedzia`, `agents_mail`) plus a thin facade, so no existing import had to change.

**Result.** 42/42 tests green (20 new). Multi-turn: 22/30 to 24/30 after fixing a real gap in the English follow-up detector ("what if" was not recognized), with no regression. Embedding cache: median 67.7ms to 0.0ms on a hit. The smaller judge model measured almost four times slower on the available endpoint, so it was rejected and never shipped. Faithfulness: 30/30 golden answers with no contradictions detected against context in this run, a diagnostic measurement worth repeating after larger prompt or model changes. The `agents.py` refactor: the sanity import and the full test suite unchanged, zero change to prompt content or logic. Full logs: `pomiary/POMIAR_MULTITURA.md`, `pomiary/POMIAR_LATENCJA.md`, `pomiary/POMIAR_FAITHFULNESS.md`, `pomiary/POMIAR_REFAKTOR_AGENTS.md`.

### 16. Fixes from demo reports: prompts, model fallback, chat and mail panel frontend

**Problem.** Real demo usage surfaced 17 issues across three layers: dead markdown links in answers (`[here]()` after the URL was stripped), mail drafts defaulting to masculine phrasing and reading as a wall of text, general questions narrowed to a single special case (e.g. Allegro Smart), a pointless SSE step flashing even when no mail offer would follow, no fallback when the main model errored out, no live token streaming on the frontend (the answer only appeared at the very end), `[n]` markers not clickable, the source list showing every retrieved chunk instead of only the cited ones, raw URLs instead of readable titles, a closed mail panel with no way to reopen it, "Regenerate" expensively re-querying the model instead of simply undoing an edit, a dead "Save template" button, and no flag on the language switch.

**Solution.** Backend (`agents_core.py`, `agents_generacja.py`, `pipeline.py`): a new `zwin_linki_markdown` function cleans up dead markdown links before URL stripping, the `email_system_*` prompts (PL/EN, all four categories) now require gender-neutral phrasing and paragraph structure, `grounding` now states the general-before-special ordering, the pointless SSE step was removed, and `MODEL_FALLBACK` retries on a backup model in `answer`/`answer_stream` when the main model raises. Frontend (`frontend-next/`): the SSE `token` event is now handled, with the streamed buffer swapped for the final `dane.answer` on completion; `[n]` becomes a clickable markdown link to its source; `lib/zrodla.ts` derives a readable title from the URL slug; the source list is built from `citations` instead of `sources`; the mail panel keeps the last draft after closing (an "Open draft" button reopens it); "Undo edits" restores the remembered original draft with no API call; "Save template" was removed; a PL/UK flag was added next to the language switch.

**Result.** 42/42 backend tests green, `ruff` clean, `ocena_stylu` with no regression (4.33 → 4.67 on a small sample). The model fallback was confirmed with a live test that forced a 403 error on the main model: the answer still came through. Along the way, browser testing caught and fixed a real bug: reopening the panel showed an empty editor, because the `contentEditable` node was conditionally unmounted and lost sync with the restored state even though the React state itself was preserved. `tsc`/`eslint` clean. Full logs: `pomiary/POMIAR_PROMPTY_MAIL.md`, `pomiary/POMIAR_FALLBACK.md`, `pomiary/POMIAR_17_ZGLOSZEN_FRONT.md`.

### 18. Second round of demo reports: parallel conversations, escalation category, mail subject, privacy page, EN polish, unified format contract

**Problem.** A second round of testing surfaced eight reports. The frontend blocked sending in a second conversation thread until the first stream finished, because sending state was a single global boolean instead of per thread. The report "the package never arrived" did not generate a mail offer, because the escalation category only matched a seller not responding, not a missing delivery. The mail edit panel sometimes ended up with an empty subject line when the model skipped the "Subject:" line or formatted it differently. The `/prywatnosc` page was a one sentence placeholder. The English path had three separate issues: the streaming step showed the raw internal section name (`section: konto`), the model sometimes copied single Polish words straight from the translated corpus, and one of the starter suggestions ended in a refusal. The three answering personas had directly conflicting format instructions (steps vs paragraphs vs no preamble), so answers looked inconsistent across sections.

**Solution.** Frontend (`ChatApp.tsx`): sending state changed from a single boolean to a `Set<string>` of thread ids, each stream with its own `AbortController`. Backend (`lang_config.py`): the escalation category's phrase list extended with missing delivery variants in PL/EN. Mail subject: a tolerant regex in `rozdzielSzkic` (leading spaces, `#`, `**`), a fallback header from a new `ChatResponse.naglowek_ui` field, and an explicit `Temat:`/`Subject:` format instruction across all eight mail prompts. The `/prywatnosc` page was rewritten into full, bilingual content grounded in the actual code (what goes to the LLM provider, what the server log stores, what it doesn't store, the rate limits, how to delete your data), in first person singular. EN: a new section-name map in `lang_config.py`, a warning in the EN grounding prompt against copying Polish fragments from the context, and a new permanent measurement gate checking that no frontend suggestion ends in a refusal. The format contract (no meta preamble, one intro sentence, steps or paragraphs in one consistent convention, no markdown headings) was moved out of the conflicting personas into the shared `grounding`, leaving the personas with tone only.

**Result.** 47/47 tests green, `ruff` clean. On two parallel streams, the backend showed a 1.33x speedup over sequential execution (neither full serialization nor full parallelism, matching the hypothesis about the GIL and network bound work). The mail offer after "package never arrived"/"order never arrived": zero before the fix, correct after, with no regression on golden (0/100 false positives for the explicit request path). Format: across 93 golden PL+EN answers, zero markdown headings and a similar form distribution across sections, but the meta preamble did not drop to zero (17/93, 18%), the model partially ignores the explicit ban in the prompt, an honestly measured and documented open result, not misreported as a success. Frontend suggestions: 19/20 end in an answer, one EN case ("I suspect my account was hacked") still ends in a refusal because of a genuine retrieval quality gap in the EN corpus for that topic (a matching article exists and ranks well in PL, but its EN counterpart does not surface in the top results), left as a known limitation for a separate plan rather than patched with an ad hoc prompt change. Full log: `Pomiary/POMIAR_POPRAWKI_RUNDA3.md`.

### 19. Seller section: the other half of Allegro's Help Center

**Problem.** The knowledge base covered only the buyer Help Center. Every seller question (how to list an offer, how to add invoice and VAT details, how One Fulfillment works, when seller payouts arrive) ended in a refusal, even though the matching article exists on `help.allegro.com/{pl,en}/sell`, a completely separate site.

**Solution.** A new scraper (`links_scraping_sprzedaz.py`) discovers categories with a breadth first search over the site's department pages (135 categories, fully programmatic, no hand maintained list), and fetches content with plain `httpx`, the same method already used for the buyer corpus; browser automation turned out to be unnecessary despite the initial assumption. A new `scal_korpus.py` appends the seller chunks after the buyer chunks with an assertion that the existing positions and vectors stay untouched. `embedder.py` gained a `--dopisz` (append) mode that encodes only the new chunks instead of re-encoding the whole corpus. A new `sprzedaz` persona (factual, business tone) and a widened topic scope for the LLM judge.

**Result.** 169 PL articles (1,287 chunks) and 173 EN articles (801 chunks) added without disturbing the existing 822 (PL) and 641 (EN) buyer chunks. The new section is fully retrievable: hit@5 = 1.000 on the new golden set (20 PL questions, 19 EN). Regression on buyer questions: PL hit@5 unchanged (0.840), EN hit@5 dropped from 0.920 to 0.800. The cause was measured directly: the buyer and seller sections genuinely compete for top 5 slots (on average 30% of PL and 41% of EN top 5 slots on buyer questions are now seller chunks), because Allegro documents account, sign in, and GDPR topics almost in parallel for both audiences. This confirms the risk flagged going in: the most important next step is explicit routing between the buyer and seller sections, not relying solely on a shared index and reranker to sort it out. The gate thresholds (`prog_rerank`, `prog_pokrycia`) were checked after the merge and left unchanged, the IDF weights shifted but not enough to threaten legitimate questions. Full log with numbers: `Pomiary/POMIAR_SEKCJA_SPRZEDAJACY.md`.

### 20. Buyer versus seller routing: two rejected versions, one shipped

**Problem.** Continuation of the recommendation from section 19: the buyer and seller sections genuinely compete for top 5 slots, so buyer questions increasingly land on an article from the wrong section.

**First attempt, rejected by measurement.** Per the plan: when there was no signal about which side a question belonged to, the system still forced a side by comparing the raw reranker score between the buyer pool and the seller pool. Measured result: buyer PL hit@5 dropped to 0.540, EN to 0.600, worse than the state before this change. A second version summing the top three scores instead of one did not help (buyer EN even dropped further to 0.560). The cause: a lexical or conversation-continuity signal covers only 10 to 26% of questions, so for most traffic the system was still guessing the side purely from the reranker score, on the exact same near-duplicate account and sign-in articles that already confused ranking before.

**Shipped version.** Routing and homogenizing the context to one side kicks in only when there is a real signal: an explicit declaration in the UI, conversation continuity, or a matched lexical marker in the question. Without any of those signals, the system searches the whole corpus exactly as it did before this change, with no guessing.

**Result.** Buyer PL: hit@5 = 0.840, the plan's gate met. Seller PL: hit@5 = 1.000, the ceiling. Buyer EN: hit@5 = 0.800, parity with today's production, without returning to the pre-merge 0.920, because most EN questions carry no signal at all. Seller EN: hit@5 = 0.947, one question below the pre-change state. Zero clarifying questions across all four golden sets. The change's biggest real value is the explicit switch in the side panel (Auto, Buying, Selling): free, zero risk, and it closes the entire gap to the ceiling for a user who knows which side they're on. Full log with numbers, the two rejected versions, and the calibration grid: `Pomiary/POMIAR_ROUTING_STRONY.md`.

---

## Security and robustness

**Prompt-injection protection.** Input filters reject known patterns, but the real defence is grounding the answer in the context plus the coverage gate. The pattern filter is one layer, not the whole thing.

**Logs without personal data.** Only unrecognised single words are stored, never the question text. Emails, phone numbers, order numbers and URLs are filtered out by pattern-matching against the original. Verified on 7 cases: personal data disappears, typos (`kotno`, `smrtem`, `blikeim`) remain as material for extending the dictionary.

**Rate limiting.** A global limiter, 15/min and 200/day by default, configurable. Protects the API budget. The limit is global, not per-IP: with a project this size and an account topped up with $2, per-IP is unnecessary.

**Error handling.** An API failure returns "model temporarily unavailable" instead of a traceback, with a server-side log entry. Streamlit starts with error details disabled, so an unforeseen exception won't expose container paths in the browser.

**Handling unintelligible questions.** Two levels, driven by the corrector. When the corrector changed something, a confirmation prompt appears: "Searching for: … is that what you meant?"; "no" reverts to the original. "I didn't understand" only fires when every word of 4+ characters is unknown. Confirmation turns don't enter the history or the retrieval.

---

## Citations, sources and conversation memory

**Citations.** The prompt requires `[n]` markers and forbids bare URLs. A function strips links from the text and maps `[n]` to its source, and collapses dead markdown links (`[text](url)`, if the model inserts one despite the instructions) into plain text or a `[n]` citation before stripping. The reason is in the data: all 141 articles contain links in their own body, so the smaller model would copy them out as a list and duplicate the "Sources" section. Citations serve display only: refusal uses coverage, not the presence of `[n]`. On the frontend, `[n]` is a clickable link to its source, and the source list shows only what is actually cited, with a readable title instead of the raw URL.

**Conversation memory.** A 3-turn window. Follow-ups caught by a cheap detector are rewritten into a standalone question by an LLM before retrieval (`przepisz_zapytanie`), so e.g. "and what if the seller does not respond?" after a complaint question lands correctly. One extra model call, only when a follow-up is actually detected, not on every turn.

---

## API and frontend

Backend: **FastAPI**. `POST /chat` returns JSON (answer, sources, citations). `POST /chat/stream` is the same process over SSE, streaming each step and each answer token as it happens, with automatic fallback to a backup model if the main one fails.

Frontend: **Next.js** (`frontend-next/`). Chat with live answer streaming, clickable citations and sources, mail edit panel that can be reopened after closing.

---

## Sending the message to the seller (demo)

The email panel in `frontend-next` has a real send button, not just a preview. The customer enters their address, the message goes out in one call to a fixed demo seller inbox (`.env`, outside the repo) and a second call, with a confirmation and a ticket number, to the customer's address. `src/wysylka.py` generates the ticket (`secrets.token_hex`), calls the Resend REST API through `httpx`, no SMTP involved. The `POST /send-email` endpoint has its own, lower rate limit than `/chat` (a real external call, spam risk). Without a configured `RESEND_API_KEY`, sending returns a clear configuration error, never a fake success. The server log only stores the ticket, category, and outcome, never the address or the message body.

Measurement (`pomiary/measure_send_email.py`, mocked httpx, zero cost and zero spam risk): 4/4 cases pass, ticket generation, category carried into both messages, rejection without configuration, server log free of the email address and body.

---

## Bilingual version (PL/EN)

A second, parallel path for English-speaking clients. Everything is driven by the `lang` parameter (default `'pl'`): its own embedder, its own index, its own answering model, its own refusal thresholds. Full measurement log: `src/POMIAR_DWUJEZYCZNOSC.md`.

**Corpus.** 641 chunks translated into English (using `Bielik-11B`: despite being a Polish model, the translation came out cleaner and faster than with EN-specialised candidates). Spot-check of 10 chunks: meaning and terminology (`Allegro Pay`, `Allegro Smart!`, `BLIK`) preserved.

**Retrieval.** Embedder `multilingual-e5-base` (768-dim, same as the Polish one), its own FAISS/BM25 index. Hit@5 on the English golden set: 0.920, comparable to the Polish 0.940.

**Answering.** Model `Olmo-3-7B-Instruct`, the only one of four tested that didn't falsely refuse on questions with an unambiguous answer in the context (a problem with the Polish models and overloaded endpoints). Refusal thresholds calibrated separately for EN (different score distribution): `RERANK_THRESHOLD=-3.6`, `COVERAGE_THRESHOLD=0.35`. Reranker→judge test on 29 off-topic questions: 29/29 caught.

**Anti-hallucination gate (coverage), OOD side.** The first calibration measured the threshold on valid questions only: none of the 29 OOD questions reached the coverage gate at that point (the reranker and the judge caught them earlier), so there was no way to tell how the coverage gate alone would behave in isolation. Closing that gap: forced generation on all 79 questions (50 golden + 29 OOD), bypassing both earlier gates.

| | min | median | max |
|---|---|---|---|
| golden EN (n=50) | 0.000 | 0.744 | 1.000 |
| OOD EN (n=29) | 0.000 | 0.368 | 1.000 |

At `COVERAGE_THRESHOLD=0.35`: 1/50 false refusal ("Is Allegro Pay safe": a short answer with no lexical overlap with the context), 13/29 OOD caught by coverage alone. The remaining 16/29 OOD would have enough coverage to pass this gate on their own, the same pattern as in PL (section 7): coverage catches hallucination, it doesn't distinguish domain. Irrelevant in production, since the reranker plus judge catch 29/29 earlier, but if something ever leaked through, coverage would catch some of it, not all.

**Answer-language selection.** Detection (sum of PL vs EN word frequencies) overrides the UI toggle: a question in Polish always gets a Polish answer, regardless of the toggle. Measured: 0 incorrect PL→EN routings out of 100 cases (with and without Polish diacritics).

**Regression on the Polish path.** None.

**Demo readiness polish (`src/PLAN_EN.md`).** `MODEL_EN` and `SEDZIA_MODEL_EN` now set explicitly in `.env`, instead of relying on the hardcoded default in `lang_config.py`. Language detection hardened with measurement: 0 PL→EN errors on golden PL, with and without Polish diacritics, and 10/10 correct on short brand-heavy questions, the reverse risk the plan flagged never showed up. Along the way, a bigger problem than the plan anticipated turned up and got fixed: the EN judge was rejecting far too many valid questions, only 62% of golden EN got an answer through the full pipeline, and the dominant cause was an overly strict judge prompt, not the reranker threshold or the coverage gate. After strengthening the prompt: 90% (45/50), zero bad citations, zero Polish leakage. English follow-up questions added through `LANG[lang]['zaimki']` and `followup_prefiksy`, the Polish path untouched. Full Streamlit UI localization (labels, statuses, error messages, negation phrases) driven by the language toggle, verified by hand in the browser. Full measurement log: `src/POMIAR_ROUTING.md`, section 18.

---

**Response time in the container** (5 questions × 3 repetitions):

| median to first chunk | 5.61 s |
|---|---|
| median total | 6.31 s |
| maximum (first run) | 16.57 s |

## What I tried and rejected

**A single main link instead of three.** Picking one source with a dash of title words mixed in (weight λ). Best result 47/60 at λ=1.0; higher λ pulled in lexically similar but wrong articles. Three links gave 56/60 with no parameter to tune at all.

**A confidence threshold on retrieval alone.** Four different signals. None separated hits from misses.

**Refusing when the `[n]` citation is missing.** The smaller model (1.5B) didn't cite consistently even at 0.942 retrieval accuracy with a correct answer. Refusals fired on good answers.

**A forced citation instruction.** The worst regression in the project. After adding "the answer MUST contain [n]", the model degenerated into citation spam, cleanup stripped it down to an empty string, coverage dropped to zero and the system refused everything. Also on the 1.5B; the larger model needed no extra instructions.

**IDF coverage as an out-of-base signal.** Unstable between runs: "what's 2+2" gave 0.0 once and 0.89 another time.

**A table-of-contents filter.** Diagnostics flagged 86 of 576 chunks as suspect. Checked against the source: normal content, not tables of contents. It came back later as part of section-based chunking, driven by document structure instead of a line-length threshold.

**Multi-query.** The model generates 2–3 paraphrases of the question, results fused via RRF. It fixed one hard question and broke several easy ones: the paraphrases outvoted the original: 28/30 → 24/30 with three paraphrases. The paraphrases were also generated by the 1.5B; I didn't test with a better model.

**Query normalisation before embedding.** "Jak usunac konto" (Polish without diacritics) landed on payments instead of accounts. A single edge case. An attempt to fix it by appending a question mark: 18/20 → 15/20. Normalisation stayed on the BM25 side only, because mmlw requires Polish diacritics.

**Query rewriting by the model.** Implemented, disabled by default. Concatenating the last turn handles most cases without the cost of another call.

---

## Appendix: threshold calibration history

The thresholds are coupled to the stack. Every change of reranker, model or prompt forces a recalibration of all of them at once. Below is how it went.

**First calibration** (bge reranker, 1.5B model): reranker threshold 0.05, coverage 0.65. Back then the distributions separated cleanly: the lowest score on a test question was 0.945, the highest on an off-topic question 0.005.

**After swapping the reranker and moving to the 11B model** the thresholds stopped working. The new prompt (grounding separated from persona) raised coverage on both sides. The distributions began to overlap. Reranker threshold −2.0 → −3.2, coverage 0.10 → 0.40.

**After removing the section split and expanding the test sets** (30→61 in-domain, 18→29 off-topic): reranker threshold −3.2 → −4.3, coverage 0.40 → 0.20. Current state.

The new off-topic questions are mostly borderline (seller commission, helpline, stock quotes). The old set was dominated by obvious cases (maths, recipes, code), which the threshold cuts on its own. It inflated the impression of the system's robustness.

**Pipeline timings:**

| Step | Time |
|---|---|
| embedding | 0.07 s |
| retrieval | 0.19 s |
| reranking | 1.6 s |
| generation, Bielik 1.5B locally | 8–10 s |
| generation, Bielik-minitron 7B locally (Q4_K_M) | 53–61 s |

Slow local generation is a hardware limitation, which is why the public demo calls the model over an API.

**Answer length limit: 700 → 1500 tokens.** At 700 the longest answer in the measurement (691 tokens) was cut mid-sentence, invisibly in the logs, because the streaming loop ignored the finish reason. Without an upper limit the cost would be unbounded, and a rambling answer drives coverage down, so the gate would start rejecting its own correct answers.

**Index warm-up at startup.** Indexes loaded lazily and `lifespan` only warmed the reranker and the embedder. The first query paid for loading the index: 18.1 / 17.9 / 15.2 s instead of the usual 3–7 s.
