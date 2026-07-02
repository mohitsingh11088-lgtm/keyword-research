import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="GMB Lead Finder", layout="wide")

st.title("📍 GMB Lead Finder (Apify Powered)")
st.write("Find Google Maps businesses WITHOUT websites")

# -----------------------------
# INPUTS
# -----------------------------
API_TOKEN = st.text_input("Apify API Token", type="password")

actor_id = st.text_input("Actor ID", value="GKjtRGvi01lg33ayo")

keyword = st.text_input("Keyword (e.g. dentist, salon, restaurant)")
location = st.text_input("Location (e.g. Mumbai, Delhi, USA)")

max_results = st.slider("Max results", 10, 200, 50)

# -----------------------------
# RUN BUTTON
# -----------------------------
if st.button("🚀 Run Scraper"):

    if not API_TOKEN:
        st.error("Please enter API token")
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
        data = response.json()

        st.write("Raw response:", data)

        if "data" not in data:
            st.error("Failed to start actor. Check Actor ID or input format.")
            st.stop()

        run_id = data["data"]["id"]
        dataset_id = data["data"]["defaultDatasetId"]

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

    st.write("Sample result:", results[0])  # DEBUG (optional)

    # -----------------------------
    # STEP 4: FILTER NO WEBSITE
    # -----------------------------
    leads = []

    for item in results:

        website = item.get("url")  # IMPORTANT: your field name

        if not website:  # NO WEBSITE FILTER
            address = ", ".join(filter(None, [
                item.get("street"),
                item.get("city"),
                item.get("country")
            ]))

            leads.append({
                "Name": item.get("name"),
                "Address": address,
                "Phone": item.get("phone_number"),
                "Website": "❌ No website",
                "Email": item.get("emails"),
                "Category": item.get("business_category"),
                "Google Maps": item.get("google_maps_url")
            })

    # -----------------------------
    # STEP 5: SHOW RESULTS
    # -----------------------------
    st.success(f"Found {len(leads)} businesses WITHOUT websites")

    if leads:
        df = pd.DataFrame(leads)

        st.dataframe(df)

        # CSV download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "gmb_leads.csv", "text/csv")

    else:
        st.warning("No leads found without websites")
