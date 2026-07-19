# Atlas Quest — Question / Quiz Specification

**Read-only audit.** Documents every way the app poses a question to the learner —
mechanics, item types, and verbatim content — as of the current working tree.
Stems, options, sequences and correct answers are reproduced **verbatim** (this is
an internal spec, not learner-facing). Nothing was changed to produce this file.

Sources: `app/game_content.py` (banks, hooks, beats, books, helpers, `grade_quiz`,
`select_trial_questions`), `app/eval_content.py` (post-test),
`app/static/js/observatory.js` (constellation stars + checks),
`app/templates/game/*` (dressing), `app/routes/game.py` (attempt/grade routing).

---

## Section 1 — At-a-glance (every question surface)

**Graded surfaces**

| Surface | Display name | Item types | Bank size | Pinned | What the learner DOES | Items shown | Pass rule | Independent vs all-or-nothing | Skin |
|---|---|---|---|---|---|---|---|---|---|
| Library Trial | **The Lexicon** | matching | 7 concepts | none | **click-to-ink**: click a concept, click the case → a line inks | 4 concepts + 6 case slips (2 decoys) | 3 / 4 | independent (1 pt per concept) | shared `trial.html` + `_lexicon_board.html` |
| Chronicle Trial | **The Reckoning of Ages** | order + mcq | 8 (6 MCQ + 2 order) | 2 order (both) | **drag-to-reorder** the 2 order items; **click one option** on the 2 MCQs | 4 (2 order + 2 MCQ) | 3 / 4 | independent per item; each order item internally all-or-nothing | shared `trial.html` + `_trial_core.html` |
| AI Lab Trial | **Data Classification** (the Classification Board) | sort | 12 objects | none | **drag-to-bin**: drag each data object into a bin | 4 objects | 3 / 4 | independent (1 pt per object) | bespoke `terminal.html` |
| Observatory Trial | **Reading the Sky** | mcq + hunt(=mcq) | 6 MCQ + 3 hunt sets | 1 hunt (group → pick 1) | **click one option** (the hunt is "click the false claim") | 4 (1 hunt + 3 MCQ) | 3 / 4 | independent (1 pt each) | shared `trial.html` + `_trial_core.html` |
| Final Assessment | **The Final Ascent** | mcq | 10 (fixed set) | all 10 | **click one option** | all 10 | 8 / 10 | independent (1 pt each) | bespoke `eval/post_test.html` |

**Ungraded surfaces** (learning gates / priming / qualitative)

| Surface | Item type | Count | What the learner DOES | Graded? | On wrong answer | Skin |
|---|---|---|---|---|---|---|
| Library book quick-checks | MCQ (3-option) | 5 (1 per book) | click one option to finish a book | No (client gate) | can retry; charges "Knowledge Core" | bookshelf |
| Chronicle beat quick-checks | MCQ (3-option) | 6 (1 per era) | click one to light the era | No (client gate) | re-answer; era won't light until right | timeline |
| Observatory star quick-checks | MCQ (3-option) | 10 (1 per star) | click one to map the star | No (client gate) | re-answer; star won't map until right | constellation |
| AI Lab practice sort | drag-to-bin | 6 fixed items → 3 bins | practice drag before the real board | No (ungraded warm-up) | shows accuracy, proceeds regardless | terminal |
| Guess-first hooks | 2–3 option guess (or free tap) | 25 total (Library 5, Chronicle 6, AI Lab 4, Observatory 10) | tap a guess before a lesson chunk | **Never logged/graded** | none — any guess just reveals a "payoff" line | all scenes |
| Post-Trial reflection | free text (1 sentence) | 4 (1 per location) | type one sentence, or skip | No (qualitative data only) | n/a | results page |

**Quick read on mechanic divergence:** genuinely distinct hands-on mechanics
exist for the **Library** (click-to-ink matching), **AI Lab** (drag-to-bin sort),
and the **Chronicle's ordering items** (drag-to-reorder). The **Observatory Trial
is mechanically a plain MCQ quiz** — every item, including the "Hallucination
Hunt," is *click one of four options*; the hunt is a **framing**, not a distinct
action, and it's the same physical act as the Final Assessment. The **Chronicle is
half plain MCQ** (2 of its 4 items). See Section 5.

---

## Section 2 — Per location

### 2.1 The Library — *foundations of AI*

**2a. Taught content** (`LOCATIONS["library"]`, 5 `learn_cards` + 5 books)
- **What is AI** — a machine that learns patterns from data and makes predictions; *adds to* human judgement, doesn't replace it; often invisible (search, recommendations, speech).
- **AI vs augmented intelligence** — augmented = AI assists on impractical tasks but a human keeps the final call + accountability ("AI + human"); full AI aims to mimic human thinking.
- **Analysis → Prediction** — AI's two acts: analyse data to find hidden patterns, then predict an outcome.
- **What predictions AI makes** — vision recognition, fraud detection, customer service.
- **Three levels** — Narrow (one task), Broad (IBM's term; several narrow systems integrated on an org's own data, e.g. a self-driving car), General (any domain like a human; does not exist yet).

**2b. Learn interaction** — a **bookshelf**: 5 "glowing tomes" (`LIBRARY_BOOKS`) among decoys, each a 3-page reader (intro→concept→example) ending in a quick-check; reading charges a "Knowledge Core." Gate: read all real books to reveal the Trial. Valid book ids are **derived** from `loc["books"]` (`explore_valid_ids`), not hardcoded.

**2c. Quick-checks** — 5, one per book, MCQ (3 options), **ungraded** client gate. Wrong answer → can retry; not logged.
| Book | Quick-check stem | Options | Correct |
|---|---|---|---|
| ai | "A music app suggests songs you might like based on what you've listened to. What is this an example of?" | A fixed, hand-made playlist / **Artificial intelligence finding patterns in your behaviour** / A random shuffle / A staff member choosing for you | idx 1 |
| augmented | "A doctor uses a tool that reads 1,000 scans in minutes and flags unusual ones for review. This is best described as:" | General AI replacing the doctor / **Augmented intelligence assisting the doctor** / A simple search engine / Reinforcement learning | idx 1 |
| does | "An AI studies years of weather data, then forecasts tomorrow's rain. Which part is the 'prediction'?" | Studying the years of past data / **Forecasting tomorrow's rain** / Storing the records / Deleting old files | idx 1 |
| predict | "Your bank texts to ask if a sudden, unusual purchase was really you. Which AI skill is at work?" | Printing receipts / **Fraud detection predicting a suspicious payment** / Counting your coins / Locking the front door | idx 1 |
| levels | "A program plays chess brilliantly but can do nothing else. Which level of AI is it?" | General AI / **Narrow AI** / Broad AI / Not AI at all | idx 1 |

**2d. Hooks** — 5 guess-first prompts (before each book), never logged. E.g. "Before you open this tome — what do you think makes a machine 'intelligent'?" → [Raw speed / Learning from data & predicting / A huge memory].

**2e. The Trial — "The Lexicon"** (dressing: parchment/sepia; click-to-ink lines between index cards and catalogue slips). **Composition:** all 4 items are `matching` concepts drawn at random from the 7-item bank; the server also serves 6 case slips = the 4 correct + **2 deterministic decoys** (from undrawn concepts), shuffled. Each concept graded independently (chosen scenario id == its own `sid`).

| key | type | concept (card) | scenario / case (verbatim) | correct sid | concept_tag |
|---|---|---|---|---|---|
| lex_narrow | matching | Narrow AI | "A spam filter that flags junk mail it has never seen before — yet it can do nothing else." | sc_a7 | three_levels |
| lex_broad | matching | Broad AI | "A delivery company fuses its own vision, route-planning and scheduling systems into one integrated platform, trained on its own delivery data." | sc_b3 | three_levels |
| lex_general | matching | General AI | "A machine that could take on any intellectual task a person can — which no one has built yet." | sc_c1 | three_levels |
| lex_augmented | matching | Augmented Intelligence | "AI pre-screens loan applications and flags the risky ones, but a human officer makes the final decision." | sc_d9 | augmented_intelligence |
| lex_notai | matching | Not AI at all | "A thermostat that switches the heating on whenever the room drops below 18°C." | sc_e5 | what_is_ai |
| lex_analysis | matching | Analysis (finding the pattern) | "Combing through millions of past card transactions to surface the recurring pattern that marks fraud." | sc_f2 | analysis_prediction |
| lex_prediction | matching | Prediction (naming the outcome) | "Forecasting how much rain will fall tomorrow from decades of weather records." | sc_g8 | analysis_prediction |

---

### 2.2 The Chronicle — *history: the eras & AI Winters*

**2a. Taught content** (6 `beats`)
- **Era of Tabulation** (antiquity–1930s) — sorting raw data into tables to reveal insight.
- **Era of Programming** (1940s–50s) — ENIAC; programmable computers; the dark-data problem is born.
- **Dawn of AI — Dartmouth 1956** — McCarthy & Minsky coin "artificial intelligence."
- **First Winter** (early 1970s) — two limits: calculating power + information storage; funding collapses.
- **Expert Systems & Second Winter** (1980s) — million-dollar mainframes boom, cheap PCs overtake, 300+ companies bankrupt.
- **The Thaw** (1997–today) — Deep Blue 1997, Stanford robot 2005, Watson 2011.

**2b. Learn interaction** — a **timeline**: 6 era "lanterns," each with a story + quick-check; lighting an era draws the timeline to the next. Gate: light all 6 to reveal the Trial. Valid ids `beat-N` are **derived** from `len(beats)`.

**2c. Quick-checks** — 6, one per beat, MCQ (3 options), **ungraded** gate.
| Beat | Stem | Options | Correct |
|---|---|---|---|
| Tabulation | "What was the key idea of the Era of Tabulation?" | Machines that could think for themselves / **Sorting raw data into structured tables to reveal insight** / Predicting the future from probabilities | idx 1 |
| Programming | "Why couldn't programmable computers keep up in the end?" | They were simply too expensive to build / **The world generated more data than any program could process** / No one knew how to write programs | idx 1 |
| Dartmouth | "What is the 1956 Dartmouth gathering remembered for?" | Building the first computer / **Coining the term 'artificial intelligence'** / Deep Blue's victory at chess | idx 1 |
| First Winter | "Which two limits caused the First Winter of AI?" | Bad programmers and simple bad luck / **Limited calculating power and limited information storage** / Too much data and too little electricity | idx 1 |
| Second Winter | "What ended the expert-systems boom in the late 1980s?" | A new law banned them / **Cheaper personal computers overtook costly mainframes** / The systems simply ran out of rules | idx 1 |
| The Thaw | "Which IBM system defeated the world chess champion in 1997?" | Watson / ENIAC / **Deep Blue** | idx 2 |

**2d. Hooks** — 6 guess-first prompts. E.g. "Guess the year the term 'artificial intelligence' was first coined." → [1956 / 1985 / 2010].

**2e. The Trial — "The Reckoning of Ages"** (dressing: aged-bronze, clock watermark, "RECORD n/4"). **Composition:** both `order` items are **pinned** (always shown, first), plus **2 MCQs sampled** from the 6-item MCQ bank. So the draw is always 2 ordering + 2 MCQ.

*Ordering items* (drag-to-reorder; correct = authored order of `events`, server-side only; the client renders events shuffled):

| key | type | stem | correct sequence (top→bottom) | concept |
|---|---|---|---|---|
| chr_order_eras | order | "The archive's timeline has been corrupted. Restore these events to their true chronological order — earliest at the top." | Era of Tabulation → Era of Programming (ENIAC, 1940s) → Dartmouth coins "artificial intelligence" (1956) → First AI Winter (1970s) → Deep Blue defeats the world chess champion (1997) | eras_and_winters |
| chr_order_winter | order | "Reassemble the causal chain that led to an AI Winter — the first cause at the top." | Expert systems boom on million-dollar mainframes → Cheaper personal computers outpace those mainframes → The expert-systems market collapses → Investment and funding dry up → An AI Winter sets in | eras_and_winters |

*MCQ bank* (6; correct letter shown; **note: these MCQs carry no `concept_tag`**):

| key | stem | options (A/B/C/D) | correct |
|---|---|---|---|
| ch_s1 | "A museum shows an old machine that took stacks of raw figures and arranged them into neat tables so clerks could finally spot trends. Which era does it belong to?" | The Era of Programming / The Era of Tabulation / The Era of AI / The Era of Machine Learning | **B** |
| ch_s2 | "What is the correct chronological order of the three eras of computing?" | Programming → Tabulation → AI / AI → Programming → Tabulation / Tabulation → Programming → AI / Tabulation → AI → Programming | **C** |
| ch_s3 | "In 1956, a summer gathering at Dartmouth College led by John McCarthy and Marvin Minsky is famous for which milestone?" | Building ENIAC / Coining the term 'artificial intelligence' / Deep Blue's chess victory / The start of the First Winter | **B** |
| ch_s4 | "Grand promises went unmet and funding dried up in the early 1970s. What TWO limits were the main causes of this First AI Winter?" | Limited calculating power and limited information storage / Too many programmers and too few computers / A shortage of data and a shortage of electricity / Government bans and public fear | **A** |
| ch_s5 | "After the expert-systems boom collapsed, what finally brought AI out of the Second Winter in the mid-1990s?" | A brand-new programming language / Processing power finally becoming fast enough / Expert systems suddenly getting cheaper / A single government grant | **B** |
| ch_s6 | "Which IBM system, searching around 200 million positions per second, defeated the reigning world chess champion in 1997?" | Watson / ENIAC / Deep Blue / Apollo | **C** |

---

### 2.3 The AI Lab — *data types*

**2a. Taught content** (4 `learn_cards`) — recap of the three eras (Tabulation / Programming / AI, overlapping the Chronicle), then **Structured / Semi-structured / Unstructured data** + **dark data** (collected but never used; can be any type; ~80–90% of enterprise data is unstructured).

**2b. Learn interaction** — a **CRT terminal**: power-on → 3 "sector" era cards → a 4th card that is a **practice** data-sorting machine → reboot → the graded board. Sector switches `SECT-1…4`. **⚠ The 4 cards and the `SECT-1…4` switches are HARDCODED in `terminal.html` (`{% for n in range(4) %}`), not generated from the 4 `learn_cards`.** Server valid ids `sector-N` *are* derived from `len(learn_cards)`, so the two can disagree if content length changes.

**2c. Quick-checks** — **none of the MCQ kind.** The only interactive check in the scene is the **practice sort** (below), which is ungraded. (The 4th learn card's "Data Types" content is delivered as the practice machine's intro.)

**AI Lab practice sort** (ungraded warm-up; 6 fixed demo items → 3 bins, hardcoded in `terminal.html`): items **Spreadsheet**(structured), **Photo**(unstructured), **Tweet**(semi), **Database Row**(structured), **Voice Recording**(unstructured), **Email w/ Subject**(semi). Wrong sort → shows accuracy, proceeds anyway. *(Bins here are only 3 — Structured/Semi/Unstructured — no "Dark data" bin, unlike the graded board's 4 bins.)*

**2d. Hooks** — 4 guess-first prompts (aligns to the 4 sector cards). E.g. "Guess: what fraction of a company's data do you think ever actually gets analysed?" → [Almost all of it / About half / Only a small slice].

**2e. The Trial — "Data Classification" (the Classification Board)** (dressing: the terminal itself — "ASSESSMENT MODE — DATA CLASSIFICATION", "SPECIMENS SORTED n/4"). **Composition:** all 4 items are `sort` objects drawn at random from the 12-item bank; rendered shuffled as draggable cards; **bins** = `DATA_BINS` = `structured` / `semi` / `unstructured` / `dark` (correct bin held server-side). Each object graded independently.

| key | type | data object (verbatim) | correct bin | concept |
|---|---|---|---|---|
| lab_o1 | sort | "A spreadsheet of customer names, ages and account balances in fixed columns" | structured | data_types |
| lab_o2 | sort | "A relational table of daily stock prices, one row per date" | structured | data_types |
| lab_o3 | sort | "A payroll database with fixed fields for employee ID, salary and start date" | structured | data_types |
| lab_o4 | sort | "A stream of JSON API logs, each tagged with keys but no fixed table schema" | semi | data_types |
| lab_o5 | sort | "An XML product feed where every entry carries its own descriptive tags" | semi | data_types |
| lab_o6 | sort | "Sensor readings streamed as key–value pairs with no rigid table schema" | semi | data_types |
| lab_o7 | sort | "Customer support emails and call recordings the support team works through daily" | unstructured | data_types |
| lab_o8 | sort | "The photo library of product images the marketing team publishes each week" | unstructured | data_types |
| lab_o9 | sort | "Voicemail messages the call centre transcribes and acts on every day" | unstructured | data_types |
| lab_o10 | sort | "Six years of CCTV footage that no one has ever reviewed" | dark | data_types |
| lab_o11 | sort | "Archived server logs the company keeps but never analyses" | dark | data_types |
| lab_o12 | sort | "Old transaction records, neatly tabulated, sitting in a legacy system nobody queries" | dark | data_types |

---

### 2.4 The Observatory — *machine learning + modern AI*

**2a. Taught content** — 4 `learn_cards` (ML vs programming; supervised; unsupervised + reinforcement; three levels revisited) **plus 10 constellation stars** (`observatory.js CONCEPTS`): (1) how ML learns/answers (deterministic vs probabilistic), (2) supervised, (3) unsupervised, (4) reinforcement, (5) three levels, (6) overfitting & bias, (7) NLP, (8) LLMs (Atlas is an LLM), (9) hallucination, (10) few-shot prompting.

**2b. Learn interaction** — a **constellation**: 10 stars revealed one at a time, each with a concept + inline check; a line connects each to the next. Gate: map all 10 stars → Trial unlocks (`discoveredCount >= CONSTELLATION_STARS.length`). **⚠ Star count lives in FOUR parallel lists** — `CONSTELLATION_STARS` (JS, 10 hardcoded coords), `CONCEPTS` (JS, 10), `CHECKS` (JS, 10), and `HOOKS["observatory"]` (Python, 10, the server's source for valid `star-N` ids). A content test asserts they stay equal at 10.

**2c. Quick-checks** — 10, one per star, MCQ (3 options), **ungraded** gate (`observatory.js CHECKS`).
| # | Stem | Options | Correct |
|---|---|---|---|
| 1 | "How is machine learning different from a traditional computer program?" | It follows exact pre-written rules / **It gives probabilities and improves itself over time** / It can only work with numbers | idx 1 |
| 2 | "What does supervised learning need to work?" | **Labelled examples with correct answers** / No data at all / A human watching at all times | idx 0 |
| 3 | "What does unsupervised learning do with unlabelled data?" | Ignores it completely / **Finds hidden patterns and groupings by itself** / Waits for a human to label it | idx 1 |
| 4 | "How does reinforcement learning improve?" | **Through rewards for correct and penalties for wrong predictions** / By copying answers from a database / It never improves | idx 0 |
| 5 | "Which level of AI is available and used by enterprises today?" | General AI / **Broad AI** / None of them exist yet | idx 1 |
| 6 | "What is overfitting?" | **A model that memorises training data and then fails on new, unseen data** / A model trained on too little data / A model with no training data at all | idx 0 |
| 7 | "What does Natural Language Processing let machines do?" | Only work with numbers / **Understand and generate human language** / Run ordinary calculations faster | idx 1 |
| 8 | "What is a Large Language Model — like Professor Atlas?" | A database of every sentence ever written / **A model trained on huge amounts of text that predicts language** / A human answering in real time | idx 1 |
| 9 | "What is an AI 'hallucination'?" | **A confident answer that is actually false** / A picture an AI draws / A hardware failure | idx 0 |
| 10 | "What is few-shot prompting?" | **Giving the model a few examples to steer its output** / Asking the same question many times / Training a whole model from scratch | idx 0 |

**2d. Hooks** — 10 guess-first prompts, 1:1 with the stars (this list's length is the server's star-count source). E.g. "An AI confidently states a fake 'fact'. What is that called?" → [A hallucination / A victory / A calculation].

**2e. The Trial — "Reading the Sky"** (dressing: cyan star-field; the pinned item is "Atlas speaking"). **Composition:** **1 "Hallucination Hunt" set is pinned** (the server picks ONE of `obs_hunt1/2/3` per attempt via a pinned *group*; the other two never appear), plus **3 MCQs sampled** from `obs_s1…s6`. All 4 items are click-one-of-four.

*MCQ bank* (6; correct letter; **no `concept_tag` on these**):

| key | stem | options (A/B/C/D) | correct |
|---|---|---|---|
| obs_s1 | "A team has 50,000 emails already labelled \"spam\" or \"not spam\" and wants to train a filter. Which ML method fits?" | Supervised learning / Unsupervised learning / Reinforcement learning / None of these | **A** |
| obs_s2 | "A streaming service wants to group viewers with similar tastes, but nobody has defined what the groups should be. Which method?" | Supervised learning / Unsupervised learning / Reinforcement learning / Deterministic rules | **B** |
| obs_s3 | "Amazon trains warehouse robots to pick and move goods, rewarding good actions and penalising mistakes so they improve through trial and error. This is:" | Supervised learning / Unsupervised learning / Reinforcement learning / Structured data sorting | **C** |
| obs_s4 | "A calculator returns exactly the same answer every time you enter 7 × 8, and an autonomous car's braking logic is built to behave the same predictable way. These are examples of:" | Probabilistic systems / Unsupervised learning / Dark data / Deterministic systems | **D** |
| obs_s5 | "A medical AI outputs \"78% likelihood this scan shows a tumour\" instead of a flat yes/no. What kind of system is this, and why is it useful?" | Probabilistic — it expresses confidence/uncertainty, helping doctors prioritise / Deterministic — it's always exact / Unsupervised — it has no data / Broken; AI should never be unsure | **A** |
| obs_s6 | "Recall from the Library that a self-driving car is broad AI. Which ML method most likely helps the car improve its driving decisions through trial, reward and consequence?" | Supervised only / Reinforcement learning / Unsupervised only / It uses no machine learning | **B** |

*Hallucination Hunt sets* (`hunt: True`; an ordinary 4-option MCQ where **`correct` = the FALSE claim** to catch; all-or-nothing per item; stem identical across the three):

Stem (all three): *"I am a language model — and a language model can state a falsehood with complete confidence. Below are four of my readings on how machines learn. Exactly one is a hallucination: confidently worded, but false. Find it."*

| key | A | B | C | D | correct (the FALSE claim) |
|---|---|---|---|---|---|
| obs_hunt1 | Supervised learning uses labelled examples to learn a mapping from inputs to outputs. | Unsupervised learning finds structure in data without labelled outcomes. | Reinforcement learning requires a labelled dataset of correct actions before training can begin. | A probabilistic model expresses its output as a confidence rather than a definite yes or no. | **C** |
| obs_hunt2 | Overfitting occurs when a model performs well on training data but poorly on new data. | A large language model verifies each statement against a database of facts before it answers. | Few-shot prompting steers a model by including a small number of examples in the prompt. | A model trained on biased historical data can reproduce that bias in its predictions. | **B** |
| obs_hunt3 | Natural language processing lets a model work with unstructured human language such as emails and speech. | A deterministic system returns the same output every time it is given the same input. | A confident, fluent answer from a model can still be completely false. | If a model scores 100% on its training data, it is guaranteed to do just as well on new, unseen data. | **D** |

---

## Section 3 — Final Assessment (post-test)

Display name **"The Final Ascent"** (`eval/post_test.html`). Uniformly **MCQ** (4
options, click one). Fixed 10-item set (no sampling). **Pass rule: 8 / 10**
(`POST_TEST_PASS`). Single-attempt, server-authoritative timing. Chapter tags are
presentation only.

| key | chapter | concept | teaches @ | stem | options (A/B/C/D) | correct |
|---|---|---|---|---|---|---|
| p1 | 1 Foundations | what_is_ai | Library | "The Library taught that artificial intelligence is best described as a machine that…" | follows a fixed set of hand-written rules and never changes / learns patterns from data to make predictions, adding to human judgement / simply stores large amounts of information for fast lookup / is just faster hardware for running ordinary calculations | **B** |
| p2 | 1 | three_levels | Library | "Which statement about the three levels of AI is correct?" | General AI already runs most businesses today / Narrow AI can transfer its skill to any new task / Broad AI integrates several narrow systems and is what's available today; General AI does not exist yet / Super AI is the level used in everyday spam filters | **C** |
| p3 | 1 | augmented_intelligence | Library | "A bank uses AI to pre-screen loan applications and flag risks, but a human officer makes the final decision. This 'AI assists, human decides' arrangement is called:" | General AI / Augmented intelligence / Reinforcement learning / Unsupervised learning | **B** |
| p4 | 1 | eras_and_winters | Chronicle | "Grand promises went unmet and funding collapsed in the early 1970s — the First AI Winter. What were its two main technical causes?" | Too many programmers and too few computers / Limited calculating power and limited information storage / Government bans and public fear of AI / A shortage of data and a shortage of electricity | **B** |
| p5 | 1 | ai_milestones | Chronicle | "Which milestone helped thaw the AI Winters — an IBM system that defeated the reigning world chess champion in 1997?" | ENIAC / Watson / Deep Blue / The Dartmouth workshop | **C** |
| p6 | 2 The Data Deep | data_types | AI Lab | "Which of these is an example of UNSTRUCTURED data?" | A spreadsheet of names, ages and account balances / A table of stock prices organised by date / Customer emails, photos and voice recordings / A database with fixed rows and columns | **C** |
| p7 | 2 | unstructured_data | AI Lab | "An estimated 80–90% of enterprise data is unstructured. Why is that hard for traditional, rule-based computers?" | Unstructured data doesn't really exist / It has no fixed schema, so conventional programs can't query it directly — AI (e.g. natural-language processing) is needed to make sense of it / Traditional computers can only read images / Structured data cannot be analysed at all | **B** |
| p8 | 3 The Learning Machines | ml_methods | Observatory | "A team has 50,000 emails already labelled 'spam' or 'not spam' and wants to train a filter. Which machine-learning method fits?" | Supervised learning / Unsupervised learning / Reinforcement learning / None — this needs no machine learning | **A** |
| p9 | 3 | overfitting | Observatory | "A model scores 99% on its training data but only 60% on new, unseen data. What has gone wrong?" | Underfitting / Overfitting / Nothing — it is perfectly trained / Reinforcement learning | **B** |
| p10 | 4 Final Synthesis | hallucination | Observatory | "Professor Atlas is itself a large language model. When an LLM produces a confident, fluent answer that is actually FALSE, this is called:" | A hallucination / Overfitting / A syntax error / Reinforcement | **A** |

---

## Section 4 — The machinery (brief)

**Trial composition (`select_trial_questions`, game_content.py:997).** One
generic function. Reads `PINNED_QUESTIONS[loc]`: a plain key is always shown; a
**group** (nested list) means the server picks exactly one member and excludes the
whole group from the random remainder. The rest is `random.sample`d from the bank.
Per location: **Library** — no pins, draws 4 of 7 matching; **Chronicle** — pins
both order keys, samples 2 of 6 MCQ; **AI Lab** — no pins, draws 4 of 12 sort;
**Observatory** — pins one of the `[obs_hunt1..3]` group, samples 3 of 6 MCQ.

**Grading (`grade_quiz`, game_content.py:1090).** **One shared core, one loop, one
score rule (1 pt per correct item).** It branches by type only to *compute
correctness*: `order` → whole-sequence match via `normalize_order`; `sort` →
`selected == correct` (bin id); `matching` → `selected == correct` (scenario id);
else MCQ → `selected == correct` (letter). `submit_quiz` calls it once and takes
`is_correct` from its results — **no forked per-location grading path.** Score =
count of correct items; pass ≥ 3.

**Dressing.** Library / Chronicle / Observatory use the **shared** `trial.html`
skin system (per-location kicker/title/backdrop + `trial-skin-<key>` CSS) wrapping
`_trial_core.html` — except the **Library** swaps in `_lexicon_board.html` (still
under the shared skin). The **AI Lab** is the exception: a **bespoke**
`terminal.html` that embeds its board in the scene. All post to the same
`submit_quiz`.

**Where correct answers live / DOM safety.** MCQ correct letter → only in
`game_content`, revealed only via the `/answer` commit *after* the learner locks
in (never in initial DOM). `order` → correct sequence = authored `events` order,
server-side; the DOM shows events shuffled. `sort` → correct bin in `game_content`;
bins render as neutral ids. `matching` → correct `sid` in `game_content`; concept
cards carry only their key, slips only an opaque `sid` + text; the 2 decoys are
byte-identical markup to the 4 correct slips. The Library/AI-Lab boards commit at
**submit** (not `/answer`), and `/answer` returns 400 for `sort`/`matching`.

**Coverage (tested ⊆ taught).** `TAUGHT_CONCEPTS` maps each taught concept → its
location. Every `POST_TEST` item carries a `concept` key; a unit test
(`test_post_test_concepts_are_a_subset_of_taught`) asserts the set of tested
concepts is a **subset** of the taught set. **Scope note: the coverage test checks
only the Final Assessment, not the Trials** — and Trial items are tagged
inconsistently (see flags).

---

## Section 5 — Flags (report only; nothing fixed)

**A. Converged / not-really-distinct mechanics.**
- **Observatory Trial is mechanically a plain MCQ quiz.** All 4 items — the pinned "Hallucination Hunt" plus 3 `obs_s*` — are *click one of four options*. The hunt (`obs_hunt*`, `hunt: True`) is an ordinary MCQ whose correct answer is "the false claim"; it's a **framing**, not a distinct physical action, and it's the same act as the Final Assessment. (game_content.py:850–901). So of the four realms, only Library (click-to-ink), AI Lab (drag-to-bin) and the Chronicle's ordering items (drag-to-reorder) are genuinely distinct in the hand; the Observatory has no hands-on mechanic.
- **The Chronicle Trial is half plain MCQ** — 2 of its 4 items are `ch_s*` click-one MCQs (game_content.py:526–616), the same action as the Observatory items and the Final.

**B. Hardcoded counts that should derive from content** (recurring family).
- **AI Lab terminal cards + sector switches are hardcoded.** `terminal.html` hardcodes 3 era cards + 1 practice card and `{% for n in range(4) %}` sector switches — **not** generated from the 4 `learn_cards`. The server's valid `sector-N` ids *do* derive from `len(learn_cards)`, so the two silently disagree if content length changes. (app/templates/game/terminal.html — the `range(4)` loop; game_content.py:369–393.)
- **Observatory star count is duplicated across 4 lists.** `CONSTELLATION_STARS` (10 hardcoded coords), `CONCEPTS` (10), `CHECKS` (10) in observatory.js:22–93, plus `HOOKS["observatory"]` (10) in game_content.py:1226. Only the last drives the server's valid ids; the JS three are hardcoded arrays kept in sync by a test, not by derivation. This is the same bug family as the earlier "range(5) vs 10 stars" (H1).
- (For contrast, the **Library** book ids and **Chronicle** `beat-N` ids *are* derived from content length — good.)

**C. Taught-but-never-assessed / assessed-but-not-taught.**
- **Assessed-but-not-taught: none found** — every graded item maps to taught content.
- **Taught but never assessed by any graded item: `bias`, `nlp`, `few_shot_prompting`.** All three are taught (Observatory stars 6/7/10) and only appear as *true distractor claims* inside the Hallucination Hunt (never the thing the learner must demonstrate); none is the answer to any Trial or Final item. `deterministic_probabilistic` is assessed only implicitly (obs_s4/obs_s5, which carry no `concept_tag`).
- **Concept tagging on Trial items is inconsistent.** Library `lex_*`, AI Lab `lab_o*`, the Chronicle order items and the hunt items carry a concept; the **plain MCQ banks `ch_s1–6` and `obs_s1–6` carry no `concept_tag` at all** — so any "which Trials assess concept X" analysis is unreliable, and the coverage test doesn't look at Trials anyway.

**D. Structural integrity (correct-in-options, dup keys, bank size).** No problems.
All MCQ `correct` letters are real options; order/sort/matching `correct` values are
valid; all keys unique. Bank sizes suffice: Library 7 (needs ≥6 for 4 + 2 decoys),
Chronicle 6 MCQ (samples 2) + 2 pinned order, AI Lab 12 (samples 4), Observatory 6
MCQ (samples 3) + 3-set hunt group (picks 1).

**E. Ambiguous items (a knowledgeable person could defend a second answer).**
- **`lex_analysis` vs `lex_prediction` (Library Lexicon).** The taught fraud example uses the *whole* pipeline ("spots the pattern of fraud — then predicts which new charge is stolen"), so a learner can defensibly read the fraud-pattern case as *prediction* too. The rain case is unambiguously prediction; the fraud case is the softer one. (game_content.py:504–523.) *(Flagged during authoring; disambiguated by domain but still the subtlest pair.)*
- **`obs_s6` telegraphs its own answer.** The stem literally contains the definition of the correct option — "improve its driving decisions through **trial, reward and consequence**" → Reinforcement learning. It tests recognition of a phrase, not understanding. (game_content.py:824–838.)

**F. Weak distractors (throwaway options that shrink a 4-option item to 2–3).** The
**Observatory `obs_s*` bank is the worst offender**:
- `obs_s1` D "None of these"; `obs_s3` D "Structured data sorting"; `obs_s4` C "Dark data"; `obs_s5` D "Broken; AI should never be unsure"; `obs_s6` D "It uses no machine learning" — each is off-topic/absurd and eliminable on sight.
- Chronicle: `ch_s4` D "Government bans and public fear", `ch_s6` D "Apollo" (not a chess system), `ch_s1` D "The Era of Machine Learning" (an invented era) — weak.
- Final: `p2` D "Super AI is the level used in everyday spam filters", `p10` C "A syntax error" / D "Reinforcement" — weak.
- *Contrast:* the **matching decoys** (Library) and the **hunt** true-claims (Observatory) are *strong* distractors (real cases / true statements), so those two surfaces best support the "understanding vs guessing" argument.

**G. Factual errors in stems/options/explanations.** None found. Spot-checked:
Dartmouth 1956 (McCarthy & Minsky), ENIAC 1940s @ UPenn, Deep Blue 1997 (~200M
positions/sec), Watson Jeopardy! 2011, Stanford robot 2005 (131 mi), "300+ AI
companies bankrupt," ~80–90% unstructured data. Two *editorial* (not factual)
notes: "Broad AI" is IBM-specific terminology presented as if standard; and the
Observatory learn card's "General AI… perhaps 25 years from now, superintelligent"
sits in mild tension with star 5's "still only a research goal" — both trace to the
IBM source, so not errors.

**H. Duplicated content between a Trial and the Final (rehearsal risk).** Several —
because Trials sample randomly, these are *probabilistic* rehearsals (the learner
may or may not have seen the Trial twin), but the twins exist:
- **`p8` ≈ `obs_s1` — essentially word-for-word.** Both: "A team has 50,000 emails already labelled 'spam'/'not spam' and wants to train a filter. Which … method fits?" → Supervised. (eval:122 / game_content:749.)
- **`p4` ≈ `ch_s4` — near-identical.** Both ask the First AI Winter's two causes → "limited calculating power and limited information storage." (eval:74 / game_content:572.)
- **`p5` ≈ `ch_s6` — same fact.** Both: which IBM system beat the world chess champion in 1997 → Deep Blue. (eval:86 / game_content:602.)
- **`p3` ≈ `lex_augmented` — same scenario, different format.** Both use "bank pre-screens loan applications, a human officer decides" → augmented intelligence. (eval:62 / game_content:485.)
- **Softer content overlaps:** `p6` (pick the unstructured item: emails/photos/voice) rehearses the AI Lab unstructured objects `lab_o7/8/9`; `p2` overlaps `lex_broad` (Broad AI). Different format, so weaker rehearsal.

**Bottom line for the "understanding vs guessing" thesis:** the Library and AI Lab
boards, the Chronicle ordering, and the Observatory hunt are the strong surfaces
(real distractors, hands-on or discrimination tasks). The weak spots are the
Observatory/Chronicle **plain-MCQ banks** (throwaway 4th options + one self-
telegraphing stem) and the **Final's 3–4 near-duplicate items** rehearsing Trial
questions.
