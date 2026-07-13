# Atlas Quest — Assessment Blueprint (Post-Test Content Validity)

**Purpose.** This blueprint maps every Final Assessment question to (a) the learning objective it measures and (b) the location where that objective is taught. Its function is to guarantee **content validity**: no question tests a concept the game does not teach, and every major taught strand is assessed. This directly addresses **Problem 1 (content alignment)** and is a defensible artefact for the Evaluation/Design chapters.

**Design rule.** Every post-test item must trace to a taught objective in a specific location. Any item that cannot is either (i) taught by adding content, or (ii) replaced. In this revision, six previously-orphaned concepts are brought into scope by **teaching them** (Path A), so the objective coverage widens rather than the test narrowing.

---

## Curriculum framing (revised)

The curriculum is drawn from **IBM SkillsBuild "Introduction to AI"** as the exemplar source (foundations, history, data, machine learning) and **extended with modern generative-AI / LLM literacy** (language models, prompting, hallucination, bias). This extension is deliberate and coherent: **Professor Atlas is itself a large language model**, so teaching learners what LLMs are, how prompting works, and how models fail (hallucination, bias) is self-referential and pedagogically motivated — the tutor guiding the learner is an instance of the very technology being taught.

This reframing also corrects the earlier Objective 2 wording: rather than removing "generative AI and prompting," the objective now legitimately covers it, because the game teaches it.

> **Revised Objective 2 (for the report):** *"Design a narrative game whose structure is derived from the learning objectives of an introductory AI curriculum — using IBM SkillsBuild as the exemplar source and extended with modern generative-AI and LLM literacy — covering the foundations and history of AI, data, machine learning, and language models, across distinct thematic locations."*

---

## Where the 6 previously-orphaned concepts are now taught (Path A)

No new location is added. The six concepts fold into existing locations:

| Concept | Now taught in | Rationale |
|---|---|---|
| Overfitting | **Observatory** (ML) | It's a machine-learning concept; sits with supervised/unsupervised/reinforcement. |
| Historical-data bias | **Observatory** (ML) | A property of how models learn from data; ML-adjacent. |
| Natural Language Processing (NLP) | **Observatory** — new "Modern Language AI" beat | Part of the modern-AI cluster; how machines handle human language. |
| Large Language Models (LLMs) | **Observatory** — new "Modern Language AI" beat | Self-referential to Professor Atlas. |
| Hallucination | **Observatory** — new "Modern Language AI" beat | A key LLM failure mode; ties to Atlas's own limitations. |
| Few-shot prompting | **Observatory** — new "Modern Language AI" beat | How you steer an LLM; practical AI literacy. |

The Observatory gains a compact **"Modern Language AI"** content module (NLP → LLMs → hallucination → few-shot prompting) plus **overfitting** and **bias** added to its ML content. Each new concept gets taught text + a quick-check, consistent with the location's existing pattern.

---

## The assessment blueprint (10 questions → objective → location)

Every major taught strand is represented; the test now spans all four locations plus the modern-AI extension. Target: 2–3 items per major strand, no orphans.

| Q# | Chapter | Objective measured | Taught in | Concept |
|---|---|---|---|---|
| 1 | I — Foundations | Define AI; distinguish it from ordinary software | Library | What AI is |
| 2 | I — Foundations | Distinguish narrow / broad / general AI | Library | Three levels of AI |
| 3 | I — Foundations | Explain augmented intelligence (AI assists, human decides) | Library | Augmented intelligence |
| 4 | II — History | Order the three eras; identify AI-Winter causes | Chronicle | Eras of computing / AI Winters |
| 5 | II — History | Identify a key AI milestone (e.g. Deep Blue 1997) | Chronicle | AI history milestones |
| 6 | III — Data | Distinguish structured / unstructured / dark data | AI Lab | Data types |
| 7 | III — Data | Explain why most data is hard for traditional computers | AI Lab | Unstructured data / why ML |
| 8 | IV — Machine Learning | Match a scenario to supervised / unsupervised / reinforcement | Observatory | ML methods |
| 9 | IV — Machine Learning | Distinguish deterministic vs probabilistic; recognise overfitting | Observatory | Probabilistic ML / overfitting |
| 10 | V — Modern Language AI | Identify an LLM concept: hallucination, few-shot prompting, or bias | Observatory (Modern AI beat) | LLMs / prompting / bias |

**Coverage check:**
- Library (Module 1): Q1, Q2, Q3 ✓
- Chronicle (Module 2 / history): Q4, Q5 ✓ *(previously untested — now covered)*
- AI Lab (Module 3 / data): Q6, Q7 ✓ *(previously untested — now covered)*
- Observatory (Modules 4–5 / ML): Q8, Q9 ✓
- Modern Language AI (extension): Q10 ✓ *(the orphan cluster — now taught AND tested)*

Every question now maps to a taught objective in a named location. No concept is tested that isn't taught; no major strand is left unassessed.

---

## Content-validity statement (for the dissertation)

> The Final Assessment was aligned to the taught curriculum via an assessment blueprint mapping each item to a learning objective and its location of instruction. An initial review identified six concepts (overfitting, NLP, LLMs, hallucination, few-shot prompting, and historical-data bias) that were assessed but not taught, and several taught strands (AI history, data types) that were not assessed. To restore content validity, the six concepts were incorporated into the taught curriculum — extending the IBM-derived content with modern generative-AI and LLM literacy, coherent with the system's own LLM-based tutor — and the assessment was rebalanced so that every item traces to a taught objective and every major strand is represented. This ensures a low post-test score reflects a learning gap rather than exposure to untaught material.

---

## Notes for implementation

- Keep the post-test at **10 questions, 8/10 to pass** (unchanged), and the 4-chapter structure — now 5 conceptual strands mapped across the chapters (Foundations / History / Data / ML / Modern AI).
- Each new Observatory concept needs taught text + a quick-check (ungraded gate), consistent with the location's existing lesson pattern.
- Every post-test "correct" answer must be factually accurate and one of its options (your existing test suite checks the latter; this blueprint governs the former).
- This blueprint should be cited in the Design chapter as the mechanism ensuring Problem-1 content alignment.