import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="GMB Lead Finder", layout="wide")

st.title("📍 Google Maps Lead Finder (Apify Powered)")
st.write("Find businesses and filter those WITHOUT websites")

# -----------------------------
# INPUTS
# -----------------------------
API_TOKEN = st.text_input("Apify API Token", type="password")

keyword = st.text_input("Search keyword (e.g. dentist, salon, gym)")
location = st.text_input("Location (e.g. Mumbai, Delhi, New York)")
max_results = st.slider("Max results per search", 10, 200, 50)

# -----------------------------
# ACTOR CONFIG
# -----------------------------
# Use REAL actor id from Apify store
actor_id = "compass/crawler-google-places"

# -----------------------------
# RUN BUTTON
# -----------------------------
if st.button("Find GMB Leads"):

    if not API_TOKEN or not keyword or not location:
        st.warning("Please fill all required fields")
        st.stop()

    with st.spinner("Running Apify scraper..."):

        url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={API_TOKEN}"

        payload = {
            "searchStringsArray": [keyword],
            "locationQueries": [location],
            "maxCrawledPlacesPerSearch": max_results,
            "extractContactsFromWebsite": True
        }

        # 1. Start Actor
        response = requests.post(url, json=payload)
        data = response.json()

        run_id = data["data"]["id"]
        dataset_id = data["data"]["defaultDatasetId"]

        st.success("Scraping started... fetching results")

        # 2. Wait & fetch dataset
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={API_TOKEN}"

        results = requests.get(dataset_url).json()

        # -----------------------------
        # FILTER: NO WEBSITE BUSINESSES
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
        # SHOW RESULTS
        # -----------------------------
        if leads:
            df = pd.DataFrame(leads)
            st.dataframe(df)

            # Download CSV
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "gmb_leads.csv", "text/csv")
        else:
            st.warning("No results found without websites")
