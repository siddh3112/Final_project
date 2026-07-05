"""
Professor Atlas — the NPC tutor.

Rule-based keyword responses for now, with a clear slot for an Ollama/Granite
LLM behind the OLLAMA_ENABLED config flag (Step 10).

Two hard rules:
  1. Professor Atlas NEVER gives a direct quiz answer — if a user asks for the
     answer, he responds with a Socratic deflection instead.
  2. He explains concepts to help the learner reason for themselves.

get_response() returns (text, is_fallback). is_fallback is True only when no
keyword matched and we fell back to the generic prompt — useful research data.
"""

import random
import re

# ── Per-location concept explanations (keyword -> explanation) ──
KEYWORDS = {
    "library": {
        "machine learning": (
            "Machine learning is an approach where a system learns patterns from "
            "data rather than being given explicit rules. Think about it: how is "
            "'learning from examples' different from 'following instructions'?"
        ),
        "supervised": (
            "In supervised learning the training examples come with labels — the "
            "right answer is provided during training. What role do you think those "
            "labels play while the model learns?"
        ),
        "unsupervised": (
            "Unsupervised learning works with data that has no labels — the model "
            "must find structure on its own, such as grouping similar items. How "
            "might a model organise data when nobody tells it the categories?"
        ),
        "training data": (
            "Training data is the experience a model learns from. Consider: if the "
            "data is incomplete or biased, what does that imply about what the model "
            "can possibly learn?"
        ),
        "overfitting": (
            "Overfitting is when a model memorises its training examples instead of "
            "learning the general pattern. What would you expect to happen when such "
            "a model meets brand-new data?"
        ),
        "generalisation": (
            "Generalisation is how well a model performs on data it has never seen. "
            "Why might that matter more than performance on the training set itself?"
        ),
        "neural network": (
            "A neural network is a model loosely inspired by the brain, built from "
            "layers of connected units that adjust as they learn. It is one method "
            "among many for finding patterns in data."
        ),
        "bias": (
            "Bias in machine learning often comes from the data: if history contains "
            "unfair patterns, a model can absorb them. Where do you think such "
            "patterns originate?"
        ),
        "algorithm": (
            "An algorithm is the procedure a model uses to learn from data. The same "
            "data with different algorithms can produce quite different results."
        ),
        "reinforcement learning": (
            "Reinforcement learning trains an agent through rewards and penalties as "
            "it acts in an environment — learning by trial and error rather than from "
            "labelled examples."
        ),
    },
    "chronicle": {
        "tabulation": (
            "The Era of Tabulation was about sorting raw data into structured tables so "
            "patterns could surface — the leap beyond mere counting. How is organising "
            "data different from a machine that learns from it?"
        ),
        "eras": (
            "There are three eras of computing: Tabulation (sorting data), Programming "
            "(instructions, like ENIAC and Apollo), and AI (machines that learn). Can you "
            "place them in order and say what each one added?"
        ),
        "eniac": (
            "ENIAC was a 1940s programmable computer that computed artillery tables. Yet "
            "even fast programmable machines drowned in data. Why couldn't programs alone "
            "keep up?"
        ),
        "dartmouth": (
            "In 1956 at Dartmouth College, McCarthy and Minsky coined the term artificial "
            "intelligence, claiming intelligence could be described precisely enough to "
            "simulate. Why was naming the field such a turning point?"
        ),
        "winter": (
            "An AI Winter is a period when funding and interest collapsed. The first came "
            "from two limits — too little calculating power and too little storage. What "
            "do you think it takes to end a winter?"
        ),
        "expert systems": (
            "Expert systems were 1980s rule-based programs on million-dollar mainframes. "
            "They boomed, then cheaper personal computers overtook them and the market "
            "collapsed. What does that tell you about betting everything on costly hardware?"
        ),
        "deep blue": (
            "Deep Blue was IBM's chess machine that beat the world champion in 1997, "
            "searching some 200 million positions a second. What did that prove about how "
            "far processing power had come?"
        ),
        "watson": (
            "Watson was IBM's system that won Jeopardy! in 2011. How might answering open "
            "trivia differ from the closed rules of chess?"
        ),
    },
    "ai_lab": {
        "computer vision": (
            "Computer vision lets machines interpret images and video — detecting "
            "objects, faces, or scenes. What kind of input does such a system rely on?"
        ),
        "nlp": (
            "Natural language processing (NLP) is how machines work with human "
            "language, written or spoken. Where have you seen this in everyday tools?"
        ),
        "natural language": (
            "Working with human language — understanding and generating it — is the "
            "domain of NLP. Think about translation, chatbots, and voice assistants."
        ),
        "recommendation": (
            "Recommendation systems suggest items by finding patterns in user "
            "behaviour and preferences. What data would such a system need to learn "
            "your taste?"
        ),
        "ethics": (
            "AI ethics asks whether a system is fair, transparent, and accountable. "
            "When a model affects people's lives, what responsibilities follow?"
        ),
        "fairness": (
            "Fairness concerns whether a model treats different groups equitably. If "
            "training data reflects historical bias, how might that surface in the "
            "model's decisions?"
        ),
    },
    "observatory": {
        "llm": (
            "A large language model is trained on vast amounts of text and generates "
            "language by predicting what comes next. What does 'predicting the next "
            "word' suggest about how it forms answers?"
        ),
        "large language model": (
            "Large language models learn statistical patterns across enormous text "
            "collections, then generate fluent language. They predict, rather than "
            "look up, their responses."
        ),
        "prompt": (
            "A prompt is the instruction or context you give a model. Small changes "
            "in wording can change the output a lot — why might that be?"
        ),
        "prompting": (
            "Prompting is the craft of phrasing your request well. Giving examples, "
            "context, or step-by-step guidance often improves results. What might a "
            "few worked examples do for the model?"
        ),
        "hallucination": (
            "A hallucination is when a model states something fluent and confident "
            "but false. Given how LLMs generate text, why can't confidence be trusted "
            "as truth?"
        ),
        "generative": (
            "Generative AI creates new content — text, images, code — rather than "
            "just classifying existing data. It produces, instead of merely sorting."
        ),
        "token": (
            "A token is a chunk of text (often part of a word) that a model reads and "
            "generates one at a time. Models build their output token by token."
        ),
        "gpt": (
            "GPT-style models are large language models that generate text by "
            "predicting the next token from patterns learned in training."
        ),
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
    "Ah, a tempting shortcut — but I will not simply hand you the answer. Tell "
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
    "An interesting question. I am Professor Atlas, keeper of this place — ask me "
    "about the concepts in this location and I will help you understand them. Try "
    "naming a term you have met here and we will explore it together."
)


def _looks_like_answer_request(message):
    text = message.lower()
    return any(re.search(p, text) for p in ANSWER_REQUEST_PATTERNS)


def get_response(location, message, ollama_enabled=False, recent_mistakes=None, history=None):
    """Return (response_text, is_fallback).

    recent_mistakes: optional list of question STEMS (no options/answers) the learner
    recently got wrong here — used to scaffold (ZPD). history: optional list of prior
    turns (dicts or objects with user_message/npc_response) for conversational memory.
    Both default to None so existing callers keep working.
    """
    # Step 10 slot: when enabled, defer to the local LLM.
    if ollama_enabled:
        llm_text = _query_ollama(location, message, recent_mistakes, history)
        if llm_text:
            return llm_text, False
        # If the LLM is unavailable, fall through to the rule-based engine.

    # Rule 1: never give the answer.
    if _looks_like_answer_request(message):
        return random.choice(SOCRATIC_DEFLECTIONS), False

    # Rule 2: explain a concept if a keyword is mentioned.
    text = message.lower()
    for keyword, explanation in KEYWORDS.get(location, {}).items():
        if keyword in text:
            return explanation, False

    # Nothing matched.
    return FALLBACK, True


# ── Granite RAG: course knowledge + locked-down system prompt ──
# Professor Atlas may ONLY answer from the relevant location's content below.
COURSE_KNOWLEDGE = {
    "library": """
What is AI:
Artificial intelligence (AI) refers to the ability of a machine to learn patterns and make predictions. AI does not replace human decisions — instead, AI adds value to human judgment. In its simplest form, AI is a field that combines computer science and robust datasets to enable problem-solving. AI plays an often invisible role in everyday life, powering search engines, recommendations, and speech recognition systems.

AI vs Augmented Intelligence:
Augmented intelligence has a modest goal of helping humans with tasks that are not practical to do — for example, reading 1000 pages in an hour. In contrast, AI has a loftier goal of mimicking human thinking and processes. AI today is not mature enough to perform independent tasks such as diagnosing cancer.

What Does AI Do:
AI services perform two core actions. First, Analysis — they examine large amounts of data to find hidden patterns. Second, Prediction — based on that analysis, AI predicts an outcome. That analysis and those predictions can have an enormous impact on human life.

What Predictions Can AI Make:
Vision recognition — AI helps doctors identify serious diseases based on unusual symptoms. It also reads speed limit and stop signs for self-driving cars. Fraud detection — AI analyses patterns in bank transactions to predict identity theft. Customer service — AI predicts answers to questions about shipping, business hours, merchandise, and sizes.

How is AI Evolving:
Three levels of AI exist. Narrow AI performs one specific task. Broad AI handles multiple domains — most enterprises use Broad AI today. General AI would have human-level general intelligence but will not come online until sometime in the future. Both Narrow AI and Broad AI are available right now.
""",
    "chronicle": """
The Era of Tabulation:
For centuries people struggled to read meaning in large amounts of data. The first breakthrough was sorting, not thinking: tabulating machines organised raw data into structured tables so patterns could surface. This was the leap beyond mere counting — from a heap of figures to a sum that revealed insight.

The Era of Programming:
In the 1940s came machines that could follow many instructions, called programs. ENIAC, built at the University of Pennsylvania, computed wartime artillery firing tables and ran an early thermonuclear feasibility study. Programmable computers later guided astronauts to the Moon and were reprogrammed during Apollo 13 to bring the crew home safely. But the world began generating more data than any program could process — the dark-data problem — outgrowing even the fastest supercomputer.

The Dawn of AI — Dartmouth 1956:
In the summer of 1956, John McCarthy and Marvin Minsky gathered researchers at Dartmouth College and coined the term artificial intelligence. They claimed every feature of intelligence could be described precisely enough for a machine to simulate it. Early programs proved geometry theorems, conversed in simple English, and solved algebra word problems.

The First Winter:
In the early 1970s, two limits froze progress: limited calculating power (machines were too slow) and limited information storage (they could not hold enough to reason about the real world). Promises went unmet, and funding collapsed. This was the first AI Winter.

Expert Systems and the Second Winter:
In the 1980s, expert systems — rule-based programs capturing a specialist's knowledge — boomed on mainframes costing up to a million dollars. But by the late 1980s cheaper personal computers from Apple and IBM overtook them, the market collapsed, and more than 300 AI companies went bankrupt. This was the second AI Winter.

The Thaw:
By the mid-1990s, processing power finally caught up with ambition. In 1997 IBM's Deep Blue, searching about 200 million chess positions per second, defeated the reigning world chess champion. In 2005 a Stanford robot drove 131 miles of desert road on its own. In 2011 IBM's Watson beat the champions of Jeopardy!. The two Winters had ended.
""",
    "ai_lab": """
The Era of Tabulation:
For centuries, people struggled to understand the meaning hidden in large amounts of data. Early attempts involved manual counting and tabulation — organising numbers into tables by hand. This was slow and limited.

The Era of Programming:
In the 1940s, scientists built electronic computers like ENIAC at the University of Pennsylvania that could run multiple instructions — what we now call programs. Programmable computers guided astronauts to the moon and were reprogrammed during Apollo 13 to bring astronauts safely home. But modern businesses generate so much data that even the finest programmable supercomputer cannot analyse it all. A new approach was needed.

The Era of AI:
In the summer of 1956, researchers at Dartmouth College led by John McCarthy and Marvin Minsky coined the term artificial intelligence. They proposed that every aspect of learning can be described precisely enough for a machine to simulate it. After two AI winters where funding collapsed, breakthroughs arrived — IBM Deep Blue beat the world chess champion in 1997, Watson defeated Jeopardy! champions in 2011. Today AI has proven its ability across fields from cancer research to energy production.

Types of Data:
Structured data is highly organised in rows and columns — names, dates, credit card numbers, spreadsheets. Unstructured data, also called dark data, has no built-in organisation — images, customer comments, medical records, social media posts. Semi-structured data is the bridge between the two — a video with hashtags is an example. About 80% of all data in the world today is unstructured, and AI is the only technology capable of making sense of it.
""",
    "observatory": """
What is Machine Learning:
Machine learning is the way AI solves the unstructured data problem. Traditional computers are deterministic — they say yes or no based on pre-written rules. Machine learning is probabilistic — it says I am 84% confident rather than yes or no. It constructs every possible answer and compares them in real time including changing variables. Machine learning can predict outcomes and can learn and improve by itself over time without being reprogrammed.

Supervised Learning:
Supervised learning provides AI with enough labelled examples to make accurate predictions. Labelled data is grouped into samples tagged with the correct answer. You tell the model what the key characteristics of a thing are and what the thing is. For example, thousands of photos labelled dog teach the machine the pattern for dog. When shown a new photo it has never seen, it identifies it as a dog with high accuracy. This is called a classification problem.

Unsupervised Learning:
In unsupervised learning, a machine is fed unlabelled data and finds patterns entirely by itself — no right or wrong answers are provided. A bank could feed customer financial data to an unsupervised algorithm and it would discover natural groupings of similar customers without being told what categories to create. It is ideal for customer segmentation, exploratory data analysis, and image recognition.

Reinforcement Learning:
Reinforcement learning works through trial and error. The algorithm learns by receiving positive rewards for correct predictions and penalties for incorrect ones. Over time its predictions grow more accurate automatically without any human intervention.

Three Levels of AI Revisited:
Narrow AI specialises in one area — it can look up information it was trained on but cannot apply knowledge elsewhere. Broad AI, available today, can structure vast amounts of unstructured data and find patterns to extend human expertise. General AI, expected perhaps 25 years from now, would be superintelligent — smarter than the best human brains in practically every field including scientific creativity, general wisdom, and social skills.
""",
}

SYSTEM_PROMPT = """You are Professor Atlas, a tutor inside the Atlas Quest educational game.

Your knowledge is strictly and exclusively limited to the IBM Introduction to Artificial Intelligence course content provided to you below. You have no other knowledge. You do not know anything that is not in the course content.

STRICT RULES:
1. Only answer using information from the COURSE CONTENT section below
2. If a question cannot be answered from that content, respond with exactly: That is beyond what we have covered in this course. Try asking me about the topics in the lesson above.
3. Never give direct quiz answers. If a student asks for an answer, respond with a Socratic question that helps them think it through
4. Stay in character as Professor Atlas at all times
5. Keep answers concise — 2 to 4 sentences maximum
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
            "\n\nLEARNER CONTEXT — This learner recently struggled with the following "
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
