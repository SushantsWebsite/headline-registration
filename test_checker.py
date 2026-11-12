from checker import analyse, analyse_many


def heads(r):
    return [f.head for f in r.flags]


def test_meaningless_combination_and_add_ons():
    r = analyse("Daily Dainik News")
    assert r.verdict == "Likely rejected"
    assert any("Meaningless combination" in h for h in heads(r))


def test_sound_alike_against_existing():
    r = analyse("Pahadi Awaaz", existing=["Pahari Awaz"])
    assert any("Sounds like" in h for h in heads(r))


def test_same_after_removing_add_ons():
    r = analyse("Himalaya Daily", existing=["Himalaya Times"])
    assert any("once add-on words are removed" in h for h in heads(r))


def test_job_word_depends_on_applicant():
    assert analyse("Career Guide Weekly", "individual").bad
    assert any(f.severity == "warn" and "Job-related" in f.head
               for f in analyse("Career Voice", "organization").flags)


def test_hindi_title_not_flagged_as_symbols():
    assert analyse("हिमालय दर्पण").flags == []


def test_symbols_and_own_name():
    assert any("Symbols" in h for h in heads(analyse("Hill Voice!")))
    assert any("your name" in h for h in heads(analyse("Rakesh Awaz", own_name="Rakesh Sharma")))


def test_results_sorted_lowest_risk_first():
    out = analyse_many(["Daily News", "Pahadi Awaaz"])
    assert out[0].title == "Pahadi Awaaz"
