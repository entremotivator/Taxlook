import streamlit as st
import requests

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Property Lookup", page_icon="🏠", layout="wide")

# --- Sidebar ---
st.sidebar.header("🔑 API & Search")
api_key = st.sidebar.text_input("Enter RestCast API Key", type="password")
tax_id = st.sidebar.text_input("Enter Tax Assessor ID")

if st.sidebar.button("Lookup Property"):
    if not api_key or not tax_id:
        st.sidebar.error("Please provide both API Key and Tax Assessor ID.")
    else:
        # --- API Call ---
        url = f"https://api.restcast.io/properties/{tax_id}"
        headers = {"Authorization": f"Bearer {api_key}"}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            # --- Display Property Info ---
            st.title("🏡 Property Information")
            st.json(data)  # Show raw JSON

            # Example: Format key info if available
            if isinstance(data, dict):
                st.subheader("📋 Key Details")
                st.write(f"**Address:** {data.get('address', 'N/A')}")
                st.write(f"**Owner:** {data.get('owner', 'N/A')}")
                st.write(f"**Assessed Value:** {data.get('assessed_value', 'N/A')}")
                st.write(f"**Year Built:** {data.get('year_built', 'N/A')}")
                st.write(f"**Lot Size:** {data.get('lot_size', 'N/A')} sq ft")

        except requests.exceptions.RequestException as e:
            st.error(f"API Request failed: {e}")
