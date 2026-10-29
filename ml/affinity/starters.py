"""Conversation starters derived from real shared interests.

Every starter is a template keyed by the shared interest. Nothing is invented
about either person: the text is a question, not a claim. When an interest has no
curated template, a neutral template is used that still names the interest.
"""

TEMPLATES = {
    "photography": "What kind of places do you most enjoy photographing?",
    "technology": "What is a technology project you have enjoyed exploring recently?",
    "cooking": "If you could learn one dish from any country, which would it be?",
    "food": "What is a meal you would happily travel for?",
    "travel": "Which trip changed how you see things the most?",
    "music": "What is a song or album you keep coming back to?",
    "books": "What is a book you wish you could read again for the first time?",
    "reading": "What have you been reading lately that stayed with you?",
    "fitness": "What does a good training week look like for you?",
    "hiking": "Which trail or walk would you recommend to someone who has never tried it?",
    "outdoors": "What is your favourite way to spend a day outside?",
    "art": "What kind of art do you seek out when you travel?",
    "gaming": "Which game do you think more people should try?",
    "film": "What film would you put on for someone who has not seen it?",
    "volunteering": "What kind of volunteering has felt most worthwhile to you?",
    "entrepreneurship": "What is an idea you would build if you had a free month?",
    "learning": "What is something you have learned recently that surprised you?",
    "gardening": "What are you growing, or what would you like to grow?",
    "pets": "Tell me about the animal that runs your household.",
    "mindfulness": "What helps you switch off after a long week?",
    "dance": "Is there a style of dance you would love to learn?",
    "nightlife": "What makes a good night out for you?",
}

GENERIC_TEMPLATES = [
    "What got you into {interest} in the first place?",
    "What is the best thing about {interest} for you right now?",
    "If you had a free afternoon for {interest}, what would you do with it?",
]


def conversation_starters(shared_interests, limit=4):
    """One starter per shared interest, plus nothing invented about the person."""
    out = []
    for index, interest in enumerate(shared_interests or []):
        key = str(interest).strip().lower()
        template = TEMPLATES.get(key)
        if template:
            text = template
        else:
            text = GENERIC_TEMPLATES[index % len(GENERIC_TEMPLATES)].format(interest=key)
        out.append({"interest": interest, "text": text, "source": "shared_interest"})
        if len(out) >= limit:
            break
    return out
