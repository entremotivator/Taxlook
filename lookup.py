import streamlit as st
import json
import pandas as pd
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
# Session state
# --------------------------
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

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
        st.rerun()

# --------------------------
# Helper: Create property cards
# --------------------------
def create_property_cards(data):
    st.subheader("🏠 Property Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Parcel ID", data.get('parcel_id','N/A'))
        st.metric("County", data.get('county_name','N/A'))
        st.metric("Municipality", data.get('muni_name','N/A'))
    with col2:
        st.metric("Market Value (Total)", f"${float(data.get('mkt_val_tot',0)):,.2f}")
        st.metric("Market Value (Land)", f"${float(data.get('mkt_val_land',0)):,.2f}")
        st.metric("Market Value (Building)", f"${float(data.get('mkt_val_bldg',0)):,.2f}")
    with col3:
        st.metric("Acreage", data.get('acreage','N/A'))
        st.metric("Land Use", data.get('land_use_class','N/A'))
        st.metric("Buildings", data.get('buildings','N/A'))

    st.divider()
    st.subheader("📍 Address Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Property Address:**")
        st.write(data.get('address','N/A'))
        st.write(f"{data.get('addr_city','')}, {data.get('state_abbr','')} {data.get('addr_zip','')}")
        if data.get('latitude') and data.get('longitude'):
            st.write(f"**Coordinates:** {data.get('latitude')}, {data.get('longitude')}")
    with col2:
        st.write("**Mailing Address:**")
        st.write(data.get('mail_address1','N/A'))
        if data.get('mail_address3'):
            st.write(data.get('mail_address3'))

    st.divider()
    st.subheader("👤 Owner Information")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Owner:** {data.get('owner','N/A')}")
        st.write(f"**Owner Occupied:** {'Yes' if data.get('owner_occupied') else 'No'}")
    with col2:
        if data.get('trans_date'):
            st.write(f"**Last Transaction:** {data.get('trans_date')}")
        if data.get('sale_price'):
            st.write(f"**Sale Price:** ${float(data.get('sale_price',0)):,.2f}")

    st.divider()
    st.subheader("📋 Additional Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**School District:** {data.get('school_district','N/A')}")
        st.write(f"**Zoning:** {data.get('zoning','N/A')}")
        st.write(f"**Neighborhood Code:** {data.get('ngh_code','N/A')}")
    with col2:
        st.write(f"**Census Tract:** {data.get('census_tract','N/A')}")
        st.write(f"**Census Block:** {data.get('census_block','N/A')}")
        st.write(f"**USPS Type:** {data.get('usps_residential','N/A')}")
    with col3:
        st.write(f"**Elevation:** {data.get('elevation','N/A')} ft")
        st.write(f"**Last Updated:** {data.get('last_updated','N/A')}")

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
                # Demo sample data (replace with real API call if desired)
                sample_response = {
                    "status": "OK",
                    "results": [{
                        "parcel_id": parcel_id,
                        "county_name": "Cuyahoga",
                        "muni_name": "Cleveland",
                        "address": "2469 DOBSON Ct",
                        "addr_city": "CLEVELAND",
                        "state_abbr": "OH",
                        "addr_zip": "44109",
                        "owner": "STATE OF OHIO FORF CV # 983792",
                        "sale_price": "0.00",
                        "mkt_val_tot": "2500.00",
                        "mkt_val_land": "2500.00",
                        "mkt_val_bldg": "0.00",
                        "acreage": "0.0870",
                        "land_use_class": "Residential",
                        "school_district": "Cleveland Municipal School District",
                        "owner_occupied": True,
                        "last_updated": "2025-Q3",
                        "land_cover": {"Developed Medium Intensity": 0.09},
                        "buildings": 1,
                        "latitude": 41.4993,
                        "longitude": -81.6944,
                        "trans_date": "2023-01-15",
                        "zoning": "R1F",
                        "ngh_code": "0001",
                        "census_tract": "1001",
                        "census_block": "1001",
                        "usps_residential": "Residential",
                        "elevation": "650"
                    }]
                }

                if sample_response['status']=="OK" and sample_response['results']:
                    property_data = sample_response['results'][0]
                    
                    # Update usage count and history
                    st.session_state.usage_count += 1
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    st.session_state.search_history.append(f"{parcel_id} - {timestamp}")
                    
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
                else:
                    st.error("❌ No property found for the provided Parcel ID")
                    st.info("💡 Please verify the Parcel ID and try again")
                    
            except Exception as e:
                st.error(f"❌ Error occurred while fetching data: {str(e)}")

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
