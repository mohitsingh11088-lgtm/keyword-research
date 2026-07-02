import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="GMB Lead Finder", layout="wide")

st.title("📍 GMB Lead Finder (Location Fixed Version)")
st.write("Scrapes Google Maps businesses WITHOUT websites (accurate location filtering)")

# -----------------------------
# INPUTS
# -----------------------------
API_TOKEN = st.text_input("Apify API Token", type="password")

actor_id = st.text_input("Actor ID", value="GKjtRGvi01lg33ayo")

keyword = st.text_input("Keyword (e.g. dentist, salon, restaurant)")

state = st.text_input("State (e.g. Idaho, Texas, California)")

city_list_input = st.text_area(
    "Cities (optional - one per line for better accuracy)",
    placeholder="Boise\nMeridian\nNampa\nIdaho Falls"
)

max_results = st.slider("Max results per city", 10, 200, 50)

# -----------------------------
# RUN BUTTON
# -----------------------------
if st.button("🚀 Start Scraping"):

    if not API_TOKEN:
        st.error("Missing API token")
        st.stop()

    if not keyword:
        st.error("Missing keyword")
        st.stop()

    if not state:
        st.error("Missing state")
        st.stop()

    # -----------------------------
    # PREPARE LOCATIONS
    # -----------------------------
    if city_list_input.strip():
        cities = [c.strip() for c in city_list_input.split("\n") if c.strip()]
        locations = [f"{c}, {state}, USA" for c in cities]
    else:
        locations = [f"{state}, USA"]

    st.write("📍 Target Locations:", locations)

    all_leads = []

    # -----------------------------
    # LOOP THROUGH LOCATIONS
    # -----------------------------
    for loc in locations:

        st.write(f"Scraping: {loc}")

        url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={API_TOKEN}"

        payload = {
            "searchStringsArray": [f"{keyword} in {loc}"],
            "locationQueries": [loc],
            "maxCrawledPlacesPerSearch": max_results
        }

        # 1. Run Actor
        response = requests.post(url, json=payload)
        data = response.json()

        if "data" not in data:
            st.error(f"Actor failed for {loc}")
            continue

        run_id = data["data"]["id"]
        dataset_id = data["data"]["defaultDatasetId"]

        # 2. Wait for completion
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={API_TOKEN}"

        while True:
            status_res = requests.get(status_url).json()
            status = status_res["data"]["status"]

            if status == "SUCCEEDED":
                break
            elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                st.error(f"Run failed for {loc}")
                break

            time.sleep(3)

        # 3. Get results
        dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?clean=true&token={API_TOKEN}"
        results = requests.get(dataset_url).json()

        # -----------------------------
        # FILTER + LOCATION CHECK
        # -----------------------------
        for item in results:

            website = item.get("url")

            city = (item.get("city") or "").lower()
            state_check = (state or "").lower()

            # 🔥 HARD LOCATION FILTER (IMPORTANT FIX)
            if state_check not in city and state_check not in str(item).lower():
                continue

            if not website:

                address = ", ".join(filter(None, [
                    item.get("street"),
                    item.get("city"),
                    item.get("country")
                ]))

                all_leads.append({
                    "Name": item.get("name"),
                    "Address": address,
                    "Phone": item.get("phone_number"),
                    "Website": "❌ No website",
                    "Email": item.get("emails"),
                    "Category": item.get("business_category"),
                    "Google Maps": item.get("google_maps_url")
                })

    # -----------------------------
    # SHOW RESULTS
    # -----------------------------
    st.success(f"Total leads found WITHOUT websites: {len(all_leads)}")

    if all_leads:
        df = pd.DataFrame(all_leads)

        st.dataframe(df)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", csv, "gmb_leads.csv", "text/csv")
    else:
        st.warning("No matching leads found")
