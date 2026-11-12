"""Streamlit app: newspaper title registration helper (India, PRGI)."""
import csv
import io

import streamlit as st

from checker import (APPLICANTS, analyse_many, discrepancy_deadline,
                     registration_deadline)

st.set_page_config(page_title="Newspaper title registration, India", page_icon="📰")

CHECKLIST = [
    "Searched the Verified Titles list on the PRGI website",
    "Title is not similar in words, order or sound to any existing title",
    "No banned words, affixes, names, acronyms, symbols or generic single words",
    "Meaning and nature of the content stated clearly",
    "Ownership of other titles declared and annual statements up to date",
    "No other title application pending, and the earlier title’s registration already applied for",
    "Applicant category is correct",
    "Languages listed match the content to be published",
    "Original form with no overwriting or white fluid, and seal and signature on every page",
    "DM forwards it directly to PRGI, and the 30-day and 180-day deadlines are noted",
]
ICON = {"bad": "🔴", "warn": "🟡"}


def lines(text: str) -> list[str]:
    return [x.strip() for x in text.splitlines() if x.strip()]


def read_upload(file) -> list[str]:
    """Read existing titles from a .txt or .csv upload (first column)."""
    out = []
    for row in csv.reader(io.StringIO(file.getvalue().decode("utf-8", errors="ignore"))):
        if row and row[0].strip():
            out.append(row[0].strip())
    return out


def load_example():
    st.session_state["titles"] = "Daily Dainik News\nThe Himalaya Herald\nPahadi Awaaz\nShimla Weekly Voice"
    st.session_state["existing"] = "Himalaya Times\nPahari Awaz\nHimalayan Voice"


st.title("📰 Newspaper title registration in India")
st.write("The Press Registrar General (PRGI) registers printed newspapers and periodicals that carry "
         "public news or comment on it. It happens in two steps: title verification, then registration.")

tab1, tab2, tab3, tab4 = st.tabs(["Title checker", "Who can apply", "Process and deadlines", "Checklist"])

with tab1:
    st.subheader("Test titles against the written rules")
    st.text_area("Titles to test (one per line, up to 5)", key="titles", height=120)
    c1, c2 = st.columns(2)
    applicant = c1.selectbox("Applicant", list(APPLICANTS), format_func=APPLICANTS.get)
    own_name = c2.text_input("Your own name (optional)")
    st.text_area("Existing titles to compare against (optional, one per line)", key="existing", height=120,
                 help="Paste similar titles you found in the PRGI Verified Titles list.")
    upload = st.file_uploader("Or upload a .txt or .csv of existing titles", type=["txt", "csv"])
    b1, b2 = st.columns([1, 1])
    run = b1.button("Check titles", type="primary")
    b2.button("Try an example", on_click=load_example)

    if run:
        titles = lines(st.session_state.get("titles", ""))
        existing = lines(st.session_state.get("existing", ""))
        if upload is not None:
            existing += read_upload(upload)
        if not titles:
            st.warning("Enter at least one title first.")
        else:
            if len(titles) > 5:
                st.info("Only the first 5 titles are checked.")
            results = analyse_many(titles, applicant, own_name.strip(), existing)
            st.write(f"**{len(results)} title(s) checked, lowest risk first.** "
                     f"{sum(r.bad > 0 for r in results)} likely to be rejected."
                     + ("" if existing else " Add existing titles to also test for similarity."))
            for r in results:
                with st.container(border=True):
                    colour = "red" if r.bad else ("orange" if r.warn else "green")
                    st.markdown(f"**{r.title}**  :{colour}[{r.verdict}]")
                    st.caption("Distinctive part: " + (" ".join(r.core) or "none"))
                    for fl in r.flags:
                        st.markdown(f"{ICON[fl.severity]} **{fl.head}**  \n{fl.body}")
                    if not r.flags:
                        st.caption("No word, format or similarity rule hit. That is not approval.")
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["title", "verdict", "distinctive_part", "flags"])
            for r in results:
                w.writerow([r.title, r.verdict, " ".join(r.core), "; ".join(f.head for f in r.flags)])
            st.download_button("Download results (CSV)", buf.getvalue(), "title-check.csv", "text/csv")
            st.caption("Not checked here: personal and leader names, sensitive wording, misleading "
                       "association, and PRGI’s final call on similarity. A title missing from the "
                       "Verified Titles list may still be unavailable.")

with tab2:
    with st.expander("Can apply", expanded=True):
        st.markdown(
            "- Individuals, for up to four titles in one name.\n"
            "- Organizations, societies, companies and trusts. They are the only ones allowed "
            "Employment, Rozgar, Career, Job or Naukri in a title.\n"
            "- Government departments, through the Head of Department. The title is verified in "
            "that person’s name.\n"
            "- Constitutional bodies and PSUs, which are exempt from first-come-first-served.\n"
            "- Recognized national and state political parties, for their own party names only.\n"
            "- Existing publishers, once the latest Annual Statement is filed, any penalty is paid "
            "and any earlier allotted title has been applied for.")
    with st.expander("Cannot apply", expanded=True):
        st.markdown(
            "- News agencies and feature agencies.\n"
            "- News websites and news channels.\n"
            "- Electronic versions of publications, including titles using dot com, e-, blog, "
            "portal or social media names.\n\n"
            "Owners of an existing title need no verification for a new edition from another "
            "district in the same state and language. They file the Form 1 declaration directly. "
            "A different state or language needs verification.")

with tab3:
    st.subheader("The process")
    st.markdown(
        "1. Search the Verified Titles list on the PRGI website. Absence from the list does not "
        "guarantee the title is free.\n"
        "2. Apply online at rni.nic.in and print the form.\n"
        "3. Get it authenticated by the District Magistrate, with a legible seal and signature on every page.\n"
        "4. The DM forwards the original to PRGI by official email or Registered Post. Direct "
        "applications from publishers and photocopies are not accepted.\n"
        "5. Answer any Discrepancy Letter within 30 days.\n"
        "6. Apply for registration with the Form 1 declaration within 180 days of verification.")
    st.caption("PRGI aims to decide within 30 working days. The Press Registrar’s decision is final.")
    st.subheader("Deadline calculator")
    d1 = st.date_input("Date the title was verified", value=None, format="DD/MM/YYYY")
    d2 = st.date_input("Date of the Discrepancy Letter", value=None, format="DD/MM/YYYY")
    if d1:
        st.success(f"Apply for registration by **{registration_deadline(d1):%d %B %Y}**.")
    if d2:
        st.success(f"Reply to the Discrepancy Letter by **{discrepancy_deadline(d2):%d %B %Y}**.")
    st.caption("Miss the 180 days and the title is deblocked, so others can take it. Miss the 30 days and "
               "the application is rejected and you need a fresh DM-authenticated one. Letters are "
               "posted on rni.nic.in, and not receiving one is no excuse.")
    st.table({"Step": ["Reply to a Discrepancy Letter", "Apply for registration after verification",
                       "Decision on a title application", "Transfer a registered title",
                       "Annual Statement"],
              "Limit": ["30 days", "180 days", "30 working days", "Locked for 5 years",
                        "Latest filed before a new application"],
              "If missed": ["Application rejected", "Title deblocked", "A target, not a guarantee",
                            "Earlier only on the owner’s death",
                            "Unpaid late-return penalty triggers a Discrepancy Letter"]})

with tab4:
    done = sum(st.checkbox(item, key=f"c{i}") for i, item in enumerate(CHECKLIST))
    st.progress(done / len(CHECKLIST), text=f"{done} of {len(CHECKLIST)} done")

st.divider()
st.caption("Based on the PRGI one-pager, last updated 12 November 2026. This is a summary, not legal "
           "advice, and verification is not trademark or company-name approval. Help desk: "
           "it-helpdesk.rni@gov.in, 011-24320025.")
