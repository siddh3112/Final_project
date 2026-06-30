"""
Static game content for Atlas Quest.

LOCATIONS holds metadata + description + learn cards + learning objectives for
each location. QUIZZES holds the 4 quiz questions per location.

Pass threshold is hardcoded at 3/4 — see PASS_THRESHOLD.
"""

PASS_THRESHOLD = 3  # must score at least 3 out of 4 to pass a location

# Order matters: this defines the unlock chain (each unlocks the next).
LOCATION_ORDER = ["library", "ai_lab", "observatory"]

# ── Interactive Library books ──
# Each book is a multi-page lesson (intro → concept → example) ending in a
# low-stakes "quick check" that charges the Knowledge Core and unlocks a
# collectible flashcard. The location's 4-question Trial still gates unlocking.
# Authored from the IBM "Introduction to AI" Library content.
LIBRARY_BOOKS = [
    {
        "id": "ai",
        "title": "The Book of Artificial Intelligence",
        "concept": "Artificial Intelligence",
        "art": "🤖",
        "xp": 100,
        "pages": [
            {"type": "intro", "title": "The Book of Artificial Intelligence",
             "body": "Welcome to the Atlas Archive. Before you venture onward, you must grasp the foundation of it all — what we truly mean by 'artificial intelligence'."},
            {"type": "concept", "title": "What is AI?",
             "body": "Artificial intelligence is the ability of a machine to learn patterns from data and make predictions. It does not replace human judgement — it adds to it.",
             "keywords": ["learn patterns", "data", "predictions", "human judgement"]},
            {"type": "example", "title": "In the Real World",
             "body": "AI is mostly invisible. It quietly powers search engines, recommendations, and the voice assistant that understands your words.",
             "hint": "AI is not only robots. Most of it works quietly inside the apps you already use."},
        ],
        "quiz": {
            "question": "A music app suggests songs you might like based on what you've listened to. What is this an example of?",
            "options": ["A fixed, hand-made playlist", "Artificial intelligence finding patterns in your behaviour", "A random shuffle", "A staff member choosing for you"],
            "answer": 1,
            "explanation": "The app uses AI to learn patterns in your listening and predict songs you'll enjoy.",
        },
        "flashcard": {"type": "Core Concept", "rarity": "Common",
            "meaning": "A machine's ability to learn patterns from data and make predictions.",
            "example": "Search engines, recommendations, voice assistants.",
            "remember": "AI adds to human judgement — it doesn't replace it."},
    },
    {
        "id": "augmented",
        "title": "The Book of Augmented Intelligence",
        "concept": "Augmented Intelligence",
        "art": "🧩",
        "xp": 100,
        "pages": [
            {"type": "intro", "title": "The Book of Augmented Intelligence",
             "body": "Two ideas are often confused, explorer. Let me show you the difference between true AI and its humbler cousin."},
            {"type": "concept", "title": "AI vs Augmented Intelligence",
             "body": "Augmented intelligence helps humans with impractical tasks — like reading 1000 pages in an hour. True AI aims higher: to mimic human thinking itself.",
             "keywords": ["augmented", "assists humans", "mimic human thinking"]},
            {"type": "example", "title": "In the Real World",
             "body": "Augmented intelligence can scan thousands of medical records to surface clues. But AI today is not mature enough to diagnose on its own.",
             "hint": "Think of augmented intelligence as a powerful assistant — not a replacement."},
        ],
        "quiz": {
            "question": "A doctor uses a tool that reads 1,000 scans in minutes and flags unusual ones for review. This is best described as:",
            "options": ["General AI replacing the doctor", "Augmented intelligence assisting the doctor", "A simple search engine", "Reinforcement learning"],
            "answer": 1,
            "explanation": "It assists the human expert with an impractical task rather than replacing them — that is augmented intelligence.",
        },
        "flashcard": {"type": "Core Concept", "rarity": "Common",
            "meaning": "AI that assists humans with impractical tasks rather than replacing them.",
            "example": "Scanning 1000 pages in an hour to surface key facts.",
            "remember": "Augments, not replaces. Full AI aims to mimic human thinking."},
    },
    {
        "id": "does",
        "title": "The Book of Analysis & Prediction",
        "concept": "Analysis & Prediction",
        "art": "🔮",
        "xp": 100,
        "pages": [
            {"type": "intro", "title": "The Book of Analysis & Prediction",
             "body": "Every machine mind performs two great acts. Master them, and AI will hold no mystery for you."},
            {"type": "concept", "title": "What AI Does",
             "body": "AI does two things. First it analyses huge amounts of data to find hidden patterns. Then it predicts an outcome from those patterns.",
             "keywords": ["analysis", "patterns", "prediction"]},
            {"type": "example", "title": "In the Real World",
             "body": "From a flood of bank transactions, AI spots the pattern of fraud — then predicts which new charge is likely stolen.",
             "hint": "Analysis finds the pattern; prediction acts on it."},
        ],
        "quiz": {
            "question": "An AI studies years of weather data, then forecasts tomorrow's rain. Which part is the 'prediction'?",
            "options": ["Studying the years of past data", "Forecasting tomorrow's rain", "Storing the records", "Deleting old files"],
            "answer": 1,
            "explanation": "Analysis finds patterns in past data; forecasting tomorrow's rain is the prediction step.",
        },
        "flashcard": {"type": "Core Skill", "rarity": "Common",
            "meaning": "AI examines data to find patterns, then predicts an outcome.",
            "example": "Spotting fraud across millions of bank transactions.",
            "remember": "Two steps: analyse, then predict."},
    },
    {
        "id": "predict",
        "title": "The Book of Predictions",
        "concept": "AI Predictions",
        "art": "🛰️",
        "xp": 100,
        "pages": [
            {"type": "intro", "title": "The Book of Predictions",
             "body": "What can these predictions truly do? Let me show you their reach across our world."},
            {"type": "concept", "title": "The Power of Prediction",
             "body": "AI's predictions touch daily life: spotting disease from early symptoms, reading road signs for self-driving cars, and detecting fraud among millions of payments.",
             "keywords": ["vision recognition", "fraud detection", "customer service"]},
            {"type": "example", "title": "In the Real World",
             "body": "An AI vision system helps doctors catch a disease early; another reads a stop sign so a car can brake in time.",
             "hint": "The same skill — prediction — solves very different problems."},
        ],
        "quiz": {
            "question": "Your bank texts to ask if a sudden, unusual purchase was really you. Which AI skill is at work?",
            "options": ["Printing receipts", "Fraud detection predicting a suspicious payment", "Counting your coins", "Locking the front door"],
            "answer": 1,
            "explanation": "AI learns your spending patterns and predicts which payments look suspicious.",
        },
        "flashcard": {"type": "Application", "rarity": "Uncommon",
            "meaning": "AI applies prediction to vision, fraud detection, and customer service.",
            "example": "Catching fraud; reading road signs; answering support questions.",
            "remember": "One skill, many uses."},
    },
    {
        "id": "levels",
        "title": "The Book of the Three Levels",
        "concept": "The Three Levels of AI",
        "art": "🧠",
        "xp": 100,
        "pages": [
            {"type": "intro", "title": "The Book of the Three Levels",
             "body": "Finally, gaze toward the horizon. Artificial intelligence grows in three great stages."},
            {"type": "concept", "title": "Narrow, Broad & General",
             "body": "Narrow AI does one task well. Broad AI handles many domains — most companies use it today. General AI, with human-level intelligence, is still to come.",
             "keywords": ["Narrow AI", "Broad AI", "General AI"]},
            {"type": "example", "title": "In the Real World",
             "body": "A chess engine is Narrow AI. A system that organises a company's messy data is Broad AI. A machine that thinks like us across everything would be General AI — not yet here.",
             "hint": "Narrow and Broad are real today. General AI lies in the future."},
        ],
        "quiz": {
            "question": "A program plays chess brilliantly but can do nothing else. Which level of AI is it?",
            "options": ["General AI", "Narrow AI", "Broad AI", "Not AI at all"],
            "answer": 1,
            "explanation": "Excelling at a single task is Narrow AI — it cannot apply its skill elsewhere.",
        },
        "flashcard": {"type": "Core Concept", "rarity": "Rare",
            "meaning": "Narrow (one task), Broad (many domains), General (human-level, future).",
            "example": "Chess engine (Narrow); a data-organising system (Broad).",
            "remember": "Narrow & Broad: today. General: tomorrow."},
    },
]

# Professor Atlas's overall-game tutorial, shown as a focused overlay on the hub.
GAME_INTRO_STEPS = [
    "Greetings, traveller. I am Professor Atlas — and this is Atlas Quest, your journey through the world of Artificial Intelligence.",
    "This is your map. Each glowing waypoint is a place to explore. You begin at the Library; new regions reveal themselves as you prove yourself.",
    "Within each location you will study its knowledge, then face a Trial of four questions. Score at least 3 of 4 to open the road onward.",
    "As you learn, you earn XP and badges, and your rank rises — keep an eye on the banner above the map.",
    "Master all three locations to reveal the final assessment at the journey's end. I shall guide you the whole way. Onward, explorer!",
]

LOCATIONS = {
    "library": {
        "key": "library",
        "name": "The Library",
        "icon": "📚",
        "tagline": "Where knowledge begins",
        "topic": "What is Artificial Intelligence?",
        "description": "Ancient tomes line the walls of this vast chamber. Candlelight flickers across shelves that stretch beyond sight. This is where the story of intelligence begins — not human intelligence, but the kind we build. Professor Atlas waits by the fireplace, ready to guide you through the foundations of AI.",
        "order": 1,
        "stub": False,
        "accent": "#d4a84b",
        "theme": "archive",
        "interaction": "bookshelf",
        "books": LIBRARY_BOOKS,
        "guide_intro": "Welcome, seeker. Before any grand experiment or distant star, an explorer must first know what intelligence we seek to build. Turn each page with care — I shall be at your side.",
        "atlas_steps": [
            "Welcome to the Library, explorer. I am Professor Atlas. Knowledge hides among these shelves — most volumes are mere decoration, but a precious few glow with what you truly seek.",
            "Click each glowing tome to open and read it. Every one you study grants a Concept Card and charges the Knowledge Core — fill the Core to unlock the Trial.",
            "The Trial is four questions, asked one at a time; score 3 of 4 to journey onward. Need me? Tap the owl anytime. Now… begin your reading!",
        ],
        "learn_cards": [
            {
                "heading": "What is AI?",
                "text": "Artificial intelligence (AI) refers to the ability of a machine to learn patterns and make predictions. AI does not replace human decisions — instead, AI adds value to human judgment. In its simplest form, AI is a field that combines computer science and robust datasets to enable problem-solving. AI plays an often invisible role in everyday life, powering search engines, recommendations, and speech recognition systems."
            },
            {
                "heading": "AI vs Augmented Intelligence",
                "text": "When learning about AI, you will come across the term augmented intelligence. Both share the same objective but have different approaches. Augmented intelligence has a modest goal of helping humans with tasks that are not practical to do — for example, reading 1000 pages in an hour. In contrast, AI has a loftier goal of mimicking human thinking and processes. It is important to note that AI today is not mature enough to perform independent tasks such as diagnosing cancer."
            },
            {
                "heading": "What Does AI Do?",
                "text": "How do AI services work? Let us break it down into two parts. First, Analysis — AI examines large amounts of data to find hidden patterns. Second, Prediction — based on that analysis, AI predicts an outcome. It might not seem like much, but that analysis and those predictions can have an enormous impact on human life, from diagnosing illness to detecting fraud."
            },
            {
                "heading": "What Predictions Can AI Make?",
                "text": "Vision recognition: AI helps doctors identify serious diseases based on unusual symptoms and early-warning signs. It also reads speed limit and stop signs as it guides self-driving cars through traffic. Fraud detection: AI analyses patterns created when thousands of bank customers make credit card purchases, then predicts which charges might be the result of identity theft. Customer service: AI can predict which answers to give on topics ranging from shipping or business hours to merchandise and sizes."
            },
            {
                "heading": "How is AI Evolving?",
                "text": "Computer scientists have identified three levels of AI based on predicted growth in its ability to analyse data and make predictions. Narrow AI is designed to perform one specific task. Broad AI can handle multiple domains — most enterprises use Broad AI today. General AI would have human-level general intelligence but will not come online until sometime in the future. Both Narrow AI and Broad AI are available right now."
            }
        ],
        "learning_objectives": [
            "Define artificial intelligence",
            "Differentiate between AI and augmented intelligence",
            "Describe the two core actions AI performs",
            "Identify real-world predictions AI can make",
            "Describe the three levels of artificial intelligence"
        ]
    },

    "ai_lab": {
        "key": "ai_lab",
        "name": "The AI Lab",
        "icon": "🔬",
        "tagline": "Where theory becomes application",
        "topic": "The Three Eras of Computing and Data",
        "description": "Banks of humming machines fill the room. Screens display cascading streams of data. This is where you discover how humanity arrived at the age of AI — the history of computing, the problem of dark data, and why AI was the only answer.",
        "order": 2,
        "stub": False,
        "accent": "#3fd0e0",
        "theme": "lab",
        "interaction": "terminal",
        "guide_intro": "Mind the cables, explorer. In this lab, theory meets the world. Read on, and witness how machines learned to see, to listen, and to choose — and what we owe them in return.",
        "learn_cards": [
            {
                "heading": "The Era of Tabulation",
                "text": "People have analysed data for centuries. For centuries, humans struggled to understand the meaning hidden in large amounts of data. Early attempts involved manual counting and tabulation — organising numbers into tables by hand. This was slow, limited, and exhausting. The challenge of extracting meaning from vast amounts of data has always existed. Something had to change."
            },
            {
                "heading": "The Era of Programming",
                "text": "Data analysis changed in the 1940s. Scientists began building electronic computers like ENIAC at the University of Pennsylvania that could run more than one kind of instruction — what we now call programs. Programmable computers guided astronauts from Earth to the moon and were reprogrammed during Apollo 13 to bring astronauts safely home. But modern businesses and technology now generate so much data that even the finest programmable supercomputer cannot analyse it all before the heat-death of the universe. A new approach was needed."
            },
            {
                "heading": "The Era of AI",
                "text": "In the summer of 1956, researchers led by John McCarthy and Marvin Minsky gathered at Dartmouth College and coined the term artificial intelligence. They proposed that every aspect of learning or any feature of intelligence can be described precisely enough for a machine to simulate it. After two AI winters — periods when funding collapsed and hundreds of companies shut down — breakthroughs arrived. IBM's Deep Blue beat the world chess champion in 1997. Watson defeated Jeopardy! champions in 2011. Today AI has proven its ability across fields from cancer research to energy production. The winters of AI are over."
            },
            {
                "heading": "Structured, Semi-Structured, and Unstructured Data",
                "text": "Data can be organised into three types. Structured data is highly organised and stored in rows and columns — think spreadsheets, names, dates, credit card numbers. Unstructured data, also called dark data, has no built-in organisation — examples include images, customer comments, medical records, and social media posts. Semi-structured data is the bridge between the two — a video with hashtags is a good example, because the video itself is unstructured but the hashtags give it searchable structure. About 80% of all data in the world today is unstructured, and AI is the only technology capable of making sense of it."
            }
        ],
        "learning_objectives": [
            "Describe the three eras of computing",
            "Explain why programmable computers cannot solve the dark data problem",
            "Identify key milestones in the history of AI",
            "Differentiate between structured, unstructured, and semi-structured data",
            "Explain why unstructured data requires AI to process it"
        ]
    },

    "observatory": {
        "key": "observatory",
        "name": "The Observatory",
        "icon": "🔭",
        "tagline": "Where you look beyond the horizon",
        "topic": "Machine Learning",
        "description": "A vast glass dome opens to a sky full of stars. Every constellation is a pattern waiting to be recognised. This is where you learn how machines actually learn — not through rules written by humans, but through data, probability, and the remarkable process of teaching a machine to think.",
        "order": 3,
        "stub": False,
        "accent": "#3ab8d8",
        "theme": "cosmos",
        "interaction": "constellation",
        "guide_intro": "You have climbed high indeed. Beyond this glass lies the frontier — machines that create from pattern alone. Study closely, and learn to weigh their wonders against their flaws.",
        "learn_cards": [
            {
                "heading": "What is Machine Learning?",
                "text": "Machine learning is the way AI solves the unstructured data problem. Traditional programmable computers are deterministic — they say yes or no based on pre-written rules. Machine learning is probabilistic — it never says yes or no. Instead it says something like I am 84% confident this is the fastest route. It constructs every possible answer and compares them in real time, including all changing variables. Most importantly, machine learning can predict outcomes and it can learn and improve by itself over time without being reprogrammed."
            },
            {
                "heading": "Supervised Learning",
                "text": "Supervised learning is about providing AI with enough labelled examples to make accurate predictions. Labelled data is data grouped into samples tagged with the correct answer. You tell the model what the key characteristics of a thing are and what the thing actually is. For example, the machine is shown thousands of photos labelled dog. It learns to identify the pattern for dog. When shown a new photo it has never seen, it can correctly identify it as a dog with high accuracy. This is called a classification problem and it is at the heart of how image recognition, spam filters, and medical diagnosis tools work."
            },
            {
                "heading": "Unsupervised and Reinforcement Learning",
                "text": "In unsupervised learning, a machine is fed a large amount of unlabelled data and asked to find patterns entirely by itself — no right or wrong answers are provided. A bank could feed customer financial data to an unsupervised algorithm and it would discover natural groupings of similar customers without being told what categories to create. Reinforcement learning works through trial and error. The algorithm learns by receiving positive rewards for correct predictions and penalties for incorrect ones. Over time its predictions grow more accurate automatically, without any human intervention."
            },
            {
                "heading": "The Three Levels of AI Revisited",
                "text": "Now that you understand machine learning, the three levels of AI make deeper sense. Narrow AI specialises in one area — it can look up information it was trained on but cannot apply that knowledge elsewhere. Broad AI, available today, can structure vast amounts of unstructured data and find patterns to extend human expertise. General AI, expected perhaps 25 years from now, would be superintelligent — smarter than the best human brains in practically every field including scientific creativity, general wisdom, and social skills. It will give machines the ability to interact in genuinely human-like ways."
            }
        ],
        "learning_objectives": [
            "Define machine learning and explain what makes it different from traditional programming",
            "Distinguish between deterministic and probabilistic computation",
            "Describe supervised, unsupervised, and reinforcement learning with examples",
            "Explain how machine learning solves the unstructured data problem",
            "Describe what General AI is and when it is expected to arrive"
        ]
    }
}

QUIZZES = {
    "library": [
        {
            "key": "lib_q1",
            "question": "What does artificial intelligence (AI) refer to?",
            "options": {
                "A": "The ability of a machine to store and process large amounts of data",
                "B": "The ability of a machine to learn patterns and make predictions",
                "C": "Software that follows pre-written rules to complete specific tasks",
                "D": "Hardware designed to perform calculations faster than humans"
            },
            "correct": "B",
            "explanation": "AI refers to the ability of a machine to learn patterns and make predictions. Rather than replacing human decisions, AI adds value to human judgment.",
            "hint": "Does an intelligent machine merely follow fixed rules, or does it learn patterns from data and make predictions? Recall how the Library defined AI."
        },
        {
            "key": "lib_q2",
            "question": "What two core things do AI services do?",
            "options": {
                "A": "Store data and create algorithms",
                "B": "Secure systems and enforce rules",
                "C": "Analyse data and make predictions",
                "D": "Identify emotions and transfer information"
            },
            "correct": "C",
            "explanation": "AI services analyse data and based on that analysis make predictions. These two actions — analysis and prediction — can have an enormous impact on human life.",
            "hint": "Every AI service has a two-step rhythm — one step studies the data to find patterns, the next looks ahead. What were those two steps called in your reading?"
        },
        {
            "key": "lib_q3",
            "question": "What is the key difference between AI and augmented intelligence?",
            "options": {
                "A": "Augmented intelligence is more powerful and will eventually replace AI",
                "B": "AI helps with simple tasks while augmented intelligence handles complex ones",
                "C": "AI aims to mimic human thinking while augmented intelligence helps humans with tasks not practical to do",
                "D": "There is no real difference — they are the same technology with different names"
            },
            "correct": "C",
            "explanation": "Augmented intelligence has a modest goal of helping humans with impractical tasks like reading 1000 pages in an hour. AI has the loftier goal of mimicking human thinking and processes.",
            "hint": "One of these merely assists humans with impractical tasks; the other aims to mimic human thinking itself. Which description fits augmented intelligence?"
        },
        {
            "key": "lib_q4",
            "question": "Which statement about the three levels of AI is correct?",
            "options": {
                "A": "All three levels — Narrow, Broad, and General — are available today",
                "B": "Only Narrow AI is available today, Broad and General AI are still in development",
                "C": "Narrow AI and Broad AI are available today, General AI is still in the future",
                "D": "General AI is the most commonly used type in businesses today"
            },
            "correct": "C",
            "explanation": "Narrow and Broad AI are both available today. Most enterprises use Broad AI. General AI will not come online until sometime in the future.",
            "hint": "Which levels are in use today, and which is still on the horizon? Think Narrow, Broad… and the one that has not yet arrived."
        }
    ],

    "ai_lab": [
        {
            "key": "lab_q1",
            "question": "What was the main breakthrough of the Era of Programming?",
            "options": {
                "A": "Computers could now store unlimited amounts of data",
                "B": "Computers could run multiple kinds of instructions to perform more than one type of calculation",
                "C": "Computers could understand human language for the first time",
                "D": "Computers no longer needed human operators to function"
            },
            "correct": "B",
            "explanation": "Programmable computers like ENIAC could run different programs, meaning one machine could perform many different types of calculation — a huge leap forward from single-purpose machines.",
            "hint": "Recall what made ENIAC special — could it do only one fixed job, or be given many different sets of instructions?"
        },
        {
            "key": "lab_q2",
            "question": "Where and when was the term artificial intelligence first coined?",
            "options": {
                "A": "MIT in 1971 during the first AI winter",
                "B": "IBM Research Labs in 1997 when Deep Blue beat the chess champion",
                "C": "Dartmouth College in 1956 by McCarthy and Minsky",
                "D": "The University of Pennsylvania in the 1940s when ENIAC was built"
            },
            "correct": "C",
            "explanation": "In the summer of 1956, researchers at Dartmouth College led by John McCarthy and Marvin Minsky coined the term artificial intelligence and proposed that machines could simulate every aspect of human learning.",
            "hint": "Think of a 1956 summer gathering at an American college, led by McCarthy and Minsky — not a company lab or a chess match."
        },
        {
            "key": "lab_q3",
            "question": "Which of the following is an example of unstructured data?",
            "options": {
                "A": "A spreadsheet of hotel reservation dates and prices",
                "B": "A database of customer names and addresses",
                "C": "Social media posts and customer comments",
                "D": "A table of stock prices organised by date"
            },
            "correct": "C",
            "explanation": "Unstructured data, also called dark data, lacks any built-in organisation. Social media posts, images, and customer comments cannot be processed by conventional computer programs.",
            "hint": "Which option has no neat rows and columns — something free-form like text, images, or comments?"
        },
        {
            "key": "lab_q4",
            "question": "Why is unstructured data a challenge for traditional computers?",
            "options": {
                "A": "It takes up too much storage space on a hard drive",
                "B": "It changes too slowly for computers to keep up with",
                "C": "Conventional programs cannot process data that lacks organisation",
                "D": "Traditional computers can only work with numbers, not text"
            },
            "correct": "C",
            "explanation": "About 80% of all data today is unstructured. No conventional computer program can learn much from it because it contains too many variables and changes too quickly. AI is the solution.",
            "hint": "Conventional programs need organised input. What happens when the vast majority of data has no built-in structure?"
        }
    ],

    "observatory": [
        {
            "key": "obs_q1",
            "question": "What is the key difference between deterministic and probabilistic computation?",
            "options": {
                "A": "Deterministic systems are faster than probabilistic ones",
                "B": "Deterministic systems give yes or no answers while probabilistic systems give a confidence level",
                "C": "Probabilistic systems require more storage than deterministic ones",
                "D": "Deterministic systems can handle unstructured data better than probabilistic ones"
            },
            "correct": "B",
            "explanation": "A deterministic system flags answers as YES or NO based on pre-written rules. Machine learning is probabilistic — it says I am 84% confident rather than giving a binary answer, allowing it to handle real-world complexity."
        },
        {
            "key": "obs_q2",
            "question": "What does supervised learning require that unsupervised learning does not?",
            "options": {
                "A": "A very large dataset with millions of records",
                "B": "A powerful GPU to process the data quickly",
                "C": "Labelled training data with correct answers provided",
                "D": "A constant connection to the internet during training"
            },
            "correct": "C",
            "explanation": "Supervised learning requires labelled data — samples tagged with the correct answer so the machine can learn from them. Unsupervised learning receives unlabelled data and finds patterns entirely by itself."
        },
        {
            "key": "obs_q3",
            "question": "How does reinforcement learning improve its accuracy over time?",
            "options": {
                "A": "A human programmer updates the rules manually after each mistake",
                "B": "The machine copies correct answers from a pre-built database",
                "C": "The machine receives rewards for correct predictions and penalties for incorrect ones",
                "D": "The machine downloads updated training data from the internet after each session"
            },
            "correct": "C",
            "explanation": "Reinforcement learning is based on trial and error. Positive numerical feedback rewards correct predictions and negative feedback penalises incorrect ones. Over time the machine improves automatically without human intervention."
        },
        {
            "key": "obs_q4",
            "question": "Which description best matches General AI?",
            "options": {
                "A": "AI that specialises in one specific task like playing chess or detecting spam",
                "B": "AI that can structure unstructured data and is widely used by enterprises today",
                "C": "A future superintelligence smarter than the best human brains across practically every field",
                "D": "AI that learns through trial and error using rewards and penalties"
            },
            "correct": "C",
            "explanation": "General AI is the predicted third level of artificial intelligence — an intellect much smarter than the best human brains in practically every field including scientific creativity, general wisdom, and social skills. It is not yet available."
        }
    ]
}


import random as _random

# Atmospheric decoy books that fill the Library shelves (no real content).
DECOY_TITLES = [
    "On the Nature of Numbers", "Forgotten Algorithms", "A History of Machines",
    "The Cartographer's Atlas", "Whispers of Logic", "Codex of the Ancients",
    "Theories Long Abandoned", "The Astronomer's Folly", "Mechanical Dreams",
    "Letters to a Young Scholar", "The Glass Bestiary", "Maps of Forgotten Lands",
    "Principles of Steam", "The Alchemist's Ledger", "Songs of the Deep Archive",
    "A Treatise on Shadows", "The Clockwork Compendium", "Untitled Manuscript",
    "Notes from the Margins", "The Cipher Garden", "Of Stars and Sextants",
    "The Librarian's Riddle", "Fragments of Babel", "An Index of Lost Things",
    "The Weight of Silence", "Diagrams of the Aether", "A Catalogue of Curiosities",
    "The Last Lexicon", "Echoes in the Stacks", "The Unbound Folio",
]


def build_library_shelves(items, rows=3, per_row=8, seed=7):
    """Generate a tall bookcase: real content books scattered among decoys.

    `items` is the list of real books (each with a 'concept' or 'heading'/'title').
    Deterministic (fixed seed) so the layout — and where the real books sit —
    stays stable across reloads. Returns a list of rows, each a list of book
    dicts: {type:'real'|'decoy', index, title, color, h, w}.
    """
    rng = _random.Random(seed)
    total = rows * per_row
    real_count = len(items)
    real_positions = sorted(rng.sample(range(total), real_count))
    real_at = {pos: idx for idx, pos in enumerate(real_positions)}

    titles = DECOY_TITLES[:]
    rng.shuffle(titles)

    books, t = [], 0
    for slot in range(total):
        if slot in real_at:
            idx = real_at[slot]
            item = items[idx]
            title = item.get("concept") or item.get("heading") or item.get("title", "")
            books.append({
                "type": "real", "index": idx,
                "title": title,
                "color": idx % 6,
                "h": rng.randint(178, 202), "w": rng.randint(42, 52),
            })
        else:
            books.append({
                "type": "decoy", "title": titles[t % len(titles)],
                "color": rng.randint(0, 7),
                "h": rng.randint(150, 198), "w": rng.randint(26, 46),
            })
            t += 1

    return [books[r * per_row:(r + 1) * per_row] for r in range(rows)]


def grade_quiz(location_key, submitted_answers):
    """Grade a submitted quiz.

    submitted_answers: dict like {"lib_q1": "B", ...} (a letter or None).

    Returns (results, score, total, passed) where results is a list of per-question
    dicts the results template can render directly.
    """
    quiz = QUIZZES.get(location_key, [])
    results = []
    score = 0

    for q in quiz:
        selected = submitted_answers.get(q["key"])
        is_correct = selected == q["correct"]
        if is_correct:
            score += 1
        results.append(
            {
                "key": q["key"],
                "question": q["question"],
                "options": q["options"],
                "selected": selected,
                "correct": q["correct"],
                "is_correct": is_correct,
                "explanation": q["explanation"],
            }
        )

    total = len(quiz)
    passed = score >= PASS_THRESHOLD
    return results, score, total, passed
