"""
Professor Atlas — the NPC tutor.

Rule-based keyword responses for now, with a clear slot for an Ollama/Granite
LLM behind the OLLAMA_ENABLED config flag (Step 10).

Two hard rules:
  1. Professor Atlas NEVER gives a direct quiz answer — if a user asks for the
     answer, he responds with a Socratic deflection instead.
  2. He explains concepts to help the learner reason for themselves.

get_response() returns (text, is_fallback, source). `source` is "granite" when the
local LLM answered, else "rules" (a Socratic deflection, a keyword explanation, or
the generic fallback); it is the accurate engine-source signal shown in the UI and
logged. is_fallback stays True only for the generic catch-all reply (a narrower
flag) and must NOT be used to infer Granite-vs-rules.
"""

import random
import re

# ── Per-location concept explanations (keyword -> explanation) ──
KEYWORDS = {
    "library": {
        'augmented': "Augmented intelligence amplifies human judgement rather than replacing it. The AI does the heavy lifting (say, pre-screening loan applications) but a human keeps the final decision and the accountability. How is 'assisting' different from 'replacing'?",
        'narrow': "Narrow AI is built for one specific task and can't step outside it. Spam filters, face-unlock and chess engines are all narrow. Almost every AI you meet today is narrow.",
        'broad': "Broad AI (IBM's term) integrates several narrow components into one business process trained on an organisation's own data. A self-driving car combines vision, route-planning and decisions. It is available today.",
        'general': 'General AI would reason and transfer knowledge across any domain the way a human does, but it does not exist yet; it remains a long-term research goal. Why might answering many questions NOT make something general AI?',
        'analysis': 'AI really does two things. First, analysis: it examines large amounts of data to find hidden patterns. Then prediction acts on those patterns. Which everyday tools do you think rely on that?',
        'prediction': "Prediction is the second thing AI does. After analysing data for patterns, it predicts an outcome (a likely diagnosis, a suspicious charge, tomorrow's rain). Analysis finds the pattern; prediction acts.",
        'fraud': 'Fraud detection is a classic AI prediction: it learns the patterns in millions of transactions, then predicts which new charge looks like theft.',
        'artificial intelligence': "Artificial intelligence is a machine's ability to learn patterns from data and make predictions. It adds to human judgement rather than replacing it, and much of it works invisibly inside apps you already use.",
    },
    "chronicle": {
        'tabulation': 'The Era of Tabulation was about sorting raw data into structured tables so patterns could surface: the leap beyond mere counting. How is organising data different from a machine that learns from it?',
        'eras': 'There are three eras of computing: Tabulation (sorting data), Programming (instructions, like ENIAC and Apollo), and AI (machines that learn). Can you place them in order and say what each one added?',
        'eniac': "ENIAC was a 1940s programmable computer that computed artillery tables. Yet even fast programmable machines drowned in data. Why couldn't programs alone keep up?",
        'dartmouth': 'In 1956 at Dartmouth College, McCarthy and Minsky coined the term artificial intelligence, claiming intelligence could be described precisely enough to simulate. Why was naming the field such a turning point?',
        'winter': 'An AI Winter is a period when funding and interest collapsed. The first came from two limits: too little calculating power and too little storage. What do you think it takes to end a winter?',
        'expert systems': 'Expert systems were 1980s rule-based programs on million-dollar mainframes. They boomed, then cheaper personal computers overtook them and the market collapsed. What does that tell you about betting everything on costly hardware?',
        'deep blue': "Deep Blue was IBM's chess machine that beat the world champion in 1997, searching some 200 million positions a second. What did that prove about how far processing power had come?",
        'watson': "Watson was IBM's system that won Jeopardy! in 2011. How might answering open trivia differ from the closed rules of chess?",
    },
    "ai_lab": {
        'unstructured': 'Unstructured data has no built-in schema and is kept in its native form: emails, PDFs, images, audio, chat logs. An estimated 80–90% of enterprise data looks like this, which is exactly why AI is needed to make sense of it.',
        'semi-structured': 'Semi-structured data sits between the two: it carries tags, keys or metadata that make it machine-readable without a rigid table. JSON, XML and CSV are the classic examples.',
        'semi structured': 'Semi-structured data carries tags or keys (like JSON or XML) that give partial organisation without a rigid schema, a bridge between structured tables and raw unstructured content.',
        'structured': 'Structured data is highly organised in rows and columns (names, ages, dates, account balances) and is easily queried with SQL. Which everyday file format fits that description?',
        'dark data': 'Dark data is information that is collected and stored but never used. It can be any type (even tidy structured records count if they sit unqueried), and studies suggest it is more than half of enterprise data.',
        'data': 'Data comes in three types: structured (neat rows and columns), unstructured (emails, images, audio, no schema), and semi-structured (tagged formats like JSON). Most enterprise data is unstructured.',
        'tabulation': 'The Era of Tabulation was about sorting raw data into structured tables so patterns could surface. It was the first step, long before machines could learn from data.',
        'programming': 'The Era of Programming brought machines that follow instructions (programs), like ENIAC. But the world soon generated more data than any program could process. A new approach was needed.',
        'eniac': "ENIAC was a 1940s programmable computer that ran wartime calculations. Even fast programmable machines, though, couldn't keep up with the flood of data. What finally could?",
    },
    "observatory": {
        'machine learning': "Machine learning is how AI learns patterns from data instead of following pre-written rules. It is probabilistic: it gives a confidence ('84% sure') rather than a flat yes/no, and can improve over time. How is learning from examples different from following instructions?",
        'unsupervised': 'Unsupervised learning works with UNLABELLED data. The model finds structure on its own, such as grouping similar customers, with no right answers provided. How might a model organise data nobody has labelled?',
        'supervised': "In supervised learning the training examples come with labels: the correct answer is provided (thousands of photos tagged 'dog'). The model learns the pattern, then predicts the label for new, unseen data.",
        'reinforcement': 'Reinforcement learning trains an agent through rewards and penalties as it acts in an environment, learning by trial and error, with no labelled answer key. Think game-playing agents and warehouse robots.',
        'overfitting': 'Overfitting is when a model memorises its training examples instead of learning the general pattern, so it scores high on training data but poorly on new, unseen data. What does that tell you about generalising?',
        'generalisation': 'Generalisation is how well a model performs on data it has never seen. Why might that matter more than performance on the training set itself?',
        'bias': 'Bias in machine learning often comes from the data: if the training data reflects historical or human biases, the model absorbs and can repeat them. A model is only as fair as what it learns from.',
        'deterministic': 'A deterministic system gives the same output for the same input every time, like a calculator, or braking logic. That predictability is ideal where you cannot tolerate surprises.',
        'probabilistic': "A probabilistic system expresses outputs as likelihoods ('78% chance this scan shows a tumour') rather than a flat yes/no. Why is expressing uncertainty often safer than false certainty?",
        'natural language': 'Natural language processing (NLP) is how machines work with human language: reading, understanding and generating text or speech. It powers translation, chatbots, voice assistants and spam filters.',
        'nlp': 'NLP (natural language processing) lets AI handle messy human language (emails, chat, speech) that has no fixed structure. Where have you seen it in everyday tools?',
        'large language model': 'A large language model is trained on vast amounts of text and generates language by predicting what is most likely to come next; it predicts fluent language rather than looking facts up. Atlas uses a local one when available.',
        'llm': "An LLM (large language model) generates language by predicting the next piece of text from patterns it learned in training. What does 'predicting the next word' suggest about how it forms answers?",
        'hallucination': 'A hallucination is when a language model produces a confident, fluent answer that is actually false. Because it predicts likely words rather than checking a source, confidence is not proof; always verify.',
        'few-shot': 'Few-shot prompting means giving a model a few worked examples of what you want before your real request, so it can follow the pattern. A few examples often beat asking with none (zero-shot).',
        'prompting': 'Prompting is the craft of phrasing your request well: giving examples, context or step-by-step guidance often improves results. What might a few worked examples do for the model?',
        'prompt': 'A prompt is the instruction or context you give a model. Small changes in wording can change the output a lot. Why might that be?',
        'generative': 'Generative AI creates new content (text, images, code) rather than just classifying existing data. It produces, instead of merely sorting.',
    },
}

# ── Detecting "just tell me the answer" requests ──
ANSWER_REQUEST_PATTERNS = [
    r"what('?s| is) the (correct )?answer",
    r"which (option|one|answer|choice)",
    r"\bis it [abcd]\b",
    r"tell me the answer",
    r"give me the answer",
    r"just tell me",
    r"what should i (pick|choose|select|answer)",
    r"the (right|correct) (option|choice|one)",
    r"answer to (q|question)",
]

SOCRATIC_DEFLECTIONS = [
    "Ah, a tempting shortcut, but I will not simply hand you the answer. Tell "
    "me instead: what is the question really testing?",
    "A true scholar reasons it out. Rather than the answer, let me ask you: which "
    "options can you rule out, and why?",
    "I am here to sharpen your thinking, not to replace it. What does your "
    "instinct say, and what makes you uncertain?",
    "The answer means little without the understanding behind it. Walk me through "
    "your reasoning and I will help you test it.",
    "Patience, explorer. If you can explain each option in your own words, the "
    "right one often reveals itself. Shall we try?",
]

FALLBACK = (
    "An interesting question. I am Professor Atlas, keeper of this place. Ask me "
    "about the concepts in this location and I will help you understand them. Try "
    "naming a term you have met here and we will explore it together."
)


def _looks_like_answer_request(message):
    text = message.lower()
    return any(re.search(p, text) for p in ANSWER_REQUEST_PATTERNS)


def get_response(location, message, ollama_enabled=False, recent_mistakes=None, history=None):
    """Return (response_text, is_fallback, source).

    source is "granite" when the local LLM produced this reply, otherwise "rules"
    (a Socratic deflection, a keyword explanation, or the generic fallback). It is
    the accurate "which engine answered" signal for the UI label and the research
    log, set at the point each path returns and never recomputed downstream. Note
    that is_fallback is NOT this signal: it is True only for the generic catch-all,
    so a rule-based keyword reply has is_fallback False, just like a Granite reply.

    recent_mistakes: optional list of question STEMS (no options/answers) the learner
    recently got wrong here — used to scaffold (ZPD). history: optional list of prior
    turns (dicts or objects with user_message/npc_response) for conversational memory.
    Both default to None so existing callers keep working.
    """
    # Rule 1: never give the answer — enforced FIRST, BEFORE any LLM call.
    # An answer-seeking message ("is it B?", "just tell me the answer") is
    # deflected deterministically and is never sent to the model, so the
    # no-answer guardrail holds identically whether or not Ollama is enabled
    # (previously this ran only on the rule-based fallback path, leaving the LLM
    # path guarded by the system prompt alone).
    if _looks_like_answer_request(message):
        return random.choice(SOCRATIC_DEFLECTIONS), False, "rules"

    # Step 10 slot: when enabled, defer to the local LLM. Only non-answer-seeking
    # messages reach here, so the model is never the sole line of defence against
    # handing over a Trial answer.
    if ollama_enabled:
        llm_text = _query_ollama(location, message, recent_mistakes, history)
        if llm_text:
            return llm_text, False, "granite"
        # If the LLM is unavailable, fall through to the rule-based engine.

    # Rule 2: explain a concept if a keyword is mentioned.
    text = message.lower()
    for keyword, explanation in KEYWORDS.get(location, {}).items():
        if keyword in text:
            return explanation, False, "rules"

    # Nothing matched.
    return FALLBACK, True, "rules"


# ── Granite RAG: course knowledge + locked-down system prompt ──
# Professor Atlas may ONLY answer from the relevant location's content below.
COURSE_KNOWLEDGE = {
    "library": """
What is AI:
Artificial intelligence (AI) refers to the ability of a machine to learn patterns and make predictions. AI does not replace human decisions; instead, AI adds value to human judgement. In its simplest form, AI is a field that combines computer science and large datasets to enable problem-solving. AI plays an often invisible role in everyday life, powering search engines, recommendations, and speech recognition systems.

AI vs Augmented Intelligence:
Augmented intelligence has a modest goal of helping humans with tasks that are not practical to do (for example, reading 1000 pages in an hour). In contrast, AI has a loftier goal of mimicking human thinking and processes. AI today is not mature enough to perform independent tasks such as diagnosing cancer.

What Does AI Do:
AI services perform two core actions. First, Analysis: they examine large amounts of data to find hidden patterns. Second, Prediction: based on that analysis, AI predicts an outcome. That analysis and those predictions can have an enormous impact on human life.

What Predictions Can AI Make:
Vision recognition: AI helps doctors identify serious diseases based on unusual symptoms. It also reads speed limit and stop signs for self-driving cars. Fraud detection: AI analyses patterns in bank transactions to predict identity theft. Customer service: AI predicts answers to questions about shipping, business hours, merchandise, and sizes.

How is AI Evolving:
Three levels of AI exist. Narrow AI performs one specific task. Broad AI handles multiple domains; most enterprises use Broad AI today. General AI would have human-level general intelligence but will not come online until sometime in the future. Both Narrow AI and Broad AI are available right now.
""",
    "chronicle": """
The Era of Tabulation:
For centuries people struggled to read meaning in large amounts of data. The first breakthrough was sorting, not thinking: tabulating machines organised raw data into structured tables so patterns could surface. This was the leap beyond mere counting: from a heap of figures to a sum that revealed insight.

The Era of Programming:
In the 1940s came machines that could follow many instructions, called programs. ENIAC, built at the University of Pennsylvania, computed wartime artillery firing tables and ran an early thermonuclear feasibility study. Programmable computers later guided astronauts to the Moon and were reprogrammed during Apollo 13 to bring the crew home safely. But the world began generating more data than any program could process (the dark-data problem), outgrowing even the fastest supercomputer.

The Dawn of AI, Dartmouth 1956:
In the summer of 1956, John McCarthy and Marvin Minsky gathered researchers at Dartmouth College and coined the term artificial intelligence. They claimed every feature of intelligence could be described precisely enough for a machine to simulate it. Early programs proved geometry theorems, conversed in simple English, and solved algebra word problems.

The First Winter:
In the early 1970s, two limits froze progress: limited calculating power (machines were too slow) and limited information storage (they could not hold enough to reason about the real world). Promises went unmet, and funding collapsed. This was the first AI Winter.

Expert Systems and the Second Winter:
In the 1980s, expert systems (rule-based programs capturing a specialist's knowledge) boomed on mainframes costing up to a million dollars. But by the late 1980s cheaper personal computers from Apple and IBM overtook them, the market collapsed, and more than 300 AI companies went bankrupt. This was the second AI Winter.

The Thaw:
By the mid-1990s, processing power finally caught up with ambition. In 1997 IBM's Deep Blue, searching about 200 million chess positions per second, defeated the reigning world chess champion. In 2005 a Stanford robot drove 131 miles of desert road on its own. In 2011 IBM's Watson beat the champions of Jeopardy! The two Winters had ended.
""",
    "ai_lab": """
The Era of Tabulation:
For centuries, people struggled to understand the meaning hidden in large amounts of data. Early attempts involved manual counting and tabulation, organising numbers into tables by hand. This was slow and limited.

The Era of Programming:
In the 1940s, scientists built electronic computers like ENIAC at the University of Pennsylvania that could run multiple instructions (what we now call programs). Programmable computers guided astronauts to the Moon and were reprogrammed during Apollo 13 to bring astronauts safely home. But modern businesses generate so much data that even the finest programmable supercomputer cannot analyse it all. A new approach was needed.

The Era of AI:
In the summer of 1956, researchers at Dartmouth College led by John McCarthy and Marvin Minsky coined the term artificial intelligence. They proposed that every aspect of learning can be described precisely enough for a machine to simulate it. After two AI winters where funding collapsed, breakthroughs arrived: IBM Deep Blue beat the world chess champion in 1997, Watson defeated Jeopardy! champions in 2011. Today AI has proven its ability across fields from cancer research to energy production.

Types of Data:
Structured data is highly organised in rows and columns: names, dates, credit card numbers, spreadsheets. Unstructured data, also called dark data, has no built-in organisation: images, customer comments, medical records, social media posts. Semi-structured data is the bridge between the two; a video with hashtags is an example. About 80% of all data in the world today is unstructured, and AI is the only technology capable of making sense of it.
""",
    "observatory": """
What is Machine Learning:
Machine learning is the way AI solves the unstructured data problem. Traditional computers are deterministic: they say yes or no based on pre-written rules. Machine learning is probabilistic: it says I am 84% confident rather than yes or no. It constructs every possible answer and compares them in real time including changing variables. Machine learning can predict outcomes and can learn and improve by itself over time without being reprogrammed.

Supervised Learning:
Supervised learning provides AI with enough labelled examples to make accurate predictions. Labelled data is grouped into samples tagged with the correct answer. You tell the model what the key characteristics of a thing are and what the thing is. For example, thousands of photos labelled dog teach the machine the pattern for dog. When shown a new photo it has never seen, it identifies it as a dog with high accuracy. This is called a classification problem.

Unsupervised Learning:
In unsupervised learning, a machine is fed unlabelled data and finds patterns entirely by itself; no right or wrong answers are provided. A bank could feed customer financial data to an unsupervised algorithm and it would discover natural groupings of similar customers without being told what categories to create. It is ideal for customer segmentation, exploratory data analysis, and image recognition.

Reinforcement Learning:
Reinforcement learning works through trial and error. The algorithm learns by receiving positive rewards for correct predictions and penalties for incorrect ones. Over time its predictions grow more accurate automatically without any human intervention.

Three Levels of AI Revisited:
Narrow AI specialises in one area: it can look up information it was trained on but cannot apply knowledge elsewhere. Broad AI, available today, can structure vast amounts of unstructured data and find patterns to extend human expertise. General AI, expected perhaps 25 years from now, would be superintelligent, smarter than the best human brains in practically every field including scientific creativity, general wisdom, and social skills.

Overfitting:
Overfitting is when a model memorises its training examples instead of learning the general pattern behind them. Such a model scores very high on the data it was trained on but does poorly on new, unseen data, because it never learned to generalise. Good models are judged on how well they perform on data they have not seen before.

Bias in Training Data:
A model only learns from the data it is given, so if that data reflects historical or human biases, the model absorbs those biases and can repeat them in its predictions. This is why representative, carefully chosen training data matters: a model is only as fair as what it learns from.

Natural Language Processing (NLP):
Natural language processing is how machines work with human language: reading, understanding and generating text or speech. Because human language has no fixed structure, NLP is what lets AI handle messy inputs like emails, chat messages, reviews and voice. It powers translation, chatbots, voice assistants and spam filters.

Large Language Models (LLMs):
A large language model is trained on vast amounts of text and generates language by predicting what is most likely to come next, one piece at a time. It predicts fluent language rather than looking facts up in a database. Professor Atlas uses a local large language model when one is available to help explain these lessons.

Hallucination:
A hallucination is when a language model produces a confident, fluent answer that is actually false. Because an LLM predicts likely words rather than checking a source of truth, its confidence is not proof that it is correct. Always verify important claims against reliable sources, including anything this tutor tells you.

Few-Shot Prompting:
Few-shot prompting means giving a model a few worked examples of what you want before your real request, so it can follow the pattern you have shown. Providing a handful of examples often produces better, more consistent results than asking with no examples at all (which is called zero-shot).
""",
}

SYSTEM_PROMPT = """You are Professor Atlas, a tutor inside the Atlas Quest educational game.

Your knowledge is strictly and exclusively limited to the IBM Introduction to Artificial Intelligence course content provided to you below. You have no other knowledge. You do not know anything that is not in the course content.

STRICT RULES:
1. Only answer using information from the COURSE CONTENT section below
2. If a question cannot be answered from that content, respond with exactly: That is beyond what we have covered in this course. Try asking me about the topics in the lesson above.
3. Never give direct quiz answers. If a student asks for an answer, respond with a Socratic question that helps them think it through
4. Stay in character as Professor Atlas at all times
5. Keep answers concise: 2 to 4 sentences maximum
6. When the learner answers correctly or seems close, occasionally ask them to explain WHY the other options are wrong, to deepen understanding

COURSE CONTENT:
{relevant_content}

Remember: you can ONLY draw from the course content above. Nothing else."""


def _query_ollama(location, message, recent_mistakes=None, history=None):
    """Ask Granite (via Ollama) to answer ONLY from this location's course content,
    scaffolded to the learner's recent mistakes and the last few turns of dialogue.

    Returns the generated text, or None on any failure so get_response() can fall
    back to the rule-based engine.
    """
    from flask import current_app
    import requests

    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = current_app.config.get("OLLAMA_MODEL", "granite3.3:8b")
    timeout = current_app.config.get("OLLAMA_TIMEOUT", 10)

    relevant_content = COURSE_KNOWLEDGE.get(location, "No content available for this location.")
    system = SYSTEM_PROMPT.format(relevant_content=relevant_content)

    # Adaptive tutoring (ZPD): steer toward concepts the learner recently struggled
    # with. STEMS ONLY — never options/answers; the no-answer rule above still wins.
    if recent_mistakes:
        system += (
            "\n\nLEARNER CONTEXT: This learner recently struggled with the following "
            "questions. Gently steer them toward understanding these concepts using hints "
            "and questions. You must NEVER state or hint at the correct option for any quiz "
            "question.\n"
        )
        for stem in recent_mistakes:
            system += "- {}\n".format(stem)

    # Build the message list: system, then the last 3 turns, then the new message.
    messages = [{"role": "system", "content": system}]
    for turn in (history or [])[-3:]:
        if isinstance(turn, dict):
            um, nr = turn.get("user_message"), turn.get("npc_response")
        else:
            um, nr = getattr(turn, "user_message", None), getattr(turn, "npc_response", None)
        if um:
            messages.append({"role": "user", "content": um})
        if nr:
            messages.append({"role": "assistant", "content": nr})
    messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={"model": model, "messages": messages, "stream": False},
            timeout=timeout,
        )
        response.raise_for_status()
        text = (response.json().get("message", {}).get("content", "") or "").strip()
        return text or None
    except Exception:
        return None


# ── Professor Atlas' reply to a SEALED REFLECTION (shown read-only in the Journal) ──
# A reflection is the learner's own sentence, not a question, so the Socratic hint
# path in get_response() would deflect rather than acknowledge. This dedicated path
# builds an acknowledgement prompt for the SAME Granite backend and returns
# (text, source): "granite" when the LLM answered, else an authored "rules" reply.
# It NEVER raises: any LLM failure falls back to the authored reply, so sealing a
# reflection always succeeds even when Granite is offline.

# Authored fallbacks, one per location, tied to that location's reflection prompt.
# Used verbatim when Granite is unavailable (source "rules" -> "System generated").
REFLECT_FALLBACKS = {
    "library": (
        "You have held onto the key line: narrow AI is built for one task, while "
        "general AI, matching a person across many, is still only an idea. Keep that "
        "distinction clear and most of the hype sorts itself out."
    ),
    "chronicle": (
        "Well sealed. The Winters came when the promises ran ahead of the computing "
        "power and the data to back them; what thawed them was more of both, plus "
        "learning from examples instead of hand-written rules."
    ),
    "ai_lab": (
        "A fair thought to keep. Most of the world's data is unstructured, the text, "
        "images and sound that have no tidy rows or columns, which is exactly why "
        "learning from examples matters more than fixed rules."
    ),
    "observatory": (
        "Nicely put. Reinforcement learning has no answer key; it learns from reward "
        "and consequence, trying, missing and adjusting until the good moves outweigh "
        "the bad."
    ),
}
REFLECT_FALLBACK_GENERIC = (
    "A thought worth keeping. Hold onto it as you go; the clearest ideas are the "
    "ones you can say in a single sentence."
)


def reflect_response(location, prompt_text, reflection_text, ollama_enabled=False):
    """Return (response_text, source) for Professor Atlas' reply to a sealed reflection.

    source is "granite" only when the local LLM produced the reply, otherwise "rules"
    (an authored, location-appropriate acknowledgement). Never raises; always returns
    a usable reply so sealing succeeds whether or not Granite is running.
    """
    if ollama_enabled:
        text = _query_ollama_reflection(location, prompt_text, reflection_text)
        if text:
            return text, "granite"
    return REFLECT_FALLBACKS.get(location, REFLECT_FALLBACK_GENERIC), "rules"


def _query_ollama_reflection(location, prompt_text, reflection_text):
    """Ask Granite to acknowledge the learner's reflection in one or two sentences,
    drawing ONLY on this location's course content. Returns text, or None on any
    failure so reflect_response() can fall back to the authored reply."""
    from flask import current_app
    import requests

    base_url = current_app.config.get("OLLAMA_BASE_URL", "http://localhost:11434")
    model = current_app.config.get("OLLAMA_MODEL", "granite3.3:8b")
    timeout = current_app.config.get("OLLAMA_TIMEOUT", 10)

    relevant_content = COURSE_KNOWLEDGE.get(location, "No content available for this location.")
    system = (
        "You are Professor Atlas, a warm, encouraging guide in a museum of AI. The "
        "learner has just sealed a one-sentence reflection. Reply in ONE or TWO short "
        "sentences: affirm what they got right, then gently sharpen or extend it. Speak "
        "in plain, direct British English. Never grade, score or judge. Do not greet "
        "them or use their name. Do not use dashes. Draw only on the course content "
        "below and add nothing beyond it.\n\nCOURSE CONTENT:\n" + relevant_content
    )
    user = (
        'The reflection prompt was: "{}"\nThe learner wrote: "{}"\n'
        "Give your one or two sentence reply now."
    ).format(prompt_text, reflection_text)

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        text = (response.json().get("message", {}).get("content", "") or "").strip()
        return text or None
    except Exception:
        return None
