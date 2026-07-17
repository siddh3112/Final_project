# Testing

This chapter documents the testing carried out on *Atlas Quest*, the gamified
AI-literacy web application developed for this dissertation. Because the
application is not merely a piece of software but also the **measurement
instrument** for the study — it delivers the learning intervention and records
the data on which the research conclusions rest — testing served two distinct
purposes. In the ordinary software-engineering sense it guarded against defects
and regressions. In the research sense it protected the *validity of the
instrument*: it verified that scores were graded correctly, that progression was
gated as intended, that the assessment could be taken only once, and that the
data captured for analysis could not be forged or corrupted by a participant's
browser. The chapter sets out the testing strategy and its rationale, the test
architecture, the categories of test and what each verifies, the treatment of
security and tamper-resistance, the regression tests that arose from a code
audit, the manual and exploratory testing that complemented the automated suite,
and finally the results, limitations, and reproducibility of the test process.

## 1. Testing strategy and rationale

The testing strategy followed the conventional *testing pyramid*: a broad base of
fast, isolated unit tests, a middle layer of integration tests exercising the
application through its real HTTP routes and database, and a thin top layer of
manual end-to-end verification in a real browser. The great majority of coverage
was placed in the lower two layers because those tests are deterministic, fast,
and can be run on every change, whereas full browser automation is slower and
more brittle.

A guiding principle — stated explicitly in the docstring of every test module —
was that **the tests verify the application's rules; they never relax them to
pass**. Trial and post-test grading, pass thresholds, unlock gating, the
single-attempt constraint on the assessment, the separation of study conditions,
and the anti-tamper checks are all *research-critical invariants*. If a test
failed, the correct response was either to fix a genuine defect in the
application or to correct a mistaken test — never to weaken grading, thresholds,
or logging in order to make a test go green. This discipline is what allows the
suite to double as evidence that the measurement instrument behaves as the
research design assumes.

The choice of test cases was driven by the properties the research depends on
rather than by a pursuit of a particular line-coverage figure. Priority was given
to the parts of the system where a defect would silently corrupt the study data
or bias a participant's outcome: the grading core, the progression gate, the
one-attempt post-test, and the server-authoritative handling of anything a
participant's browser might otherwise be trusted to report.

## 2. Test architecture and infrastructure

All automated tests were written in Python using the **pytest** framework and
were located in the `tests/` directory. The suite was configured through
`pytest.ini` to discover any `test_*.py` module under `tests/`.

The single most important design decision in the test infrastructure was
**isolation from the real environment**, implemented through shared fixtures in
`tests/conftest.py`:

- **A throwaway in-memory database.** Every test ran against a fresh
  `sqlite:///:memory:` database rather than the application's real
  `instance/atlas_quest.db`. A function-scoped `app` fixture created all tables
  before each test and dropped them afterwards, so every test began from an empty,
  fully isolated database and could not contaminate another test or the
  developer's real data. A hard assertion in the fixture refused to run unless the
  configured database URI was the in-memory one, guaranteeing that a
  configuration slip could never point the tests at production data.
- **A single shared connection.** SQLAlchemy's `StaticPool` was used so that the
  in-memory database created by the fixture was the very same one seen by the
  Flask test client's requests — without it, each connection would otherwise
  receive its own empty in-memory database.
- **The language model stubbed off.** The AI tutor ("Professor Atlas") is backed
  by a locally hosted large language model (Ollama). Tests set
  `OLLAMA_ENABLED = False` so that no test ever depended on the model running,
  was slowed by inference, or produced non-deterministic output. Where the tutor's
  behaviour around the model *was* under test, the model call was replaced with a
  spy using pytest's `monkeypatch`, allowing the test to assert precisely whether
  and when the model would have been invoked.
- **Reusable state builders.** A `user_factory` fixture created a participant in
  any required state in a single call — a fresh user, one who had passed a given
  set of locations, one who had completed the post-test, one with specific
  progress rows — which kept the tests concise and their intent legible. A
  companion `login` fixture authenticated the test client directly through the
  Flask-Login session key (avoiding a password round-trip), and an `as_correct`
  fixture constructed a post-test submission with exactly *N* correct answers.

The application under test is a Flask app built with the application-factory
pattern and four blueprints (`game`, `auth`, `npc`, `eval`) over an SQLAlchemy
model layer of eleven tables (including `User`, `LocationProgress`,
`QuizAttempt`, `TrialAttempt`, `KnowledgeTest`, `RunHistory`, and
`GameSession`). The integration tests drove these blueprints through Flask's
built-in test client, exercising the real routing, session handling, and
database persistence rather than mocked substitutes.

The environment used to run the suite for this dissertation was Python 3.14,
pytest 9.1, Flask 3.1, and SQLAlchemy 2.0.

## 3. Categories of test

The automated suite comprised **109 tests across six modules**, organised into
two tiers — unit tests that exercise pure logic with no HTTP layer or database,
and integration tests that drive the running application through its routes and
persist to the (in-memory) database. Table&nbsp;1 summarises the distribution.

**Table 1. Automated test suite by module.**

| Module | Tier | Focus | Tests |
| --- | --- | --- | ---: |
| `test_unit_content.py` | Unit | Content and authoring integrity | 17 |
| `test_unit_grading.py` | Unit | Grading and question-selection core | 21 |
| `test_unit_services.py` | Unit | Service layer (tutor, XP, leaderboard, badges) | 16 |
| `test_integration_auth.py` | Integration | Authentication and study-condition assignment | 9 |
| `test_integration_game.py` | Integration | Game loop and tamper resistance | 22 |
| `test_eval.py` | Integration | Post-test assessment invariants | 24 |
| **Total** | | | **109** |

### 3.1 Unit tests — content integrity

The content-integrity module (`test_unit_content.py`) treats the game's authored
material as data to be validated. Rather than testing behaviour, it asserts that
the question banks, learning content, and assessment are well-formed the moment
any are edited — catching an authoring mistake before it can reach a participant.
Its checks include: that every ordered location exists and has a populated
question bank large enough to fill a Trial; that every question is well-formed,
with a unique key, four options (A–D), non-empty option text, and a "correct"
value that is genuinely one of the options; that any "pinned" question really
exists in its location's bank; that the ten-item post-test has the expected
structure and an eight-of-ten pass mark; and that each Chronicle timeline beat and
each Library book carries a valid quick-check.

Two content tests are of particular research interest because they enforce
*construct validity* at the level of the material: one asserts that the set of
concepts measured by the post-test is a **subset of the concepts the game
actually teaches**, so that no assessment item tests untaught material; another
confirms that concept strands which had previously been taught but not assessed
(AI history, data types) are now covered by the post-test. A further pair of
source-level guards protect a recurring defect in the Observatory location by
asserting that its star count is a single consistent value across the JavaScript
content and the server-side hooks, and that the Trial only unlocks after *all*
stars are completed rather than at a mid-way point.

### 3.2 Unit tests — the grading core

The grading module (`test_unit_grading.py`) pins the deterministic behaviour of
the pure functions that score a Trial and select its questions, tested directly
and — through pytest parametrisation — across every learning location. These are
the functions on which every recorded score ultimately depends, so they are
tested exhaustively. The module verifies that a Trial's score equals exactly the
number of correct answers for every possible number correct; that the pass
boundary sits precisely at the three-of-four threshold and nowhere else; that
**only the questions the server actually served are graded**, so that a smuggled
answer to an unserved question is ignored; that an unanswered question is scored
wrong and never awarded a free point; and that each result row carries the fields
the results screen needs, with its "correct" flag consistent with the selected
answer. It also confirms that question selection returns the right number of
valid, unique questions, that a pinned question always appears first, and that
selection genuinely samples the bank rather than returning a fixed slice.

### 3.3 Unit tests — the service layer

The service module (`test_unit_services.py`) covers the supporting subsystems.
The largest group concerns the **Professor Atlas** tutor's guardrails, which are
critical to the study's construct validity: because the tutor must scaffold
learning without simply giving away Trial answers, the tests confirm that an
answer-seeking message ("just tell me the answer", "is it C?") is recognised and
deflected with a Socratic response, that this deflection fires *before* the
language model is ever queried (so a request to leak an answer can never reach the
model), that a genuine concept question still reaches the model when it is
enabled, and that the tutor's grounding knowledge and keyword maps match each
location's curriculum without smuggling in an answer key. The remaining service
tests verify the experience-point formula, the leaderboard's combined-score and
speed-bonus calculations (including their caps and floors), and the achievement
qualifier, including that badge-granting is idempotent and cannot double-award.

### 3.4 Integration tests — authentication and study condition

The authentication module (`test_integration_auth.py`) drives the real
registration, login, and logout routes. Beyond the expected checks — that
registration creates a password-*hashed* user and logs them in, that duplicate
usernames and emails are rejected, that a bad password re-renders the form, and
that protected routes redirect an anonymous visitor to the login page — this
module is where the **study-condition assignment** is verified. The study was
ultimately run as a single condition in which every participant receives the AI
tutor, and the tests assert that the server *always* assigns this condition and
**ignores any condition value supplied by the client**, whether as a URL
parameter or a form field, and that no route can change a user's condition once
assigned. Importantly, the two-group machinery was retained rather than deleted,
and a separate test confirms the control-condition gate is still intact and
reversible — evidence that the single-condition decision was a deliberate,
auditable configuration rather than an irreversible removal.

### 3.5 Integration tests — the game loop and tamper resistance

The game-loop module (`test_integration_game.py`) exercises the core progression
through the Flask test client and is the heart of the suite's *data-integrity*
argument. It verifies the **unlock chain** — that the first location is open, that
later locations are gated until the previous one is passed, and that passing a
location unlocks the next — and confirms the full set of side effects of a passing
submission: the results screen renders, progress is recorded, the correct number
of per-question attempt rows are logged against the server's served question set,
the game session is closed, and the appropriate badge is granted. It also
confirms that a participant's best score is monotonic (a worse retake never
revokes a pass or lowers the recorded best) and that a submission to a locked
location records nothing at all.

The most research-significant tests in this module concern **server-authoritative
grading and tamper resistance**, described in Section 4.

### 3.6 Integration tests — the post-test assessment

The evaluation module (`test_eval.py`) protects the invariants of the final
assessment on which the study's outcome measure depends. It verifies that the
post-test score equals the number of correct answers and that the pass mark is
eight of ten; that the assessment is **strictly single-attempt** — exactly one
result is recorded, a second submission (whether the first passed or failed) is
rejected and cannot overwrite the first, and this holds at the database level
through a unique constraint that causes a concurrent double-submission to fail
rather than create a duplicate; and that the assessment is **gated** so that it
can only be reached once all learning locations have been passed, with a premature
submission recording nothing. It distinguishes *completion* (an attempt exists)
from *passing*, since the two are tracked separately, and confirms that
re-entering the assessment after completing it shows the recorded results rather
than a fresh, blank test.

A pair of tests in this module addresses a subtle but important measurement issue:
the assessment's **timing is server-authoritative**. Because a participant's
browser could report any elapsed time it liked, the recorded duration is measured
from a server-stamped start to the server-received submission; the tests push the
server-recorded start five minutes into the past and confirm the stored duration
reflects that real interval, not a tiny forged browser value — while retaining the
browser's value only as a clearly labelled, non-authoritative reference. Further
tests confirm that the final run is recorded exactly once in the run history and
that the leaderboard's combined score correctly incorporates all four locations.

## 4. Security and tamper-resistance testing

Because participants interact with the application through a browser they fully
control, a naïve implementation could allow a participant to forge a passing score
— which would silently corrupt the study data. A significant body of integration
tests was therefore devoted to confirming that grading is
**server-authoritative**: the server, not the browser, chooses the questions,
stores them under an opaque attempt token in a durable database row, and grades
only that stored set. The tamper-resistance tests demonstrate that:

- **Forged duplicate keys cannot pass.** The classic exploit of claiming the Trial
  consisted of one known question repeated four times is defeated: the server
  ignores the browser's key list entirely and grades its own four keys, so one
  known answer scores at most one out of four.
- **A partial submission does not shrink the graded set.** Answering only one of
  four served questions still grades all four, with the missing three marked wrong.
- **Attempt tokens are validated.** An unknown or forged attempt id is rejected; a
  token belonging to a *different* user cannot be graded (an ownership check); and
  a malformed stored key-set (too few, too many, or containing a duplicate) is
  refused rather than mis-graded.
- **An attempt can be graded only once.** A replayed submission does not
  double-log, and the answer-commit endpoint locks in the first committed answer so
  it cannot be used to fish for the correct option.
- **The answer key is never sent to the browser.** A test asserts that the Trial
  page contains no `data-correct` attribute and no browser-trusted list of shown
  keys, so the correct answers are never present in the delivered page.
- **Unknown or malicious identifiers are rejected.** Progress and reading endpoints
  ignore bogus item identifiers — including a SQL-injection-style string — while
  accepting only genuine ones, and identifiers beyond a location's real content
  range are refused.

Together these tests provide concrete evidence that a participant cannot inflate a
Trial or post-test score by manipulating requests, which is a precondition for
trusting the collected data.

## 5. Regression testing

Part-way through development the codebase underwent a structured senior-engineer
audit that catalogued defects by severity. Several of the resulting fixes were
locked in with dedicated regression tests, so that a corrected defect could not
silently return. The most notable is the Observatory star-persistence defect
(audit item *H1*): the location had been expanded from five to ten constellation
stars, but a hard-coded range meant the last five were silently dropped, so a
learner who completed all ten, navigated away, and returned found the last five
un-lit and the Trial re-locked. The regression test now confirms that every star
identifier up to the location's real, content-derived count is accepted and
persisted across navigation, while identifiers beyond that count are rejected. The
content-integrity module additionally guards the same defect at the source level
by asserting the star count is consistent across the JavaScript and the server
hooks and that the Trial unlock derives from the full star count. Other
audit-driven tests confirm the server-authoritative assessment timing (*M2*), the
database-level single-attempt constraint (*M6*), and the alignment of the tutor's
knowledge with the curriculum (*M3*, *M4*, *M5*).

## 6. Manual and exploratory testing

The automated suite was complemented by manual and exploratory testing of the
running application, which is necessary because some interactions cannot be
meaningfully automated at the unit or integration level. The complete participant
journey was walked through by hand in a browser — registration, the hub world-map,
each of the four locations in turn, the AI tutor interaction, and the final
assessment — to confirm that the experience rendered correctly, that the tutor
appeared and responded, and that the visual and audio ambience behaved as
intended. This manual playthrough was supported by a browser-automation tool
(Playwright) used in an *exploratory* capacity to inspect the live page structure
and confirm that the interface elements the journey depends on were present and
correctly wired.

Two interactions were identified during this process as genuinely difficult to
automate reliably: the Observatory's constellation, whose stars are drawn on an
HTML5 canvas and so are clicked by pixel coordinate rather than by a selectable
element, and the AI Lab's data-sorting exercise, which uses native HTML5
drag-and-drop. These were therefore verified by manual playthrough rather than by
scripted automation. This limitation is recorded honestly here rather than
concealed by a test that would have simulated success without truly exercising the
interaction; the underlying grading of both interactions is, however, covered by
the server-side integration tests (for example, the test confirming that the AI
Lab's sorting question is graded on the learner's real answer and is never awarded
as a free point).

## 7. Results

At the time of writing, the full automated suite of **109 tests passed with zero
failures**, completing in approximately four seconds. The only diagnostic output
was a set of non-fatal deprecation warnings originating from a third-party
dependency's handling of UTC timestamps, which do not affect correctness. The
suite is deterministic — it does not depend on network access, the language model,
wall-clock timing, or the developer's real database — and so produces the same
result on every run, which is a prerequisite for using it as continuous evidence
of the instrument's correctness.

Coverage was deliberately concentrated on the research-critical behaviour rather
than on maximising a line-coverage percentage: grading, gating, the single-attempt
assessment, condition assignment, tamper resistance, and data persistence are all
covered by explicit, intention-revealing tests, several of which are parametrised
across every location so that a new location inherits the same guarantees
automatically.

## 8. Limitations and threats to validity

Several limitations of the test process should be acknowledged. First, the two
canvas- and drag-and-drop-based interactions were verified manually rather than by
automated end-to-end tests, so there is no continuously executed guard against a
front-end regression in those specific interactions, although their server-side
grading is covered. Second, the tests exercise the AI tutor's *guardrails and
control flow* with the language model stubbed off; the qualitative quality of the
model's live responses was assessed manually rather than by automated assertion,
since natural-language output is not amenable to exact-match testing. Third, the
integration tests run against SQLite in memory; while this matches the deployment
database engine, it does not reproduce the concurrency behaviour of a
multi-user production database server, so the concurrency guarantees are argued
from the database-level unique constraint rather than from a load test. Finally,
the suite prioritises correctness of the measurement-critical paths over
exhaustive coverage of purely cosmetic or presentational code, which was instead
checked by manual inspection.

## 9. Reproducibility

The entire automated suite is reproducible with a single command from the project
root:

```bash
python3 -m pytest
```

No additional setup is required: the tests create and tear down their own
in-memory database, require neither the language model nor network access, and are
independent of the developer's real data. This makes the suite suitable for
routine execution during development and for verification by an examiner wishing
to confirm the claims made in this chapter.
