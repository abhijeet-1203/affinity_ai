"""Text normalisation, a small concept lexicon and TF-IDF vector maths.

Everything here is standard library only, deterministic, and cheap enough to run
inside a request. It is the "semantic" half of the engine: tokens are expanded
into concept ids via an explicit lexicon, so "hiking / trekking / mountain trails"
and "outdoor photography" overlap on meaning rather than exact spelling.
"""

import math
import re

STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "also", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can", "did", "do", "does", "doing", "don", "down", "during",
    "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
    "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in",
    "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my", "myself",
    "no", "nor", "not", "now", "of", "off", "on", "once", "only", "or", "other",
    "our", "ours", "ourselves", "out", "over", "own", "really", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to",
    "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "whom", "why", "will", "with", "would", "you",
    "your", "yours", "yourself", "yourselves", "lot", "lots", "like", "love", "enjoy",
    "enjoys", "enjoying", "really", "thing", "things", "stuff", "kind", "kinds", "way",
    "ways", "make", "makes", "made", "get", "gets", "got", "go", "goes", "going",
    "want", "wants", "would", "could", "much", "many", "every", "always", "often",
    "sometimes", "usually", "try", "trying", "find", "finding", "new", "good", "great",
    "nice", "little", "bit", "time", "times", "day", "days", "week", "year", "years",
    "people", "person", "someone", "something", "anything", "everything", "am",
}

# Explicit concept lexicon. A term maps to one or more concept ids; two profiles
# sharing a concept are treated as semantically related even when their wording
# differs. Curated by hand, deliberately small and inspectable.
CONCEPTS = {
    "outdoor_hiking": [
        "hike", "hikes", "hiking", "hiker", "trek", "treks", "trekking", "trail",
        "trails", "mountain", "mountains", "hills", "hill", "outdoors", "outdoor",
        "camp", "camping", "wander", "wandering", "summit", "summits", "climb",
        "climbing", "backpack", "backpacking", "nature", "wilderness", "forest",
        "forests", "valley", "ridge", "altitude", "terrain",
    ],
    "photography": [
        "photograph", "photographs", "photography", "photographer", "photo", "photos",
        "camera", "cameras", "lens", "lenses", "capture", "capturing", "captured",
        "landscape", "landscapes", "shoot", "shooting", "portrait", "portraits",
        "framing", "composition", "aperture", "shutter", "drone", "djis",
    ],
    "cooking_food": [
        "cook", "cooks", "cooking", "cooked", "cuisine", "cuisines", "food", "foods",
        "recipe", "recipes", "bake", "baking", "baked", "dish", "dishes", "kitchen",
        "eat", "eating", "restaurant", "restaurants", "flavour", "flavours", "spice",
        "spices", "chef", "meal", "meals", "brewing", "coffee", "cafe", "cafes",
    ],
    "travel": [
        "travel", "travels", "travelling", "traveling", "travelled", "trip", "trips",
        "journey", "journeys", "explore", "explores", "exploring", "exploration",
        "abroad", "country", "countries", "backpacking", "itinerary", "wanderlust",
        "passport", "flight", "flights", "map", "maps", "route", "routes",
    ],
    "music": [
        "music", "musical", "guitar", "guitars", "piano", "drums", "concert",
        "concerts", "gig", "gigs", "song", "songs", "band", "bands", "album",
        "albums", "listen", "listening", "sing", "singing", "singer", "playlist",
        "playlists", "melody", "jazz", "indie", "classical", "vinyl",
    ],
    "books": [
        "book", "books", "read", "reads", "reading", "novel", "novels", "fiction",
        "nonfiction", "author", "authors", "literature", "poetry", "poem", "poems",
        "library", "libraries", "memoir", "essay", "essays", "storytelling",
    ],
    "technology": [
        "technology", "technologies", "tech", "code", "coding", "programming",
        "programmer", "software", "developer", "development", "engineer",
        "engineering", "computer", "computers", "ai", "ml", "robot", "robotics",
        "database", "backend", "frontend", "open", "source", "linux", "cloud",
        "startup", "startups", "product", "prototype", "hardware", "electronics",
    ],
    "fitness": [
        "fitness", "gym", "run", "runs", "running", "runner", "workout", "workouts",
        "training", "train", "yoga", "pilates", "exercise", "strength", "cardio",
        "cycling", "cycle", "swim", "swimming", "sport", "sports", "marathon",
        "football", "cricket", "basketball", "badminton", "tennis", "climbing",
    ],
    "art": [
        "art", "arts", "artist", "paint", "paints", "painting", "paintings", "draw",
        "draws", "drawing", "sketch", "sketching", "illustration", "design",
        "designing", "museum", "museums", "gallery", "galleries", "sculpture",
        "exhibition", "craft", "crafts", "ceramics",
    ],
    "film": [
        "film", "films", "filmmaking", "movie", "movies", "cinema", "cinemas",
        "series", "documentary", "documentaries", "screenplay", "director", "acting",
        "theatre", "theater", "anime", "tv", "season", "episode",
    ],
    "gaming": [
        "game", "games", "gaming", "gamer", "console", "consoles", "videogame",
        "videogames", "esports", "multiplayer", "rpg", "indie", "arcade", "chess",
        "puzzle", "puzzles", "boardgames", "boardgame",
    ],
    "volunteering": [
        "volunteer", "volunteering", "volunteers", "community", "charity", "social",
        "helping", "help", "ngo", "nonprofit", "mentor", "mentoring", "teaching",
        "tutoring", "service", "outreach", "fundraising",
    ],
    "entrepreneurship": [
        "entrepreneur", "entrepreneurship", "entrepreneurial", "business",
        "businesses", "founder", "founders", "venture", "ventures", "marketing",
        "sales", "growth", "product", "strategy", "leadership", "freelance",
        "freelancing", "consulting", "investing", "investment",
    ],
    "learning": [
        "learn", "learns", "learning", "study", "studies", "studying", "course",
        "courses", "research", "science", "scientific", "curiosity", "curious",
        "philosophy", "history", "psychology", "economics", "mathematics", "maths",
        "physics", "biology", "astronomy", "language", "languages", "lecture",
        "lectures", "seminar", "mooc", "reading",
    ],
    "pets": [
        "dog", "dogs", "cat", "cats", "puppy", "kitten", "pet", "pets", "animal",
        "animals", "rescue", "vet", "aquarium", "bird", "birds",
    ],
    "gardening": [
        "garden", "gardens", "gardening", "plant", "plants", "planting", "grow",
        "growing", "flowers", "flower", "herbs", "balcony", "sustainability",
        "compost", "seeds",
    ],
    "mindfulness": [
        "meditation", "meditate", "meditating", "mindfulness", "mindful", "calm",
        "journaling", "journal", "reflection", "reflect", "breathing", "quiet",
        "stillness", "gratitude",
    ],
    "dance": [
        "dance", "dances", "dancing", "dancer", "salsa", "bachata", "hiphop",
        "choreography", "ballet", "groove",
    ],
    "nightlife": [
        "party", "parties", "nightlife", "club", "clubs", "bar", "bars", "festival",
        "festivals", "celebration", "friends", "gathering", "brunch",
    ],
}

TERM_TO_CONCEPTS = {}
for _concept, _terms in CONCEPTS.items():
    for _term in _terms:
        TERM_TO_CONCEPTS.setdefault(_term, set()).add(_concept)

_SUFFIXES = ("ingly", "edly", "ing", "ers", "ies", "ied", "ment", "ness", "ous", "ive", "est", "ed", "es", "ly", "er", "s")


def stem(token):
    """Deliberately simple suffix stripper.

    It only has to make related surface forms collide ("trekking" -> "trekk",
    "trek" -> "trek" via the extra-k rule). A full Porter stemmer buys nothing
    here because the concept lexicon does the heavy lifting.
    """
    if len(token) <= 3:
        return token
    for suffix in _SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            token = token[: -len(suffix)]
            break
    if len(token) > 3 and token[-1] == token[-2] and token[-1] not in "aeiou":
        token = token[:-1]
    return token


def tokenize(text):
    """Lower-case word tokens, stopwords removed, lightly stemmed."""
    if not text:
        return []
    cleaned = re.sub(r"[^a-z0-9\s']", " ", str(text).lower())
    out = []
    for raw in cleaned.split():
        token = raw.strip("'")
        if len(token) < 3 or token in STOPWORDS:
            continue
        out.append(stem(token))
    return out


def concept_tokens(text):
    """Concept ids mentioned by a text, e.g. "trekking" -> outdoor_hiking."""
    if not text:
        return set()
    cleaned = re.sub(r"[^a-z0-9\s']", " ", str(text).lower())
    found = set()
    for raw in cleaned.split():
        term = raw.strip("'")
        if term in TERM_TO_CONCEPTS:
            found |= TERM_TO_CONCEPTS[term]
        else:
            stemmed = stem(term)
            for variant in (term + "s", term + "ing", stemmed):
                if variant in TERM_TO_CONCEPTS:
                    found |= TERM_TO_CONCEPTS[variant]
                    break
    return found


def feature_counts(text):
    """Bag of weighted features: word stems plus concept ids (concepts weight 2)."""
    counts = {}
    for token in tokenize(text):
        counts[token] = counts.get(token, 0.0) + 1.0
    for concept in concept_tokens(text):
        key = "concept:" + concept
        counts[key] = counts.get(key, 0.0) + 2.0
    return counts


def build_idf(documents):
    """Inverse document frequency over a small corpus (exactly the profiles in play).

    Usual smoothed form: idf = ln((1 + N) / (1 + df)) + 1.
    """
    n = max(len(documents), 1)
    df = {}
    for doc in documents:
        for term in set(feature_counts(doc)):
            df[term] = df.get(term, 0) + 1
    return {term: math.log((1.0 + n) / (1.0 + count)) + 1.0 for term, count in df.items()}


def tfidf_vector(text, idf):
    counts = feature_counts(text)
    if not counts:
        return {}
    total = sum(counts.values())
    vector = {}
    for term, count in counts.items():
        # Unseen terms get the maximum idf so a novel word still counts.
        weight = idf.get(term, math.log(2.0) + 1.0)
        vector[term] = (count / total) * weight
    return vector


def cosine(a, b):
    """Cosine similarity between two sparse vectors; 0.0 when either is empty."""
    if not a or not b:
        return 0.0
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[t] * b[t] for t in shared)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))
