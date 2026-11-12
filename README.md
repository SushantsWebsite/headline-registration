# Newspaper title registration helper (India)

A Streamlit app that tests proposed newspaper titles against the written PRGI title rules,
compares them with existing titles you paste in, and tracks the 30-day and 180-day deadlines.

**This is not a PRGI decision.** It can’t judge personal or leader names, sensitive wording, or
PRGI’s final call on whether titles are the same or similar. Check the Verified Titles list on the
PRGI website and read the current guidelines before you apply.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows. On macOS or Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Test it

```bash
pip install pytest
pytest
```

## Publish it

1. `git init`, then `git add .` and `git commit -m "Title checker"`.
2. Create an empty repository on GitHub and push to it.
3. Optional: deploy free on Streamlit Community Cloud by pointing it at `app.py`.

## Files

- `checker.py`: the rules and similarity checks, with no Streamlit code, so you can reuse or test it.
- `app.py`: the Streamlit interface.
- `tests/test_checker.py`: sample tests.

The rules are a summary of a PRGI one-pager last updated 12 November 2026. Update the word lists
at the top of `checker.py` when the guidelines change.
