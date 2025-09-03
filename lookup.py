import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import time

# Configure the Streamlit page
st.set_page_config(
    page_title="Property Tax ID Lookup",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏠 Property Tax ID Lookup")
    st.markdown("Look up property information using Tax ID (Parcel ID) via ReportAll API")
    
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
        if not api_key:
            st.error("Please enter your ReportAll API client key")
        elif not any(region_param.values()):
            st.error("Please specify a region")
        elif not parcel_ids.strip():
            st.error("Please enter at least one parcel ID")
        else:
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
                    display_results(results)
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

def display_results(results):
    """Display search results in a formatted way"""
    st.success(f"✅ Found {results['count']} property record(s)")
    
    # Results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Results", results['count'])
    with col2:
        st.metric("Current Page", results['page'])
    with col3:
        st.metric("Results per Page", results['rpp'])
    
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

def create_pdf_report(results):
    """Generate a PDF report of the search results"""
    if not REPORTLAB_AVAILABLE:
        raise ImportError("ReportLab is not installed. Install it with: pip install reportlab")
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )
    
    # Build the PDF content
    story = []
    
    # Title
    story.append(Paragraph("Property Lookup Report", title_style))
    story.append(Spacer(1, 12))
    
    # Summary information
    summary_data = [
        ['Status:', results.get('status', 'N/A')],
        ['Total Properties:', str(results.get('count', 0))],
        ['Page:', str(results.get('page', 1))],
        ['Results per Page:', str(results.get('rpp', 10))],
        ['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Property details
    properties = results.get('results', [])
    for idx, prop in enumerate(properties):
        story.append(Paragraph(f"Property #{idx + 1}", styles['Heading2']))
        
        # Basic property information
        prop_data = [
            ['Parcel ID:', prop.get('parcel_id', 'N/A')],
            ['Address:', prop.get('address', 'N/A')],
            ['Owner:', prop.get('owner', 'N/A')],
            ['City:', prop.get('addr_city', 'N/A')],
            ['County:', prop.get('county_name', 'N/A')],
            ['State:', prop.get('state_abbr', 'N/A')],
            ['Zip Code:', prop.get('addr_zip', 'N/A')],
            ['Market Value:', f"${float(prop.get('mkt_val_tot', 0)):,.2f}" if prop.get('mkt_val_tot') else 'N/A'],
            ['Land Value:', f"${float(prop.get('mkt_val_land', 0)):,.2f}" if prop.get('mkt_val_land') else 'N/A'],
            ['Building Value:', f"${float(prop.get('mkt_val_bldg', 0)):,.2f}" if prop.get('mkt_val_bldg') else 'N/A'],
            ['Acreage:', prop.get('acreage', 'N/A')],
            ['School District:', prop.get('school_district', 'N/A')],
        ]
        
        prop_table = Table(prop_data, colWidths=[2*inch, 4*inch])
        prop_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(prop_table)
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    main()
