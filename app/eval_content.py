"""
Post-test content for Atlas Quest.

This is the ONLY knowledge test in the study. It appears on the hub only after
all three locations are passed, and tests material from all three locations.
10 multiple-choice questions.

Each question carries a "chapter" tag (1-4) used purely for the cinematic "Final
Ascent" presentation — the question text, options and correct answers are
unchanged, and scoring is unaffected. An "explanation" line is shown only in the
post-submit learning review (never during the graded test).
"""

# Chapter titles for the cinematic 4-act structure.
CHAPTER_TITLES = {
    1: "Foundations",
    2: "The Data Deep",
    3: "The Learning Machines",
    4: "Final Synthesis",
}

POST_TEST = [
    {
        "key": "p1",
        "chapter": 1,
        "question": "What is artificial intelligence best described as?",
        "options": {
            "A": "Software that can only do tasks it was explicitly programmed to do",
            "B": "The simulation of human intelligence processes by machines",
            "C": "A type of database that stores large amounts of information",
            "D": "Hardware designed to run calculations faster than normal computers",
        },
        "correct": "B",
        "explanation": "AI is the simulation of human intelligence processes — reasoning, learning and perception — by machines, not just fixed pre-programmed steps.",
    },
    {
        "key": "p2",
        "chapter": 3,
        "question": "In supervised learning what does the supervision refer to?",
        "options": {
            "A": "A human watching the model train in real time",
            "B": "The model supervising other models",
            "C": "Labelled training examples that guide learning",
            "D": "Rules written by a programmer to control the model",
        },
        "correct": "C",
        "explanation": "The 'supervision' is the labelled training examples — each input paired with its correct answer — that guide the model's learning.",
    },
    {
        "key": "p3",
        "chapter": 3,
        "question": "Which of the following is an example of unsupervised learning?",
        "options": {
            "A": "Training a model to detect whether an email is spam using labelled examples",
            "B": "Grouping customers by purchasing behaviour without predefined categories",
            "C": "Teaching a robot to walk by rewarding it for moving forward",
            "D": "Using a pre-trained image model to classify new photos",
        },
        "correct": "B",
        "explanation": "Grouping customers with no predefined categories is unsupervised learning — it finds structure in unlabelled data (clustering).",
    },
    {
        "key": "p4",
        "chapter": 3,
        "question": "A model performs very well on training data but poorly on new test data. What problem does this describe?",
        "options": {
            "A": "Underfitting",
            "B": "Data leakage",
            "C": "Overfitting",
            "D": "Feature scaling",
        },
        "correct": "C",
        "explanation": "Excelling on training data but failing on new data is overfitting — the model memorised the training set instead of learning general patterns.",
    },
    {
        "key": "p5",
        "chapter": 1,
        "question": "Which technology allows computers to understand spoken and written human language?",
        "options": {
            "A": "Computer vision",
            "B": "Natural language processing",
            "C": "Reinforcement learning",
            "D": "Genetic algorithms",
        },
        "correct": "B",
        "explanation": "Natural language processing (NLP) is the field that lets computers understand and generate human language.",
    },
    {
        "key": "p6",
        "chapter": 2,
        "question": "What does a recommendation system like Netflix primarily rely on?",
        "options": {
            "A": "Human editors choosing content for each user",
            "B": "Patterns in user behaviour and preferences from historical data",
            "C": "A fixed list of popular items shown to everyone",
            "D": "Random selection from available content",
        },
        "correct": "B",
        "explanation": "Recommendation systems learn from patterns in your past behaviour and preferences in historical data to predict what you'll like.",
    },
    {
        "key": "p7",
        "chapter": 1,
        "question": "What is a large language model?",
        "options": {
            "A": "A database of every sentence ever written",
            "B": "A model trained on large amounts of text to generate and understand language",
            "C": "A translation program that converts code into human language",
            "D": "A robot that learns language by interacting with humans",
        },
        "correct": "B",
        "explanation": "A large language model is trained on huge amounts of text so it can understand and generate human language.",
    },
    {
        "key": "p8",
        "chapter": 4,
        "question": "When an LLM generates confident but factually incorrect information this is called a:",
        "options": {
            "A": "Training error",
            "B": "Bias spike",
            "C": "Hallucination",
            "D": "Context overflow",
        },
        "correct": "C",
        "explanation": "Confident but false output from a language model is called a hallucination — a key reason to verify AI answers.",
    },
    {
        "key": "p9",
        "chapter": 2,
        "question": "Which prompting technique involves giving the model a few examples of the desired input-output format before asking your question?",
        "options": {
            "A": "Zero-shot prompting",
            "B": "Chain-of-thought prompting",
            "C": "Few-shot prompting",
            "D": "System prompting",
        },
        "correct": "C",
        "explanation": "Providing a few worked examples before your question is few-shot prompting — the examples steer the model's output format.",
    },
    {
        "key": "p10",
        "chapter": 2,
        "question": "An AI hiring tool is found to favour male candidates. What is the most likely cause?",
        "options": {
            "A": "The model was too small to understand gender",
            "B": "Historical training data reflected existing human biases",
            "C": "The model was deliberately programmed to discriminate",
            "D": "The hardware running the model introduced random errors",
        },
        "correct": "B",
        "explanation": "The usual cause of biased AI is biased historical training data, which the model learns and then reproduces.",
    },
]
