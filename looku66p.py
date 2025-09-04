import streamlit as st
import json
import pandas as pd
import requests
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io

# --------------------------
# Page configuration
# --------------------------
st.set_page_config(
    page_title="Property Tax Lookup Pro - Ohio",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Hide Streamlit elements and add custom CSS
# --------------------------
hide_streamlit_style = """
<style>
    /* Hide main menu */
    #MainMenu {visibility: hidden;}
    
    /* Hide footer */
    footer {visibility: hidden;}
    
    /* Hide header */
    header {visibility: hidden;}
    
    /* Hide deploy button */
    .stDeployButton {display:none;}
    
    /* Hide "Made with Streamlit" */
    .stApp > footer {visibility: hidden;}
    
    /* Hide hamburger menu */
    .st-emotion-cache-1629p8f {display: none;}
    
    /* Hide fullscreen button on charts/dataframes */
    button[title="View fullscreen"] {
        visibility: hidden;
    }
    
    /* Custom styling for better appearance */
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Hide settings menu */
    .stActionButton {display: none;}
    
    /* Custom footer */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e1117;
        color: white;
        text-align: center;
        padding: 10px 0;
        z-index: 999;
    }
    
    .ohio-counties {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --------------------------
# API Configuration for Ohio Property Data
# --------------------------
# Configure these based on your Ohio property API service
API_BASE_URL = st.secrets.get("OHIO_PROPERTY_API_URL", "https://api.ohiopropertydata.com")
API_KEY = st.secrets.get("OHIO_PROPERTY_API_KEY", "")
API_VERSION = "v1"

# Ohio county configurations
OHIO_COUNTIES = {
    'CUYAHOGA': {'code': '18', 'name': 'Cuyahoga County'},
    'FRANKLIN': {'code': '25', 'name': 'Franklin County'},
    'HAMILTON': {'code': '31', 'name': 'Hamilton County'},
    'SUMMIT': {'code': '77', 'name': 'Summit County'},
    'LUCAS': {'code': '43', 'name': 'Lucas County'},
    'BUTLER': {'code': '07', 'name': 'Butler County'},
    'STARK': {'code': '75', 'name': 'Stark County'},
    'LORAIN': {'code': '41', 'name': 'Lorain County'},
    'MAHONING': {'code': '47', 'name': 'Mahoning County'},
    'MONTGOMERY': {'code': '53', 'name': 'Montgomery County'},
    'LAKE': {'code': '35', 'name': 'Lake County'},
    'WARREN': {'code': '85', 'name': 'Warren County'},
    'TRUMBULL': {'code': '79', 'name': 'Trumbull County'},
    'CLERMONT': {'code': '13', 'name': 'Clermont County'},
    'MEDINA': {'code': '51', 'name': 'Medina County'}
}

# --------------------------
# API Functions for Ohio Property Data
# --------------------------
def fetch_ohio_property_data(parcel_id, county_code=None, region=None):
    """
    Fetch property data from Ohio property API
    """
    try:
        if not API_KEY:
            return {
                "status": "ERROR", 
                "message": "API key not configured. Please set OHIO_PROPERTY_API_KEY in secrets."
            }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "X-API-Version": API_VERSION
        }
        
        # Build API URL based on available parameters
        if county_code:
            url = f"{API_BASE_URL}/{API_VERSION}/property/county/{county_code}/parcel/{parcel_id}"
        elif region:
            url = f"{API_BASE_URL}/{API_VERSION}/property/region/{region}/parcel/{parcel_id}"
        else:
            # General Ohio search
            url = f"{API_BASE_URL}/{API_VERSION}/property/ohio/parcel/{parcel_id}"
        
        # Add query parameters for Ohio-specific data
        params = {
            'include_tax_data': 'true',
            'include_assessments': 'true',
            'include_sales_history': 'true',
            'include_zoning': 'true',
            'format': 'json'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "OK",
                "results": [data] if isinstance(data, dict) else data,
                "api_source": "Ohio Property Data API"
            }
        elif response.status_code == 404:
            return {
                "status": "NOT_FOUND", 
                "message": f"Property with parcel ID '{parcel_id}' not found in Ohio records."
            }
        elif response.status_code == 401:
            return {
                "status": "ERROR", 
                "message": "API authentication failed. Please check your API key."
            }
        elif response.status_code == 429:
            return {
                "status": "ERROR", 
                "message": "API rate limit exceeded. Please try again later."
            }
        else:
            return {
                "status": "ERROR", 
                "message": f"API returned status code: {response.status_code}. Response: {response.text[:200]}"
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "ERROR", 
            "message": "Request timed out. The Ohio property API may be experiencing delays."
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "ERROR", 
            "message": "Connection error. Unable to reach Ohio property API."
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "ERROR", 
            "message": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Unexpected error: {str(e)}"
        }

def search_property_by_address(address, city, county=None):
    """
    Search property by address in Ohio
    """
    try:
        if not API_KEY:
            return {
                "status": "ERROR", 
                "message": "API key not configured."
            }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        url = f"{API_BASE_URL}/{API_VERSION}/property/search/address"
        
        data = {
            "address": address,
            "city": city,
            "state": "OH",
            "county": county
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "status": "ERROR", 
                "message": f"Address search failed: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Address search error: {str(e)}"
        }

# --------------------------
# Session state
# --------------------------
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'cached_results' not in st.session_state:
    st.session_state.cached_results = {}

# Maximum usage limit
MAX_SEARCHES = 10

# --------------------------
# Sidebar: Usage stats and Ohio counties
# --------------------------
with st.sidebar:
    st.header("📈 Usage Statistics")
    usage_remaining = MAX_SEARCHES - st.session_state.usage_count
    if usage_remaining > 0:
        st.metric("Searches Remaining", usage_remaining)
        progress_value = st.session_state.usage_count / MAX_SEARCHES
        st.progress(progress_value)
        
        # Color-coded warning
        if usage_remaining <= 2:
            st.error(f"⚠️ Only {usage_remaining} searches left!")
        elif usage_remaining <= 5:
            st.warning(f"⚠️ {usage_remaining} searches remaining")
        else:
            st.success(f"✅ {usage_remaining} searches available")
    else:
        st.error("❌ Usage limit reached (10 searches)")
        st.markdown("**Refresh the page to reset your search count**")

    # Ohio Counties Information
    st.divider()
    st.subheader("🏛️ Ohio Counties Supported")
    with st.expander("View Supported Counties"):
        for county_key, county_info in OHIO_COUNTIES.items():
            st.write(f"**{county_info['name']}** (Code: {county_info['code']})")

    if st.session_state.search_history:
        st.divider()
        st.subheader("🔍 Recent Searches")
        for i, search in enumerate(st.session_state.search_history[-5:]):
            st.text(f"{i+1}. {search}")
    
    # Reset button
    st.divider()
    if st.button("🔄 Reset Search Count", type="secondary"):
        st.session_state.usage_count = 0
        st.session_state.search_history = []
        st.session_state.cached_results = {}
        st.rerun()

    # API Status
    st.divider()
    st.subheader("🔌 API Status")
    if not API_KEY:
        st.error("❌ API Key Missing")
        st.caption("Set OHIO_PROPERTY_API_KEY in secrets")
    else:
        st.success("✅ Ohio API Configured")
        st.caption("Ready for live Ohio property data")

# --------------------------
# Helper: Create property cards for Ohio data
# --------------------------
def create_ohio_property_cards(data):
    """Create enhanced property cards specifically for Ohio property data"""
    
    # Create colorful Property Overview section
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 25px; border-radius: 20px; margin: 15px 0; color: white; 
                box-shadow: 0 8px 25px rgba(30,60,114,0.3);'>
        <h2 style='color: white; margin-bottom: 20px; text-align: center; font-size: 28px;'>🏠 Ohio Property Overview</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create three colorful metric columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Location Info - Ohio Blue gradient
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(33,150,243,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>📍 Ohio Location</h4>
            <div style='margin-bottom: 12px;'><strong>Parcel ID:</strong><br><span style='font-size: 18px; font-weight: bold;'>{data.get('parcel_id', data.get('parcel_number', 'N/A'))}</span></div>
            <div style='margin-bottom: 12px;'><strong>County:</strong><br><span style='font-size: 16px;'>{data.get('county_name', data.get('county', 'N/A'))}</span></div>
            <div><strong>Municipality:</strong><br><span style='font-size: 16px;'>{data.get('municipality', data.get('city', 'N/A'))}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Market Values - Green gradient
        total_value = data.get('market_value_total', data.get('assessed_value_total', data.get('total_value', 0)))
        land_value = data.get('market_value_land', data.get('assessed_value_land', data.get('land_value', 0)))
        building_value = data.get('market_value_building', data.get('assessed_value_building', data.get('building_value', 0)))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(76,175,80,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>💰 Assessed Values</h4>
            <div style='margin-bottom: 12px;'><strong>Total Value:</strong><br><span style='font-size: 18px; font-weight: bold;'>${float(total_value):,.0f}</span></div>
            <div style='margin-bottom: 12px;'><strong>Land Value:</strong><br><span style='font-size: 16px;'>${float(land_value):,.0f}</span></div>
            <div><strong>Building Value:</strong><br><span style='font-size: 16px;'>${float(building_value):,.0f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Property Details - Orange gradient
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(255,152,0,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏘️ Property Info</h4>
            <div style='margin-bottom: 12px;'><strong>Acreage:</strong><br><span style='font-size: 18px; font-weight: bold;'>{data.get('acreage', data.get('lot_size', 'N/A'))}</span></div>
            <div style='margin-bottom: 12px;'><strong>Property Class:</strong><br><span style='font-size: 16px;'>{data.get('property_class', data.get('land_use', 'N/A'))}</span></div>
            <div><strong>Tax District:</strong><br><span style='font-size: 16px;'>{data.get('tax_district', 'N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Address Information
    st.markdown("""
    <div style='background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>📍 Address Information</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        property_address = data.get('property_address', data.get('address', 'N/A'))
        city = data.get('city', data.get('municipality', 'N/A'))
        zip_code = data.get('zip_code', data.get('postal_code', 'N/A'))
        
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Property Address:</div>
        <div style='color: #4a5568; margin-bottom: 5px;'>{property_address}</div>
        <div style='color: #4a5568; margin-bottom: 10px;'>{city}, OH {zip_code}</div>
        """, unsafe_allow_html=True)
        
        if data.get('latitude') and data.get('longitude'):
            st.markdown(f"<div style='color: #2d3748;'><strong>Coordinates:</strong> {data.get('latitude')}, {data.get('longitude')}</div>", unsafe_allow_html=True)
    
    with col2:
        mailing_address = data.get('mailing_address', property_address)
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Mailing Address:</div>
        <div style='color: #4a5568; margin-bottom: 5px;'>{mailing_address}</div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Owner Information
    st.markdown("""
    <div style='background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>👤 Owner Information</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        owner_name = data.get('owner_name', data.get('property_owner', 'N/A'))
        st.markdown(f"""
        <div style='color: #2d3748;'><strong>Owner:</strong> {owner_name}</div><br>
        <div style='color: #2d3748;'><strong>Owner Occupied:</strong> {data.get('owner_occupied', 'Unknown')}</div>
        """, unsafe_allow_html=True)
    with col2:
        if data.get('sale_date', data.get('last_sale_date')):
            st.markdown(f"<div style='color: #2d3748;'><strong>Last Sale Date:</strong> {data.get('sale_date', data.get('last_sale_date'))}</div><br>", unsafe_allow_html=True)
        if data.get('sale_price', data.get('last_sale_price')):
            sale_price = float(data.get('sale_price', data.get('last_sale_price', 0)))
            st.markdown(f"<div style='color: #2d3748;'><strong>Sale Price:</strong> ${sale_price:,.2f}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Ohio Tax Information
    if data.get('tax_amount') or data.get('annual_tax') or data.get('property_tax'):
        st.markdown("""
        <div style='background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <h3 style='color: #2d3748; margin-bottom: 15px;'>🏛️ Ohio Tax Information</h3>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tax_amount = data.get('tax_amount', data.get('annual_tax', data.get('property_tax', 0)))
            st.markdown(f"<div style='color: #2d3748;'><strong>Annual Tax:</strong> ${float(tax_amount):,.2f}</div>", unsafe_allow_html=True)
        with col2:
            tax_year = data.get('tax_year', data.get('assessment_year', 'N/A'))
            st.markdown(f"<div style='color: #2d3748;'><strong>Tax Year:</strong> {tax_year}</div>", unsafe_allow_html=True)
        with col3:
            if data.get('homestead_exemption'):
                st.markdown(f"<div style='color: #2d3748;'><strong>Homestead:</strong> {data.get('homestead_exemption')}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # Additional Ohio Details
    st.markdown("""
    <div style='background: linear-gradient(135deg, #F3E5F5 0%, #E1BEE7 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>📋 Additional Ohio Details</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>School District:</strong> {data.get('school_district', 'N/A')}</div>
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Zoning:</strong> {data.get('zoning', 'N/A')}</div>
        <div style='color: #2d3748;'><strong>Township:</strong> {data.get('township', 'N/A')}</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Neighborhood:</strong> {data.get('neighborhood', 'N/A')}</div>
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Census Tract:</strong> {data.get('census_tract', 'N/A')}</div>
        <div style='color: #2d3748;'><strong>Deed Book:</strong> {data.get('deed_book', 'N/A')}</div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Year Built:</strong> {data.get('year_built', 'N/A')}</div>
        <div style='color: #2d3748;'><strong>Last Updated:</strong> {data.get('last_updated', data.get('data_date', 'N/A'))}</div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("📄 Complete Raw JSON Data")
    with st.expander("View Full API Response", expanded=False):
        st.json(data)

# --------------------------
# Helper: Create PDF for Ohio data
# --------------------------
def create_ohio_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, alignment=1, textColor=colors.darkblue)
    story = [Paragraph("Ohio Property Tax Lookup Report", title_style), Spacer(1,20)]

    # Add generation timestamp
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1,20))

    # Ohio-specific property data table
    overview_data = [
        ['Ohio Property Information', ''],
        ['Parcel ID', data.get('parcel_id', data.get('parcel_number', 'N/A'))],
        ['Property Address', data.get('property_address', data.get('address', 'N/A'))],
        ['City, State ZIP', f"{data.get('city', 'N/A')}, OH {data.get('zip_code', 'N/A')}"],
        ['County', data.get('county_name', data.get('county', 'N/A'))],
        ['Owner', data.get('owner_name', data.get('property_owner', 'N/A'))],
        ['Total Assessed Value', f"${float(data.get('market_value_total', data.get('assessed_value_total', 0))):,.2f}"],
        ['Annual Tax', f"${float(data.get('tax_amount', data.get('annual_tax', 0))):,.2f}"],
        ['School District', data.get('school_district', 'N/A')],
        ['Property Class', data.get('property_class', data.get('land_use', 'N/A'))]
    ]
    
    table = Table(overview_data, colWidths=[2*inch,4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'TOP')
    ]))
    story.append(table)
    story.append(Spacer(1,20))

    # Add raw JSON data (truncated for PDF)
    story.append(Paragraph("Raw API Response Data", styles['Heading2']))
    json_text = json.dumps(data, indent=2)
    json_lines = json_text.split('\n')[:50]
    for line in json_lines:
        if line.strip():
            story.append(Paragraph(f"<font name='Courier' size='8'>{line}</font>", styles['Normal']))
    if len(json_lines) > 50:
        story.append(Paragraph("... (Data truncated for PDF)", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Main App UI
# --------------------------
st.title("🏠 Property Tax Lookup Pro - Ohio")
st.markdown("**Ohio property research with live API integration** | *Limited to 10 searches per session*")

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.stop()

# Search tabs
tab1, tab2 = st.tabs(["🔍 Search by Parcel ID", "📍 Search by Address"])

with tab1:
    st.subheader("🔍 Ohio Property Search by Parcel ID")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        parcel_id = st.text_input(
            "Enter Ohio Parcel ID", 
            placeholder="e.g., 12-34567-890", 
            help="Enter a valid Ohio parcel ID"
        )
    with col2:
        selected_county = st.selectbox(
            "County (Optional)",
            ["Auto-detect"] + [county_info['name'] for county_info in OHIO_COUNTIES.values()],
            help="Select county to narrow search"
        )
    with col3:
        search_button = st.button(
            "🔍 Search Property", 
            type="primary", 
            disabled=(st.session_state.usage_count >= MAX_SEARCHES)
        )

    # Parcel ID search functionality
    if search_button and parcel_id:
        if st.session_state.usage_count >= MAX_SEARCHES:
            st.error("Usage limit reached!")
        elif not parcel_id.strip():
            st.error("Please enter a valid Parcel ID")
        else:
            with st.spinner("Fetching Ohio property data from API..."):
                try:
                    # Determine county code if selected
                    county_code = None
                    if selected_county != "Auto-detect":
                        for key, info in OHIO_COUNTIES.items():
                            if info['name'] == selected_county:
                                county_code = info['code']
                                break
                    
                    # Fetch real Ohio property data
                    api_response = fetch_ohio_property_data(parcel_id, county_code)

                    if api_response.get('status') == "OK" and api_response.get('results'):
                        property_data = api_response['results'][0]
                        
                        # Update usage count and history
                        st.session_state.usage_count += 1
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        county_info = f" - {selected_county}" if selected_county != "Auto-detect" else ""
                        st.session_state.search_history.append(f"{parcel_id}{county_info} - {timestamp}")
                        
                        # Success message
                        st.success(f"✅ Ohio property data found! (Search {st.session_state.usage_count}/{MAX_SEARCHES})")
                        
                        create_ohio_property_cards(property_data)

                        # Export buttons
                        st.divider()
                        st.subheader("📥 Export Options")
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_buffer = create_ohio_pdf(property_data)
                            st.download_button(
                                "📄 Download Ohio Property PDF", 
                                pdf_buffer.getvalue(),
                                file_name=f"ohio_property_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                                mime="application/pdf"
                            )
                        with col2:
                            json_str = json.dumps(property_data, indent=2)
                            st.download_button(
                                "📋 Download JSON Data", 
                                json_str,
                                file_name=f"ohio_property_data_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                            
                    elif api_response.get('status') == "NOT_FOUND":
                        st.error("❌ No Ohio property found for the provided Parcel ID")
                        st.info("💡 Please verify the Parcel ID and try again. Make sure it's a valid Ohio parcel ID.")
                        # Still increment usage count for failed searches
                        st.session_state.usage_count += 1
                    else:
                        error_msg = api_response.get('message', 'Unknown error occurred')
                        st.error(f"❌ Error: {error_msg}")
                        st.info("💡 Please check your API configuration or try again later.")
                        # Still increment usage count for failed searches
                        st.session_state.usage_count += 1
                        
                except Exception as e:
                    st.error(f"❌ Unexpected error occurred: {str(e)}")
                    st.info("💡 Please try again or contact support")
                    # Increment usage count for errors too
                    st.session_state.usage_count += 1

with tab2:
    st.subheader("📍 Ohio Property Search by Address")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_address = st.text_input(
            "Property Address", 
            placeholder="e.g., 123 Main Street", 
            help="Enter the property address"
        )
    with col2:
        search_city = st.text_input(
            "City", 
            placeholder="e.g., Columbus", 
            help="Enter the city name"
        )
    with col3:
        address_county = st.selectbox(
            "County",
            ["Auto-detect"] + [county_info['name'] for county_info in OHIO_COUNTIES.values()],
            help="Select county",
            key="address_county"
        )
    
    address_search_button = st.button(
        "🔍 Search by Address", 
        type="primary", 
        disabled=(st.session_state.usage_count >= MAX_SEARCHES),
        key="address_search"
    )

    # Address search functionality
    if address_search_button and search_address and search_city:
        if st.session_state.usage_count >= MAX_SEARCHES:
            st.error("Usage limit reached!")
        else:
            with st.spinner("Searching Ohio property by address..."):
                try:
                    county_name = address_county if address_county != "Auto-detect" else None
                    api_response = search_property_by_address(search_address, search_city, county_name)
                    
                    if api_response.get('status') == "OK" and api_response.get('results'):
                        st.session_state.usage_count += 1
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        st.session_state.search_history.append(f"{search_address}, {search_city} - {timestamp}")
                        
                        if len(api_response['results']) == 1:
                            # Single result found
                            property_data = api_response['results'][0]
                            st.success(f"✅ Property found! (Search {st.session_state.usage_count}/{MAX_SEARCHES})")
                            create_ohio_property_cards(property_data)
                        else:
                            # Multiple results found
                            st.success(f"✅ Found {len(api_response['results'])} properties matching your search!")
                            for i, property_data in enumerate(api_response['results'][:5]):  # Show max 5 results
                                with st.expander(f"Property {i+1}: {property_data.get('address', 'N/A')} - Parcel: {property_data.get('parcel_id', 'N/A')}"):
                                    create_ohio_property_cards(property_data)
                    else:
                        error_msg = api_response.get('message', 'No properties found for this address')
                        st.error(f"❌ {error_msg}")
                        st.session_state.usage_count += 1
                        
                except Exception as e:
                    st.error(f"❌ Address search error: {str(e)}")
                    st.session_state.usage_count += 1

# API Configuration Help
st.divider()
with st.expander("⚙️ API Configuration Help"):
    st.markdown("""
    ### Setting up Ohio Property API
    
    To use this application with live Ohio property data, you need to:
    
    1. **Get API Access**: Sign up for Ohio property data API service
    2. **Configure Secrets**: In your Streamlit app, go to Settings → Secrets and add:
    ```toml
    OHIO_PROPERTY_API_KEY = "your_api_key_here"
    OHIO_PROPERTY_API_URL = "https://api.ohiopropertydata.com"
    ```
    
    ### Supported Ohio Counties
    This application supports property lookups for major Ohio counties including:
    - **Cuyahoga County** (Cleveland area)
    - **Franklin County** (Columbus area) 
    - **Hamilton County** (Cincinnati area)
    - **Summit County** (Akron area)
    - **Lucas County** (Toledo area)
    - And many more...
    
    ### Search Tips
    - **Parcel ID Format**: Usually follows county-specific patterns (e.g., 12-34567-890)
    - **Address Search**: Works best with complete street addresses
    - **County Selection**: Helps narrow search and improve accuracy
    """)

# Usage warning at bottom
st.divider()
remaining = MAX_SEARCHES - st.session_state.usage_count
if remaining <= 2 and remaining > 0:
    st.warning(f"⚠️ Only {remaining} searches remaining in this session!")
elif remaining == 0:
    st.error("❌ No searches remaining. Refresh the page to reset.")

# Custom footer with upgrade option
st.markdown(
    f"""
    <div class="custom-footer">
        Ohio Property Tax Lookup Pro | Searches Used: {st.session_state.usage_count}/{MAX_SEARCHES} | 
        Session: {datetime.now().strftime('%Y-%m-%d')} | 
        <a href="https://aipropiq.com/funnel-evergreen-checkout/" target="_blank" style="color: #ff6b6b; text-decoration: none;">
            💎 Upgrade to Premium
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)
