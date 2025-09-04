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
    page_title="Property Tax Lookup Pro",
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
def fetch_property_data(parcel_id):
    """
    Fetch property data from the actual API
    Replace this function with your actual API call
    """
    try:
        # Example API call structure - adjust based on your API
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Construct API URL - adjust based on your API endpoint
        url = f"{API_BASE_URL}/property/{parcel_id}"
        
        # Make the API request
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"status": "NOT_FOUND", "message": "Property not found"}
        else:
            return {"status": "ERROR", "message": f"API returned status code: {response.status_code}"}
            
    except requests.exceptions.Timeout:
        return {"status": "ERROR", "message": "Request timed out"}
    except requests.exceptions.ConnectionError:
        return {"status": "ERROR", "message": "Connection error"}
    except Exception as e:
        return {"status": "ERROR", "message": f"Unexpected error: {str(e)}"}

def generate_mock_data(parcel_id):
    """
    Generate realistic mock data for demonstration
    Remove this function when implementing real API
    """
    import random
    
    # Generate varied mock data based on parcel_id
    random.seed(hash(parcel_id) % 10000)  # Consistent data for same parcel_id
    
    counties = ["Cuyahoga", "Franklin", "Hamilton", "Summit", "Montgomery"]
    cities = ["Cleveland", "Columbus", "Cincinnati", "Akron", "Dayton"]
    streets = ["Main St", "Oak Ave", "Elm Dr", "Park Blvd", "First Ave", "Second St"]
    owners = [
        "JOHNSON, MARY A",
        "SMITH FAMILY TRUST", 
        "BROWN, ROBERT & SUSAN",
        "DAVIS PROPERTIES LLC",
        "WILSON, JAMES M"
    ]
    
    county = random.choice(counties)
    city = random.choice(cities)
    street_num = random.randint(100, 9999)
    street = random.choice(streets)
    
    return {
        "status": "OK",
        "results": [{
            "parcel_id": parcel_id,
            "county_name": county,
            "muni_name": city,
            "address": f"{street_num} {street}",
            "addr_city": city.upper(),
            "state_abbr": "OH",
            "addr_zip": f"{random.randint(43000, 45999)}",
            "owner": random.choice(owners),
            "sale_price": f"{random.randint(50000, 500000)}.00",
            "mkt_val_tot": f"{random.randint(75000, 600000)}.00",
            "mkt_val_land": f"{random.randint(15000, 100000)}.00",
            "mkt_val_bldg": f"{random.randint(50000, 500000)}.00",
            "acreage": f"{random.uniform(0.1, 2.0):.4f}",
            "land_use_class": random.choice(["Residential", "Commercial", "Industrial", "Agricultural"]),
            "school_district": f"{city} City Schools",
            "owner_occupied": random.choice([True, False]),
            "last_updated": f"2024-Q{random.randint(1, 4)}",
            "land_cover": {"Developed Medium Intensity": round(random.uniform(0.05, 0.95), 2)},
            "buildings": random.randint(1, 3),
            "latitude": round(random.uniform(39.0, 42.0), 4),
            "longitude": round(random.uniform(-84.5, -80.5), 4),
            "trans_date": f"202{random.randint(1, 4)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "zoning": random.choice(["R1F", "R2", "C1", "M1", "A1"]),
            "ngh_code": f"{random.randint(1000, 9999)}",
            "census_tract": f"{random.randint(1000, 9999)}",
            "census_block": f"{random.randint(1000, 9999)}",
            "usps_residential": random.choice(["Residential", "Commercial", "Mixed Use"]),
            "elevation": f"{random.randint(500, 1200)}",
            "mail_address1": f"{street_num} {street}",
            "mail_address3": f"{city}, OH {random.randint(43000, 45999)}"
        }]
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
# Sidebar: Usage stats
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

    if st.session_state.search_history:
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
    if API_KEY == "your_api_key_here":
        st.warning("⚠️ Using Demo Mode")
        st.caption("Set API_KEY in secrets for live data")
    else:
        st.success("✅ API Configured")

# --------------------------
# Helper: Create property cards
# --------------------------
def create_property_cards(data):
    # Create colorful Property Overview section
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 25px; border-radius: 20px; margin: 15px 0; color: white; 
                box-shadow: 0 8px 25px rgba(102,126,234,0.3);'>
        <h2 style='color: white; margin-bottom: 20px; text-align: center; font-size: 28px;'>🏠 Property Overview</h2>
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
    story = [Paragraph("Property Tax Lookup Report", title_style), Spacer(1,20)]

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
st.title("🏠 Property Tax Lookup Pro")
st.markdown("**Advanced property research with PDF/JSON export** | *Limited to 10 searches per session*")

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.stop()

st.subheader("🔍 Property Search")
col1, col2 = st.columns([3,1])
with col1:
    parcel_id = st.text_input("Enter Parcel ID", placeholder="e.g., 00824064", help="Enter a valid parcel ID to search for property information")
with col2:
    search_button = st.button("🔍 Search Property", type="primary", disabled=(st.session_state.usage_count >= MAX_SEARCHES))

# Search functionality
if search_button and parcel_id:
    if st.session_state.usage_count >= MAX_SEARCHES:
        st.error("Usage limit reached!")
    elif not parcel_id.strip():
        st.error("Please enter a valid Parcel ID")
    else:
        with st.spinner("Fetching property data..."):
            try:
                # Check if we have cached results for this parcel (optional optimization)
                cache_key = parcel_id.strip().upper()
                
                # Always fetch fresh data - remove caching for true fresh data every time
                if API_KEY == "your_api_key_here":
                    # Demo mode - generate mock data
                    st.info("🔄 Demo Mode: Generating sample data...")
                    api_response = generate_mock_data(parcel_id)
                else:
                    # Production mode - call real API
                    st.info("🔄 Fetching live data from API...")
                    api_response = fetch_property_data(parcel_id)

                if api_response.get('status') == "OK" and api_response.get('results'):
                    property_data = api_response['results'][0]
                    
                    # Update usage count and history
                    st.session_state.usage_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    st.session_state.search_history.append(f"{parcel_id} - {timestamp}")
                    
                    # Cache the result (optional)
                    st.session_state.cached_results[cache_key] = property_data
                    
                    # Success message
                    st.success(f"✅ Property data found! (Search {st.session_state.usage_count}/{MAX_SEARCHES})")
                    
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
                            file_name=f"property_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                            mime="application/pdf"
                        )
                    with col2:
                        json_str = json.dumps(property_data, indent=2)
                        st.download_button(
                            "📋 Download JSON Data", 
                            json_str,
                            file_name=f"property_data_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                            mime="application/json"
                        )
                        
                elif api_response.get('status') == "NOT_FOUND":
                    st.error("❌ No property found for the provided Parcel ID")
                    st.info("💡 Please verify the Parcel ID and try again")
                    # Still increment usage count for failed searches
                    st.session_state.usage_count += 1
                else:
                    error_msg = api_response.get('message', 'Unknown error occurred')
                    st.error(f"❌ Error: {error_msg}")
                    st.info("💡 Please try again or contact support if the issue persists")
                    # Still increment usage count for failed searches
                    st.session_state.usage_count += 1
                    
            except Exception as e:
                st.error(f"❌ Unexpected error occurred: {str(e)}")
                st.info("💡 Please try again or contact support")
                # Increment usage count for errors too
                st.session_state.usage_count += 1

# Clear cache button (for development/testing)
if st.session_state.cached_results and st.button("🗑️ Clear Cache", help="Clear cached results (for testing)"):
    st.session_state.cached_results = {}
    st.success("Cache cleared!")

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
        Property Tax Lookup Pro | Searches Used: {st.session_state.usage_count}/{MAX_SEARCHES} | 
        Session: {datetime.now().strftime('%Y-%m-%d')} | 
        <a href="https://aipropiq.com/funnel-evergreen-checkout/" target="_blank" style="color: #ff6b6b; text-decoration: none;">
            💎 Upgrade to Premium
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)
