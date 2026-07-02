import streamlit as st
import requests
import time
import pandas as pd

st.set_page_config(page_title="Apify GMB Scraper", layout="wide")

st.title("📍 GMB Lead Finder (Apify Powered)")

st.write("Scrape Google Maps and find businesses WITHOUT websites")

# -----------------------------
# INPUTS
# -----------------------------
API_TOKEN = st.text_input("🔑 Apify API Token", type="password")

actor_id = st.text_input(
    "🤖 Apify Actor ID",
    value="compass/crawler-google-places"
)

keyword = st.text_input("🔍 Keyword (e.g. dentist, salon, gym)")
location = st.text_input("📍 Location (e.g. Mumbai, Delhi, USA)")
max_results = st.slider("Max results", 10, 200, 50)

# -----------------------------
# RUN BUTTON
# -----------------------------
if st.button("🚀 Start Scraping"):

    if not API_TOKEN:
        st.error("Please enter API token")
        st.stop()

    if not actor_id:
        st.error("Please enter Actor ID")
        st.stop()

    if not keyword or not location:
        st.error("Please enter keyword and location")
        st.stop()

    # -----------------------------
    # STEP 1: RUN ACTOR
    # -----------------------------
    url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={API_TOKEN}"

    payload = {
        "searchStringsArray": [keyword],
        "locationQueries": [location],
        "maxCrawledPlacesPerSearch": max_results
    }

    with st.spinner("Starting Apify Actor..."):

        response = requests.post(url, json=payload)
        run_data = response.json()

        # Debug (important for you)
        st.write("Raw response:", run_data)

        if "data" not in run_data:
            st.error("Failed to start Actor. Check Actor ID or API token.")
            st.stop()

        run_id = run_data["data"]["id"]
        dataset_id = run_data["data"]["defaultDatasetId"]

    st.success(f"Actor started! Run ID: {run_id}")

    # -----------------------------
    # STEP 2: WAIT FOR COMPLETION
    # -----------------------------
    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"

    with st.spinner("Waiting for scraping to finish..."):

        while True:
            status_res = requests.get(status_url).json()
            status = status_res["data"]["status"]

            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                st.error(f"Run failed: {status}")
                st.stop()

            time.sleep(3)

    st.success("Scraping completed!")

    # -----------------------------
    # STEP 3: GET RESULTS
    # -----------------------------
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={API_TOKEN}"

    results = requests.get(dataset_url).json()

    # -----------------------------
    # STEP 4: FILTER NO WEBSITE
    # -----------------------------
    leads = []

    for item in results:
        if not item.get("website"):
            leads.append({
                "Name": item.get("title"),
                "Address": item.get("address"),
                "Phone": item.get("phone"),
                "Rating": item.get("totalScore"),
                "Category": item.get("categoryName")
            })

    st.success(f"Found {len(leads)} businesses WITHOUT websites")

    # -----------------------------
    # STEP 5: SHOW DATA
    # -----------------------------
    if leads:
        df = pd.DataFrame(leads)
        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "gmb_leads.csv", "text/csv")
    else:
        st.warning("No leads found without websites")
