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
             "body": "Welcome to the Atlas Archive. Before you venture onward, you must grasp the foundation of it all. What do we truly mean by 'artificial intelligence'?"},
            {"type": "concept", "title": "What is AI?",
             "body": "Artificial intelligence is the ability of a machine to learn patterns from data and make predictions. It does not replace human judgement; it adds to it.",
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
            "remember": "AI adds to human judgement; it doesn't replace it."},
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
             "body": "Augmented intelligence helps humans with impractical tasks, like reading 1000 pages in an hour. Its defining trait is that it amplifies human judgement rather than replacing it: a person always keeps the final call and the accountability. True AI aims higher, to mimic human thinking itself.",
             "keywords": ["augmented", "amplifies judgement", "human keeps accountability"]},
            {"type": "example", "title": "In the Real World",
             "body": "A bank might use AI to pre-screen loan applications and flag risk factors, but a human officer makes the final decision. That 'AI + human' arrangement (the most common and responsible pattern in the real world) is augmented intelligence.",
             "hint": "Think of augmented intelligence as a powerful assistant that keeps a human in charge, not a replacement."},
        ],
        "quiz": {
            "question": "A doctor uses a tool that reads 1,000 scans in minutes and flags unusual ones for review. This is best described as:",
            "options": ["General AI replacing the doctor", "Augmented intelligence assisting the doctor", "A simple search engine", "Reinforcement learning"],
            "answer": 1,
            "explanation": "It assists the human expert with an impractical task rather than replacing them. That is augmented intelligence.",
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
             "body": "From a flood of bank transactions, AI spots the pattern of fraud, then predicts which new charge is likely stolen.",
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
             "hint": "The same skill (prediction) solves very different problems."},
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
             "body": "Think of AI on a spectrum. Narrow AI is built for one task and can't step outside it. Spam filters, face unlock and chess engines are all narrow. Broad AI, IBM's term for today's systems, integrates several narrow components into one business process trained on an organisation's own data. General AI (reasoning across any domain like a human) does not exist yet; it remains a long-term research goal.",
             "keywords": ["Narrow AI", "Broad AI (integrated)", "General AI (not yet)"]},
            {"type": "example", "title": "In the Real World",
             "body": "A self-driving car is Broad AI: it combines separate systems for vision, route-planning and decision-making into one integrated whole. A single spam filter is Narrow AI. A machine that could teach itself any new task the way a person does would be General AI, which no one has built.",
             "hint": "Narrow and Broad are real today. A self-driving car is Broad AI; General AI lies in the future."},
        ],
        "quiz": {
            "question": "A program plays chess brilliantly but can do nothing else. Which level of AI is it?",
            "options": ["General AI", "Narrow AI", "Broad AI", "Not AI at all"],
            "answer": 1,
            "explanation": "Excelling at a single task is Narrow AI; it cannot apply its skill elsewhere.",
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
    "Four realms hold its lost pages.",
    "Restore them all… and earn the rank of Atlas Sage.",
]

# Professor Atlas's overall-game tutorial, shown as a focused overlay on the hub.
GAME_INTRO_STEPS = [
    "Greetings, traveller. I am Professor Atlas, and this is Atlas Quest, your journey through the world of Artificial Intelligence.",
    "This is your map. Each glowing waypoint is a place to explore. You begin at the Library; new regions reveal themselves as you prove yourself.",
    "Within each location you will study its knowledge, then face a Trial of four questions. Score at least 3 of 4 to open the road onward.",
    "As you learn, you earn XP and badges, and your rank rises. Keep an eye on the banner above the map.",
    "Master all four locations to reveal the final assessment at the journey's end. I shall guide you the whole way. Onward, explorer!",
]

LOCATIONS = {
    "library": {
        "key": "library",
        "name": "The Library",
        "icon": "📚",
        "tagline": "Where knowledge begins",
        "topic": "What is Artificial Intelligence?",
        "description": "Ancient tomes line the walls of this vast chamber. Candlelight flickers across shelves that stretch beyond sight. This is where the story of intelligence begins, not human intelligence, but the kind we build. Professor Atlas waits by the fireplace, ready to guide you through the foundations of AI.",
        "order": 1,
        "stub": False,
        "accent": "#d4a84b",
        "theme": "archive",
        "interaction": "bookshelf",
        "books": LIBRARY_BOOKS,
        "guide_intro": "Welcome, seeker. Before any grand experiment or distant star, an explorer must first know what intelligence we seek to build. Turn each page with care. I shall be at your side.",
        "atlas_steps": [
            "Welcome to the Library, explorer. I am Professor Atlas. Knowledge hides among these shelves. Most volumes are mere decoration, but a precious few glow with what you truly seek.",
            "Click each glowing tome to open and read it. Every one you study grants a Concept Card and charges the Knowledge Core. Fill the Core to unlock the Trial.",
            "The Trial is four questions, asked one at a time; score 3 of 4 to journey onward. Need me? Tap the owl anytime. Now… begin your reading!",
        ],
        "learn_cards": [
            {
                "heading": "What is AI?",
                "text": "Artificial intelligence (AI) refers to the ability of a machine to learn patterns and make predictions. AI does not replace human decisions. Instead, AI adds value to human judgement. In its simplest form, AI is a field that combines computer science and robust datasets to enable problem-solving. AI plays an often invisible role in everyday life, powering search engines, recommendations, and speech recognition systems."
            },
            {
                "heading": "AI vs Augmented Intelligence",
                "text": "When learning about AI, you will come across the term augmented intelligence. Both share the same objective but have different approaches. Augmented intelligence has a modest goal of helping humans with tasks that are not practical to do (for example, reading 1000 pages in an hour). Crucially, it amplifies human judgement rather than replacing it: a bank might use AI to pre-screen loan applications and flag risks, but a human officer makes the final call and keeps accountability. This 'AI + human' pattern is the most common, responsible use of AI in the real world. In contrast, full AI has a loftier goal of mimicking human thinking and processes, and today it is not mature enough to perform independent tasks such as diagnosing cancer."
            },
            {
                "heading": "What Does AI Do?",
                "text": "How do AI services work? Let us break it down into two parts. First, Analysis. AI examines large amounts of data to find hidden patterns. Second, Prediction. Based on that analysis, AI predicts an outcome. It might not seem like much, but that analysis and those predictions can have an enormous impact on human life, from diagnosing illness to detecting fraud."
            },
            {
                "heading": "What Predictions Can AI Make?",
                "text": "Vision recognition: AI helps doctors identify serious diseases based on unusual symptoms and early-warning signs. It also reads speed limit and stop signs as it guides self-driving cars through traffic. Fraud detection: AI analyses patterns created when thousands of bank customers make credit card purchases, then predicts which charges might be the result of identity theft. Customer service: AI can predict which answers to give on topics ranging from shipping or business hours to merchandise and sizes."
            },
            {
                "heading": "How is AI Evolving?",
                "text": "It helps to picture AI on a spectrum of capability. Narrow AI is built for one specific task and can't step outside it. Spam filters, face-unlock and chess engines are all narrow, and almost every AI you meet today is too. Broad AI, IBM's term for the middle of the spectrum, integrates several narrow components into one business process trained on an organisation's own data. A self-driving car, for instance, combines vision, route-planning and decision-making into one integrated system. General AI would reason and transfer knowledge across any domain the way a human does, but it does not exist yet; it remains a long-term research goal. Both Narrow AI and Broad AI are available right now."
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
        "description": "A long hall of clocks, star-charts and dust-jacketed ledgers, where a single luminous timeline runs from wall to wall. Here the history of AI is recorded. Three great eras, two long winters, and the milestones that thawed them. Travel the timeline era by era, and watch how humanity arrived at the age of intelligent machines.",
        "order": 2,
        "stub": False,
        "accent": "#c1824a",
        "theme": "timeline",
        "interaction": "timeline",
        "guide_intro": "Every discovery has a history, explorer, and AI's is the richest of all. Walk the timeline with me: from machines that merely sorted, to the two long winters, to the day a machine outplayed the world's finest mind.",
        "atlas_steps": [
            "Welcome to the Chronicle, explorer. I am Professor Atlas. Before us stretches the timeline of thinking machines. Six eras, each a lantern waiting to be lit.",
            "Travel left to right through time. Click the glowing era to study its story; answer its quick-check and the era lights, drawing the timeline forward to the next.",
            "Light all six eras to unlock the Trial. Four questions; score 3 of 4 to journey on. Tap the owl if you need me. Now… let us begin at the beginning.",
        ],
        # The 6 timeline era-beats (taught content + an ungraded quick-check each).
        # Facts checked against the IBM course: Dartmouth 1956 (McCarthy & Minsky),
        # ENIAC (1940s), two AI Winters, Deep Blue 1997, Stanford robot 2005,
        # Watson 2011. Passed via JSON to timeline.js.
        "beats": [
            {
                "title": "The Era of Tabulation",
                "era": "ANTIQUITY – 1930s",
                "text": "For centuries, people drowned in numbers they could not read. The first breakthrough was not a thinking machine but a sorting one, tabulating machines that organised raw data into structured tables so patterns could finally surface. This was the leap beyond mere counting: from a heap of figures to a sum that revealed insight. Data had begun to speak, if only in a whisper.",
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
                "text": "In the 1940s came machines that could follow many instructions (programs). ENIAC, built at the University of Pennsylvania, computed wartime artillery firing tables and ran an early thermonuclear feasibility study. Programmable computers later guided astronauts to the Moon, and were reprogrammed mid-crisis to bring Apollo 13 safely home. Yet the world soon generated more data than any program could ever process. The dark-data problem was born, and it would outgrow even the fastest supercomputer.",
                "keywords": ["programming", "eniac", "apollo", "programs", "dark data"],
                "check": {
                    "q": "Why couldn't programmable computers keep up in the end?",
                    "options": ["They were simply too expensive to build", "The world generated more data than any program could process", "No one knew how to write programs"],
                    "correct": 1,
                },
            },
            {
                "title": "The Dawn of AI: Dartmouth, 1956",
                "era": "1956",
                "text": "In the summer of 1956, John McCarthy and Marvin Minsky gathered researchers at Dartmouth College and coined a new term: artificial intelligence. Their bold claim was that every feature of intelligence could be described so precisely that a machine could be made to simulate it. Early programs delivered on the promise, proving geometry theorems, conversing in simple English, and solving algebra word problems. Optimism soared.",
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
                "text": "Optimism met hard walls. Two limits froze progress: limited calculating power (the machines were simply too slow) and limited information storage (they could not hold enough to reason about the real world). Grand promises went unmet, sponsors lost patience, and funding collapsed. The first AI Winter had begun.",
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
                "text": "AI thawed in the 1980s with expert systems, rule-based programs that captured a specialist's knowledge, running on mainframes that could cost a million dollars. For a time they boomed. But by the late 1980s, cheaper personal computers from Apple and IBM outpaced those costly machines, the expert-system market collapsed, and more than 300 AI companies went bankrupt. The second Winter set in. Both Winters told the same story: each began with big promises that the technology could not yet deliver, and when the results fell short, investment and confidence collapsed.",
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
                "text": "By the mid-1990s, processing power finally caught up with ambition. In 1997, IBM's Deep Blue (searching some 200 million chess positions per second) defeated the reigning world chess champion. In 2005, a Stanford robot drove 131 miles of unrehearsed desert road on its own. In 2011, IBM's Watson beat the champions of Jeopardy! The two Winters had ended, and AI has proven itself across fields ever since.",
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
        "description": "Banks of humming machines fill the room. Screens display cascading streams of data. This is where you discover how humanity arrived at the age of AI, through the history of computing, the problem of dark data, and why AI was the only answer.",
        "order": 2,
        "stub": False,
        "accent": "#3fd0e0",
        "theme": "lab",
        "interaction": "terminal",
        "guide_intro": "Mind the cables, explorer. In this lab, theory meets the world. Read on, and witness how machines learned to see, to listen, and to choose, and what we owe them in return.",
        "learn_cards": [
            {
                "heading": "The Era of Tabulation",
                "text": "People have worked with data for a very long time. For centuries, humans struggled to understand the meaning hidden in large amounts of data. Early attempts involved manual counting and tabulation, organising numbers into tables by hand. This was slow, limited, and exhausting. The challenge of extracting meaning from vast amounts of data has always existed. Something had to change."
            },
            {
                "heading": "The Era of Programming",
                "text": "Data analysis changed in the 1940s. Scientists began building electronic computers like ENIAC at the University of Pennsylvania that could run more than one kind of instruction (what we now call programs). Programmable computers guided astronauts from Earth to the moon and were reprogrammed during Apollo 13 to bring astronauts safely home. But modern businesses and technology now generate so much data that even the finest programmable supercomputer cannot analyse it all before the heat-death of the universe. A new approach was needed."
            },
            {
                "heading": "The Era of AI",
                "text": "In the summer of 1956, researchers led by John McCarthy and Marvin Minsky gathered at Dartmouth College and coined the term artificial intelligence. They proposed that every aspect of learning or any feature of intelligence can be described precisely enough for a machine to simulate it. After two AI winters (periods when funding collapsed and hundreds of companies shut down), breakthroughs arrived. IBM's Deep Blue beat the world chess champion in 1997. Watson defeated Jeopardy! champions in 2011. Today AI has proven its ability across fields from cancer research to energy production. The winters of AI are over."
            },
            {
                "heading": "Structured, Semi-Structured, and Unstructured Data",
                "text": "Data can be organised into three types. Structured data is highly organised and stored in rows and columns, such as spreadsheets of names, ages, dates and account balances, easily queried with SQL. Unstructured data has no built-in schema and is kept in its native form, such as emails, PDFs, contracts, images, audio, video, chat logs and social media posts. Semi-structured data is the bridge between the two: it carries tags, keys or metadata that make it machine-readable without a rigid schema. JSON, XML and CSV are the classic examples (a video with hashtags is another). An estimated 80–90% of enterprise data is unstructured, yet most reporting tools were built for the structured 10–20%, so company dashboards often cover only a thin slice. AI is what finally makes the unstructured majority usable. Beware of dark data too: information that is collected and stored but never used. Dark data can be any type (even perfectly tidy structured records count as dark if they sit unqueried), and studies suggest it is more than half of all enterprise data."
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
        "description": "A vast glass dome opens to a sky full of stars. Every constellation is a pattern waiting to be recognised. This is where you learn how machines actually learn, not through rules written by humans, but through data, probability, and the remarkable process of teaching a machine to think.",
        "order": 3,
        "stub": False,
        "accent": "#3ab8d8",
        "theme": "cosmos",
        "interaction": "constellation",
        "guide_intro": "You have climbed high indeed. Beyond this glass lies the frontier, machines that create from pattern alone. Study closely, and learn to weigh their wonders against their flaws.",
        "learn_cards": [
            {
                "heading": "What is Machine Learning?",
                "text": "Machine learning is the way AI solves the unstructured data problem. Traditional programmable computers are deterministic. They say yes or no based on pre-written rules. Machine learning is probabilistic. It never says yes or no. Instead it says something like I am 84% confident this is the fastest route. It constructs every possible answer and compares them in real time, including all changing variables. Most importantly, machine learning can predict outcomes and it can learn and improve by itself over time without being reprogrammed."
            },
            {
                "heading": "Supervised Learning",
                "text": "Supervised learning is about providing AI with enough labelled examples to make accurate predictions. Labelled data is data grouped into samples tagged with the correct answer. You tell the model what the key characteristics of a thing are and what the thing actually is. For example, the machine is shown thousands of photos labelled dog. It learns to identify the pattern for dog. When shown a new photo it has never seen, it can correctly identify it as a dog with high accuracy. This is called a classification problem and it is at the heart of how image recognition, spam filters, and medical diagnosis tools work."
            },
            {
                "heading": "Unsupervised and Reinforcement Learning",
                "text": "In unsupervised learning, a machine is fed a large amount of unlabelled data and asked to find patterns entirely by itself. No right or wrong answers are provided. A bank could feed customer financial data to an unsupervised algorithm and it would discover natural groupings of similar customers without being told what categories to create. Reinforcement learning works through trial and error. The algorithm learns by receiving positive rewards for correct predictions and penalties for incorrect ones. Over time its predictions grow more accurate automatically, without any human intervention."
            },
            {
                "heading": "The Three Levels of AI Revisited",
                "text": "Now that you understand machine learning, the three levels of AI make deeper sense. Narrow AI specialises in one area. It can look up information it was trained on but cannot apply that knowledge elsewhere. Broad AI, available today, can structure vast amounts of unstructured data and find patterns to extend human expertise. General AI, expected perhaps 25 years from now, would be superintelligent, smarter than the best human brains in practically every field, including scientific creativity, general wisdom, and social skills. It will give machines the ability to interact in genuinely human-like ways."
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
    # ── "The Lexicon" — the Library's whole Trial is a click-to-ink matching board ──
    # Each item is ONE concept card (kind: "matching") whose CORRECT scenario is held
    # SERVER-SIDE only (q["correct"] = a scenario id `sid`, never in the DOM). The
    # server draws 4 concepts, adds 2 deterministic DECOY scenarios (from undrawn
    # concepts), shuffles the pool, and grades each concept INDEPENDENTLY through the
    # shared core (chosen scenario id == correct = 1 point). Scenarios are concrete
    # CASES (transfer, not recall), authored against the Library's taught definitions;
    # every case fits exactly one concept. `sid`s are decoupled from concept keys so
    # the DOM never links a concept to its answer.
    "library": [
        {
            "key": "lex_narrow", "kind": "matching", "concept_tag": "three_levels",
            "concept": "Narrow AI",
            "sid": "sc_a7", "correct": "sc_a7",
            "scenario": "A spam filter that flags junk mail it has never seen before, yet it can do nothing else.",
            "feedback_correct": "Narrow AI, built for one task and unable to step outside it, exactly like a spam filter.",
            "feedback_wrong": "This case is Narrow AI: built for one specific task (filtering spam) and unable to do anything else.",
            "explanation": "Narrow AI is built for one specific task and can't generalise. Spam filters, face-unlock and chess engines are all narrow.",
            "hint": "One job, done well, and nothing beyond it. Which level is locked to a single task?",
        },
        {
            "key": "lex_broad", "kind": "matching", "concept_tag": "three_levels",
            "concept": "Broad AI",
            "sid": "sc_b3", "correct": "sc_b3",
            "scenario": "A delivery company fuses its own vision, route-planning and scheduling systems into one integrated platform, trained on its own delivery data.",
            "feedback_correct": "Broad AI, several narrow components integrated into one business process on the organisation's own data.",
            "feedback_wrong": "This case is Broad AI (IBM's term): several narrow systems integrated into one business process, trained on the organisation's own data.",
            "explanation": "Broad AI integrates several narrow components into one business process trained on an organisation's own data.",
            "hint": "Several narrow systems combined into one business process on a company's own data, IBM's middle of the spectrum.",
        },
        {
            "key": "lex_general", "kind": "matching", "concept_tag": "three_levels",
            "concept": "General AI",
            "sid": "sc_c1", "correct": "sc_c1",
            "scenario": "A machine that could take on any intellectual task a person can, which no one has built yet.",
            "feedback_correct": "General AI, human-level across any domain, and it does not exist yet.",
            "feedback_wrong": "This case is General AI: reasoning across any domain like a human. It remains a research goal; it doesn't exist yet.",
            "explanation": "General AI would reason and transfer knowledge across any domain like a human, but it does not exist yet.",
            "hint": "Any task a human can do, but no one has built it. Which level is still a research goal?",
        },
        {
            "key": "lex_augmented", "kind": "matching", "concept_tag": "augmented_intelligence",
            "concept": "Augmented Intelligence",
            "sid": "sc_d9", "correct": "sc_d9",
            "scenario": "AI pre-screens loan applications and flags the risky ones, but a human officer makes the final decision.",
            "feedback_correct": "Augmented intelligence, where the AI assists and the human keeps the final call and the accountability.",
            "feedback_wrong": "This case is augmented intelligence: the AI does the heavy lifting, but a human keeps the decision and the accountability.",
            "explanation": "Augmented intelligence amplifies human judgement rather than replacing it; a human always keeps the final call.",
            "hint": "The AI flags, but a person decides. What do we call AI that assists rather than replaces?",
        },
        {
            "key": "lex_notai", "kind": "matching", "concept_tag": "what_is_ai",
            "concept": "Not AI at all",
            "sid": "sc_e5", "correct": "sc_e5",
            "scenario": "A thermostat that switches the heating on whenever the room drops below 18°C.",
            "feedback_correct": "Not AI. It follows one fixed rule and never learns patterns from data.",
            "feedback_wrong": "This case is not AI: it follows a single fixed rule (below 18°C → heat on) and learns nothing from data.",
            "explanation": "AI learns patterns from data to make predictions; a fixed if-then rule that never learns is not AI.",
            "hint": "The same fixed rule every time, with no learning from data. Is that AI at all?",
        },
        {
            "key": "lex_analysis", "kind": "matching", "concept_tag": "analysis_prediction",
            "concept": "Analysis (finding the pattern)",
            "sid": "sc_f2", "correct": "sc_f2",
            "scenario": "Combing through millions of past card transactions to surface the recurring pattern that marks fraud.",
            "feedback_correct": "Analysis, examining large amounts of data to find the hidden pattern, the first of AI's two steps.",
            "feedback_wrong": "This case is Analysis: AI examining large amounts of data to find a hidden pattern, before any prediction is made.",
            "explanation": "Analysis is AI's first step: examine large amounts of data to find hidden patterns.",
            "hint": "Surfacing a hidden pattern from a mountain of data, which of AI's two steps is that?",
        },
        {
            "key": "lex_prediction", "kind": "matching", "concept_tag": "analysis_prediction",
            "concept": "Prediction (naming the outcome)",
            "sid": "sc_g8", "correct": "sc_g8",
            "scenario": "Forecasting how much rain will fall tomorrow from decades of weather records.",
            "feedback_correct": "Prediction, using what was learned to name an outcome, AI's second step.",
            "feedback_wrong": "This case is Prediction: AI's second step, using the learned pattern to predict an outcome (tomorrow's rainfall).",
            "explanation": "Prediction is AI's second step: based on the analysis, predict an outcome.",
            "hint": "Naming tomorrow's outcome from past data, which of AI's two steps is that?",
        },
    ],

    "chronicle": [
        {
            "key": "ch_s1",
            "question": "A museum shows an old machine that took stacks of raw figures and arranged them into neat tables so clerks could finally spot trends. Which era does it belong to?",
            "options": {
                "A": "The Era of Programming",
                "B": "The Era of Tabulation",
                "C": "The Era of AI",
                "D": "The Industrial Revolution"
            },
            "correct": "B",
            "feedback_correct": "Correct. Tabulation was about sorting raw data into structure to reveal insight, long before machines could 'think'.",
            "feedback_wrong": "Sorting raw data into structured tables to reveal insight is the hallmark of the Era of Tabulation; it came before programmable computers and before AI.",
            "explanation": "The Era of Tabulation organised data into tables so patterns could surface, the leap beyond mere counting.",
            "hint": "This era only organised data; it did not run programs or learn."
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
            "feedback_correct": "Correct. First we sorted data (Tabulation), then we ran instructions (Programming), then machines began to learn (AI).",
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
            "feedback_correct": "Correct. Dartmouth 1956 is where the term 'artificial intelligence' was coined.",
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
                "D": "Computers were simply too expensive for labs to afford"
            },
            "correct": "A",
            "feedback_correct": "Correct. Machines were too slow (limited calculating power) and could not hold enough (limited storage).",
            "feedback_wrong": "The First Winter came from two hard technical limits: limited calculating power (too slow) and limited information storage (too little memory to reason about the world).",
            "explanation": "Early AI hit two walls (not enough compute and not enough storage), so promises went unmet and funding collapsed.",
            "hint": "Both limits are about the machines themselves, speed and memory."
        },
        {
            "key": "ch_s5",
            "question": "After the expert-systems boom collapsed, what finally brought AI out of the Second Winter in the mid-1990s?",
            "options": {
                "A": "A brand-new programming language",
                "B": "Processing power finally becoming fast enough",
                "C": "A new algorithm that needed no extra computing power",
                "D": "The arrival of the internet and its flood of data"
            },
            "correct": "B",
            "feedback_correct": "Correct. By the mid-1990s, processing power finally caught up with ambition, and the thaw began.",
            "feedback_wrong": "The thaw came because processing power finally became fast enough for AI's ambitions. Soon after, Deep Blue won at chess.",
            "explanation": "The Second Winter ended when hardware caught up: fast enough processing made the old ambitions achievable (Deep Blue, 1997).",
            "hint": "Think about what the machines had been lacking all along, raw speed."
        },
        {
            "key": "ch_s6",
            "question": "Which IBM system, searching around 200 million positions per second, defeated the reigning world chess champion in 1997?",
            "options": {
                "A": "Watson",
                "B": "ENIAC",
                "C": "Deep Blue",
                "D": "The Stanford self-driving robot"
            },
            "correct": "C",
            "feedback_correct": "Correct. Deep Blue beat the world chess champion in 1997. (Watson won Jeopardy! in 2011.)",
            "feedback_wrong": "Watson won Jeopardy! in 2011 and ENIAC was a 1940s calculator. The chess victory of 1997 belonged to IBM's Deep Blue.",
            "explanation": "Deep Blue's 1997 chess win was a landmark of the thaw; Watson's Jeopardy! win followed in 2011.",
            "hint": "It played chess, not Jeopardy!."
        },

        # ── "The Broken Timeline" — the Chronicle's signature ORDERING items ──
        # The learner repairs a scrambled sequence of events. Authored content (not
        # model-generated) so grading is deterministic. `kind: "order"` marks it; the
        # CORRECT sequence is the authored order of `events` (ids), held server-side
        # only — never emitted to the Trial DOM (the client renders the events
        # SHUFFLED via the shuffle_events filter). Graded all-or-nothing through the
        # shared core: 1 point only if the whole sequence matches. Both are pinned for
        # the Chronicle so sequencing is the Trial's dominant mode (2 order + 2 MCQ).
        {
            "key": "chr_order_eras",
            "kind": "order",
            "concept": "eras_and_winters",
            "question": "The archive's timeline has been corrupted. Restore these events to their true chronological order, earliest at the top.",
            "events": [
                {"id": "ev_tabulation", "label": "The Era of Tabulation, sorting raw data into tables"},
                {"id": "ev_programming", "label": "The Era of Programming, ENIAC runs stored instructions (1940s)"},
                {"id": "ev_dartmouth", "label": "Dartmouth coins the term “artificial intelligence” (1956)"},
                {"id": "ev_first_winter", "label": "The First AI Winter, funding collapses (1970s)"},
                {"id": "ev_deep_blue", "label": "Deep Blue defeats the world chess champion (1997)"},
            ],
            "feedback_correct": "Restored. Tabulation gave way to Programming, then Dartmouth named the field in 1956; the First Winter froze it in the 1970s, and Deep Blue marked the thaw in 1997.",
            "feedback_wrong": "Not the true order. It runs: Tabulation → Programming (ENIAC, 1940s) → Dartmouth 1956 → the First Winter (1970s) → Deep Blue (1997).",
            "explanation": "The eras run Tabulation → Programming → the naming of AI at Dartmouth (1956) → the First Winter (1970s) → Deep Blue's 1997 victory in the thaw.",
            "hint": "Start with sorting data by hand and end with a machine beating a chess champion. Where do the 1940s, 1956, the 1970s and 1997 fall?",
        },
        {
            "key": "chr_order_winter",
            "kind": "order",
            "concept": "eras_and_winters",
            "question": "Reassemble the causal chain that led to an AI Winter, the first cause at the top.",
            "events": [
                {"id": "ev_boom", "label": "Expert systems boom on million-dollar mainframes"},
                {"id": "ev_pcs", "label": "Cheaper personal computers outpace those mainframes"},
                {"id": "ev_collapse", "label": "The expert-systems market collapses"},
                {"id": "ev_funding", "label": "Investment and funding dry up"},
                {"id": "ev_winter", "label": "An AI Winter sets in"},
            ],
            "feedback_correct": "Exactly the chain: the boom drew investment, cheap PCs undercut the costly mainframes, the market collapsed, funding dried up, and the Winter set in.",
            "feedback_wrong": "The chain runs: expert-systems boom → cheap PCs outpace mainframes → the market collapses → funding dries up → the Winter sets in.",
            "explanation": "Expert systems boomed on costly mainframes; cheaper PCs overtook them, the market collapsed, funding evaporated, and an AI Winter followed.",
            "hint": "Begin with the thing that was thriving, and end with the freeze. What has to fail before funding disappears?",
        }
    ],

    # ── "The Classification Board" — the AI Lab's whole Trial is one drag-and-drop
    # sorting task. Each item is ONE data object (kind: "sort") whose CORRECT bin is
    # held SERVER-SIDE only (q["correct"] = a DATA_BINS id) — never in the DOM. The
    # server draws 4, renders them shuffled as draggable cards, and grades each
    # INDEPENDENTLY through the shared core (selected bin == correct bin = 1 point).
    # Each object classifies unambiguously: dark-data objects are defined by being
    # collected-but-never-used; the others by FORMAT with no "unused" framing (so
    # they can't defensibly be dark). Aim ~8-10+ so the 4-object draw varies.
    "ai_lab": [
        {"key": "lab_o1", "kind": "sort", "concept": "data_types", "icon": "📊", "correct": "structured",
         "question": "A spreadsheet of customer names, ages and account balances in fixed columns",
         "feedback_correct": "Structured. Fixed fields in labelled columns, easily queried with SQL.",
         "feedback_wrong": "This is STRUCTURED data: predefined columns (name, age, balance) that fit neat rows and are SQL-queryable.",
         "explanation": "Rows-and-columns with a fixed schema is the definition of structured data.",
         "hint": "It fits neat labelled rows and columns you could query with SQL."},
        {"key": "lab_o2", "kind": "sort", "concept": "data_types", "icon": "📈", "correct": "structured",
         "question": "A relational table of daily stock prices, one row per date",
         "feedback_correct": "Structured. A fixed table schema, one row per date.",
         "feedback_wrong": "This is STRUCTURED data: a rigid table with one row per date and fixed columns.",
         "explanation": "A relational table with a fixed schema is structured data.",
         "hint": "One row per date, fixed columns. What kind of data has a rigid table schema?"},
        {"key": "lab_o3", "kind": "sort", "concept": "data_types", "icon": "🗃️", "correct": "structured",
         "question": "A payroll database with fixed fields for employee ID, salary and start date",
         "feedback_correct": "Structured. Predefined fields in a rigid schema.",
         "feedback_wrong": "This is STRUCTURED data: fixed fields (ID, salary, start date) in a rigid, queryable schema.",
         "explanation": "Fixed, predefined fields in a database are structured data.",
         "hint": "Predefined fields in a rigid schema. Structured, semi or unstructured?"},

        {"key": "lab_o4", "kind": "sort", "concept": "data_types", "icon": "🏷️", "correct": "semi",
         "question": "A stream of JSON API logs, each tagged with keys but no fixed table schema",
         "feedback_correct": "Semi-structured. Tags and keys give partial order without a rigid table.",
         "feedback_wrong": "This is SEMI-STRUCTURED data: JSON carries keys/tags that make it machine-readable without a fixed table schema.",
         "explanation": "Tags/keys without a rigid schema (JSON, XML) is semi-structured, the bridge between structured and unstructured.",
         "hint": "It has keys and tags but no rigid table. What sits between structured and unstructured?"},
        {"key": "lab_o5", "kind": "sort", "concept": "data_types", "icon": "🔖", "correct": "semi",
         "question": "An XML product feed where every entry carries its own descriptive tags",
         "feedback_correct": "Semi-structured. XML tags give partial structure without a rigid schema.",
         "feedback_wrong": "This is SEMI-STRUCTURED data: XML tags give partial organisation without a fixed table schema.",
         "explanation": "XML with self-describing tags is a classic semi-structured format.",
         "hint": "Self-describing tags, but no fixed table. Which category is that?"},
        {"key": "lab_o6", "kind": "sort", "concept": "data_types", "icon": "📟", "correct": "semi",
         "question": "Sensor readings streamed as key–value pairs with no rigid table schema",
         "feedback_correct": "Semi-structured. Key–value pairs are machine-readable without a fixed schema.",
         "feedback_wrong": "This is SEMI-STRUCTURED data: key–value pairs carry partial structure without a rigid table.",
         "explanation": "Key–value pairs with no fixed schema are semi-structured.",
         "hint": "Key–value pairs, no rigid table. Between structured and unstructured."},

        {"key": "lab_o7", "kind": "sort", "concept": "data_types", "icon": "📧", "correct": "unstructured",
         "question": "Customer support emails and call recordings the support team works through daily",
         "feedback_correct": "Unstructured. Free-text and audio with no rows-and-columns schema.",
         "feedback_wrong": "This is UNSTRUCTURED data: emails and audio have no fixed schema (and the team actively uses them, so it isn't dark data).",
         "explanation": "Native-format text and audio with no schema is unstructured; it's in active use, so not dark.",
         "hint": "Free-text and audio, no schema, and it's actively used. Which category?"},
        {"key": "lab_o8", "kind": "sort", "concept": "data_types", "icon": "🖼️", "correct": "unstructured",
         "question": "The photo library of product images the marketing team publishes each week",
         "feedback_correct": "Unstructured. Images have no schema, and they're actively used, so not dark.",
         "feedback_wrong": "This is UNSTRUCTURED data: images have no rows-and-columns schema, and they're actively published (so not dark data).",
         "explanation": "Images in native form have no schema, so unstructured; actively used, so not dark.",
         "hint": "Images with no schema, published weekly. Which category (and it's not dark)?"},
        {"key": "lab_o9", "kind": "sort", "concept": "data_types", "icon": "🎙️", "correct": "unstructured",
         "question": "Voicemail messages the call centre transcribes and acts on every day",
         "feedback_correct": "Unstructured. Raw audio with no schema, and it's used daily, so not dark.",
         "feedback_wrong": "This is UNSTRUCTURED data: audio has no schema, and it's transcribed daily (so not dark data).",
         "explanation": "Raw audio has no schema, so unstructured; used daily, so not dark.",
         "hint": "Raw audio, no schema, used every day. Which category?"},

        {"key": "lab_o10", "kind": "sort", "concept": "data_types", "icon": "📹", "correct": "dark",
         "question": "Six years of CCTV footage that no one has ever reviewed",
         "feedback_correct": "Dark data. Collected and stored, but never used. That's what makes it dark.",
         "feedback_wrong": "This is DARK DATA: the defining trait is that it's collected but NEVER used or reviewed, regardless of its format.",
         "explanation": "Dark data is information collected and stored but never used. Here, footage nobody has reviewed.",
         "hint": "It's kept but NOBODY has ever looked at it. What do we call collected-but-unused data?"},
        {"key": "lab_o11", "kind": "sort", "concept": "data_types", "icon": "🗄️", "correct": "dark",
         "question": "Archived server logs the company keeps but never analyses",
         "feedback_correct": "Dark data. Stored but never analysed.",
         "feedback_wrong": "This is DARK DATA: it's retained but never analysed. Collected-but-unused is the signature of dark data.",
         "explanation": "Kept but never analysed = dark data, whatever its underlying format.",
         "hint": "Retained but never analysed. Which category is defined by being unused?"},
        {"key": "lab_o12", "kind": "sort", "concept": "data_types", "icon": "💾", "correct": "dark",
         "question": "Old transaction records, neatly tabulated, sitting in a legacy system nobody queries",
         "feedback_correct": "Dark data. Even tidy, structured records are dark if they're never used.",
         "feedback_wrong": "This is DARK DATA: though neatly structured, nobody queries it. Dark data can be any type, including tidy tables.",
         "explanation": "Dark data can be perfectly structured; what makes it dark is that it's never used. Here, records nobody queries.",
         "hint": "Tidy tables, but nobody queries them. Dark data can be any type. What defines it?"}
    ],

    "observatory": [
        {
            "key": "obs_s1",
            "question": "A team has 50,000 emails already labelled \"spam\" or \"not spam\" and wants to train a filter. Which ML method fits?",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "Deterministic rule-based filtering"
            },
            "correct": "A",
            "feedback_correct": "Right. Labelled data with known answers is the hallmark of supervised learning.",
            "feedback_wrong": "This is supervised learning. It trains on labelled examples (spam/not-spam) and learns to predict the label for new, unseen emails.",
            "explanation": "Right. Labelled data with known answers is the hallmark of supervised learning.",
            "hint": "The training data already carries the correct answers. Which method learns from labelled examples?"
        },
        {
            "key": "obs_s2",
            "question": "A streaming service wants to group viewers with similar tastes, but nobody has defined what the groups should be. Which method?",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "Sorting them with a fixed database query"
            },
            "correct": "B",
            "feedback_correct": "Correct. With no predefined labels, the model discovers clusters on its own.",
            "feedback_wrong": "This is unsupervised learning. It finds hidden structure in unlabelled data. Grouping viewers with no preset categories is a classic clustering (segmentation) task.",
            "explanation": "Correct. With no predefined labels, the model discovers clusters on its own.",
            "hint": "There are no predefined groups or labels. The model must find the patterns itself. Which method is that?"
        },
        {
            "key": "obs_s3",
            "question": "Amazon trains warehouse robots to pick and move goods, rewarding good actions and penalising mistakes so they improve through trial and error. This is:",
            "options": {
                "A": "Supervised learning",
                "B": "Unsupervised learning",
                "C": "Reinforcement learning",
                "D": "Deterministic pre-programmed control"
            },
            "correct": "C",
            "feedback_correct": "Yes. Learning through rewards and feedback while interacting with an environment is reinforcement learning.",
            "feedback_wrong": "This is reinforcement learning. An agent learns which actions maximise reward through trial and error, exactly like game-playing AIs and warehouse robots. There's no labelled answer key.",
            "explanation": "Yes. Learning through rewards and feedback while interacting with an environment is reinforcement learning.",
            "hint": "The robot learns from rewards and penalties by trial and error. Which method uses feedback from an environment?"
        },
        {
            "key": "obs_s4",
            "question": "A calculator returns exactly the same answer every time you enter 7 × 8, and an autonomous car's braking logic is built to behave the same predictable way. These are examples of:",
            "options": {
                "A": "Probabilistic systems",
                "B": "Reinforcement-learning agents",
                "C": "Machine-learning models that adapt over time",
                "D": "Deterministic systems"
            },
            "correct": "D",
            "feedback_correct": "Right. Same input, same output, no randomness. Ideal where predictability is critical.",
            "feedback_wrong": "These are deterministic. They map the same input to the same output every time. That predictability is exactly what you want for braking or calculation.",
            "explanation": "Right. Same input, same output, no randomness. Ideal where predictability is critical.",
            "hint": "Same input, same output, every single time. Is that predictable behaviour deterministic or probabilistic?"
        },
        {
            "key": "obs_s5",
            "question": "A medical AI outputs \"78% likelihood this scan shows a tumour\" instead of a flat yes/no. What kind of system is this, and why is it useful?",
            "options": {
                "A": "Probabilistic, it expresses confidence/uncertainty, helping doctors prioritise",
                "B": "Deterministic, it's always exact",
                "C": "A rule-based system following fixed medical guidelines",
                "D": "An overfitted model that is just guessing"
            },
            "correct": "A",
            "feedback_correct": "Exactly. A confidence score lets a clinician weigh uncertainty rather than trust a false black-and-white answer.",
            "feedback_wrong": "This is probabilistic. It expresses outputs as likelihoods. A \"78% likelihood\" helps a doctor prioritise and handle uncertainty, which is far safer in medicine than false certainty.",
            "explanation": "Exactly. A confidence score lets a clinician weigh uncertainty rather than trust a false black-and-white answer.",
            "hint": "The output is a confidence percentage, not a flat yes/no. Which kind of system expresses likelihoods?"
        },
        {
            "key": "obs_s6",
            "question": "A team is training a four-legged robot to walk across rough ground. It is given no examples of \"correct\" steps; instead it scores points each time it stays balanced and loses points each time it stumbles, and over thousands of attempts it grows steadier on its own. Which machine-learning method is this?",
            "options": {
                "A": "Supervised learning",
                "B": "Reinforcement learning",
                "C": "Unsupervised learning",
                "D": "Deterministic control with pre-written rules"
            },
            "correct": "B",
            "feedback_correct": "Right. With no answer key and only a score to learn from, this is reinforcement learning: the robot improves its own actions through repeated attempts.",
            "feedback_wrong": "This is reinforcement learning. There is no labelled set of correct steps to copy. The robot only receives higher or lower scores as it tries, and it improves its actions from that feedback alone.",
            "explanation": "No labelled \"correct move\" exists. The robot improves only from the score it earns as it practises: higher when it stays balanced, lower when it stumbles. Learning from that feedback through repeated attempts is reinforcement learning.",
            "hint": "There is no answer key. The robot only gets a better or worse score each time it tries. Which method learns from that kind of feedback rather than from labelled examples?"
        },

        # ── "The Hallucination Hunt" — the Observatory's WHOLE Trial ──
        # Professor Atlas states four claims; exactly ONE is a hallucination
        # (confidently worded but false). Authored content (NOT model-generated) so
        # grading is deterministic and independent of Ollama. Each set is an ordinary
        # 4-option MCQ where `correct` is the FALSE claim (the one to catch), so it
        # grades through the normal server path as 1 point, INDEPENDENT of the other
        # rounds. The Observatory Trial draws 4 of these sets (see TRIAL_DRAW_ONLY),
        # so all four rounds are hunts; the plain obs_s* MCQs stay defined below but
        # are retired from the draw. shuffle_options randomises display order, so the
        # false claim's identity is never in the DOM and has no positional tell.
        # `hunt: True` switches on the "Atlas speaking" presentation in
        # _trial_core.html; grading is unaffected. `false_concept` names the taught
        # concept each set's FALSE claim tests, so bias, nlp and few_shot_prompting
        # are finally assessed by a graded item, not only true filler.
        {
            "key": "obs_hunt1",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "ml_methods",
            "question": "Four of my readings on how machines learn. One is a hallucination: confident, but false. Which?",
            "options": {
                "A": "Supervised learning trains on labelled examples, where each item already carries its correct answer.",
                "B": "Unsupervised learning finds structure in data that has no labelled outcomes.",
                "C": "Reinforcement learning needs a labelled dataset of correct actions before any training can start.",
                "D": "A probabilistic model reports its answer as a confidence rather than a flat yes or no."
            },
            "correct": "C",
            "feedback_correct": "Well caught. Reinforcement learning has no labelled set of correct actions to copy; it learns from rewards and penalties as it tries. The other three readings were true.",
            "feedback_wrong": "That reading was true. The false one claimed reinforcement learning needs a labelled dataset of correct actions first. It does not: it learns from rewards and penalties by trial and error.",
            "explanation": "Reinforcement learning learns from reward and penalty as it acts; it has no labelled dataset of correct actions to imitate. That was the false claim."
        },
        {
            "key": "obs_hunt2",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "llm",
            "question": "Here are four claims from my notes. Exactly one is false. Find it.",
            "options": {
                "A": "Overfitting is when a model does well on its training data but poorly on new data.",
                "B": "A large language model checks each statement against a stored database of facts before it answers.",
                "C": "Few-shot prompting guides a model by placing a few worked examples in the prompt.",
                "D": "A model trained on biased data can carry that bias into its predictions."
            },
            "correct": "B",
            "feedback_correct": "Exactly, and this one is close to home. A language model like me predicts likely text; it does not look anything up or check a database. That is why I can state a falsehood fluently.",
            "feedback_wrong": "That reading was true. The false one claimed a large language model checks each statement against a database of facts. It does no such thing; it predicts likely text, which is why confident wording is never proof.",
            "explanation": "A large language model predicts the most likely next text from patterns in its training; it does not consult or verify against a fact database. That was the false claim."
        },
        {
            "key": "obs_hunt3",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "overfitting",
            "question": "Four statements about what you have studied. One is a hallucination. Catch it.",
            "options": {
                "A": "Natural language processing lets a model work with human language such as emails and speech.",
                "B": "A deterministic system returns the same output every time for the same input.",
                "C": "A fluent, confident answer from a model can still be completely false.",
                "D": "If a model scores full marks on its training data, it is certain to do just as well on new data."
            },
            "correct": "D",
            "feedback_correct": "Well caught. Full marks on training data often means the model has memorised the examples, which is overfitting, so it can fail on new data. Performance on unseen data is what counts.",
            "feedback_wrong": "That reading was true. The false one promised that full training accuracy guarantees success on new data. It does not; that is often a sign of overfitting, not mastery.",
            "explanation": "Perfect training accuracy can signal overfitting rather than genuine learning; a model is judged on new, unseen data. That was the false claim."
        },
        {
            "key": "obs_hunt4",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "bias",
            "question": "I offer four readings on machine learning. One of them is false. Which one?",
            "options": {
                "A": "A model trained on biased data will correct that bias on its own once it sees enough examples.",
                "B": "Reinforcement learning improves by earning rewards for good actions and penalties for poor ones.",
                "C": "Supervised learning can predict a category or a number once it has been trained on labelled data.",
                "D": "A large language model has no real understanding; it predicts the most likely next words."
            },
            "correct": "A",
            "feedback_correct": "Well caught. More data does not remove bias; a model repeats whatever bias sits in its training data. It takes varied, fair data to fix, not simply more of the same.",
            "feedback_wrong": "That reading was true. The false one claimed a model corrects its own bias once it sees enough examples. It does not; more biased data just repeats the bias. Varied, fair data is what matters.",
            "explanation": "A model absorbs the bias in its training data and repeats it; a larger amount of the same biased data does not correct it. That was the false claim."
        },
        {
            "key": "obs_hunt5",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "nlp",
            "question": "Four claims, navigator. Three are sound; one is a confident falsehood. Name it.",
            "options": {
                "A": "Unsupervised learning groups similar items together without being told the groups in advance.",
                "B": "Natural language processing can handle written text but not the spoken word.",
                "C": "Overfitting shows up as strong results on training data and weak results on new data.",
                "D": "A probabilistic system can express its answer as a percentage of confidence."
            },
            "correct": "B",
            "feedback_correct": "Well caught. Natural language processing works with both writing and speech; voice assistants are a taught example of it handling the spoken word.",
            "feedback_wrong": "That reading was true. The false one claimed natural language processing cannot handle the spoken word. It can: it powers voice assistants as well as written text.",
            "explanation": "Natural language processing works with human language in both writing and speech, including voice assistants. That was the false claim."
        },
        {
            "key": "obs_hunt6",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "few_shot_prompting",
            "question": "Read these four carefully. One is a hallucination dressed as fact. Which?",
            "options": {
                "A": "Supervised learning needs labelled examples whose correct answers are already known.",
                "B": "A deterministic calculator returns the same result for the same sum every time.",
                "C": "Few-shot prompting means writing one long, detailed instruction and giving the model no examples.",
                "D": "An AI can state a false fact with complete confidence, so its answers are worth checking."
            },
            "correct": "C",
            "feedback_correct": "Well caught. Few-shot prompting is defined by including a few worked examples in the prompt so the model copies the pattern. An instruction with no examples is not few-shot prompting.",
            "feedback_wrong": "That reading was true. The false one described few-shot prompting as a long instruction with no examples. Few-shot prompting is the opposite: it includes a few worked examples.",
            "explanation": "Few-shot prompting works by placing a few worked examples in the prompt so the model copies the pattern; an instruction with no examples is not few-shot. That was the false claim."
        },
        {
            "key": "obs_hunt7",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "deterministic_probabilistic",
            "question": "Four of my readings on how machines work. Spot the one that is false.",
            "options": {
                "A": "Reinforcement learning has no answer key; it learns from rewards and penalties as it goes.",
                "B": "A probabilistic system always returns exactly the same answer for the same input.",
                "C": "Natural language processing powers tools such as translation and voice assistants.",
                "D": "Broad AI is available today and combines several narrow systems into one."
            },
            "correct": "B",
            "feedback_correct": "Well caught. Returning the same answer every time describes a deterministic system. A probabilistic system weighs likelihoods and reports confidence, so it can handle uncertainty.",
            "feedback_wrong": "That reading was true. The false one claimed a probabilistic system always returns the same answer. That describes a deterministic system; a probabilistic one expresses confidence and can vary.",
            "explanation": "A system that always returns the same output for the same input is deterministic; a probabilistic system expresses likelihoods rather than one fixed answer. That was the false claim."
        },
        {
            "key": "obs_hunt8",
            "hunt": True,
            "concept": "hallucination",
            "false_concept": "hallucination",
            "question": "Four claims about what machines can and cannot do. One is false. Find it.",
            "options": {
                "A": "Bias in a model usually comes from bias already present in its training data.",
                "B": "Few-shot prompting steers a model by showing it a few examples first.",
                "C": "When a language model is unsure of a fact, it flags that it is guessing instead of answering with confidence.",
                "D": "Unsupervised learning finds patterns in data that carries no labels."
            },
            "correct": "C",
            "feedback_correct": "Well caught. A language model does not know what it does not know; it predicts likely text and can state a falsehood with full confidence, so it will not warn you when it is unsure.",
            "feedback_wrong": "That reading was true. The false one claimed a model flags when it is guessing. It does not: it predicts likely text and can sound completely certain while being wrong, which is why its answers need checking.",
            "explanation": "A language model predicts plausible text rather than checking facts, and it can state a falsehood with total confidence; it does not flag its own uncertainty. That was the false claim."
        }
    ]
}

# How many questions each Trial shows (and grades). Kept at 4 — PASS_THRESHOLD
# of 3/4 is unchanged.
TRIAL_COUNT = 4

# Questions that must always appear in a location's Trial. The AI Lab pins its
# hands-on data-sorting diagnostic (lab_q3, rendered as the sorting machine).
# ── Data-classification bins for the AI Lab's "Classification Board" (sort items).
# Rendered as neutral drop targets; each object's correct bin lives only in its
# question's `correct` field (a bin id here), never in the Trial DOM.
DATA_BINS = [
    {"id": "structured", "label": "STRUCTURED"},
    {"id": "semi", "label": "SEMI-STRUCTURED"},
    {"id": "unstructured", "label": "UNSTRUCTURED"},
    {"id": "dark", "label": "DARK DATA"},
]
BIN_IDS = {b["id"] for b in DATA_BINS}
BIN_LABELS = {b["id"]: b["label"] for b in DATA_BINS}


PINNED_QUESTIONS = {
    # The AI Lab no longer pins a single item — its whole Trial is the sorting board
    # (4 `sort` objects drawn from the bank, each graded independently).
    # The Observatory no longer pins a single hunt: its WHOLE Trial is the
    # Hallucination Hunt now, so all 4 rounds are hunts drawn at random (see
    # TRIAL_DRAW_ONLY below) rather than 1 pinned hunt plus 3 plain MCQs.
    # The Chronicle pins BOTH "Broken Timeline" ordering items, so sequencing is the
    # Trial's dominant mode (2 ordering + 2 sampled MCQs).
    "chronicle": ["chr_order_eras", "chr_order_winter"],
}


# Some Trials draw from only PART of their bank; the rest of the bank stays defined
# (nothing deleted, so a revert is a one-line change) but is not offered in the
# draw. The Observatory Trial is entirely "The Hallucination Hunt": it draws only
# hunt sets, so the plain obs_s* MCQs remain in the bank for reference but are
# retired from the composition. The value is the item flag a Trial restricts to.
TRIAL_DRAW_ONLY = {
    "observatory": "hunt",   # draw only items whose q["hunt"] is truthy
}


# ── Ordering items ("Broken Timeline") — server-authoritative sequence grading ──
def order_canonical(q):
    """The CORRECT sequence for an ordering item: its event ids in authored order,
    comma-joined. Server-side only — never rendered into the Trial DOM."""
    return ",".join(e["id"] for e in q.get("events", []))


def normalize_order(value, q):
    """Validate + normalise a submitted ordering.

    Returns the comma-joined id string if `value` lists EXACTLY this item's event
    ids — each exactly once, none missing, none extra (the shown_keys discipline);
    otherwise None, so a forged/malformed sequence is never scored as correct.
    """
    if not value:
        return None
    ids = [s for s in str(value).split(",") if s]
    valid = [e["id"] for e in q.get("events", [])]
    if sorted(ids) != sorted(valid):
        return None
    return ",".join(ids)


# ── Matching items ("The Lexicon") — server-authoritative concept↔scenario pairing ──
def _matching_bank(location_key):
    return [q for q in QUIZZES.get(location_key, []) if q.get("kind") == "matching"]


def lexicon_pool(location_key, concept_keys):
    """The scenario pool for a Lexicon board: the drawn concepts' correct scenarios
    PLUS 2 deterministic decoy scenarios (from undrawn concepts). Returns a list of
    {sid, text}. Deterministic given `concept_keys`, so the pool re-derives identically
    at grade time (no per-attempt storage). The correct/decoy scenarios are
    indistinguishable in the result — only their `sid` + text, no 'decoy' marker.
    """
    by_key = {q["key"]: q for q in _matching_bank(location_key)}
    drawn = [by_key[k] for k in concept_keys if k in by_key]
    pool = [{"sid": q["sid"], "text": q["scenario"]} for q in drawn]
    undrawn = sorted(
        (q for q in by_key.values() if q["key"] not in concept_keys),
        key=lambda q: q["key"],
    )
    for q in undrawn[:2]:                       # 2 deterministic decoys
        pool.append({"sid": q["sid"], "text": q["scenario"]})
    return pool


def lexicon_pool_sids(location_key, concept_keys):
    """The set of scenario ids a Lexicon submission may legally reference."""
    return {s["sid"] for s in lexicon_pool(location_key, concept_keys)}


def scenario_text(location_key, sid):
    """The case text for a scenario id (results/feedback only; never the pairing)."""
    for q in _matching_bank(location_key):
        if q.get("sid") == sid:
            return q["scenario"]
    return None


def select_trial_questions(location_key, count=TRIAL_COUNT):
    """Pick which question keys to show for one Trial attempt.

    Pinned entries are always included and kept first. A pinned entry may be
    either a single key (e.g. a single always-shown item) or a GROUP — a list/tuple
    of interchangeable keys. For a group the server picks exactly ONE member per
    attempt and the WHOLE group is excluded from the random remainder, so only the
    chosen set ever appears. The remainder is sampled at random from the bank.

    A location listed in TRIAL_DRAW_ONLY draws from only the flagged SUBSET of its
    bank (e.g. the Observatory draws only ``hunt`` items — the whole Trial is the
    Hallucination Hunt — so the retired obs_s* MCQs are never offered). Returns a
    list of question keys.
    """
    bank = QUIZZES.get(location_key, [])
    only_flag = TRIAL_DRAW_ONLY.get(location_key)
    if only_flag:
        bank = [q for q in bank if q.get(only_flag)]
    by_key = {q["key"]: q for q in bank}
    pinned = []
    grouped = set()  # every key belonging to a pinned entry (chosen or not)
    for entry in PINNED_QUESTIONS.get(location_key, []):
        if isinstance(entry, (list, tuple)):
            members = [k for k in entry if k in by_key]
            grouped.update(members)
            if members:
                pinned.append(_random.choice(members))  # server picks ONE set
        elif entry in by_key:
            pinned.append(entry)
            grouped.add(entry)
    pool = [q["key"] for q in bank if q["key"] not in grouped]
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
    "The Cartographer's Atlas", "Whispers of Logic", "A Study of Hidden Patterns",
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
        # One shared loop, one score rule (1 point per correct item). Ordering items
        # grade all-or-nothing on the WHOLE sequence; SORT items compare the chosen
        # bin id (independent, 1 point each); MCQs compare the option letter.
        if q.get("kind") == "order":
            correct = order_canonical(q)
            is_correct = normalize_order(selected, q) == correct
            options = None
        elif q.get("kind") == "sort":
            correct = q["correct"]                 # a bin id, server-side only
            is_correct = selected == correct
            options = None
        elif q.get("kind") == "matching":
            correct = q["correct"]                 # a scenario id, server-side only
            is_correct = selected == correct
            options = None
        else:
            correct = q["correct"]
            is_correct = selected == correct
            options = q["options"]
        if is_correct:
            score += 1
        row = {
            "key": q["key"],
            "question": q.get("question") or q.get("concept", ""),
            "kind": q.get("kind", "mcq"),
            "options": options,
            "events": q.get("events"),
            "selected": selected,
            "correct": correct,
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
            "feedback": (q.get("feedback_correct") if is_correct
                         else q.get("feedback_wrong")) or q.get("explanation", ""),
        }
        if q.get("kind") == "sort":
            row["correct_label"] = BIN_LABELS.get(correct, correct)
            row["selected_label"] = BIN_LABELS.get(selected, selected)
        elif q.get("kind") == "matching":
            row["concept"] = q.get("concept", "")
            row["correct_text"] = q.get("scenario", "")   # the correct case
            row["selected_text"] = scenario_text(location_key, selected)
        results.append(row)

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
#   observatory -> aligns 1:1 to the 10 constellation stars — this list's LENGTH
#                  is the server-side source of truth for the Observatory star
#                  count (see explore_valid_ids in routes/game.py)
# Each: {"question": str, "options": [2-3 short strings] (omit/empty = freeform
# tap-to-reveal), "payoff": one-line bridge shown after the guess}.
# Hooks must never reveal a Trial answer — they prime curiosity, nothing more.
HOOKS = {
    "library": [
        {"question": "Before you open this tome, what do you think makes a machine “intelligent”?",
         "options": ["Raw speed", "Learning from data & predicting", "A huge memory"],
         "payoff": "Hold that thought. One of these is the real heart of it. Let's read on.",
         "insight": "A fair guess, but raw speed and memory alone are just a fast filing cabinet. What we mean by intelligence here is learning patterns from data and predicting from them, and that is where we begin."},
        {"question": "If an AI screens loans but a human makes the final call, who is really in charge?",
         "options": ["The AI", "The human", "Neither"],
         "payoff": "Keep your guess in mind. This balance of power has a name.",
         "insight": "You have spotted the tension. A machine can advise, but when a person keeps the final say and the responsibility, that partnership has a name, and it is the most responsible way we use AI today."},
        {"question": "At its core, AI really does just two things. Care to guess what they are?",
         "options": ["Store & delete", "Analyse & predict", "Type & print"],
         "payoff": "Interesting. Let's see if the two acts match what you pictured.",
         "insight": "Two acts, and you are right to look for them. Strip everything else away and an AI studies data to find a pattern, then predicts from it. Hold onto that pair as we read on."},
        {"question": "Which of these do you think is powered by AI prediction?",
         "options": ["Spotting bank fraud", "Reading road signs", "Both, and more"],
         "payoff": "Hold that thought. The reach might surprise you.",
         "insight": "Tempting to pick just one. In truth AI prediction quietly runs through fraud checks, road signs and far more you never notice. Let me show you its reach."},
        {"question": "A program plays chess brilliantly but can do nothing else. What would you call that kind of AI?",
         "options": ["Narrow", "General", "Super"],
         "payoff": "Note your instinct. The three levels are about to come into focus.",
         "insight": "Good instinct. A mind brilliant at one task and helpless at all others sits at the narrow end of a spectrum, and there are three levels in all. Let us place them."},
    ],
    "chronicle": [
        {"question": "Before any 'thinking' machine, what was the first useful thing machines did with data?",
         "options": ["Sorted it into tables", "Predicted the future", "Wrote their own programs"],
         "payoff": "Hold that thought. The story begins with sorting, not thinking.",
         "insight": "Before machines could think, they could sort. The first breakthrough was tidying raw figures into tables so a pattern could surface, long before anything learned. That is where our timeline opens."},
        {"question": "What first let a single 1940s machine do many different jobs?",
         "options": ["Programs (instructions)", "More metal", "Sheer luck"],
         "payoff": "Keep that in mind as we power up ENIAC.",
         "insight": "Not brute metal but instructions. Once a machine could follow a program, a single device could take on many jobs. Keep that in mind as ENIAC powers up."},
        {"question": "Guess the year the term “artificial intelligence” was first coined.",
         "options": ["1956", "1985", "2010"],
         "payoff": "Hold that thought. It's older than most people expect.",
         "insight": "Most place it far later than it truly is. The name was coined in a single summer of bold ambition that set the whole field in motion. Let us visit that room."},
        {"question": "Early AI stalled hard in the 1970s. What do you think held it back?",
         "options": ["Slow machines & tiny memory", "Too many rules", "No electricity"],
         "payoff": "Keep your guess. The First Winter is closing in.",
         "insight": "You are circling the truth. The first freeze came from two hard limits in the machines themselves, and naming them explains why the winter fell. Feel the cold set in."},
        {"question": "Million-dollar 'expert' machines boomed in the 1980s. What toppled them?",
         "options": ["Cheap personal computers", "A new law", "Public boredom"],
         "payoff": "Hold that thought. The second thaw and freeze are near.",
         "insight": "Follow the money. The mighty machines were not banned or forgotten; something far cheaper simply outran them. Watch the boom turn to bust."},
        {"question": "In 1997 a machine first beat the reigning world champion at which game?",
         "options": ["Chess", "Go", "Poker"],
         "payoff": "Keep your guess. The Winters are about to end.",
         "insight": "A famous first. In 1997 a machine faced the reigning champion of an ancient game of pure strategy and won, and that victory helped thaw the long winter."},
    ],
    "ai_lab": [
        {"question": "Before computers, how did people make sense of huge piles of numbers?",
         "options": ["By hand, in tables", "They simply couldn't", "With pocket calculators"],
         "payoff": "Hold that thought. The story starts slower than you'd think.",
         "insight": "Slow, patient work. For centuries the only tool was the human hand, sorting numbers into tables one at a time. That struggle is where the story of data begins."},
        {"question": "What first let a single machine do many different jobs?",
         "options": ["More metal", "Programs (instructions)", "More electricity"],
         "payoff": "Keep that in mind as we power up the 1940s.",
         "insight": "It was never about more metal. The leap came when a machine could follow instructions, a program, and so turn its hand to many tasks. Let us power up the 1940s."},
        {"question": "Guess the year the term “artificial intelligence” was first coined.",
         "options": ["1956", "1985", "2007"],
         "payoff": "Hold that thought. It's older than most people expect.",
         "insight": "Older than it feels. The field was named in one summer of ambition, decades before the tools could catch up. Keep that gap in mind."},
        {"question": "Guess: what fraction of a company's data do you think ever actually gets analysed?",
         "options": ["Almost all of it", "About half", "Only a small slice"],
         "payoff": "Keep your guess, then let's sort some data and find out.",
         "insight": "Brace yourself. Only a thin slice of what a company gathers is ever analysed; the rest sits untouched. Why that is, and what AI does with the pile, is what this lab uncovers."},
    ],
    "observatory": [
        {"question": "A calculator always says 7×8=56. A weather AI says “70% chance of rain.” What's the key difference?",
         "options": ["One is certain, one gives odds", "One is just faster", "No real difference"],
         "payoff": "Hold that thought. Certainty vs. confidence is the whole idea.",
         "insight": "You have felt the difference. One machine is always certain; the other weighs the odds and states its confidence. That shift from certainty to probability is what machine learning relies on."},
        {"question": "To teach an AI to spot spam, what would you give it first?",
         "options": ["Thousands of labelled examples", "Nothing, let it guess", "A written rulebook"],
         "payoff": "Keep that in mind as we trace this star.",
         "insight": "Good thinking. To learn a task like spotting spam, a model first needs examples already marked with the right answer. That labelled data is what lets it learn. Watch how."},
        {"question": "Could a machine group similar customers together with NO labels telling it the groups?",
         "options": ["Yes, it finds patterns itself", "No, impossible", "Only if a human helps"],
         "payoff": "Hold that thought. Pattern-finding without answers is next.",
         "insight": "It can, and that surprises people. Given no labels at all, a model can still uncover natural groupings hiding in the data. That is the idea we trace next."},
        {"question": "How do you think a machine could learn chess with NO teacher and NO answer key?",
         "options": ["Reward good moves, penalise bad", "It simply can't", "Memorise every game ever played"],
         "payoff": "Keep your guess. Trial, reward and consequence await.",
         "insight": "Exactly the right instinct. With no answer key, a machine can still learn by trying, earning rewards for good moves and penalties for poor ones. Over many games it teaches itself."},
        {"question": "Which kind of AI actually exists and runs real businesses today?",
         "options": ["Narrow & Broad AI", "General AI", "Super AI"],
         "payoff": "Hold that thought. Let's map the big picture.",
         "insight": "You are close. Some levels of AI already work quietly around you, while the most powerful remains only a goal. Which is which is what this star reveals."},
        {"question": "A model aces its practice data but flops on brand-new data. What went wrong?",
         "options": ["It memorised instead of learning", "It's simply perfect", "It needs less data"],
         "payoff": "Keep your guess. This trap has a name.",
         "insight": "A classic trap. When a model shines on its practice data but stumbles on anything new, it has memorised rather than learned. This failing has a name worth knowing."},
        {"question": "How do machines make sense of messy human language (emails, speech, chat)?",
         "options": ["Natural Language Processing", "They can't at all", "Only via spreadsheets"],
         "payoff": "Hold that thought. Language is the next frontier.",
         "insight": "Yes, and it is harder than it sounds. Teaching a machine to read our emails, speech and chat is a whole field of its own. You are about to meet it by name."},
        {"question": "Your guide, Professor Atlas, what kind of AI do you think it is?",
         "options": ["A large language model", "A human typing", "A search engine"],
         "payoff": "Keep that in mind. The tutor IS the technology.",
         "insight": "A fair question to ask of your guide. I am a model trained on vast amounts of text, predicting language rather than truly understanding it. Knowing what I am will change how you weigh my answers."},
        {"question": "An AI confidently states a fake 'fact'. What is that called?",
         "options": ["A hallucination", "A victory", "A calculation"],
         "payoff": "Hold that thought. Even Atlas can do this.",
         "insight": "Unsettling, is it not? Even a fluent, confident answer from a model can be flatly untrue, and that failing has a name. Yes, I can do it too."},
        {"question": "To steer an LLM, what helps most before your real question?",
         "options": ["A few example answers", "Asking louder", "Nothing at all"],
         "payoff": "Keep your guess. Prompting is a real skill.",
         "insight": "Shrewd. Show a model a few worked examples before your real request and it follows the pattern far better than asking cold. How you ask turns out to be a genuine skill."},
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
