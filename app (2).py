import streamlit as st
import requests

st.set_page_config(page_title="Keyword Research Tool", layout="centered")

st.title("🔍 Keyword Research Tool")

# ---- INPUT ----
api_key = st.text_input("Enter your API key", type="password")
keyword = st.text_input("Enter a keyword")

# Optional filters
country = st.text_input("Country (optional)", value="us")

# ---- BUTTON ----
if st.button("Get Keywords"):

    if not api_key or not keyword:
        st.warning("Please enter API key and keyword")
    else:
        with st.spinner("Fetching keyword data..."):

            # Replace this URL with YOUR keyword API endpoint
            url = "https://your-api.com/keyword-research"

            headers = {
                "Authorization": f"Bearer {api_key}"
            }

            params = {
                "q": keyword,
                "country": country
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                data = response.json()

                st.success("Results loaded!")

                # ---- DISPLAY RESULTS ----
                st.subheader("Results")

                if "keywords" in data:
                    for item in data["keywords"]:
                        st.write(f"• {item}")
                else:
                    st.json(data)

            except Exception as e:
                st.error(f"Error: {e}")