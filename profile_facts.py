"""Checked education facts, shared by the prompt and factual replies."""
from datetime import date
import re
import unicodedata


def education_facts(as_of=None):
    today = as_of or date.today()
    academic_start = today.year if today.month >= 9 else today.year - 1
    year = academic_start - 2024 + 1
    # The industry placement starts in June, after the second academic year.
    if date(2026, 6, 1) <= today < date(2027, 9, 1):
        year = 3
    if date(2026, 6, 1) <= today < date(2027, 7, 1):
        stage = "third year of the programme, on his year in industry (2026–2027)"
        introduction = "a third-year Electronics & Computer Engineering student at the University of Sheffield, currently on his year in industry (2026–2027)"
    elif date(2027, 7, 1) <= today < date(2027, 9, 1):
        stage = "third year of the programme, after his industry placement and before his final academic year"
        introduction = "an Electronics & Computer Engineering student at the University of Sheffield, returning for his final academic year in 2027–2028 after his industry placement"
    elif year == 4:
        stage = "fourth and final year of the programme (2027–2028), after the industry placement"
        introduction = "a fourth-year Electronics & Computer Engineering student at the University of Sheffield, in the final academic year of his programme (2027–2028)"
    elif year in (1, 2):
        ordinal = {1: "first", 2: "second"}[year]
        stage = f"{ordinal} year of the programme"
        introduction = f"a {ordinal}-year Electronics & Computer Engineering student at the University of Sheffield"
    else:
        year = None
        stage = "programme scheduled for 2024–2028; completion status is not confirmed in the supplied profile"
        introduction = "an Electronics & Computer Engineering student whose Sheffield BEng programme was scheduled for 2024–2028; his latest academic status needs confirmation"
    return {"as_of": today.isoformat(), "year": year, "stage": stage, "introduction": introduction}


TIMELINE = (
    "Year 1: 2024–2025 — academic year.\n"
    "Year 2: 2025–2026 — academic year.\n"
    "Year 3: 2026–2027 — year in industry.\n"
    "Year 4: 2027–2028 — final academic year, after the placement."
)


def education_context(as_of=None):
    facts = education_facts(as_of)
    return (
        f"As of {facts['as_of']}, Swapnanil is in the {facts['stage']}.\n"
        "Degree: BEng Electronics & Computer Engineering, University of Sheffield, 2024–2028, including a year in industry.\n"
        f"{TIMELINE}\n"
        "The four-year course duration does not mean he is currently in fourth year. "
        "During the 2026–2027 industry placement he is a THIRD-YEAR student, not a fourth-year student. "
        "The fourth/final academic year is 2027–2028."
    )


def factual_reply(message, as_of=None):
    text = unicodedata.normalize("NFKC", message).casefold()
    text = re.sub(r"[^\w\s]", " ", text)
    text = " ".join(text.split())
    facts = education_facts(as_of)
    bio = re.fullmatch(
        r"(?:please )?(?:who (?:is|os|s) swapnanil(?: chattopadhyay)?|"
        r"tell me about (?:swapnanil(?: chattopadhyay)?|yourself)|"
        r"introduce (?:yourself|swapnanil(?: chattopadhyay)?))(?: please)?", text
    )
    if bio:
        intro = f"Swapnanil Chattopadhyay is {facts['introduction']}."
        if facts["year"] == 3 and (as_of or date.today()) < date(2027, 7, 1):
            intro += " He is a Software Engineering Intern in Application Infrastructure at Morgan Stanley, working with Java, Spring Boot, Angular and Linux."
        return (
            intro + "\n\nHe previously interned in AI/ML at Mastek, achieved 80%+ across his first two academic years, "
            "and was a Top 6 finalist at the OpenAI DevDay Community Hackathon with Agent Arena. "
            "His interests span software, AI, algorithms and technology for financial markets."
        )
    if text in {"who are you", "what are you"}:
        return "I’m Swapnanil Chattopadhyay’s AI assistant. I can answer questions about his experience, projects and education."
    year_question = len(text.split()) <= 28 and (
        bool(re.search(r"\b(?:what|which) (?:academic |programme |program |study )?year\b", text))
        or bool(re.search(r"\b(?:third|3rd) year\b.*\b(?:fourth|4th) year\b|\b(?:fourth|4th) year\b.*\b(?:third|3rd) year\b", text))
        or bool(re.search(r"^(?:is|are) (?:he|you|swapnanil) (?:currently |in |a |the )*(?:third|3rd|fourth|4th) year\b", text))
        or bool(re.search(r"^(?:but )?(?:you|u) (?:said|mentioned|called|told).*\b(?:third|3rd|fourth|4th)\b", text))
    )
    if year_question:
        return (
            f"Swapnanil is in the **{facts['stage']}**.\n\n{TIMELINE}\n\n"
            "The degree lasts four years in total. His industry placement is Year 3; the final academic year follows it."
        )
    return None
