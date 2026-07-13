"""
Static game content for Atlas Quest.

LOCATIONS holds metadata + description + learn cards + learning objectives for
each location. QUIZZES holds the 4 quiz questions per location.

Pass threshold is hardcoded at 3/4 — see PASS_THRESHOLD.
"""

PASS_THRESHOLD = 3  # must score at least 3 out of 4 to pass a location

# Order matters: this defines the unlock chain (each unlocks the next).
LOCATION_ORDER = ["library", "chronicle", "ai_lab", "observatory"]

# ── Content-validity registry (Assessment_Blueprint.md) ──
# The concepts the game TEACHES, mapped to the location that teaches them. This is
# the machine-readable side of the Assessment Blueprint: every POST_TEST question
# tags one of these `concept` keys, and a coverage test asserts the SET of tested
# concepts is a subset of the taught set — so no post-test item is an orphan
# (tested but not taught). The Observatory row includes the Modern-AI additions
# (overfitting, bias, NLP, LLMs, hallucination, few-shot prompting) folded in
# under Path A. Keep this in sync when adding/removing taught content.
TAUGHT_CONCEPTS = {
    # Library — Module 1 (foundations)
    "what_is_ai": "library",
    "augmented_intelligence": "library",
    "analysis_prediction": "library",
    "three_levels": "library",
    # Chronicle — Module 2 (history)
    "eras_and_winters": "chronicle",
    "ai_milestones": "chronicle",
    # AI Lab — Module 3 (data)
    "data_types": "ai_lab",
    "unstructured_data": "ai_lab",
    # Observatory — Modules 4–5 (machine learning) + Modern-AI extension
    "ml_methods": "observatory",
    "deterministic_probabilistic": "observatory",
    "overfitting": "observatory",
    "bias": "observatory",
    "nlp": "observatory",
    "llm": "observatory",
    "hallucination": "observatory",
    "few_shot_prompting": "observatory",
}

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
             "body": "Augmented intelligence helps humans with impractical tasks — like reading 1000 pages in an hour. Its defining trait is that it amplifies human judgement rather than replacing it: a person always keeps the final call and the accountability. True AI aims higher — to mimic human thinking itself.",
             "keywords": ["augmented", "amplifies judgement", "human keeps accountability"]},
            {"type": "example", "title": "In the Real World",
             "body": "A bank might use AI to pre-screen loan applications and flag risk factors, but a human officer makes the final decision. That 'AI + human' arrangement — the most common and responsible pattern in the real world — is augmented intelligence.",
             "hint": "Think of augmented intelligence as a powerful assistant that keeps a human in charge — not a replacement."},
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
             "body": "Think of AI on a spectrum. Narrow AI is built for one task and can't step outside it — spam filters, face unlock and chess engines are all narrow. Broad AI, IBM's term for today's systems, integrates several narrow components into one business process trained on an organisation's own data. General AI — reasoning across any domain like a human — does not exist yet; it remains a long-term research goal.",
             "keywords": ["Narrow AI", "Broad AI (integrated)", "General AI (not yet)"]},
            {"type": "example", "title": "In the Real World",
             "body": "A self-driving car is Broad AI: it combines separate systems for vision, route-planning and decision-making into one integrated whole. A single spam filter is Narrow AI. A machine that could teach itself any new task the way a person does would be General AI — which no one has built.",
             "hint": "Narrow and Broad are real today. A self-driving car is Broad AI; General AI lies in the future."},
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

# Opening cinematic (hub, first visit, always skippable). Short narrative frame
# in the GAME_INTRO_STEPS voice — presentation only.
CINEMATIC_LINES = [
    "The Atlas of Knowledge has faded.",
    "Three realms hold its lost pages.",
    "Restore them all… and earn the rank of Atlas Sage.",
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
                "text": "When learning about AI, you will come across the term augmented intelligence. Both share the same objective but have different approaches. Augmented intelligence has a modest goal of helping humans with tasks that are not practical to do — for example, reading 1000 pages in an hour. Crucially, it amplifies human judgement rather than replacing it: a bank might use AI to pre-screen loan applications and flag risks, but a human officer makes the final call and keeps accountability. This 'AI + human' pattern is the most common, responsible use of AI in the real world. In contrast, full AI has a loftier goal of mimicking human thinking and processes, and today it is not mature enough to perform independent tasks such as diagnosing cancer."
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
                "text": "It helps to picture AI on a spectrum of capability. Narrow AI is built for one specific task and can't step outside it — spam filters, face-unlock and chess engines are all narrow, and almost every AI you meet today is too. Broad AI, IBM's term for the middle of the spectrum, integrates several narrow components into one business process trained on an organisation's own data — a self-driving car, for instance, combines vision, route-planning and decision-making into one integrated system. General AI would reason and transfer knowledge across any domain the way a human does, but it does not exist yet; it remains a long-term research goal. Both Narrow AI and Broad AI are available right now."
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

    "chronicle": {
        "key": "chronicle",
        "name": "The Chronicle",
        "icon": "⏳",
        "tagline": "Where the story of thinking machines is kept",
        "topic": "The Three Eras of Computing & the AI Winters",
        "description": "A long hall of clocks, star-charts and dust-jacketed ledgers, where a single luminous timeline runs from wall to wall. Here the history of AI is recorded — three great eras, two long winters, and the milestones that thawed them. Travel the timeline era by era, and watch how humanity arrived at the age of intelligent machines.",
        "order": 2,
        "stub": False,
        "accent": "#c1824a",
        "theme": "timeline",
        "interaction": "timeline",
        "guide_intro": "Every discovery has a history, explorer — and AI's is the richest of all. Walk the timeline with me: from machines that merely sorted, to the two long winters, to the day a machine outplayed the world's finest mind.",
        "atlas_steps": [
            "Welcome to the Chronicle, explorer. I am Professor Atlas. Before us stretches the timeline of thinking machines — six eras, each a lantern waiting to be lit.",
            "Travel left to right through time. Click the glowing era to study its story; answer its quick-check and the era lights, drawing the timeline forward to the next.",
            "Light all six eras to unlock the Trial — four questions, score 3 of 4 to journey on. Tap the owl if you need me. Now… let us begin at the beginning.",
        ],
        # The 6 timeline era-beats (taught content + an ungraded quick-check each).
        # Facts checked against the IBM course: Dartmouth 1956 (McCarthy & Minsky),
        # ENIAC (1940s), two AI Winters, Deep Blue 1997, Stanford robot 2005,
        # Watson 2011. Passed via JSON to timeline.js.
        "beats": [
            {
                "title": "The Era of Tabulation",
                "era": "ANTIQUITY – 1930s",
                "text": "For centuries, people drowned in numbers they could not read. The first breakthrough was not a thinking machine but a sorting one — tabulating machines that organised raw data into structured tables so patterns could finally surface. This was the leap beyond mere counting: from a heap of figures to a sum that revealed insight. Data had begun to speak, if only in a whisper.",
                "keywords": ["tabulation", "sorting", "structured data", "tables", "counting"],
                "check": {
                    "q": "What was the key idea of the Era of Tabulation?",
                    "options": ["Machines that could think for themselves", "Sorting raw data into structured tables to reveal insight", "Predicting the future from probabilities"],
                    "correct": 1,
                },
            },
            {
                "title": "The Era of Programming",
                "era": "1940s – 1950s",
                "text": "In the 1940s came machines that could follow many instructions — programs. ENIAC, built at the University of Pennsylvania, computed wartime artillery firing tables and ran an early thermonuclear feasibility study. Programmable computers later guided astronauts to the Moon, and were reprogrammed mid-crisis to bring Apollo 13 safely home. Yet the world soon generated more data than any program could ever process — the dark-data problem was born, and it would outgrow even the fastest supercomputer.",
                "keywords": ["programming", "eniac", "apollo", "programs", "dark data"],
                "check": {
                    "q": "Why couldn't programmable computers keep up in the end?",
                    "options": ["They were simply too expensive to build", "The world generated more data than any program could process", "No one knew how to write programs"],
                    "correct": 1,
                },
            },
            {
                "title": "The Dawn of AI — Dartmouth, 1956",
                "era": "1956",
                "text": "In the summer of 1956, John McCarthy and Marvin Minsky gathered researchers at Dartmouth College and coined a new term: artificial intelligence. Their bold claim was that every feature of intelligence could be described so precisely that a machine could be made to simulate it. Early programs delivered on the promise — proving geometry theorems, conversing in simple English, and solving algebra word problems. Optimism soared.",
                "keywords": ["dartmouth", "mccarthy", "minsky", "1956", "coined"],
                "check": {
                    "q": "What is the 1956 Dartmouth gathering remembered for?",
                    "options": ["Building the first computer", "Coining the term 'artificial intelligence'", "Deep Blue's victory at chess"],
                    "correct": 1,
                },
            },
            {
                "title": "The First Winter",
                "era": "EARLY 1970s",
                "text": "Optimism met hard walls. Two limits froze progress: limited calculating power — the machines were simply too slow — and limited information storage — they could not hold enough to reason about the real world. Grand promises went unmet, sponsors lost patience, and funding collapsed. The first AI Winter had begun.",
                "keywords": ["first winter", "calculating power", "storage", "funding", "limits"],
                "check": {
                    "q": "Which two limits caused the First Winter of AI?",
                    "options": ["Bad programmers and simple bad luck", "Limited calculating power and limited information storage", "Too much data and too little electricity"],
                    "correct": 1,
                },
            },
            {
                "title": "Expert Systems & the Second Winter",
                "era": "1980s",
                "text": "AI thawed in the 1980s with expert systems — rule-based programs that captured a specialist's knowledge, running on mainframes that could cost a million dollars. For a time they boomed. But by the late 1980s, cheaper personal computers from Apple and IBM outpaced those costly machines, the expert-system market collapsed, and more than 300 AI companies went bankrupt. The second Winter set in.",
                "keywords": ["expert systems", "mainframes", "second winter", "bankrupt", "personal computers"],
                "check": {
                    "q": "What ended the expert-systems boom in the late 1980s?",
                    "options": ["A new law banned them", "Cheaper personal computers overtook costly mainframes", "The systems simply ran out of rules"],
                    "correct": 1,
                },
            },
            {
                "title": "The Thaw",
                "era": "1997 – TODAY",
                "text": "By the mid-1990s, processing power finally caught up with ambition. In 1997, IBM's Deep Blue — searching some 200 million chess positions per second — defeated the reigning world chess champion. In 2005, a Stanford robot drove 131 miles of unrehearsed desert road on its own. In 2011, IBM's Watson beat the champions of Jeopardy! The two Winters had ended, and AI has proven itself across fields ever since.",
                "keywords": ["thaw", "deep blue", "1997", "stanford", "watson", "2011"],
                "check": {
                    "q": "Which IBM system defeated the world chess champion in 1997?",
                    "options": ["Watson", "ENIAC", "Deep Blue"],
                    "correct": 2,
                },
            },
        ],
        "learning_objectives": [
            "Name the three eras of computing in order (Tabulation, Programming, AI)",
            "Explain the significance of the 1956 Dartmouth gathering",
            "Identify the two causes of the First AI Winter",
            "Explain what caused the boom and bust of expert systems",
            "Recall the milestones that ended the AI Winters (Deep Blue, Watson)",
        ],
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
                "text": "Data can be organised into three types. Structured data is highly organised and stored in rows and columns — spreadsheets of names, ages, dates and account balances, easily queried with SQL. Unstructured data has no built-in schema and is kept in its native form — emails, PDFs, contracts, images, audio, video, chat logs and social media posts. Semi-structured data is the bridge between the two: it carries tags, keys or metadata that make it machine-readable without a rigid schema — JSON, XML and CSV are the classic examples (a video with hashtags is another). An estimated 80–90% of enterprise data is unstructured, yet most reporting tools were built for the structured 10–20%, so company dashboards often cover only a thin slice — AI is what finally makes the unstructured majority usable. Beware of dark data too: information that is collected and stored but never used. Dark data can be any type — even perfectly tidy structured records count as dark if they sit unqueried — and studies suggest it is more than half of all enterprise data."
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

# ── Scenario-based question banks (Content Enrichment Pack) ──
# Each Trial draws TRIAL_COUNT questions at random from its bank (the AI Lab
# additionally pins lab_q3, its live data-sorting diagnostic). The exact set
# shown is stored per-attempt so the graded questions == the shown questions.
# Every question tests APPLICATION and carries elaborative feedback
# (feedback_correct / feedback_wrong) plus a non-revealing hint.
QUIZZES = {
    "library": [
        {
            "key": "lib_s1",
            "question": "A hospital deploys a system that reads chest X-rays to flag possible pneumonia. It cannot schedule surgeries or answer patient questions — only read X-rays. What type of AI is this?",
            "options": {
                "A": "Narrow AI",
                "B": "General AI",
                "C": "Broad AI",
                "D": "Super AI"
            },
            "correct": "A",
            "feedback_correct": "Exactly — narrow AI is built for one specific task and can't transfer to others. That inability to generalise is its signature.",
            "feedback_wrong": "This is narrow AI. A pneumonia-detector that can't do anything else is task-locked — the defining trait of narrow AI. General AI (which doesn't exist yet) could move across tasks like a human.",
            "explanation": "Exactly — narrow AI is built for one specific task and can't transfer to others. That inability to generalise is its signature.",
            "hint": "The system does exactly one job and nothing else. Which level of AI is locked to a single task?"
        },
        {
            "key": "lib_s2",
            "question": "A self-driving car combines separate systems for vision, route-planning and decision-making, all trained on one company's driving data. IBM would classify this integrated, business-specific system as:",
            "options": {
                "A": "Narrow AI",
                "B": "Broad AI",
                "C": "General AI",
                "D": "Not AI at all"
            },
            "correct": "B",
            "feedback_correct": "Right — broad AI integrates several narrow components into one business process using enterprise-specific data.",
            "feedback_wrong": "This is broad AI — a collection of narrow-AI systems working together on a specific business problem. It's broader than a single task, but still far from general, human-like intelligence.",
            "explanation": "Right — broad AI integrates several narrow components into one business process using enterprise-specific data.",
            "hint": "Several narrow systems working together on one company's problem — that's the middle of the AI spectrum. What does IBM call it?"
        },
        {
            "key": "lib_s3",
            "question": "Someone claims their chatbot is \"General AI because it can answer questions on any topic.\" Why is this claim almost certainly wrong?",
            "options": {
                "A": "Chatbots can't process language",
                "B": "General AI only works on images",
                "C": "General AI doesn't exist yet; the chatbot is narrow AI predicting text from training data",
                "D": "It's actually Super AI"
            },
            "correct": "C",
            "feedback_correct": "Spot on — answering many questions isn't the same as reasoning across domains like a human.",
            "feedback_wrong": "General AI — reasoning and learning across any domain like a human — is still theoretical. A wide-ranging chatbot is still narrow AI: it predicts text statistically and can't truly transfer understanding.",
            "explanation": "Spot on — answering many questions isn't the same as reasoning across domains like a human.",
            "hint": "Answering many questions isn't the same as reasoning like a human. Has true general AI actually been built yet?"
        },
        {
            "key": "lib_s4",
            "question": "A bank uses AI to pre-screen loan applications and highlight risk factors, while human officers make the final decision. This \"AI + human\" arrangement is best described as:",
            "options": {
                "A": "General AI",
                "B": "Replacing humans entirely",
                "C": "Unsupervised learning",
                "D": "Augmented intelligence"
            },
            "correct": "D",
            "feedback_correct": "Yes — augmented intelligence amplifies human judgement rather than replacing it.",
            "feedback_wrong": "This is augmented intelligence — AI does the heavy lifting (screening, flagging) but a human keeps judgement and accountability. It's the responsible, common real-world pattern.",
            "explanation": "Yes — augmented intelligence amplifies human judgement rather than replacing it.",
            "hint": "The AI assists but a human makes the final call. What do we call AI that amplifies human judgement instead of replacing it?"
        },
        {
            "key": "lib_s5",
            "question": "Which of these is NOT an example of narrow AI?",
            "options": {
                "A": "A machine that could teach itself any new task on its own, like a human",
                "B": "A spam filter",
                "C": "A face-unlock feature",
                "D": "A film recommendation engine"
            },
            "correct": "A",
            "feedback_correct": "Correct — that describes general AI, which doesn't exist yet. The other three are all narrow AI.",
            "feedback_wrong": "Spam filters, face unlock and recommendations are all narrow AI — each does one job well. A system that could learn any new task the way a person does would be general AI, which doesn't exist.",
            "explanation": "Correct — that describes general AI, which doesn't exist yet. The other three are all narrow AI.",
            "hint": "Three of these each do one fixed job. The odd one out describes a human-like, learn-anything machine."
        }
    ],

    "chronicle": [
        {
            "key": "ch_s1",
            "question": "A museum shows an old machine that took stacks of raw figures and arranged them into neat tables so clerks could finally spot trends. Which era does it belong to?",
            "options": {
                "A": "The Era of Programming",
                "B": "The Era of Tabulation",
                "C": "The Era of AI",
                "D": "The Era of Machine Learning"
            },
            "correct": "B",
            "feedback_correct": "Correct — tabulation was about sorting raw data into structure to reveal insight, long before machines could 'think'.",
            "feedback_wrong": "Sorting raw data into structured tables to reveal insight is the hallmark of the Era of Tabulation — it came before programmable computers and before AI.",
            "explanation": "The Era of Tabulation organised data into tables so patterns could surface — the leap beyond mere counting.",
            "hint": "This era only organised data — it did not run programs or learn."
        },
        {
            "key": "ch_s2",
            "question": "What is the correct chronological order of the three eras of computing?",
            "options": {
                "A": "Programming → Tabulation → AI",
                "B": "AI → Programming → Tabulation",
                "C": "Tabulation → Programming → AI",
                "D": "Tabulation → AI → Programming"
            },
            "correct": "C",
            "feedback_correct": "Correct — first we sorted data (Tabulation), then we ran instructions (Programming), then machines began to learn (AI).",
            "feedback_wrong": "The order runs Tabulation → Programming → AI: sort the data, then program instructions, then build machines that learn.",
            "explanation": "Tabulation (sorting) came first, then Programming (ENIAC, Apollo), then the Era of AI (Dartmouth 1956 onward).",
            "hint": "Start with the simplest capability (sorting) and end with the most advanced (learning)."
        },
        {
            "key": "ch_s3",
            "question": "In 1956, a summer gathering at Dartmouth College led by John McCarthy and Marvin Minsky is famous for which milestone?",
            "options": {
                "A": "Building ENIAC",
                "B": "Coining the term 'artificial intelligence'",
                "C": "Deep Blue's chess victory",
                "D": "The start of the First Winter"
            },
            "correct": "B",
            "feedback_correct": "Correct — Dartmouth 1956 is where the term 'artificial intelligence' was coined.",
            "feedback_wrong": "ENIAC was the 1940s; Deep Blue was 1997. The 1956 Dartmouth gathering is where the term 'artificial intelligence' itself was coined.",
            "explanation": "McCarthy and Minsky's Dartmouth workshop (1956) named the field and claimed intelligence could be described precisely enough for a machine to simulate it.",
            "hint": "This milestone gave the whole field its name."
        },
        {
            "key": "ch_s4",
            "question": "Grand promises went unmet and funding dried up in the early 1970s. What TWO limits were the main causes of this First AI Winter?",
            "options": {
                "A": "Limited calculating power and limited information storage",
                "B": "Too many programmers and too few computers",
                "C": "A shortage of data and a shortage of electricity",
                "D": "Government bans and public fear"
            },
            "correct": "A",
            "feedback_correct": "Correct — machines were too slow (limited calculating power) and could not hold enough (limited storage).",
            "feedback_wrong": "The First Winter came from two hard technical limits: limited calculating power (too slow) and limited information storage (too little memory to reason about the world).",
            "explanation": "Early AI hit two walls — not enough compute and not enough storage — so promises went unmet and funding collapsed.",
            "hint": "Both limits are about the machines themselves — speed and memory."
        },
        {
            "key": "ch_s5",
            "question": "After the expert-systems boom collapsed, what finally brought AI out of the Second Winter in the mid-1990s?",
            "options": {
                "A": "A brand-new programming language",
                "B": "Processing power finally becoming fast enough",
                "C": "Expert systems suddenly getting cheaper",
                "D": "A single government grant"
            },
            "correct": "B",
            "feedback_correct": "Correct — by the mid-1990s, processing power finally caught up with ambition, and the thaw began.",
            "feedback_wrong": "The thaw came because processing power finally became fast enough for AI's ambitions — soon after, Deep Blue won at chess.",
            "explanation": "The Second Winter ended when hardware caught up: fast enough processing made the old ambitions achievable (Deep Blue, 1997).",
            "hint": "Think about what the machines had been lacking all along — raw speed."
        },
        {
            "key": "ch_s6",
            "question": "Which IBM system, searching around 200 million positions per second, defeated the reigning world chess champion in 1997?",
            "options": {
                "A": "Watson",
                "B": "ENIAC",
                "C": "Deep Blue",
                "D": "Apollo"
            },
            "correct": "C",
            "feedback_correct": "Correct — Deep Blue beat the world chess champion in 1997. (Watson won Jeopardy! in 2011.)",
            "feedback_wrong": "Watson won Jeopardy! in 2011 and ENIAC was a 1940s calculator. The chess victory of 1997 belonged to IBM's Deep Blue.",
            "explanation": "Deep Blue's 1997 chess win was a landmark of the thaw; Watson's Jeopardy! win followed in 2011.",
            "hint": "It played chess, not Jeopardy!."
        }
    ],

    "ai_lab": [
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
            "feedback_correct": "Unstructured data, also called dark data, lacks any built-in organisation. Social media posts, images, and customer comments cannot be processed by conventional programs.",
            "feedback_wrong": "The answer is social media posts and customer comments. Unstructured data has no built-in rows and columns — unlike spreadsheets, databases and tables.",
            "explanation": "Unstructured data, also called dark data, lacks any built-in organisation. Social media posts, images, and customer comments cannot be processed by conventional computer programs.",
            "hint": "Which option has no neat rows and columns — something free-form like text, images, or comments?",
            "no_shuffle": True
        },
        {
            "key": "lab_s1",
            "question": "A retailer wants to analyse customer emails and call-centre recordings to understand complaints. What type of data is this?",
            "options": {
                "A": "Structured — fits neatly in tables",
                "B": "Unstructured — no fixed schema, needs AI like NLP to interpret",
                "C": "Semi-structured — it has a rigid schema",
                "D": "It isn't data"
            },
            "correct": "B",
            "feedback_correct": "Right — emails and audio have no rows-and-columns schema, so traditional databases can't query them directly.",
            "feedback_wrong": "This is unstructured data. Around 80–90% of enterprise data looks like this (Gartner/IBM), and AI like natural-language processing is what unlocks it.",
            "explanation": "Right — emails and audio have no rows-and-columns schema, so traditional databases can't query them directly.",
            "hint": "Emails and audio recordings don't fit into neat rows and columns. Which data type has no fixed schema?"
        },
        {
            "key": "lab_s2",
            "question": "A company stores millions of JSON API logs with tags and key-value pairs, but no rigid table schema. This is:",
            "options": {
                "A": "Structured data",
                "B": "Unstructured data",
                "C": "Semi-structured data",
                "D": "Dark data by definition"
            },
            "correct": "C",
            "feedback_correct": "Correct — tags and keys make it machine-readable without a fixed schema.",
            "feedback_wrong": "This is semi-structured data — JSON and XML carry metadata/keys that give partial organisation without a rigid schema. It sits between structured tables and raw unstructured content.",
            "explanation": "Correct — tags and keys make it machine-readable without a fixed schema.",
            "hint": "It has tags and key-value pairs but no rigid table. What sits between structured and unstructured?"
        },
        {
            "key": "lab_s3",
            "question": "A bank finds years of archived transaction records in an old system that nobody ever queries. Though neatly organised, what is this an example of?",
            "options": {
                "A": "Dark data",
                "B": "Unstructured data",
                "C": "Semi-structured data",
                "D": "Real-time data"
            },
            "correct": "A",
            "feedback_correct": "Yes — dark data is collected and stored but never used, and it can be perfectly structured.",
            "feedback_wrong": "This is dark data — unused information that can be any type, including tidy structured tables. More than half of enterprise data is estimated to be dark (Splunk): a huge untapped, and unsecured, resource.",
            "explanation": "Yes — dark data is collected and stored but never used, and it can be perfectly structured.",
            "hint": "The records are tidy but nobody ever uses them. What do we call collected data that just sits unused?"
        },
        {
            "key": "lab_s4",
            "question": "Why do most companies' dashboards and reports only cover a small slice of their total data?",
            "options": {
                "A": "Unstructured data doesn't exist",
                "B": "Structured data can't be analysed",
                "C": "All data is equally easy to use",
                "D": "Traditional tools were built for the ~10–20% that's structured"
            },
            "correct": "D",
            "feedback_correct": "Right — legacy reporting tools were designed for structured data, leaving the unstructured 80%+ largely untouched until AI arrived.",
            "feedback_wrong": "Most reporting tools target structured data — the ~10–20% that fits neat tables. The unstructured majority (emails, PDFs, images, audio) stayed hard to use until AI made it actionable.",
            "explanation": "Right — legacy reporting tools were designed for structured data, leaving the unstructured 80%+ largely untouched until AI arrived.",
            "hint": "Old reporting tools were designed for one kind of data. Which small slice — structured or unstructured — could they actually handle?"
        },
        {
            "key": "lab_s5",
            "question": "Which item is structured data?",
            "options": {
                "A": "A folder of scanned contracts",
                "B": "A spreadsheet of customer names, ages and balances in fixed columns",
                "C": "A podcast recording",
                "D": "A collection of social-media photos"
            },
            "correct": "B",
            "feedback_correct": "Correct — fixed fields in labelled columns, easily queried with SQL.",
            "feedback_wrong": "The spreadsheet is structured — predefined fields like name/age/balance. Contracts, audio and photos are unstructured: no fixed schema, stored in native form.",
            "explanation": "Correct — fixed fields in labelled columns, easily queried with SQL.",
            "hint": "Only one of these fits neatly into labelled rows and columns you could query with SQL."
        }
    ],

    "observatory": [
        {
            "key": "obs_s1",
            "question": "A team has 50,000 emails already labelled \"spam\" or \"not spam\" and wants to train a filter. Which ML method fits?",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "None of these"
            },
            "correct": "A",
            "feedback_correct": "Right — labelled data with known answers is the hallmark of supervised learning.",
            "feedback_wrong": "This is supervised learning — it trains on labelled examples (spam/not-spam) and learns to predict the label for new, unseen emails.",
            "explanation": "Right — labelled data with known answers is the hallmark of supervised learning.",
            "hint": "The training data already carries the correct answers. Which method learns from labelled examples?"
        },
        {
            "key": "obs_s2",
            "question": "A streaming service wants to group viewers with similar tastes, but nobody has defined what the groups should be. Which method?",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "Deterministic rules"
            },
            "correct": "B",
            "feedback_correct": "Correct — with no predefined labels, the model discovers clusters on its own.",
            "feedback_wrong": "This is unsupervised learning — it finds hidden structure in unlabelled data. Grouping viewers with no preset categories is a classic clustering (segmentation) task.",
            "explanation": "Correct — with no predefined labels, the model discovers clusters on its own.",
            "hint": "There are no predefined groups or labels — the model must find the patterns itself. Which method is that?"
        },
        {
            "key": "obs_s3",
            "question": "Amazon trains warehouse robots to pick and move goods, rewarding good actions and penalising mistakes so they improve through trial and error. This is:",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "Structured data sorting"
            },
            "correct": "C",
            "feedback_correct": "Yes — learning through rewards and feedback while interacting with an environment is reinforcement learning.",
            "feedback_wrong": "This is reinforcement learning — an agent learns which actions maximise reward through trial and error, exactly like game-playing AIs and warehouse robots. There's no labelled answer key.",
            "explanation": "Yes — learning through rewards and feedback while interacting with an environment is reinforcement learning.",
            "hint": "The robot learns from rewards and penalties by trial and error. Which method uses feedback from an environment?"
        },
        {
            "key": "obs_s4",
            "question": "A calculator returns exactly the same answer every time you enter 7 × 8, and an autonomous car's braking logic is built to behave the same predictable way. These are examples of:",
            "options": {
                "A": "Probabilistic systems",
                "B": "Unsupervised learning",
                "C": "Dark data",
                "D": "Deterministic systems"
            },
            "correct": "D",
            "feedback_correct": "Right — same input, same output, no randomness. Ideal where predictability is critical.",
            "feedback_wrong": "These are deterministic — they map the same input to the same output every time. That predictability is exactly what you want for braking or calculation.",
            "explanation": "Right — same input, same output, no randomness. Ideal where predictability is critical.",
            "hint": "Same input, same output, every single time. Is that predictable behaviour deterministic or probabilistic?"
        },
        {
            "key": "obs_s5",
            "question": "A medical AI outputs \"78% likelihood this scan shows a tumour\" instead of a flat yes/no. What kind of system is this, and why is it useful?",
            "options": {
                "A": "Probabilistic — it expresses confidence/uncertainty, helping doctors prioritise",
                "B": "Deterministic — it's always exact",
                "C": "Unsupervised — it has no data",
                "D": "Broken; AI should never be unsure"
            },
            "correct": "A",
            "feedback_correct": "Exactly — a confidence score lets a clinician weigh uncertainty rather than trust a false black-and-white answer.",
            "feedback_wrong": "This is probabilistic — it expresses outputs as likelihoods. A \"78% likelihood\" helps a doctor prioritise and handle uncertainty, which is far safer in medicine than false certainty.",
            "explanation": "Exactly — a confidence score lets a clinician weigh uncertainty rather than trust a false black-and-white answer.",
            "hint": "The output is a confidence percentage, not a flat yes/no. Which kind of system expresses likelihoods?"
        },
        {
            "key": "obs_s6",
            "question": "Recall from the Library that a self-driving car is broad AI. Which ML method most likely helps the car improve its driving decisions through trial, reward and consequence?",
            "options": {
                "A": "Supervised only",
                "B": "Reinforcement learning",
                "C": "Unsupervised only",
                "D": "It uses no machine learning"
            },
            "correct": "B",
            "feedback_correct": "Right — self-driving decision systems often use reinforcement learning, and the car as a whole is broad AI (many methods combined).",
            "feedback_wrong": "Reinforcement learning — improving actions through feedback and reward, like a game-playing agent. It also ties back to \"broad AI\": many ML methods integrated into one system.",
            "explanation": "Right — self-driving decision systems often use reinforcement learning, and the car as a whole is broad AI (many methods combined).",
            "hint": "The key words are trial, reward and consequence. Which learning method improves through feedback?"
        }
    ]
}

# How many questions each Trial shows (and grades). Kept at 4 — PASS_THRESHOLD
# of 3/4 is unchanged.
TRIAL_COUNT = 4

# Questions that must always appear in a location's Trial. The AI Lab pins its
# hands-on data-sorting diagnostic (lab_q3, rendered as the sorting machine).
PINNED_QUESTIONS = {
    "ai_lab": ["lab_q3"],
}


def select_trial_questions(location_key, count=TRIAL_COUNT):
    """Pick which question keys to show for one Trial attempt.

    Pinned questions (e.g. the AI Lab sorting diagnostic) are always included
    and kept first; the remainder are sampled at random from the bank. Returns
    a list of question keys.
    """
    bank = QUIZZES.get(location_key, [])
    by_key = {q["key"]: q for q in bank}
    pinned = [k for k in PINNED_QUESTIONS.get(location_key, []) if k in by_key]
    pool = [q["key"] for q in bank if q["key"] not in pinned]
    need = max(0, count - len(pinned))
    chosen = _random.sample(pool, min(need, len(pool)))
    return pinned + chosen


def get_questions_by_keys(location_key, keys):
    """Return the question dicts for `keys`, in the given order."""
    by_key = {q["key"]: q for q in QUIZZES.get(location_key, [])}
    return [by_key[k] for k in keys if k in by_key]


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


def grade_quiz(location_key, submitted_answers, shown_keys=None):
    """Grade a submitted quiz.

    submitted_answers: dict like {"lib_s1": "B", ...} (a letter or None).
    shown_keys: the exact question keys that were shown this attempt. Only these
        are graded, so the graded set always matches what the learner saw. When
        omitted, the whole bank is graded (legacy behaviour).

    Returns (results, score, total, passed) where results is a list of per-question
    dicts the results template can render directly.
    """
    if shown_keys:
        quiz = get_questions_by_keys(location_key, shown_keys)
    else:
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
                "explanation": q.get("explanation", ""),
                "feedback": (q.get("feedback_correct") if is_correct
                             else q.get("feedback_wrong")) or q.get("explanation", ""),
            }
        )

    total = len(quiz)
    passed = score >= PASS_THRESHOLD
    return results, score, total, passed


# ══════════════════════════════════════════════════════════════════════
#  LEARNING LOOP — hook questions (guess-first priming) + reflections
#  Presentation/qualitative-data layer only. Hooks are NEVER logged, graded,
#  or gating. Reflections save to the additive `reflections` table and never
#  affect scoring, progression, XP, or any existing research measure.
# ══════════════════════════════════════════════════════════════════════

# Guess-first "hook" per lesson chunk, in chunk order for each location:
#   library     -> aligns to LIBRARY_BOOKS (5)
#   ai_lab      -> aligns to the 4 terminal sector cards
#   observatory -> aligns to the 5 constellation stars
# Each: {"question": str, "options": [2-3 short strings] (omit/empty = freeform
# tap-to-reveal), "payoff": one-line bridge shown after the guess}.
# Hooks must never reveal a Trial answer — they prime curiosity, nothing more.
HOOKS = {
    "library": [
        {"question": "Before you open this tome — what do you think makes a machine “intelligent”?",
         "options": ["Raw speed", "Learning from data & predicting", "A huge memory"],
         "payoff": "Hold that thought — one of these is the real heart of it. Let's read on."},
        {"question": "If an AI screens loans but a human makes the final call — who is really in charge?",
         "options": ["The AI", "The human", "Neither"],
         "payoff": "Keep your guess in mind — this balance of power has a name."},
        {"question": "At its core, AI really does just two things. Care to guess what they are?",
         "options": ["Store & delete", "Analyse & predict", "Type & print"],
         "payoff": "Interesting — let's see if the two acts match what you pictured."},
        {"question": "Which of these do you think is powered by AI prediction?",
         "options": ["Spotting bank fraud", "Reading road signs", "Both — and more"],
         "payoff": "Hold that thought — the reach might surprise you."},
        {"question": "A program plays chess brilliantly but can do nothing else. What would you call that kind of AI?",
         "options": ["Narrow", "General", "Super"],
         "payoff": "Note your instinct — the three levels are about to come into focus."},
    ],
    "chronicle": [
        {"question": "Before any 'thinking' machine, what was the first useful thing machines did with data?",
         "options": ["Sorted it into tables", "Predicted the future", "Wrote their own programs"],
         "payoff": "Hold that thought — the story begins with sorting, not thinking."},
        {"question": "What first let a single 1940s machine do many different jobs?",
         "options": ["Programs (instructions)", "More metal", "Sheer luck"],
         "payoff": "Keep that in mind as we power up ENIAC."},
        {"question": "Guess the year the term “artificial intelligence” was first coined.",
         "options": ["1956", "1985", "2010"],
         "payoff": "Hold that thought — it's older than most people expect."},
        {"question": "Early AI stalled hard in the 1970s. What do you think held it back?",
         "options": ["Slow machines & tiny memory", "Too many rules", "No electricity"],
         "payoff": "Keep your guess — the First Winter is closing in."},
        {"question": "Million-dollar 'expert' machines boomed in the 1980s. What toppled them?",
         "options": ["Cheap personal computers", "A new law", "Public boredom"],
         "payoff": "Hold that thought — the second thaw and freeze are near."},
        {"question": "In 1997 a machine first beat the reigning world champion at which game?",
         "options": ["Chess", "Go", "Poker"],
         "payoff": "Keep your guess — the Winters are about to end."},
    ],
    "ai_lab": [
        {"question": "Before computers, how did people make sense of huge piles of numbers?",
         "options": ["By hand, in tables", "They simply couldn't", "With pocket calculators"],
         "payoff": "Hold that thought — the story starts slower than you'd think."},
        {"question": "What first let a single machine do many different jobs?",
         "options": ["More metal", "Programs (instructions)", "More electricity"],
         "payoff": "Keep that in mind as we power up the 1940s."},
        {"question": "Guess the year the term “artificial intelligence” was first coined.",
         "options": ["1956", "1985", "2007"],
         "payoff": "Hold that thought — it's older than most people expect."},
        {"question": "Guess: what fraction of a company's data do you think ever actually gets analysed?",
         "options": ["Almost all of it", "About half", "Only a small slice"],
         "payoff": "Keep your guess — then let's sort some data and find out."},
    ],
    "observatory": [
        {"question": "A calculator always says 7×8=56. A weather AI says “70% chance of rain.” What's the key difference?",
         "options": ["One is certain, one gives odds", "One is just faster", "No real difference"],
         "payoff": "Hold that thought — certainty vs. confidence is the whole idea."},
        {"question": "To teach an AI to spot spam, what would you give it first?",
         "options": ["Thousands of labelled examples", "Nothing — let it guess", "A written rulebook"],
         "payoff": "Keep that in mind as we trace this star."},
        {"question": "Could a machine group similar customers together with NO labels telling it the groups?",
         "options": ["Yes — it finds patterns itself", "No, impossible", "Only if a human helps"],
         "payoff": "Hold that thought — pattern-finding without answers is next."},
        {"question": "How do you think a machine could learn chess with NO teacher and NO answer key?",
         "options": ["Reward good moves, penalise bad", "It simply can't", "Memorise every game ever played"],
         "payoff": "Keep your guess — trial, reward and consequence await."},
        {"question": "Which kind of AI actually exists and runs real businesses today?",
         "options": ["Narrow & Broad AI", "General AI", "Super AI"],
         "payoff": "Hold that thought — let's map the big picture."},
        {"question": "A model aces its practice data but flops on brand-new data. What went wrong?",
         "options": ["It memorised instead of learning", "It's simply perfect", "It needs less data"],
         "payoff": "Keep your guess — this trap has a name."},
        {"question": "How do machines make sense of messy human language — emails, speech, chat?",
         "options": ["Natural Language Processing", "They can't at all", "Only via spreadsheets"],
         "payoff": "Hold that thought — language is the next frontier."},
        {"question": "Your guide, Professor Atlas — what kind of AI do you think it is?",
         "options": ["A large language model", "A human typing", "A search engine"],
         "payoff": "Keep that in mind — the tutor IS the technology."},
        {"question": "An AI confidently states a fake 'fact'. What is that called?",
         "options": ["A hallucination", "A victory", "A calculation"],
         "payoff": "Hold that thought — even Atlas can do this."},
        {"question": "To steer an LLM, what helps most before your real question?",
         "options": ["A few example answers", "Asking louder", "Nothing at all"],
         "payoff": "Keep your guess — prompting is a real skill."},
    ],
}


def get_hooks(location_key):
    """Hook list for a location (chunk order), or [] if none."""
    return HOOKS.get(location_key, [])


# One post-Trial reflection prompt per location (generative learning). Saved to
# the reflections table when answered or skipped; ungraded, never gates.
REFLECTION_PROMPTS = {
    "library": {
        "key": "narrow_vs_general",
        "text": "In one sentence: what's the difference between narrow AI and general AI?",
    },
    "chronicle": {
        "key": "why_winters",
        "text": "In one sentence: why did the AI Winters happen, and what finally ended them?",
    },
    "ai_lab": {
        "key": "why_data_hard",
        "text": "In one sentence: why is most of the world's data hard for computers to use?",
    },
    "observatory": {
        "key": "rl_no_answer_key",
        "text": "In one sentence: how does reinforcement learning learn without an answer key?",
    },
}
