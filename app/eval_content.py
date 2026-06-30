"""
Post-test content for Atlas Quest.

This is the ONLY knowledge test in the study. It appears on the hub only after
all three locations are passed, and tests material from all three locations.
10 multiple-choice questions.
"""

POST_TEST = [
    {
        "key": "p1",
        "question": "What is artificial intelligence best described as?",
        "options": {
            "A": "Software that can only do tasks it was explicitly programmed to do",
            "B": "The simulation of human intelligence processes by machines",
            "C": "A type of database that stores large amounts of information",
            "D": "Hardware designed to run calculations faster than normal computers",
        },
        "correct": "B",
    },
    {
        "key": "p2",
        "question": "In supervised learning what does the supervision refer to?",
        "options": {
            "A": "A human watching the model train in real time",
            "B": "The model supervising other models",
            "C": "Labelled training examples that guide learning",
            "D": "Rules written by a programmer to control the model",
        },
        "correct": "C",
    },
    {
        "key": "p3",
        "question": "Which of the following is an example of unsupervised learning?",
        "options": {
            "A": "Training a model to detect whether an email is spam using labelled examples",
            "B": "Grouping customers by purchasing behaviour without predefined categories",
            "C": "Teaching a robot to walk by rewarding it for moving forward",
            "D": "Using a pre-trained image model to classify new photos",
        },
        "correct": "B",
    },
    {
        "key": "p4",
        "question": "A model performs very well on training data but poorly on new test data. What problem does this describe?",
        "options": {
            "A": "Underfitting",
            "B": "Data leakage",
            "C": "Overfitting",
            "D": "Feature scaling",
        },
        "correct": "C",
    },
    {
        "key": "p5",
        "question": "Which technology allows computers to understand spoken and written human language?",
        "options": {
            "A": "Computer vision",
            "B": "Natural language processing",
            "C": "Reinforcement learning",
            "D": "Genetic algorithms",
        },
        "correct": "B",
    },
    {
        "key": "p6",
        "question": "What does a recommendation system like Netflix primarily rely on?",
        "options": {
            "A": "Human editors choosing content for each user",
            "B": "Patterns in user behaviour and preferences from historical data",
            "C": "A fixed list of popular items shown to everyone",
            "D": "Random selection from available content",
        },
        "correct": "B",
    },
    {
        "key": "p7",
        "question": "What is a large language model?",
        "options": {
            "A": "A database of every sentence ever written",
            "B": "A model trained on large amounts of text to generate and understand language",
            "C": "A translation program that converts code into human language",
            "D": "A robot that learns language by interacting with humans",
        },
        "correct": "B",
    },
    {
        "key": "p8",
        "question": "When an LLM generates confident but factually incorrect information this is called a:",
        "options": {
            "A": "Training error",
            "B": "Bias spike",
            "C": "Hallucination",
            "D": "Context overflow",
        },
        "correct": "C",
    },
    {
        "key": "p9",
        "question": "Which prompting technique involves giving the model a few examples of the desired input-output format before asking your question?",
        "options": {
            "A": "Zero-shot prompting",
            "B": "Chain-of-thought prompting",
            "C": "Few-shot prompting",
            "D": "System prompting",
        },
        "correct": "C",
    },
    {
        "key": "p10",
        "question": "An AI hiring tool is found to favour male candidates. What is the most likely cause?",
        "options": {
            "A": "The model was too small to understand gender",
            "B": "Historical training data reflected existing human biases",
            "C": "The model was deliberately programmed to discriminate",
            "D": "The hardware running the model introduced random errors",
        },
        "correct": "B",
    },
]
