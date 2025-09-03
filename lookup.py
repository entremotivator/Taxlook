import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time
import io
import hashlib
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfgen import canvas

# Configure the Streamlit page
st.set_page_config(
    page_title="Property Tax ID Lookup",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_user_id():
    """Generate a unique user ID based on session"""
    if 'user_id' not in st.session_state:
        # Create a simple user identifier (in production, use proper authentication)
        st.session_state.user_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
    return st.session_state.user_id

def check_usage_limit():
    """Check if user has exceeded usage limit"""
    user_id = get_user_id()
    usage_key = f"usage_{user_id}"
    
    if usage_key not in st.session_state:
        st.session_state[usage_key] = 0
    
    return st.session_state[usage_key] < 30

def increment_usage():
    """Increment user's usage count"""
    user_id = get_user_id()
    usage_key = f"usage_{user_id}"
    
    if usage_key not in st.session_state:
        st.session_state[usage_key] = 0
    
    st.session_state[usage_key] += 1

def get_usage_count():
    """Get current usage count"""
    user_id = get_user_id()
    usage_key = f"usage_{user_id}"
    return st.session_state.get(usage_key, 0)

def main():
    st.title("🏠 Property Tax ID Lookup")
    st.markdown("Look up property information using Tax ID (Parcel ID) via ReportAll API")
    
    usage_count = get_usage_count()
    remaining_uses = 30 - usage_count
    
    if remaining_uses <= 0:
        st.error("❌ You have reached your limit of 30 searches. Please refresh the page to reset your session.")
        st.stop()
    
    # Display usage information
    col_usage1, col_usage2 = st.columns(2)
    with col_usage1:
        st.metric("Searches Used", usage_count, delta=None)
    with col_usage2:
        st.metric("Remaining Searches", remaining_uses, delta=None)
    
    if remaining_uses <= 5:
        st.warning(f"⚠️ You have {remaining_uses} searches remaining in this session.")
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("API Configuration")
        
        # API Key input
        api_key = st.text_input(
            "ReportAll Client Key", 
            type="password", 
            help="Enter your ReportAll API client key"
        )
        
        # API version
        api_version = st.selectbox(
            "API Version",
            options=[9, 8, 7],
            index=0,
            help="Select the API version to use"
        )
        
        # Building footprints option
        return_buildings = st.checkbox(
            "Return Building Footprints",
            value=False,
            help="Include building footprint polygons in results"
        )
        
        # Results per page
        rpp = st.slider(
            "Results per Page",
            min_value=1,
            max_value=100,
            value=10,
            help="Number of results to return per page"
        )
        
        st.header("PDF Export Options")
        include_raw_json = st.checkbox(
            "Include Full Raw JSON",
            value=True,
            help="Include complete API response in PDF"
        )
        
        pdf_format = st.selectbox(
            "PDF Format",
            options=["Detailed Report", "Summary Only", "JSON Only"],
            help="Choose PDF content format"
        )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Search Parameters")
        
        # Region input
        region_type = st.radio(
            "Region Type",
            options=["Text Region", "County ID", "Zip Code"],
            help="Choose how to specify the region"
        )
        
        if region_type == "Text Region":
            region = st.text_input(
                "Region",
                placeholder="e.g., Cuyahoga County, Ohio",
                help="Enter county, state, or zip code as text"
            )
            region_param = {"region": region}
        elif region_type == "County ID":
            county_id = st.text_input(
                "County FIPS55 Code",
                placeholder="e.g., 39035",
                help="Enter the 5-digit FIPS55 county code"
            )
            region_param = {"county_id": county_id}
        else:
            zip_code = st.text_input(
                "Zip Code",
                placeholder="e.g., 44114",
                help="Enter the 5-digit zip code"
            )
            region_param = {"zip_code": zip_code}
        
        # Parcel ID input
        parcel_ids = st.text_area(
            "Tax ID / Parcel ID(s)",
            placeholder="Enter one or more parcel IDs separated by semicolons\ne.g., 44327012;44327010;44327013",
            help="Enter parcel IDs separated by semicolons for multiple lookups"
        )
        
        # Search button
        search_button = st.button("🔍 Search Properties", type="primary")
    
    with col2:
        st.header("Account Information")
        
        if api_key:
            if st.button("Check Account Status"):
                account_info = get_account_info(api_key)
                if account_info:
                    display_account_info(account_info)
                else:
                    st.error("Failed to retrieve account information")
        else:
            st.info("Enter your API key to check account status")
    
    # Search results
    if search_button:
        if not check_usage_limit():
            st.error("❌ You have reached your limit of 30 searches.")
            return
            
        if not api_key:
            st.error("Please enter your ReportAll API client key")
        elif not any(region_param.values()):
            st.error("Please specify a region")
        elif not parcel_ids.strip():
            st.error("Please enter at least one parcel ID")
        else:
            increment_usage()
            
            with st.spinner("Searching for property information..."):
                results = search_parcels(
                    api_key=api_key,
                    region_param=region_param,
                    parcel_ids=parcel_ids.strip(),
                    api_version=api_version,
                    return_buildings=return_buildings,
                    rpp=rpp
                )
                
                if results:
                    display_results(results, include_raw_json, pdf_format)
                else:
                    st.error("Search failed. Please check your parameters and try again.")

def get_account_info(api_key):
    """Retrieve account information from ReportAll API"""
    try:
        url = "https://reportallusa.com/api/account"
        params = {"client": api_key}
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "OK":
            return data
        else:
            st.error(f"API Error: {data.get('message', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid JSON response from API")
        return None

def display_account_info(account_info):
    """Display account information in a formatted way"""
    st.success("✅ Account information retrieved successfully")
    
    # Basic account info
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Client Key", account_info.get("client", "N/A")[:20] + "...")
    with col2:
        expires_at = account_info.get("expires_at")
        if expires_at:
            expiry_date = datetime.fromtimestamp(expires_at).strftime("%Y-%m-%d %H:%M:%S")
            st.metric("Account Expires", expiry_date)
    
    # Quotas
    quotas = account_info.get("quotas", {})
    if quotas:
        st.subheader("API Quotas")
        for endpoint, quota_info in quotas.items():
            with st.expander(f"Endpoint: {endpoint}"):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Period", quota_info.get("period", "N/A").title())
                with col2:
                    st.metric("Total Requests", quota_info.get("requests", "N/A"))
                with col3:
                    st.metric("Used", quota_info.get("usage", "N/A"))
                with col4:
                    st.metric("Remaining", quota_info.get("remaining", "N/A"))

def search_parcels(api_key, region_param, parcel_ids, api_version, return_buildings, rpp):
    """Search for parcels using the ReportAll API"""
    try:
        url = "https://reportallusa.com/api/parcels"
        
        params = {
            "client": api_key,
            "v": api_version,
            "parcel_id": parcel_ids,
            "rpp": rpp
        }
        
        # Add region parameter
        params.update(region_param)
        
        # Add building footprints if requested
        if return_buildings:
            params["return_buildings"] = "true"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "OK":
            return data
        else:
            st.error(f"API Error: {data.get('message', 'Unknown error')}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        st.error("Invalid JSON response from API")
        return None

def display_results(results, include_raw_json=True, pdf_format="Detailed Report"):
    """Display search results in a formatted way with enhanced PDF options"""
    st.success(f"✅ Found {results['count']} property record(s)")
    
    # Results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Results", results['count'])
    with col2:
        st.metric("Current Page", results['page'])
    with col3:
        st.metric("Results per Page", results['rpp'])
    
    st.header("📄 Export Options")
    col_pdf1, col_pdf2 = st.columns(2)
    
    with col_pdf1:
        if st.button("📥 Download Detailed PDF Report", type="primary"):
            try:
                pdf_buffer = create_enhanced_pdf_report(results, include_raw_json, pdf_format)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"property_report_{timestamp}.pdf"
                
                st.download_button(
                    label="💾 Save PDF Report",
                    data=pdf_buffer.getvalue(),
                    file_name=filename,
                    mime="application/pdf"
                )
                st.success("✅ PDF report generated successfully!")
            except Exception as e:
                st.error(f"Failed to generate PDF: {str(e)}")
    
    with col_pdf2:
        if st.button("📋 Download Raw JSON"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"property_data_{timestamp}.json"
            
            st.download_button(
                label="💾 Save JSON Data",
                data=json.dumps(results, indent=2),
                file_name=filename,
                mime="application/json"
            )
    
    # Display each property
    properties = results.get('results', [])
    
    if not properties:
        st.warning("No property records found")
        return
    
    for idx, property_data in enumerate(properties):
        with st.expander(f"Property #{idx + 1} - {property_data.get('address', 'Address not available')}", expanded=True):
            display_property_details(property_data)
    
    # Raw JSON data toggle
    with st.expander("📄 View Raw JSON Response"):
        st.json(results)

def display_property_details(property_data):
    """Display detailed property information"""
    # Basic property info
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Basic Information")
        basic_fields = {
            "Address": "address",
            "Parcel ID": "parcel_id",
            "Owner Name": "owner_name",
            "Property Type": "property_type",
            "Land Use": "land_use_description"
        }
        
        for label, field in basic_fields.items():
            value = property_data.get(field, "N/A")
            if value and value != "N/A":
                st.text(f"{label}: {value}")
    
    with col2:
        st.subheader("Assessment Information")
        assessment_fields = {
            "Assessed Value": "assessed_value",
            "Market Value": "market_value",
            "Land Value": "land_value",
            "Building Value": "building_value",
            "Assessment Year": "assessment_year"
        }
        
        for label, field in assessment_fields.items():
            value = property_data.get(field, "N/A")
            if value and value != "N/A":
                if "value" in label.lower() and str(value).replace(".", "").isdigit():
                    st.text(f"{label}: ${float(value):,.2f}")
                else:
                    st.text(f"{label}: {value}")
    
    # Property characteristics
    st.subheader("Property Characteristics")
    char_col1, char_col2 = st.columns(2)
    
    with char_col1:
        char_fields = {
            "Year Built": "year_built",
            "Square Feet": "building_square_feet",
            "Lot Size": "lot_size_square_feet",
            "Bedrooms": "bedrooms",
            "Bathrooms": "bathrooms"
        }
        
        for label, field in char_fields.items():
            value = property_data.get(field, "N/A")
            if value and value != "N/A":
                if "square_feet" in field or "lot_size" in field:
                    if str(value).replace(".", "").isdigit():
                        st.text(f"{label}: {float(value):,.0f} sq ft")
                    else:
                        st.text(f"{label}: {value}")
                else:
                    st.text(f"{label}: {value}")
    
    with char_col2:
        location_fields = {
            "City": "city",
            "County": "county",
            "State": "state",
            "Zip Code": "zip_code",
            "School District": "school_district"
        }
        
        for label, field in location_fields.items():
            value = property_data.get(field, "N/A")
            if value and value != "N/A":
                st.text(f"{label}: {value}")
    
    # Building footprints (if available)
    buildings = property_data.get("buildings_poly", [])
    if buildings:
        st.subheader("Building Footprints")
        st.info(f"Found {len(buildings)} building footprint(s)")
        for i, building in enumerate(buildings):
            with st.expander(f"Building {i+1} Geometry"):
                st.text(building.get("geom_as_wkt", "No geometry data"))
    
    # Geometry information
    geometry = property_data.get("geom_as_wkt")
    if geometry:
        with st.expander("🗺️ Property Boundary (WKT Format)"):
            st.text_area("Well-Known Text (WKT) Geometry", geometry, height=100)
            st.info("This geometry is in WGS84 (EPSG:4326) projection")

def create_enhanced_pdf_report(results, include_raw_json=True, pdf_format="Detailed Report"):
    """Generate an enhanced PDF report with full JSON data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch
    )
    
    # Define enhanced styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    json_style = ParagraphStyle(
        'JSONStyle',
        parent=styles['Code'],
        fontSize=8,
        fontName='Courier',
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6
    )
    
    # Build the PDF content
    story = []
    
    story.append(Paragraph("🏠 Property Tax Lookup Report", title_style))
    story.append(Spacer(1, 20))
    
    # Enhanced summary information
    summary_data = [
        ['Report Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')],
        ['API Status:', results.get('status', 'N/A')],
        ['Total Properties Found:', str(results.get('count', 0))],
        ['Current Page:', str(results.get('page', 1))],
        ['Results per Page:', str(results.get('rpp', 10))],
        ['Report Format:', pdf_format],
        ['Includes Raw JSON:', 'Yes' if include_raw_json else 'No']
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    properties = results.get('results', [])
    
    if pdf_format != "JSON Only":
        story.append(Paragraph("Property Details", heading_style))
        story.append(Spacer(1, 15))
        
        for idx, prop in enumerate(properties):
            story.append(Paragraph(f"Property #{idx + 1}", styles['Heading3']))
            story.append(Spacer(1, 10))
            
            if pdf_format == "Detailed Report":
                # Comprehensive property information
                prop_data = []
                
                # Basic Information
                basic_info = [
                    ['Parcel ID:', prop.get('parcel_id', 'N/A')],
                    ['Address:', prop.get('address', 'N/A')],
                    ['Owner Name:', prop.get('owner_name', 'N/A')],
                    ['Property Type:', prop.get('property_type', 'N/A')],
                    ['Land Use:', prop.get('land_use_description', 'N/A')]
                ]
                prop_data.extend(basic_info)
                
                # Location Information
                location_info = [
                    ['City:', prop.get('city', 'N/A')],
                    ['County:', prop.get('county', 'N/A')],
                    ['State:', prop.get('state', 'N/A')],
                    ['Zip Code:', prop.get('zip_code', 'N/A')],
                    ['School District:', prop.get('school_district', 'N/A')]
                ]
                prop_data.extend(location_info)
                
                # Financial Information
                financial_info = [
                    ['Assessed Value:', f"${float(prop.get('assessed_value', 0)):,.2f}" if prop.get('assessed_value') else 'N/A'],
                    ['Market Value:', f"${float(prop.get('market_value', 0)):,.2f}" if prop.get('market_value') else 'N/A'],
                    ['Land Value:', f"${float(prop.get('land_value', 0)):,.2f}" if prop.get('land_value') else 'N/A'],
                    ['Building Value:', f"${float(prop.get('building_value', 0)):,.2f}" if prop.get('building_value') else 'N/A'],
                    ['Assessment Year:', str(prop.get('assessment_year', 'N/A'))]
                ]
                prop_data.extend(financial_info)
                
                # Property Characteristics
                char_info = [
                    ['Year Built:', str(prop.get('year_built', 'N/A'))],
                    ['Building Sq Ft:', f"{float(prop.get('building_square_feet', 0)):,.0f}" if prop.get('building_square_feet') else 'N/A'],
                    ['Lot Size Sq Ft:', f"{float(prop.get('lot_size_square_feet', 0)):,.0f}" if prop.get('lot_size_square_feet') else 'N/A'],
                    ['Bedrooms:', str(prop.get('bedrooms', 'N/A'))],
                    ['Bathrooms:', str(prop.get('bathrooms', 'N/A'))]
                ]
                prop_data.extend(char_info)
                
            else:  # Summary Only
                prop_data = [
                    ['Parcel ID:', prop.get('parcel_id', 'N/A')],
                    ['Address:', prop.get('address', 'N/A')],
                    ['Owner:', prop.get('owner_name', 'N/A')],
                    ['Market Value:', f"${float(prop.get('market_value', 0)):,.2f}" if prop.get('market_value') else 'N/A'],
                    ['Year Built:', str(prop.get('year_built', 'N/A'))]
                ]
            
            prop_table = Table(prop_data, colWidths=[2*inch, 4*inch])
            prop_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('BACKGROUND', (1, 0), (1, -1), colors.white),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(prop_table)
            story.append(Spacer(1, 20))
    
    if include_raw_json:
        story.append(PageBreak())
        story.append(Paragraph("Complete API Response (Raw JSON)", heading_style))
        story.append(Spacer(1, 15))
        
        # Format JSON with proper indentation
        json_text = json.dumps(results, indent=2, ensure_ascii=False)
        
        # Split JSON into chunks to fit on pages
        lines = json_text.split('\n')
        chunk_size = 50  # Lines per chunk
        
        for i in range(0, len(lines), chunk_size):
            chunk = '\n'.join(lines[i:i + chunk_size])
            story.append(Paragraph(f"<pre>{chunk}</pre>", json_style))
            
            # Add page break if not the last chunk
            if i + chunk_size < len(lines):
                story.append(PageBreak())
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    main()
