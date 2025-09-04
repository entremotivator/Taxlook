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
    page_title="Ohio Property Tax Lookup Pro",
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
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --------------------------
# API Configuration
# --------------------------
# Replace these with your actual API details
API_BASE_URL = "https://api.yourpropertyservice.com"  # Replace with actual API URL
API_KEY = st.secrets.get("PROPERTY_API_KEY", "your_api_key_here")  # Use Streamlit secrets

# --------------------------
# API Functions
# --------------------------
def fetch_property_data(parcel_id, county=None):
    """
    Fetch property data from the actual API for Ohio statewide
    Replace this function with your actual API call
    """
    try:
        # Example API call structure - adjust based on your API
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Construct API URL - adjust based on your API endpoint
        # Include Ohio state parameter and optional county filter
        params = {
            "state": "OH",
            "parcel_id": parcel_id
        }
        if county:
            params["county"] = county
            
        url = f"{API_BASE_URL}/property/search"
        
        # Make the API request
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"status": "NOT_FOUND", "message": "Property not found in Ohio"}
        elif response.status_code == 401:
            return {"status": "ERROR", "message": "API authentication failed"}
        elif response.status_code == 429:
            return {"status": "ERROR", "message": "API rate limit exceeded"}
        else:
            return {"status": "ERROR", "message": f"API returned status code: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"status": "ERROR", "message": "Request timed out - try again"}
    except requests.exceptions.ConnectionError:
        return {"status": "ERROR", "message": "Connection error - check internet connection"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Unexpected error: {str(e)}"}

def search_property_by_address(address, city=None, county=None):
    """
    Search property by address in Ohio
    """
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {
            "state": "OH",
            "address": address
        }
        if city:
            params["city"] = city
        if county:
            params["county"] = county
            
        url = f"{API_BASE_URL}/property/address-search"
        response = requests.get(url, headers=headers, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "ERROR", "message": f"Address search failed: {response.status_code}"}
            
    except Exception as e:
        return {"status": "ERROR", "message": f"Address search error: {str(e)}"}

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
MAX_SEARCHES = 25  # Increased for Ohio statewide

# Ohio Counties for dropdown
OHIO_COUNTIES = [
    "Adams", "Allen", "Ashland", "Ashtabula", "Athens", "Auglaize", "Belmont", "Brown",
    "Butler", "Carroll", "Champaign", "Clark", "Clermont", "Clinton", "Columbiana",
    "Coshocton", "Crawford", "Cuyahoga", "Darke", "Defiance", "Delaware", "Erie",
    "Fairfield", "Fayette", "Franklin", "Fulton", "Gallia", "Geauga", "Greene",
    "Guernsey", "Hamilton", "Hancock", "Hardin", "Harrison", "Henry", "Highland",
    "Hocking", "Holmes", "Huron", "Jackson", "Jefferson", "Knox", "Lake", "Lawrence",
    "Licking", "Logan", "Lorain", "Lucas", "Madison", "Mahoning", "Marion", "Medina",
    "Meigs", "Mercer", "Miami", "Monroe", "Montgomery", "Morgan", "Morrow", "Muskingum",
    "Noble", "Ottawa", "Paulding", "Perry", "Pickaway", "Pike", "Portage", "Preble",
    "Putnam", "Richland", "Ross", "Sandusky", "Scioto", "Seneca", "Shelby", "Stark",
    "Summit", "Trumbull", "Tuscarawas", "Union", "Van Wert", "Vinton", "Warren",
    "Washington", "Wayne", "Williams", "Wood", "Wyandot"
]

# --------------------------
# Sidebar: Usage stats and filters
# --------------------------
with st.sidebar:
    st.header("🏛️ Ohio Property Search")
    st.markdown("**Statewide Coverage - All 88 Counties**")
    
    # County filter
    st.subheader("🗺️ Search Filters")
    selected_county = st.selectbox(
        "Filter by County (Optional)", 
        ["All Counties"] + OHIO_COUNTIES,
        help="Select a specific Ohio county to narrow your search"
    )
    
    st.divider()
    st.header("📈 Usage Statistics")
    usage_remaining = MAX_SEARCHES - st.session_state.usage_count
    if usage_remaining > 0:
        st.metric("Searches Remaining", usage_remaining)
        progress_value = st.session_state.usage_count / MAX_SEARCHES
        st.progress(progress_value)
        
        # Color-coded warning
        if usage_remaining <= 3:
            st.error(f"⚠️ Only {usage_remaining} searches left!")
        elif usage_remaining <= 8:
            st.warning(f"⚠️ {usage_remaining} searches remaining")
        else:
            st.success(f"✅ {usage_remaining} searches available")
    else:
        st.error("❌ Usage limit reached (25 searches)")
        st.markdown("**Refresh the page to reset your search count**")

    if st.session_state.search_history:
        st.subheader("🔍 Recent Searches")
        for i, search in enumerate(st.session_state.search_history[-8:]):
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
    if API_KEY == "your_api_key_here":
        st.error("❌ API Not Configured")
        st.caption("Set PROPERTY_API_KEY in secrets")
    else:
        st.success("✅ API Ready - Ohio Statewide")

# --------------------------
# Helper: Create property cards
# --------------------------
def create_property_cards(data):
    # Create colorful Property Overview section
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 20px; margin: 15px 0; color: white; 
                box-shadow: 0 8px 25px rgba(102,126,234,0.3);'>
        <h2 style='color: white; margin-bottom: 20px; text-align: center; font-size: 28px;'>🏠 Ohio Property Overview</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create three colorful metric columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Location Info - Blue/Teal gradient
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(79,172,254,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>📍 Location</h4>
            <div style='margin-bottom: 12px;'><strong>Parcel ID:</strong><br><span style='font-size: 18px; font-weight: bold;'>{data.get('parcel_id','N/A')}</span></div>
            <div style='margin-bottom: 12px;'><strong>County:</strong><br><span style='font-size: 16px;'>{data.get('county_name','N/A')}</span></div>
            <div><strong>Municipality:</strong><br><span style='font-size: 16px;'>{data.get('muni_name','N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Market Values - Green/Emerald gradient
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(67,233,123,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>💰 Market Values</h4>
            <div style='margin-bottom: 12px;'><strong>Total Value:</strong><br><span style='font-size: 18px; font-weight: bold;'>${float(data.get('mkt_val_tot',0)):,.0f}</span></div>
            <div style='margin-bottom: 12px;'><strong>Land Value:</strong><br><span style='font-size: 16px;'>${float(data.get('mkt_val_land',0)):,.0f}</span></div>
            <div><strong>Building Value:</strong><br><span style='font-size: 16px;'>${float(data.get('mkt_val_bldg',0)):,.0f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Property Details - Orange/Pink gradient
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(250,112,154,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏘️ Property Info</h4>
            <div style='margin-bottom: 12px;'><strong>Acreage:</strong><br><span style='font-size: 18px; font-weight: bold;'>{data.get('acreage','N/A')}</span></div>
            <div style='margin-bottom: 12px;'><strong>Land Use:</strong><br><span style='font-size: 16px;'>{data.get('land_use_class','N/A')}</span></div>
            <div><strong>Buildings:</strong><br><span style='font-size: 16px;'>{data.get('buildings','N/A')}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <div style='background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>📍 Address Information</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Property Address:</div>
        <div style='color: #4a5568; margin-bottom: 5px;'>{data.get('address','N/A')}</div>
        <div style='color: #4a5568; margin-bottom: 10px;'>{data.get('addr_city','')}, {data.get('state_abbr','')} {data.get('addr_zip','')}</div>
        """, unsafe_allow_html=True)
        if data.get('latitude') and data.get('longitude'):
            st.markdown(f"<div style='color: #2d3748;'><strong>Coordinates:</strong> {data.get('latitude')}, {data.get('longitude')}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Mailing Address:</div>
        <div style='color: #4a5568; margin-bottom: 5px;'>{data.get('mail_address1','N/A')}</div>
        """, unsafe_allow_html=True)
        if data.get('mail_address3'):
            st.markdown(f"<div style='color: #4a5568;'>{data.get('mail_address3')}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>👤 Owner Information</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div style='color: #2d3748;'><strong>Owner:</strong> {data.get('owner','N/A')}</div><br>
        <div style='color: #2d3748;'><strong>Owner Occupied:</strong> {'Yes' if data.get('owner_occupied') else 'No'}</div>
        """, unsafe_allow_html=True)
    with col2:
        if data.get('trans_date'):
            st.markdown(f"<div style='color: #2d3748;'><strong>Last Transaction:</strong> {data.get('trans_date')}</div><br>", unsafe_allow_html=True)
        if data.get('sale_price'):
            st.markdown(f"<div style='color: #2d3748;'><strong>Sale Price:</strong> ${float(data.get('sale_price',0)):,.2f}</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>📋 Additional Details</h3>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>School District:</strong> {data.get('school_district','N/A')}</div>
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Zoning:</strong> {data.get('zoning','N/A')}</div>
        <div style='color: #2d3748;'><strong>Neighborhood Code:</strong> {data.get('ngh_code','N/A')}</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Census Tract:</strong> {data.get('census_tract','N/A')}</div>
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Census Block:</strong> {data.get('census_block','N/A')}</div>
        <div style='color: #2d3748;'><strong>USPS Type:</strong> {data.get('usps_residential','N/A')}</div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style='color: #2d3748; margin-bottom: 8px;'><strong>Elevation:</strong> {data.get('elevation','N/A')} ft</div>
        <div style='color: #2d3748;'><strong>Last Updated:</strong> {data.get('last_updated','N/A')}</div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    if data.get('land_cover'):
        st.divider()
        st.subheader("🌍 Land Cover Analysis")
        land_cover_df = pd.DataFrame(list(data['land_cover'].items()), columns=['Cover Type','Percentage'])
        st.dataframe(land_cover_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("📄 Complete Raw JSON Data")
    with st.expander("View Full JSON Response", expanded=False):
        st.json(data)

# --------------------------
# Helper: Create PDF
# --------------------------
def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=20, alignment=1, textColor=colors.darkblue)
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, textColor=colors.darkblue)
    story = [Paragraph("Ohio Property Tax Lookup Report", title_style), Spacer(1,20)]

    # Add generation timestamp
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Spacer(1,20))

    overview_data = [
        ['Property Information', ''],
        ['Parcel ID', data.get('parcel_id','N/A')],
        ['Address', data.get('address','N/A')],
        ['City, State ZIP', f"{data.get('addr_city','')}, {data.get('state_abbr','')} {data.get('addr_zip','')}"],
        ['County', data.get('county_name','N/A')],
        ['Municipality', data.get('muni_name','N/A')],
        ['Owner', data.get('owner','N/A')],
        ['Market Value (Total)', f"${float(data.get('mkt_val_tot',0)):,.2f}"],
        ['Acreage', str(data.get('acreage','N/A'))]
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

    story.append(Paragraph("Raw JSON Data", heading_style))
    json_text = json.dumps(data, indent=2)
    json_lines = json_text.split('\n')[:50]  # Limit lines for PDF
    for line in json_lines:
        if line.strip():  # Skip empty lines
            story.append(Paragraph(f"<font name='Courier' size='8'>{line}</font>", styles['Normal']))
    if len(json_lines) > 50:
        story.append(Paragraph("... (JSON data truncated for PDF)", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Main App UI
# --------------------------
st.title("🏛️ Ohio Property Tax Lookup Pro")
st.markdown("**Statewide Ohio Property Research - All 88 Counties** | *25 searches per session*")

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (25 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.stop()

# Search options
st.subheader("🔍 Property Search Options")

# Create tabs for different search methods
tab1, tab2 = st.tabs(["📋 Parcel ID Search", "🏠 Address Search"])

with tab1:
    st.markdown("**Search by Parcel ID**")
    col1, col2 = st.columns([3,1])
    with col1:
        parcel_id = st.text_input("Enter Parcel ID", placeholder="e.g., 00824064", help="Enter a valid Ohio parcel ID")
    with col2:
        search_button = st.button("🔍 Search by Parcel", type="primary", disabled=(st.session_state.usage_count >= MAX_SEARCHES))

with tab2:
    st.markdown("**Search by Property Address**")
    col1, col2, col3 = st.columns([2,1,1])
    with col1:
        address_search = st.text_input("Property Address", placeholder="e.g., 123 Main St", help="Enter property address")
    with col2:
        city_search = st.text_input("City", placeholder="Columbus", help="City name (optional)")
    with col3:
        address_search_button = st.button("🔍 Search by Address", type="primary", disabled=(st.session_state.usage_count >= MAX_SEARCHES))

# Parcel ID Search
if search_button and parcel_id:
    if st.session_state.usage_count >= MAX_SEARCHES:
        st.error("Usage limit reached!")
    elif not parcel_id.strip():
        st.error("Please enter a valid Parcel ID")
    else:
        with st.spinner("Searching Ohio statewide property database..."):
            try:
                county_filter = None if selected_county == "All Counties" else selected_county
                
                # Call real API
                api_response = fetch_property_data(parcel_id.strip(), county_filter)

                if api_response.get('status') == "OK" and api_response.get('results'):
                    property_data = api_response['results'][0]
                    
                    # Update usage count and history
                    st.session_state.usage_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    st.session_state.search_history.append(f"{parcel_id} ({property_data.get('county_name', 'Unknown')}) - {timestamp}")
                    
                    # Success message
                    st.success(f"✅ Property found in {property_data.get('county_name', 'Unknown')} County, Ohio! (Search {st.session_state.usage_count}/{MAX_SEARCHES})")
                    
                    create_property_cards(property_data)

                    # Export buttons
                    st.divider()
                    st.subheader("📥 Export Options")
                    col1, col2 = st.columns(2)
                    with col1:
                        pdf_buffer = create_pdf(property_data)
                        st.download_button(
                            "📄 Download PDF Report", 
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
                    st.error("❌ No property found for the provided Parcel ID in Ohio")
                    if county_filter:
                        st.info(f"💡 No results found in {county_filter} County. Try searching all counties or verify the Parcel ID.")
                    else:
                        st.info("💡 Please verify the Parcel ID and try again")
                    st.session_state.usage_count += 1
                else:
                    error_msg = api_response.get('message', 'Unknown error occurred')
                    st.error(f"❌ Error: {error_msg}")
                    st.info("💡 Please try again or contact support if the issue persists")
                    st.session_state.usage_count += 1
                    
            except Exception as e:
                st.error(f"❌ Unexpected error occurred: {str(e)}")
                st.info("💡 Please try again or contact support")
                st.session_state.usage_count += 1

# Address Search
if address_search_button and address_search:
    if st.session_state.usage_count >= MAX_SEARCHES:
        st.error("Usage limit reached!")
    elif not address_search.strip():
        st.error("Please enter a valid address")
    else:
        with st.spinner("Searching Ohio properties by address..."):
            try:
                county_filter = None if selected_county == "All Counties" else selected_county
                
                # Call address search API
                api_response = search_property_by_address(address_search.strip(), city_search.strip() if city_search else None, county_filter)

                if api_response.get('status') == "OK" and api_response.get('results'):
                    properties = api_response['results']
                    
                    # Update usage count
                    st.session_state.usage_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    search_location = f"{address_search}, {city_search}" if city_search else address_search
                    st.session_state.search_history.append(f"Address: {search_location} - {timestamp}")
                    
                    if len(properties) == 1:
                        # Single result
                        property_data = properties[0]
                        st.success(f"✅ Property found: {property_data.get('address', 'N/A')}, {property_data.get('county_name', 'Unknown')} County!")
                        create_property_cards(property_data)
                        
                        # Export options for single result
                        st.divider()
                        st.subheader("📥 Export Options")
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_buffer = create_pdf(property_data)
                            st.download_button(
                                "📄 Download PDF Report", 
                                pdf_buffer.getvalue(),
                                file_name=f"ohio_property_report_{property_data.get('parcel_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                                mime="application/pdf"
                            )
                        with col2:
                            json_str = json.dumps(property_data, indent=2)
                            st.download_button(
                                "📋 Download JSON Data", 
                                json_str,
                                file_name=f"ohio_property_data_{property_data.get('parcel_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                    else:
                        # Multiple results
                        st.success(f"✅ Found {len(properties)} properties matching your address search!")
                        
                        # Display results in a table format
                        st.subheader("🏘️ Multiple Properties Found")
                        
                        # Create a summary table
                        summary_data = []
                        for i, prop in enumerate(properties):
                            summary_data.append({
                                "Select": f"View Details #{i+1}",
                                "Address": prop.get('address', 'N/A'),
                                "City": prop.get('addr_city', 'N/A'),
                                "County": prop.get('county_name', 'N/A'),
                                "Parcel ID": prop.get('parcel_id', 'N/A'),
                                "Market Value": f"${float(prop.get('mkt_val_tot', 0)):,.0f}",
                                "Owner": prop.get('owner', 'N/A')[:30] + "..." if len(prop.get('owner', '')) > 30 else prop.get('owner', 'N/A')
                            })
                        
                        # Display as dataframe
                        df = pd.DataFrame(summary_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Allow selection of specific property
                        st.subheader("📋 Select Property for Details")
                        selected_index = st.selectbox(
                            "Choose a property to view full details:",
                            range(len(properties)),
                            format_func=lambda x: f"Property #{x+1}: {properties[x].get('address', 'N/A')} - {properties[x].get('county_name', 'N/A')} County"
                        )
                        
                        if st.button("🔍 View Selected Property Details", type="secondary"):
                            selected_property = properties[selected_index]
                            st.markdown("---")
                            st.markdown(f"### 🏠 Detailed View: Property #{selected_index + 1}")
                            create_property_cards(selected_property)
                            
                            # Export options for selected property
                            st.divider()
                            st.subheader("📥 Export Selected Property")
                            col1, col2 = st.columns(2)
                            with col1:
                                pdf_buffer = create_pdf(selected_property)
                                st.download_button(
                                    "📄 Download PDF Report", 
                                    pdf_buffer.getvalue(),
                                    file_name=f"ohio_property_report_{selected_property.get('parcel_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                                    mime="application/pdf"
                                )
                            with col2:
                                json_str = json.dumps(selected_property, indent=2)
                                st.download_button(
                                    "📋 Download JSON Data", 
                                    json_str,
                                    file_name=f"ohio_property_data_{selected_property.get('parcel_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                    mime="application/json"
                                )
                        
                        # Bulk export option
                        st.divider()
                        st.subheader("📦 Bulk Export All Results")
                        col1, col2 = st.columns(2)
                        with col1:
                            # Export all as JSON
                            all_json = json.dumps(properties, indent=2)
                            st.download_button(
                                "📋 Download All as JSON", 
                                all_json,
                                file_name=f"ohio_properties_bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                        with col2:
                            # Export summary as CSV
                            csv_data = pd.DataFrame(summary_data).to_csv(index=False)
                            st.download_button(
                                "📊 Download Summary CSV", 
                                csv_data,
                                file_name=f"ohio_properties_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
                                mime="text/csv"
                            )
                        
                elif api_response.get('status') == "NOT_FOUND":
                    st.error("❌ No properties found for the provided address in Ohio")
                    if county_filter:
                        st.info(f"💡 No results found in {county_filter} County. Try searching all counties or check the address.")
                    else:
                        st.info("💡 Please verify the address and try again. Make sure to include street number and name.")
                    st.session_state.usage_count += 1
                else:
                    error_msg = api_response.get('message', 'Unknown error occurred')
                    st.error(f"❌ Address search error: {error_msg}")
                    st.info("💡 Please try again or contact support if the issue persists")
                    st.session_state.usage_count += 1
                    
            except Exception as e:
                st.error(f"❌ Unexpected error during address search: {str(e)}")
                st.info("💡 Please try again or contact support")
                st.session_state.usage_count += 1

# Additional Information Section
st.divider()
st.subheader("ℹ️ Ohio Property Search Information")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **🗺️ Coverage Area:**
    - All 88 Ohio Counties
    - Statewide property records
    - Municipal and township data
    - Rural and urban properties
    
    **📊 Search Capabilities:**
    - Parcel ID lookup
    - Address-based search
    - County filtering
    - Multiple result handling
    """)

with col2:
    st.markdown("""
    **📋 Data Includes:**
    - Property valuations
    - Owner information
    - Tax assessments
    - Land use classifications
    - Zoning information
    - Geographic coordinates
    
    **📥 Export Formats:**
    - PDF reports
    - JSON data files
    - CSV summaries (bulk)
    """)

# Usage warning at bottom
st.divider()
remaining = MAX_SEARCHES - st.session_state.usage_count
if remaining <= 5 and remaining > 0:
    st.warning(f"⚠️ Only {remaining} searches remaining in this session!")
elif remaining == 0:
    st.error("❌ No searches remaining. Refresh the page to reset.")

# Ohio-specific help section
with st.expander("❓ Ohio Property Search Help", expanded=False):
    st.markdown("""
    ### How to Search Ohio Properties
    
    **Parcel ID Format Examples:**
    - Franklin County: `010-123456`
    - Cuyahoga County: `124-05-123`
    - Hamilton County: `456-0-123-00`
    
    **Address Search Tips:**
    - Include street number: `123 Main St`
    - City name helps narrow results: `Columbus`, `Cleveland`
    - Use county filter for better results
    
    **Common Ohio Counties:**
    - **Franklin** (Columbus area)
    - **Cuyahoga** (Cleveland area)  
    - **Hamilton** (Cincinnati area)
    - **Montgomery** (Dayton area)
    - **Summit** (Akron area)
    - **Lucas** (Toledo area)
    
    **Troubleshooting:**
    - No results? Try different county
    - Multiple results? Use specific city name
    - API errors? Check internet connection
    """)

# Custom footer with upgrade option
st.markdown(
    f"""
    <div class="custom-footer">
        Ohio Property Tax Lookup Pro | Searches Used: {st.session_state.usage_count}/{MAX_SEARCHES} | 
        Statewide Coverage: All 88 Counties | Session: {datetime.now().strftime('%Y-%m-%d')} | 
        <a href="https://aipropiq.com/funnel-evergreen-checkout/" target="_blank" style="color: #ff6b6b; text-decoration: none;">
            💎 Upgrade to Premium
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)
