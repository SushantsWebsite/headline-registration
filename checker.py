"""Rule checker for Indian newspaper titles, based on a summary of PRGI guidelines.

It tests word and format rules and compares titles against a list the user
supplies. It is NOT a PRGI decision: personal names, sensitive wording and
final "same or similar" calls are made only by the Press Registrar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

DIGITAL = ["dot com", "dot in", ".com", "blog", "portal", "facebook", "twitter",
           "orkut", "linkedin", "youtube", "yahoo", "google", "wikipedia", "wikileaks"]
JOB = ["employment", "rozgar", "career", "job", "naukri"]
ENTITY = ["sarkar", "government", "parliament", "proceedings", "rebel", "rebellion"]
NON_NEWS = ["ad", "advertisement", "classifieds", "tender", "real estate", "press",
            "calendar", "panchaang", "matrimonial", "yellow pages", "guide", "diary",
            "gist", "fact sheet", "bulletin", "pamphlet", "brochure", "directory"]
AFFIXES = ["the", "times", "daily", "dainik", "weekly", "wartha", "aaj", "today",
           "express", "news", "khabar", "samachar", "bulletin", "diary", "india",
           "national", "rashtriya"]
PREPOSITIONS = ["of", "in", "for", "at", "and", "a", "an", "new"]
PLACES = ["delhi", "mumbai", "kolkata", "chennai", "bengaluru", "bangalore", "hyderabad",
          "pune", "jaipur", "lucknow", "patna", "bhopal", "punjab", "haryana", "gujarat",
          "maharashtra", "kerala", "bihar", "odisha", "assam", "bengal", "rajasthan",
          "karnataka", "shimla", "himachal"]
OFFICIAL = ["police", "bureau", "investigation", "vigilance", "cid", "cbi", "defence"]
EXAM = ["exam", "coaching", "study"]
GENERIC = ["manthan", "darpan", "chronology", "inspire", "success", "khulasa",
           "rahasya", "katha", "herald", "batkahi", "nukkad", "crossroads"]
SYNONYMS = [["daily", "dainik", "rozana"], ["weekly", "saptahik"],
            ["evening", "sandhya", "shaam"], ["monthly", "masik"],
            ["fortnightly", "pakshik"], ["news", "samachar", "khabar", "wartha"]]
STOP = set(AFFIXES + PREPOSITIONS + PLACES)

APPLICANTS = {"individual": "Individual",
              "organization": "Organization, society, company or trust",
              "government": "Government body (Head of Department)"}


@dataclass
class Flag:
    severity: str  # "bad" or "warn"
    head: str
    body: str


@dataclass
class Result:
    title: str
    flags: list[Flag] = field(default_factory=list)
    core: list[str] = field(default_factory=list)

    @property
    def bad(self) -> int:
        return sum(f.severity == "bad" for f in self.flags)

    @property
    def warn(self) -> int:
        return len(self.flags) - self.bad

    @property
    def score(self) -> int:
        return self.bad * 3 + self.warn

    @property
    def verdict(self) -> str:
        return "Likely rejected" if self.bad else ("Caution" if self.warn else "No rule flagged")


# ---------- text helpers ----------
def words(text: str) -> list[str]:
    """Split into lowercase tokens, keeping letters, combining marks and digits (Indic safe)."""
    out, cur = [], []
    for ch in text.lower():
        if unicodedata.category(ch)[0] in "LMN":
            cur.append(ch)
        elif cur:
            out.append("".join(cur))
            cur = []
    if cur:
        out.append("".join(cur))
    return out


def has_symbol(text: str) -> bool:
    return any(not c.isspace() and unicodedata.category(c)[0] not in "LMN" for c in text)


def _contiguous(part: list[str], whole: list[str]) -> bool:
    return any(whole[i:i + len(part)] == part for i in range(len(whole) - len(part) + 1))


def _subsequence(part: list[str], whole: list[str]) -> bool:
    j = 0
    for w in whole:
        if j < len(part) and w == part[j]:
            j += 1
    return j == len(part)


def find(low: str, ws: list[str], terms: list[str]) -> list[str]:
    hits = []
    for t in terms:
        if t.startswith("."):
            ok = re.search(re.escape(t) + r"(?!\w)", low) is not None
        else:
            ok = _contiguous(t.split(), ws)
        if ok:
            hits.append(t)
    return hits


def core_words(ws: list[str]) -> list[str]:
    return [w for w in ws if w not in STOP]


def _key(ws: list[str]) -> str:
    return " ".join(sorted(ws))


def phonetic(text: str) -> str:
    s = re.sub(r"[^a-z ]", "", text.lower())
    for a, b in (("ph", "f"), ("w", "v"), ("z", "j"), ("ck", "k"), ("q", "k"),
                 ("aa", "a"), ("ee", "i"), ("ii", "i"), ("ie", "i"), ("oo", "u"), ("uu", "u")):
        s = s.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", s).strip()


def skeleton(text: str) -> str:
    return "".join(w[:1] + re.sub(r"[aeiou]", "", w[1:]) for w in text.split(" "))


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ---------- comparison with an existing title ----------
def compare(candidate: str, existing: str) -> Flag | None:
    cw, ew = words(candidate), words(existing)
    cc, ec = core_words(cw), core_words(ew)
    if not cw or not ew:
        return None
    if _key(cw) == _key(ew):
        return Flag("bad", f"Same words as “{existing}”",
                    "The same words in any order count as the same title.")
    if cc and ec and _key(cc) == _key(ec):
        return Flag("bad", f"Same as “{existing}” once add-on words are removed",
                    "Words like The, Daily or News don’t make a title different.")
    if _contiguous(cw, ew) or _contiguous(ew, cw):
        return Flag("bad", f"Contains or is part of “{existing}”",
                    "A part of an existing title, or a combination containing one, is rejected.")
    if len(ew) > 1 and _subsequence(ew, cw):
        return Flag("warn", f"Inserts a word into “{existing}”",
                    "Allowed only if the meaning changes significantly.")
    if (candidate + existing).isascii():  # sound-alike test only works for Latin script
        a = phonetic(" ".join(cc or cw))
        b = phonetic(" ".join(ec or ew))
        ratio = 1 - levenshtein(a, b) / max(len(a), len(b), 1)
        if a and b and (ratio >= 0.82 or (len(a) > 3 and skeleton(a) == skeleton(b))):
            return Flag("bad", f"Sounds like “{existing}”",
                        "Phonetic lookalikes are treated as similar even when spelled differently.")
        if ratio >= 0.7:
            return Flag("warn", f"Close to “{existing}”",
                        "Similar spelling or sound. PRGI decides what counts as similar.")
    return None


# ---------- full analysis of one title ----------
def analyse(title: str, applicant: str = "individual", own_name: str = "",
            existing: list[str] | None = None) -> Result:
    existing = existing or []
    low, ws = title.lower(), words(title)
    cc = core_words(ws)
    f: list[Flag] = []

    if has_symbol(title):
        f.append(Flag("bad", "Symbols or punctuation",
                      "Signs, symbols, emojis and other non-alphanumeric characters are not allowed."))
    if any(c.isdigit() for c in title):
        f.append(Flag("warn", "Numerals", "Meaningless numerals are rejected."))
    if any(2 <= len(t) <= 4 and t.isalpha() and t.isupper() for t in title.split()):
        f.append(Flag("warn", "Possible acronym",
                      "Acronyms and abbreviations such as B2B or A2Z are rejected."))
    if re.search(r"(^|\s)e-", low):
        f.append(Flag("bad", "Digital form", "Titles starting with e- are treated as electronic versions."))
    if (h := find(low, ws, DIGITAL)):
        f.append(Flag("bad", f"Digital or social media wording: {', '.join(h)}",
                      "Electronic versions and platform names are not registered."))
    if (h := find(low, ws, JOB)):
        ok = applicant == "organization"
        f.append(Flag("warn" if ok else "bad", f"Job-related word: {', '.join(h)}",
                      "Allowed for organizations, societies, companies and trusts." if ok
                      else "Only organizations, societies, companies and trusts can use these."))
    if (h := find(low, ws, ENTITY)):
        gov = applicant == "government"
        f.append(Flag("warn" if gov else "bad", f"Restricted word: {', '.join(h)}",
                      "Verified only for the entity concerned."
                      + (" Make sure it is your own entity." if gov else "")))
    if (h := find(low, ws, NON_NEWS)):
        f.append(Flag("bad", f"Non-news word: {', '.join(h)}",
                      "Titles for advertising, directories, guides and similar material are rejected."))
    if (h := find(low, ws, OFFICIAL)):
        f.append(Flag("warn", f"Suggests an official body: {', '.join(h)}",
                      "Police, investigation and defence names are allowed only for the department concerned."))
    if (h := find(low, ws, EXAM)):
        f.append(Flag("warn", f"Exam-related: {', '.join(h)}",
                      "Titles for content aimed solely at exams, study or coaching are rejected."))
    if (h := find(low, ws, AFFIXES + PLACES)):
        f.append(Flag("warn", f"Add-on words: {', '.join(h)}",
                      "City, state, periodicity, language and words like these added to an existing "
                      "title make it similar to that title."))
    for group in SYNONYMS:
        h = [w for w in group if w in ws]
        if len(h) > 1:
            f.append(Flag("bad", f"Meaningless combination: {' + '.join(h)}",
                          "The same idea twice, as in Saptahik Weekly or Daily Dainik News, is rejected."))
    if own_name:
        hit = [w for w in words(own_name) if len(w) > 2 and w in ws]
        if hit:
            f.append(Flag("bad", f"Contains your name: {', '.join(hit)}",
                          "The applicant’s name or any person’s proper noun is rejected."))
    if not cc:
        f.append(Flag("bad", "Nothing distinctive",
                      "The title is only add-on words, so it will match an existing title."))
    elif len(cc) == 1 and cc[0] in GENERIC:
        f.append(Flag("bad", "Too generic", f"A single root word like “{cc[0]}” is rejected."))

    matches = [m for e in existing if (m := compare(title, e))]
    matches.sort(key=lambda m: 0 if m.severity == "bad" else 1)  # stable sort
    f.extend(matches[:3])
    return Result(title=title, flags=f, core=cc)


def analyse_many(titles: list[str], applicant: str = "individual", own_name: str = "",
                 existing: list[str] | None = None) -> list[Result]:
    """Check up to 5 titles and return them with the lowest risk first."""
    results = [analyse(t, applicant, own_name, existing) for t in titles[:5]]
    return sorted(results, key=lambda r: r.score)


# ---------- deadlines ----------
def registration_deadline(verified_on: date) -> date:
    return verified_on + timedelta(days=180)


def discrepancy_deadline(letter_on: date) -> date:
    return letter_on + timedelta(days=30)
