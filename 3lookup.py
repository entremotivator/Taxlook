import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import base64

# Page configuration
st.set_page_config(
    page_title="Property Tax Lookup Pro",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'gsheet_client' not in st.session_state:
    st.session_state.gsheet_client = None

# Sidebar for Google Sheets Authentication
with st.sidebar:
    st.header("🔐 Google Sheets Authentication")
    
    if not st.session_state.authenticated:
        st.info("Upload your Google Service Account JSON to enable Google Sheets integration")
        
        uploaded_file = st.file_uploader(
            "Upload Service Account JSON",
            type=['json'],
            help="Upload your Google Cloud Service Account JSON file"
        )
        
        if uploaded_file is not None:
            try:
                # Parse the JSON credentials
                credentials_info = json.load(uploaded_file)
                
                # Define the scope
                scope = [
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ]
                
                # Create credentials
                credentials = Credentials.from_service_account_info(
                    credentials_info, scopes=scope
                )
                
                # Initialize gspread client
                st.session_state.gsheet_client = gspread.authorize(credentials)
                st.session_state.authenticated = True
                
                st.success("✅ Successfully authenticated with Google Sheets!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Authentication failed: {str(e)}")
    else:
        st.success("✅ Google Sheets Connected")
        
        # Spreadsheet configuration
        st.subheader("📊 Spreadsheet Settings")
        spreadsheet_url = st.text_input(
            "Google Sheets URL",
            placeholder="https://docs.google.com/spreadsheets/d/your-sheet-id/edit",
            help="Paste your Google Sheets URL here"
        )
        
        worksheet_name = st.text_input(
            "Worksheet Name",
            value="PropertyData",
            help="Name of the worksheet to write data to"
        )
        
        if st.button("🔄 Reset Authentication"):
            st.session_state.authenticated = False
            st.session_state.gsheet_client = None
            st.rerun()
    
    # Usage tracking
    st.divider()
    st.subheader("📈 Usage Statistics")
    usage_remaining = 30 - st.session_state.usage_count
    
    if usage_remaining > 0:
        st.metric("Searches Remaining", usage_remaining)
        progress = st.session_state.usage_count / 30
        st.progress(progress)
    else:
        st.error("❌ Usage limit reached (30 searches)")
    
    if st.session_state.search_history:
        st.subheader("🔍 Recent Searches")
        for i, search in enumerate(st.session_state.search_history[-5:]):
            st.text(f"{i+1}. {search}")

def send_to_gsheet(data, spreadsheet_url, worksheet_name):
    """Send property data to Google Sheets"""
    try:
        if not st.session_state.gsheet_client:
            return False, "Google Sheets not authenticated"
        
        # Extract spreadsheet ID from URL
        if '/d/' in spreadsheet_url:
            sheet_id = spreadsheet_url.split('/d/')[1].split('/')[0]
        else:
            return False, "Invalid Google Sheets URL"
        
        # Open the spreadsheet
        spreadsheet = st.session_state.gsheet_client.open_by_key(sheet_id)
        
        # Try to open existing worksheet or create new one
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows="1000", cols="50")
        
        # Flatten the JSON data
        flattened_data = {}
        
        def flatten_dict(d, parent_key='', sep='_'):
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    items.extend(flatten_dict(v, new_key, sep=sep).items())
                elif isinstance(v, list):
                    items.append((new_key, str(v)))
                else:
                    items.append((new_key, v))
            return dict(items)
        
        flattened_data = flatten_dict(data)
        
        # Add timestamp
        flattened_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Get existing headers or create new ones
        try:
            existing_headers = worksheet.row_values(1)
            if not existing_headers:
                # First time - add headers
                headers = list(flattened_data.keys())
                worksheet.append_row(headers)
                worksheet.append_row([flattened_data.get(h, '') for h in headers])
            else:
                # Append data matching existing headers
                row_data = [flattened_data.get(h, '') for h in existing_headers]
                worksheet.append_row(row_data)
        except Exception:
            # If there's an issue with existing data, start fresh
            headers = list(flattened_data.keys())
            worksheet.clear()
            worksheet.append_row(headers)
            worksheet.append_row([flattened_data.get(h, '') for h in headers])
        
        return True, "Data successfully sent to Google Sheets!"
        
    except Exception as e:
        return False, f"Error sending to Google Sheets: {str(e)}"

def create_property_cards(property_data):
    """Create detailed property information cards"""
    
    # Main Property Information Card
    with st.container():
        st.subheader("🏠 Property Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Parcel ID", property_data.get('parcel_id', 'N/A'))
            st.metric("County", property_data.get('county_name', 'N/A'))
            st.metric("Municipality", property_data.get('muni_name', 'N/A'))
        
        with col2:
            st.metric("Market Value (Total)", f"${float(property_data.get('mkt_val_tot', 0)):,.2f}")
            st.metric("Market Value (Land)", f"${float(property_data.get('mkt_val_land', 0)):,.2f}")
            st.metric("Market Value (Building)", f"${float(property_data.get('mkt_val_bldg', 0)):,.2f}")
        
        with col3:
            st.metric("Acreage", property_data.get('acreage', 'N/A'))
            st.metric("Land Use", property_data.get('land_use_class', 'N/A'))
            st.metric("Buildings", property_data.get('buildings', 'N/A'))
    
    st.divider()
    
    # Address Information Card
    with st.container():
        st.subheader("📍 Address Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Property Address:**")
            st.write(property_data.get('address', 'N/A'))
            st.write(f"{property_data.get('addr_city', '')}, {property_data.get('state_abbr', '')} {property_data.get('addr_zip', '')}")
            
            if property_data.get('latitude') and property_data.get('longitude'):
                st.write(f"**Coordinates:** {property_data.get('latitude')}, {property_data.get('longitude')}")
        
        with col2:
            st.write("**Mailing Address:**")
            st.write(property_data.get('mail_address1', 'N/A'))
            if property_data.get('mail_address3'):
                st.write(property_data.get('mail_address3'))
    
    st.divider()
    
    # Owner Information Card
    with st.container():
        st.subheader("👤 Owner Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Owner:** {property_data.get('owner', 'N/A')}")
            st.write(f"**Owner Occupied:** {'Yes' if property_data.get('owner_occupied') else 'No'}")
        
        with col2:
            if property_data.get('trans_date'):
                st.write(f"**Last Transaction:** {property_data.get('trans_date')}")
            if property_data.get('sale_price'):
                st.write(f"**Sale Price:** ${float(property_data.get('sale_price', 0)):,.2f}")
    
    st.divider()
    
    # Additional Details Card
    with st.container():
        st.subheader("📋 Additional Details")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**School District:** {property_data.get('school_district', 'N/A')}")
            st.write(f"**Zoning:** {property_data.get('zoning', 'N/A')}")
            st.write(f"**Neighborhood Code:** {property_data.get('ngh_code', 'N/A')}")
        
        with col2:
            st.write(f"**Census Tract:** {property_data.get('census_tract', 'N/A')}")
            st.write(f"**Census Block:** {property_data.get('census_block', 'N/A')}")
            st.write(f"**USPS Type:** {property_data.get('usps_residential', 'N/A')}")
        
        with col3:
            st.write(f"**Elevation:** {property_data.get('elevation', 'N/A')} ft")
            st.write(f"**Last Updated:** {property_data.get('last_updated', 'N/A')}")
    
    # Land Cover Information
    if property_data.get('land_cover'):
        st.divider()
        st.subheader("🌍 Land Cover Analysis")
        
        land_cover_df = pd.DataFrame(
            list(property_data['land_cover'].items()),
            columns=['Cover Type', 'Percentage']
        )
        st.dataframe(land_cover_df, use_container_width=True)
    
    # Raw JSON Data Card
    st.divider()
    st.subheader("📄 Complete Raw JSON Data")
    
    with st.expander("View Full JSON Response", expanded=False):
        st.json(property_data)

def create_enhanced_pdf(property_data, include_json=True):
    """Create an enhanced PDF report with complete property data"""
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkblue,
        borderWidth=1,
        borderColor=colors.darkblue,
        borderPadding=5
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph("Property Tax Lookup Report", title_style))
    story.append(Spacer(1, 20))
    
    # Property Overview
    story.append(Paragraph("Property Overview", heading_style))
    
    overview_data = [
        ['Parcel ID', property_data.get('parcel_id', 'N/A')],
        ['Address', property_data.get('address', 'N/A')],
        ['City, State ZIP', f"{property_data.get('addr_city', '')}, {property_data.get('state_abbr', '')} {property_data.get('addr_zip', '')}"],
        ['County', property_data.get('county_name', 'N/A')],
        ['Municipality', property_data.get('muni_name', 'N/A')],
        ['Owner', property_data.get('owner', 'N/A')],
    ]
    
    overview_table = Table(overview_data, colWidths=[2*inch, 4*inch])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(overview_table)
    story.append(Spacer(1, 20))
    
    # Market Values
    story.append(Paragraph("Market Valuation", heading_style))
    
    value_data = [
        ['Total Market Value', f"${float(property_data.get('mkt_val_tot', 0)):,.2f}"],
        ['Land Value', f"${float(property_data.get('mkt_val_land', 0)):,.2f}"],
        ['Building Value', f"${float(property_data.get('mkt_val_bldg', 0)):,.2f}"],
        ['Acreage', property_data.get('acreage', 'N/A')],
        ['Land Use Class', property_data.get('land_use_class', 'N/A')],
    ]
    
    value_table = Table(value_data, colWidths=[2*inch, 4*inch])
    value_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(value_table)
    story.append(Spacer(1, 20))
    
    # Additional Information
    story.append(Paragraph("Additional Information", heading_style))
    
    additional_data = [
        ['School District', property_data.get('school_district', 'N/A')],
        ['Zoning', property_data.get('zoning', 'N/A')],
        ['Census Tract', str(property_data.get('census_tract', 'N/A'))],
        ['Owner Occupied', 'Yes' if property_data.get('owner_occupied') else 'No'],
        ['Last Updated', property_data.get('last_updated', 'N/A')],
    ]
    
    additional_table = Table(additional_data, colWidths=[2*inch, 4*inch])
    additional_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightyellow),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(additional_table)
    
    # Include full JSON if requested
    if include_json:
        story.append(Spacer(1, 30))
        story.append(Paragraph("Complete Raw JSON Data", heading_style))
        
        json_text = json.dumps(property_data, indent=2)
        # Split long JSON into chunks for PDF
        json_lines = json_text.split('\n')
        
        for line in json_lines[:50]:  # Limit to first 50 lines to prevent PDF issues
            story.append(Paragraph(f"<font name='Courier' size='8'>{line}</font>", styles['Normal']))
        
        if len(json_lines) > 50:
            story.append(Paragraph("... (JSON truncated for PDF display)", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Main App
st.title("🏠 Property Tax Lookup Pro")
st.markdown("**Advanced property research with Google Sheets integration and comprehensive reporting**")

# Check usage limit
if st.session_state.usage_count >= 30:
    st.error("❌ You have reached the maximum usage limit of 30 searches. Please refresh the page to reset.")
    st.stop()

# Main search interface
st.subheader("🔍 Property Search")

col1, col2 = st.columns([3, 1])

with col1:
    parcel_id = st.text_input(
        "Enter Parcel ID",
        placeholder="e.g., 00824064",
        help="Enter the parcel ID to search for property information"
    )

with col2:
    st.write("")  # Spacing
    search_button = st.button("🔍 Search Property", type="primary", use_container_width=True)

if search_button and parcel_id:
    if st.session_state.usage_count >= 30:
        st.error("Usage limit reached!")
    else:
        with st.spinner("Searching property information..."):
            try:
                # Make API call (using sample data for demo)
                # In production, replace with actual API call
                api_url = f"https://api.reportallusa.com/search"
                params = {
                    'client': 'kcuk4HJnjt',
                    'parcel_id': parcel_id,
                    'region': 'Cleveland, Ohio',
                    'rpp': 10,
                    'v': 9
                }
                
                # For demo purposes, using the provided sample data
                sample_response = {
                    "status": "OK",
                    "count": 1,
                    "page": 1,
                    "rpp": 10,
                    "results": [{
                        "parcel_id": parcel_id,
                        "county_id": 39035,
                        "cty_row_id": 393150,
                        "county_name": "Cuyahoga",
                        "muni_name": "Cleveland",
                        "census_place": "Cleveland city",
                        "state_abbr": "OH",
                        "county_link": "https://reportallusa.com/cama_redir?robust_id=AACYe7CzAyix5ZWX",
                        "address": "2469 DOBSON Ct",
                        "addr_number": "2469",
                        "addr_street_name": "DOBSON",
                        "addr_street_type": "Ct",
                        "addr_city": "CLEVELAND",
                        "addr_zip": "44109",
                        "addr_zipplusfour": "2801",
                        "census_zip": "44109",
                        "owner": "STATE OF OHIO FORF CV # 983792",
                        "mail_address1": "2469 DOBSON CT",
                        "mail_address3": "CLEVELAND OH 44109",
                        "trans_date": "2024-11-01",
                        "sale_price": "0.00",
                        "mkt_val_land": "2500.00",
                        "mkt_val_bldg": "0.00",
                        "mkt_val_tot": "2500.00",
                        "ngh_code": "02143",
                        "land_use_code": "5000",
                        "land_use_class": "Residential",
                        "muni_id": 1085963,
                        "school_district": "Cleveland Municipal School District",
                        "acreage": "0.0870",
                        "acreage_calc": "0.09",
                        "latitude": "41.4523866931776",
                        "longitude": "-81.7002652422765",
                        "acreage_adjacent_with_sameowner": "0.0870220702317969",
                        "census_block": 1006,
                        "census_tract": 105602,
                        "owner_occupied": True,
                        "robust_id": "AACYe7CzAyix5ZWX",
                        "usps_residential": "Residential",
                        "elevation": "687.69685039095",
                        "buildings": 1,
                        "last_updated": "2025-Q3",
                        "mail_addressnumber": "2469",
                        "mail_streetname": "DOBSON",
                        "mail_streetnameposttype": "CT",
                        "mail_placename": "CLEVELAND",
                        "mail_statename": "OH",
                        "mail_zipcode": "44109",
                        "zoning": "LR",
                        "land_cover": {"Developed Medium Intensity": 0.09},
                        "crop_cover": {"Developed/Low Intensity": 0.09},
                        "geom_as_wkt": "MULTIPOLYGON(((-81.7002462595665 41.4525395375969,-81.7001807903486 41.4525357550468,-81.7002092822145 41.4522566368486,-81.7003444409355 41.4522644463868,-81.7003159508663 41.452543561185,-81.7002462595665 41.4525395375969)))"
                    }]
                }
                
                if sample_response['status'] == 'OK' and sample_response['results']:
                    property_data = sample_response['results'][0]
                    
                    # Update usage count and history
                    st.session_state.usage_count += 1
                    st.session_state.search_history.append(f"{parcel_id} - {datetime.now().strftime('%H:%M:%S')}")
                    
                    st.success(f"✅ Property found! (Search {st.session_state.usage_count}/30)")
                    
                    # Display property cards
                    create_property_cards(property_data)
                    
                    # Action buttons
                    st.divider()
                    st.subheader("📤 Export & Share Options")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Google Sheets export
                        if st.session_state.authenticated and 'spreadsheet_url' in locals() and 'worksheet_name' in locals():
                            if st.button("📊 Send to Google Sheets", use_container_width=True):
                                success, message = send_to_gsheet(property_data, spreadsheet_url, worksheet_name)
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                        else:
                            st.info("🔐 Authenticate Google Sheets to enable export")
                    
                    with col2:
                        # PDF Download
                        pdf_buffer = create_enhanced_pdf(property_data, include_json=True)
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_buffer.getvalue(),
                            file_name=f"property_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    with col3:
                        # JSON Download
                        json_str = json.dumps(property_data, indent=2)
                        st.download_button(
                            label="📋 Download JSON Data",
                            data=json_str,
                            file_name=f"property_data_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                
                else:
                    st.error("❌ No property found with that Parcel ID")
                    
            except Exception as e:
                st.error(f"❌ Error searching property: {str(e)}")

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>Property Tax Lookup Pro | Enhanced with Google Sheets Integration</p>
        <p>Searches remaining: {}/30</p>
    </div>
    """.format(30 - st.session_state.usage_count),
    unsafe_allow_html=True
)
