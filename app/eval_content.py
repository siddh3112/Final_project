"""
Post-test content for Atlas Quest.

This is the ONLY knowledge test in the study. It appears on the hub only after
all four locations are passed, and tests material taught across them. 10
multiple-choice questions; 8/10 to pass (POST_TEST_PASS).

CONTENT VALIDITY (Assessment_Blueprint.md): every question carries a `concept`
key that must exist in game_content.TAUGHT_CONCEPTS — so no question tests a
concept the game doesn't teach (a coverage test enforces this). Each also carries
a "chapter" tag (1-4) used purely for the cinematic "Final Ascent" presentation;
the question text, options, correct answers and scoring are unaffected by it.
"""

# Chapter titles for the cinematic 4-act structure.
CHAPTER_TITLES = {
    1: "Foundations",
    2: "The Data Deep",
    3: "The Learning Machines",
    4: "Final Synthesis",
}

# Minimum correct answers (out of len(POST_TEST) = 10) to PASS the Final
# Assessment. Passing marks the Final Ascent conquered (post_test_done) and
# unlocks the certificate / Atlas Sage. Every attempt is still recorded for
# research regardless of pass/fail.
POST_TEST_PASS = 8

# Blueprint mapping (Assessment_Blueprint.md), 10 items across 5 strands folded
# into the 4 cinematic chapters:
#   Ch 1 Foundations  — Q1 what AI is · Q2 three levels · Q3 augmented ·
#                       Q4 eras/AI-Winters · Q5 milestone (Deep Blue)   [Library + Chronicle]
#   Ch 2 The Data Deep— Q6 data types · Q7 why unstructured data is hard [AI Lab]
#   Ch 3 The Learning Machines — Q8 ML method · Q9 overfitting          [Observatory]
#   Ch 4 Final Synthesis       — Q10 LLM hallucination                   [Observatory / Modern AI]
POST_TEST = [
    {
        "key": "p1", "chapter": 1, "concept": "what_is_ai",
        "question": "The Library taught that artificial intelligence is best described as a machine that…",
        "options": {
            "A": "follows a fixed set of hand-written rules and never changes",
            "B": "learns patterns from data to make predictions, adding to human judgement",
            "C": "simply stores large amounts of information for fast lookup",
            "D": "is just faster hardware for running ordinary calculations",
        },
        "correct": "B",
        "explanation": "AI learns patterns from data and makes predictions, adding to human judgement rather than replacing it, unlike ordinary software that only follows fixed, hand-written rules.",
    },
    {
        "key": "p2", "chapter": 1, "concept": "three_levels",
        "question": "Which statement about the three levels of AI is correct?",
        "options": {
            "A": "General AI already runs most businesses today",
            "B": "Narrow AI can transfer its skill to any new task",
            "C": "Broad AI integrates several narrow systems and is what's available today; General AI does not exist yet",
            "D": "General AI is what powers today's self-driving cars",
        },
        "correct": "C",
        "explanation": "Narrow AI does one task; Broad AI (IBM's term) integrates several narrow components and is what's used today; General AI (human-level across any domain) does not exist yet.",
    },
    {
        "key": "p3", "chapter": 1, "concept": "augmented_intelligence",
        "question": "An airport's software analyses live radar and aircraft data and recommends which flights to delay, but a human duty manager reviews every recommendation and makes the final decision. Which approach does this describe?",
        "options": {
            "A": "Augmented intelligence",
            "B": "Fully autonomous AI that makes the decisions itself",
            "C": "General AI",
            "D": "A deterministic rule-based system",
        },
        "correct": "A",
        "explanation": "Augmented intelligence supports human judgement rather than replacing it. The AI analyses the data, but a person makes the final decision and is accountable for it.",
    },
    {
        "key": "p4", "chapter": 1, "concept": "eras_and_winters",
        "question": "Both AI Winters followed the same underlying pattern. Which statement best captures WHY an AI Winter happens?",
        "options": {
            "A": "Bold promises outrun what the technology can actually deliver, so investment and confidence collapse",
            "B": "A government deliberately halts AI research over safety fears",
            "C": "Researchers fully solve AI, so further funding becomes unnecessary",
            "D": "A newer programming language makes the existing AI systems obsolete overnight",
        },
        "correct": "A",
        "explanation": "Each AI Winter began with big promises that the technology could not yet deliver. When the results fell short, investment and confidence collapsed. The cause was hype running ahead of what the machines could do, not government bans or a new programming language.",
    },
    {
        "key": "p5", "chapter": 1, "concept": "ai_milestones",
        "question": "The thaw brought a run of headline breakthroughs. Which IBM system defeated the human champions at the television quiz show Jeopardy! in 2011?",
        "options": {
            "A": "ENIAC",
            "B": "Deep Blue",
            "C": "Watson",
            "D": "The Stanford self-driving robot",
        },
        "correct": "C",
        "explanation": "In 2011 IBM's Watson beat the human champions of Jeopardy!, a milestone of the thaw. (ENIAC was a 1940s calculator; Deep Blue won at chess in 1997; the Stanford robot drove an unrehearsed desert course in 2005.)",
    },
    {
        "key": "p6", "chapter": 2, "concept": "data_types",
        "question": "Which of these is an example of UNSTRUCTURED data?",
        "options": {
            "A": "A spreadsheet of names, ages and account balances",
            "B": "A table of stock prices organised by date",
            "C": "Customer emails, photos and voice recordings",
            "D": "A database with fixed rows and columns",
        },
        "correct": "C",
        "explanation": "Unstructured data has no rows-and-columns schema (emails, images, audio). Structured data fits neat, SQL-queryable tables.",
    },
    {
        "key": "p7", "chapter": 2, "concept": "unstructured_data",
        "question": "An estimated 80–90% of enterprise data is unstructured. Why is that hard for traditional, rule-based computers?",
        "options": {
            "A": "It is just poorly organised data that behaves normally once it has been cleaned up",
            "B": "It has no fixed rows-and-columns schema, so rule-based programs cannot query it",
            "C": "There is simply far too much of it to fit inside a traditional relational database",
            "D": "Rule-based programs can read it, but doing so is only slower than reading structured data",
        },
        "correct": "B",
        "explanation": "Without a fixed schema, legacy tools (built for the structured ~10–20%) can't process the unstructured majority; machine learning/AI is what finally makes it usable.",
    },
    {
        "key": "p8", "chapter": 3, "concept": "ml_methods",
        "question": "A property firm holds records of 100,000 past house sales, each one labelled with the price the house finally sold for. It wants a model that predicts the sale price of a newly listed home. Which machine-learning method fits?",
        "options": {
            "A": "Supervised learning",
            "B": "Unsupervised learning",
            "C": "Reinforcement learning",
            "D": "Deterministic rule-based programming",
        },
        "correct": "A",
        "explanation": "The training records carry known answers, the actual sale prices, which is the hallmark of supervised learning. It learns how the inputs relate to the price, then predicts the price for a new, unseen house (a regression task).",
    },
    {
        "key": "p9", "chapter": 3, "concept": "overfitting",
        "question": "A model scores 99% on its training data but only 60% on new, unseen data. What has gone wrong?",
        "options": {
            "A": "Underfitting",
            "B": "Overfitting",
            "C": "Nothing, it is perfectly trained",
            "D": "Reinforcement learning",
        },
        "correct": "B",
        "explanation": "Overfitting: the model memorised its training examples instead of learning general patterns, so it fails on data it hasn't seen.",
    },
    {
        "key": "p10", "chapter": 4, "concept": "hallucination",
        "question": "Professor Atlas is itself a large language model. When an LLM produces a confident, fluent answer that is actually FALSE, this is called:",
        "options": {
            "A": "A hallucination",
            "B": "Overfitting",
            "C": "A bias",
            "D": "A false positive",
        },
        "correct": "A",
        "explanation": "A 'hallucination' is confident but false output from a language model, which is a good reason to check what any AI (including this tutor) tells you. (Bias is systematic skew inherited from training data; a false positive is a classification error. Neither names a made-up fact.)",
    },
]


# ── Closing cinematic (epilogue) — resolves the opening's "the Atlas has faded"
# arc after the player earns Atlas Sage. Presentation only; never scored. ──
EPILOGUE_LINES = [
    "The realms are restored. Foundations, data, and learning machines, all mapped.",
    "You crossed every trial, and the Atlas is whole again.",
    "You are no longer an explorer. You are an Atlas Sage.",
]
