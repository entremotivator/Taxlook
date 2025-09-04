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
    page_title="Ohio Property Tax Lookup Pro - All 88 Counties",
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
# Complete Ohio Counties Configuration (All 88 Counties)
# --------------------------
OHIO_COUNTIES = {
    '01': {'code': '01', 'name': 'Adams County', 'seat': 'West Union'},
    '02': {'code': '02', 'name': 'Allen County', 'seat': 'Lima'},
    '03': {'code': '03', 'name': 'Ashland County', 'seat': 'Ashland'},
    '04': {'code': '04', 'name': 'Ashtabula County', 'seat': 'Jefferson'},
    '05': {'code': '05', 'name': 'Athens County', 'seat': 'Athens'},
    '06': {'code': '06', 'name': 'Auglaize County', 'seat': 'Wapakoneta'},
    '07': {'code': '07', 'name': 'Belmont County', 'seat': 'St. Clairsville'},
    '08': {'code': '08', 'name': 'Brown County', 'seat': 'Georgetown'},
    '09': {'code': '09', 'name': 'Butler County', 'seat': 'Hamilton'},
    '10': {'code': '10', 'name': 'Carroll County', 'seat': 'Carrollton'},
    '11': {'code': '11', 'name': 'Champaign County', 'seat': 'Urbana'},
    '12': {'code': '12', 'name': 'Clark County', 'seat': 'Springfield'},
    '13': {'code': '13', 'name': 'Clermont County', 'seat': 'Batavia'},
    '14': {'code': '14', 'name': 'Clinton County', 'seat': 'Wilmington'},
    '15': {'code': '15', 'name': 'Columbiana County', 'seat': 'Lisbon'},
    '16': {'code': '16', 'name': 'Coshocton County', 'seat': 'Coshocton'},
    '17': {'code': '17', 'name': 'Crawford County', 'seat': 'Bucyrus'},
    '18': {'code': '18', 'name': 'Cuyahoga County', 'seat': 'Cleveland'},
    '19': {'code': '19', 'name': 'Darke County', 'seat': 'Greenville'},
    '20': {'code': '20', 'name': 'Defiance County', 'seat': 'Defiance'},
    '21': {'code': '21', 'name': 'Delaware County', 'seat': 'Delaware'},
    '22': {'code': '22', 'name': 'Erie County', 'seat': 'Sandusky'},
    '23': {'code': '23', 'name': 'Fairfield County', 'seat': 'Lancaster'},
    '24': {'code': '24', 'name': 'Fayette County', 'seat': 'Washington Court House'},
    '25': {'code': '25', 'name': 'Franklin County', 'seat': 'Columbus'},
    '26': {'code': '26', 'name': 'Fulton County', 'seat': 'Wauseon'},
    '27': {'code': '27', 'name': 'Gallia County', 'seat': 'Gallipolis'},
    '28': {'code': '28', 'name': 'Geauga County', 'seat': 'Chardon'},
    '29': {'code': '29', 'name': 'Greene County', 'seat': 'Xenia'},
    '30': {'code': '30', 'name': 'Guernsey County', 'seat': 'Cambridge'},
    '31': {'code': '31', 'name': 'Hamilton County', 'seat': 'Cincinnati'},
    '32': {'code': '32', 'name': 'Hancock County', 'seat': 'Findlay'},
    '33': {'code': '33', 'name': 'Hardin County', 'seat': 'Kenton'},
    '34': {'code': '34', 'name': 'Harrison County', 'seat': 'Cadiz'},
    '35': {'code': '35', 'name': 'Henry County', 'seat': 'Napoleon'},
    '36': {'code': '36', 'name': 'Highland County', 'seat': 'Hillsboro'},
    '37': {'code': '37', 'name': 'Hocking County', 'seat': 'Logan'},
    '38': {'code': '38', 'name': 'Holmes County', 'seat': 'Millersburg'},
    '39': {'code': '39', 'name': 'Huron County', 'seat': 'Norwalk'},
    '40': {'code': '40', 'name': 'Jackson County', 'seat': 'Jackson'},
    '41': {'code': '41', 'name': 'Jefferson County', 'seat': 'Steubenville'},
    '42': {'code': '42', 'name': 'Knox County', 'seat': 'Mount Vernon'},
    '43': {'code': '43', 'name': 'Lake County', 'seat': 'Painesville'},
    '44': {'code': '44', 'name': 'Lawrence County', 'seat': 'Ironton'},
    '45': {'code': '45', 'name': 'Licking County', 'seat': 'Newark'},
    '46': {'code': '46', 'name': 'Logan County', 'seat': 'Bellefontaine'},
    '47': {'code': '47', 'name': 'Lorain County', 'seat': 'Elyria'},
    '48': {'code': '48', 'name': 'Lucas County', 'seat': 'Toledo'},
    '49': {'code': '49', 'name': 'Madison County', 'seat': 'London'},
    '50': {'code': '50', 'name': 'Mahoning County', 'seat': 'Youngstown'},
    '51': {'code': '51', 'name': 'Marion County', 'seat': 'Marion'},
    '52': {'code': '52', 'name': 'Medina County', 'seat': 'Medina'},
    '53': {'code': '53', 'name': 'Meigs County', 'seat': 'Pomeroy'},
    '54': {'code': '54', 'name': 'Mercer County', 'seat': 'Celina'},
    '55': {'code': '55', 'name': 'Miami County', 'seat': 'Troy'},
    '56': {'code': '56', 'name': 'Monroe County', 'seat': 'Woodsfield'},
    '57': {'code': '57', 'name': 'Montgomery County', 'seat': 'Dayton'},
    '58': {'code': '58', 'name': 'Morgan County', 'seat': 'McConnelsville'},
    '59': {'code': '59', 'name': 'Morrow County', 'seat': 'Mount Gilead'},
    '60': {'code': '60', 'name': 'Muskingum County', 'seat': 'Zanesville'},
    '61': {'code': '61', 'name': 'Noble County', 'seat': 'Caldwell'},
    '62': {'code': '62', 'name': 'Ottawa County', 'seat': 'Port Clinton'},
    '63': {'code': '63', 'name': 'Paulding County', 'seat': 'Paulding'},
    '64': {'code': '64', 'name': 'Perry County', 'seat': 'New Lexington'},
    '65': {'code': '65', 'name': 'Pickaway County', 'seat': 'Circleville'},
    '66': {'code': '66', 'name': 'Pike County', 'seat': 'Waverly'},
    '67': {'code': '67', 'name': 'Portage County', 'seat': 'Ravenna'},
    '68': {'code': '68', 'name': 'Preble County', 'seat': 'Eaton'},
    '69': {'code': '69', 'name': 'Putnam County', 'seat': 'Ottawa'},
    '70': {'code': '70', 'name': 'Richland County', 'seat': 'Mansfield'},
    '71': {'code': '71', 'name': 'Ross County', 'seat': 'Chillicothe'},
    '72': {'code': '72', 'name': 'Sandusky County', 'seat': 'Fremont'},
    '73': {'code': '73', 'name': 'Scioto County', 'seat': 'Portsmouth'},
    '74': {'code': '74', 'name': 'Seneca County', 'seat': 'Tiffin'},
    '75': {'code': '75', 'name': 'Shelby County', 'seat': 'Sidney'},
    '76': {'code': '76', 'name': 'Stark County', 'seat': 'Canton'},
    '77': {'code': '77', 'name': 'Summit County', 'seat': 'Akron'},
    '78': {'code': '78', 'name': 'Trumbull County', 'seat': 'Warren'},
    '79': {'code': '79', 'name': 'Tuscarawas County', 'seat': 'New Philadelphia'},
    '80': {'code': '80', 'name': 'Union County', 'seat': 'Marysville'},
    '81': {'code': '81', 'name': 'Van Wert County', 'seat': 'Van Wert'},
    '82': {'code': '82', 'name': 'Vinton County', 'seat': 'McArthur'},
    '83': {'code': '83', 'name': 'Warren County', 'seat': 'Lebanon'},
    '84': {'code': '84', 'name': 'Washington County', 'seat': 'Marietta'},
    '85': {'code': '85', 'name': 'Wayne County', 'seat': 'Wooster'},
    '86': {'code': '86', 'name': 'Williams County', 'seat': 'Bryan'},
    '87': {'code': '87', 'name': 'Wood County', 'seat': 'Bowling Green'},
    '88': {'code': '88', 'name': 'Wyandot County', 'seat': 'Upper Sandusky'}
}

# --------------------------
# Real Property Data API Configuration - ReportAllUSA
# --------------------------
# Configure with ReportAllUSA API credentials
# Expected secrets format:
# [reportallusa]
# client = "kcuk4HJnjt"
PROPERTY_API_CONFIG = {
    "REPORTALLUSA_CLIENT_KEY": st.secrets.get("reportallusa", {}).get("client", ""),
    "REPORTALLUSA_BASE_URL": "https://reportallusa.com/api/parcels",
    "API_VERSION": "9"
}

# --------------------------
# Enhanced API Functions for Real Ohio Property Data - ReportAllUSA
# --------------------------
def fetch_ohio_property_data_reportallusa(parcel_id, county_name=None):
    """
    Fetch property data using ReportAllUSA API for Ohio state-wide search
    """
    try:
        client_key = PROPERTY_API_CONFIG["REPORTALLUSA_CLIENT_KEY"]
        if not client_key:
            return {
                "status": "ERROR", 
                "message": "ReportAllUSA client key not configured. Please set client key in [reportallusa] section of secrets."
            }

        base_url = PROPERTY_API_CONFIG["REPORTALLUSA_BASE_URL"]
        api_version = PROPERTY_API_CONFIG["API_VERSION"]
        
        # Build search parameters for Ohio state-wide search
        params = {
            'client': client_key,
            'v': api_version,
            'region': f"{county_name}, Ohio" if county_name else "Ohio",
            'parcel_id': parcel_id,
            'return_buildings': 'true',
            'rpp': 10
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK' and data.get('results'):
                return {
                    "status": "OK",
                    "results": data.get('results', []),
                    "api_source": "ReportAllUSA - Ohio Statewide",
                    "total_records": data.get('count', 0),
                    "query_info": data.get('query', '')
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": f"No property found with parcel ID '{parcel_id}' in Ohio."
                }
        elif response.status_code == 401:
            return {
                "status": "ERROR", 
                "message": "API authentication failed. Please check your ReportAllUSA client key."
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
            "message": "Request timed out. The ReportAllUSA API may be experiencing delays."
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "ERROR", 
            "message": "Connection error. Unable to reach ReportAllUSA API."
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

def search_multiple_parcels_ohio(parcel_ids, county_name=None):
    """
    Search multiple parcel IDs at once using ReportAllUSA API
    """
    try:
        client_key = PROPERTY_API_CONFIG["REPORTALLUSA_CLIENT_KEY"]
        if not client_key:
            return {
                "status": "ERROR", 
                "message": "ReportAllUSA client key not configured."
            }

        base_url = PROPERTY_API_CONFIG["REPORTALLUSA_BASE_URL"]
        api_version = PROPERTY_API_CONFIG["API_VERSION"]
        
        # Join multiple parcel IDs with semicolon as per API documentation
        parcel_ids_str = ";".join(parcel_ids) if isinstance(parcel_ids, list) else parcel_ids
        
        params = {
            'client': client_key,
            'v': api_version,
            'region': f"{county_name}, Ohio" if county_name else "Ohio",
            'parcel_id': parcel_ids_str,
            'return_buildings': 'true',
            'rpp': 50  # Higher limit for multiple parcels
        }
        
        response = requests.get(base_url, params=params, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                return {
                    "status": "OK",
                    "results": data.get('results', []),
                    "api_source": "ReportAllUSA - Ohio Statewide",
                    "total_records": data.get('count', 0),
                    "query_info": data.get('query', '')
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": "No properties found for the provided parcel IDs in Ohio."
                }
        else:
            return {
                "status": "ERROR", 
                "message": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Multiple parcel search error: {str(e)}"
        }

def search_ohio_property_comprehensive(search_term, search_type="parcel", county_name=None):
    """
    Comprehensive Ohio property search using ReportAllUSA API with state-wide coverage
    """
    if search_type == "parcel":
        # Handle single or multiple parcel IDs
        if ";" in search_term or "," in search_term:
            # Multiple parcel IDs
            parcel_ids = [pid.strip() for pid in search_term.replace(",", ";").split(";")]
            return search_multiple_parcels_ohio(parcel_ids, county_name)
        else:
            # Single parcel ID
            return fetch_ohio_property_data_reportallusa(search_term, county_name)
    else:
        # For address searches, we'll still use parcel search but inform user
        return {
            "status": "ERROR",
            "message": "Address search not directly supported. Please use parcel ID search for Ohio properties."
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
# Sidebar: Enhanced Ohio counties display and usage stats
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

    # Complete Ohio Counties Information
    st.divider()
    st.subheader("🏛️ All Ohio Counties (88 Total)")
    
    # Group counties by region for better organization
    regions = {
        "Northeast Ohio": ['18', '28', '43', '47', '50', '67', '76', '77', '78'],
        "Central Ohio": ['21', '23', '25', '45', '49', '65', '80'],
        "Southwest Ohio": ['09', '13', '31', '68', '83'],
        "Southeast Ohio": ['05', '07', '27', '30', '40', '44', '56', '58', '60', '61', '71', '73', '84'],
        "Northwest Ohio": ['02', '20', '22', '26', '32', '35', '39', '48', '62', '69', '72', '74', '86', '87'],
        "Other Counties": [code for code in OHIO_COUNTIES.keys() if code not in 
                          ['18', '28', '43', '47', '50', '67', '76', '77', '78', '21', '23', '25', '45', '49', '65', '80',
                           '09', '13', '31', '68', '83', '05', '07', '27', '30', '40', '44', '56', '58', '60', '61', '71', '73', '84',
                           '02', '20', '22', '26', '32', '35', '39', '48', '62', '69', '72', '74', '86', '87']]
    }
    
    with st.expander("View All 88 Counties by Region"):
        for region, county_codes in regions.items():
            st.markdown(f"**{region}:**")
            for code in county_codes:
                county_info = OHIO_COUNTIES[code]
                st.write(f"• {county_info['name']} ({code}) - {county_info['seat']}")
            st.write("")

    if st.session_state.search_history:
        st.divider()
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

    # Enhanced API Status
    st.divider()
    st.subheader("🔌 ReportAllUSA API Status")
    
    if PROPERTY_API_CONFIG["REPORTALLUSA_CLIENT_KEY"]:
        st.success("✅ ReportAllUSA API Connected")
        st.caption("Ohio statewide property data enabled")
    else:
        st.error("❌ ReportAllUSA API Key Missing")
        st.caption("Set client key in [reportallusa] section of secrets")
    
    st.info("🌟 **State-wide Coverage**: Search all of Ohio with one API")

# --------------------------
# Enhanced Property Cards for Ohio Data
# --------------------------
def create_enhanced_ohio_property_cards(data):
    """Create enhanced property cards with comprehensive Ohio property data"""
    
    # Enhanced Property Overview section
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                padding: 25px; border-radius: 20px; margin: 15px 0; color: white; 
                box-shadow: 0 8px 25px rgba(30,60,114,0.3);'>
        <h2 style='color: white; margin-bottom: 20px; text-align: center; font-size: 28px;'>🏠 Ohio Property Details - Comprehensive Data</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Create four enhanced metric columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Location Info - Ohio Blue gradient
        county_name = data.get('county', data.get('county_name', 'N/A'))
        parcel_id = data.get('parcel_id', data.get('parcelid', data.get('parcel_number', 'N/A')))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(33,150,243,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>📍 Location</h4>
            <div style='margin-bottom: 12px;'><strong>Parcel ID:</strong><br><span style='font-size: 16px; font-weight: bold;'>{parcel_id}</span></div>
            <div style='margin-bottom: 12px;'><strong>County:</strong><br><span style='font-size: 14px;'>{county_name}</span></div>
            <div><strong>State:</strong><br><span style='font-size: 14px;'>Ohio</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Market Values - Green gradient
        market_value = data.get('market_value', data.get('assessed_value', data.get('value', 0)))
        land_value = data.get('land_value', data.get('lot_value', 0))
        building_value = data.get('building_value', data.get('improvement_value', 0))
        
        try:
            market_value = float(market_value) if market_value else 0
            land_value = float(land_value) if land_value else 0
            building_value = float(building_value) if building_value else 0
        except:
            market_value = land_value = building_value = 0
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4CAF50 0%, #388E3C 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(76,175,80,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>💰 Values</h4>
            <div style='margin-bottom: 12px;'><strong>Market Value:</strong><br><span style='font-size: 16px; font-weight: bold;'>${market_value:,.0f}</span></div>
            <div style='margin-bottom: 12px;'><strong>Land Value:</strong><br><span style='font-size: 14px;'>${land_value:,.0f}</span></div>
            <div><strong>Building Value:</strong><br><span style='font-size: 14px;'>${building_value:,.0f}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Property Details - Orange gradient
        property_type = data.get('property_type', data.get('land_use', data.get('property_class', 'N/A')))
        year_built = data.get('year_built', data.get('built_year', 'N/A'))
        lot_size = data.get('lot_size', data.get('acreage', data.get('lot_area', 'N/A')))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(255,152,0,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏘️ Property Info</h4>
            <div style='margin-bottom: 12px;'><strong>Type:</strong><br><span style='font-size: 14px; font-weight: bold;'>{property_type}</span></div>
            <div style='margin-bottom: 12px;'><strong>Year Built:</strong><br><span style='font-size: 14px;'>{year_built}</span></div>
            <div><strong>Lot Size:</strong><br><span style='font-size: 14px;'>{lot_size}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Tax Information - Purple gradient
        annual_tax = data.get('annual_tax', data.get('tax_amount', data.get('taxes', 0)))
        tax_year = data.get('tax_year', datetime.now().year)
        school_district = data.get('school_district', data.get('district', 'N/A'))
        
        try:
            annual_tax = float(annual_tax) if annual_tax else 0
        except:
            annual_tax = 0
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(156,39,176,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏛️ Tax Info</h4>
            <div style='margin-bottom: 12px;'><strong>Annual Tax:</strong><br><span style='font-size: 16px; font-weight: bold;'>${annual_tax:,.0f}</span></div>
            <div style='margin-bottom: 12px;'><strong>Tax Year:</strong><br><span style='font-size: 14px;'>{tax_year}</span></div>
            <div><strong>School District:</strong><br><span style='font-size: 12px;'>{school_district}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    # Enhanced Address Information
    st.markdown("""
    <div style='background: linear-gradient(135deg, #E8F5E8 0%, #C8E6C9 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h3 style='color: #2d3748; margin-bottom: 15px;'>📍 Complete Address Information</h3>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        property_address = data.get('address', data.get('property_address', data.get('street_address', 'N/A')))
        city = data.get('city', data.get('municipality', 'N/A'))
        zip_code = data.get('zip', data.get('zip_code', data.get('postal_code', 'N/A')))
        
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Property Address:</div>
        <div style='color: #4a5568; margin-bottom: 5px; font-size: 16px;'>{property_address}</div>
        <div style='color: #4a5568; margin-bottom: 10px; font-size: 16px;'>{city}, OH {zip_code}</div>
        """, unsafe_allow_html=True)
        
        # Coordinates if available
        lat = data.get('latitude', data.get('lat'))
        lng = data.get('longitude', data.get('lng', data.get('lon')))
        if lat and lng:
            st.markdown(f"<div style='color: #2d3748;'><strong>Coordinates:</strong> {lat}, {lng}</div>", unsafe_allow_html=True)
    
    with col2:
        # Owner information
        owner_name = data.get('owner', data.get('owner_name', data.get('property_owner', 'N/A')))
        mailing_address = data.get('mailing_address', data.get('owner_address', property_address))
        
        st.markdown(f"""
        <div style='color: #2d3748; font-weight: 600; margin-bottom: 8px;'>Owner Information:</div>
        <div style='color: #4a5568; margin-bottom: 5px;'><strong>Owner:</strong> {owner_name}</div>
        <div style='color: #4a5568; margin-bottom: 5px;'><strong>Mailing Address:</strong> {mailing_address}</div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Additional Property Details
    if any(key in data for key in ['bedrooms', 'bathrooms', 'square_feet', 'stories']):
        st.markdown("""
        <div style='background: linear-gradient(135deg, #FFF3E0 0%, #FFE0B2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 0; color: #2d3748; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
            <h3 style='color: #2d3748; margin-bottom: 15px;'>🏠 Building Details</h3>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            bedrooms = data.get('bedrooms', data.get('beds', 'N/A'))
            st.markdown(f"<div style='color: #2d3748;'><strong>Bedrooms:</strong> {bedrooms}</div>", unsafe_allow_html=True)
        with col2:
            bathrooms = data.get('bathrooms', data.get('baths', 'N/A'))
            st.markdown(f"<div style='color: #2d3748;'><strong>Bathrooms:</strong> {bathrooms}</div>", unsafe_allow_html=True)
        with col3:
            sqft = data.get('square_feet', data.get('sqft', data.get('living_area', 'N/A')))
            st.markdown(f"<div style='color: #2d3748;'><strong>Square Feet:</strong> {sqft}</div>", unsafe_allow_html=True)
        with col4:
            stories = data.get('stories', data.get('floors', 'N/A'))
            st.markdown(f"<div style='color: #2d3748;'><strong>Stories:</strong> {stories}</div>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# Enhanced PDF Generation
# --------------------------
def create_enhanced_ohio_pdf(data):
    """Create enhanced PDF report for Ohio property data"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1  # Center alignment
    )
    story.append(Paragraph("Ohio Property Tax Report - ReportAllUSA Data", title_style))
    story.append(Spacer(1, 20))

    # Property overview table with enhanced data
    overview_data = [
        ['Property Information', 'Details'],
        ['Parcel ID', data.get('parcel_id', data.get('parcelid', 'N/A'))],
        ['Property Address', data.get('address', data.get('property_address', 'N/A'))],
        ['City, State ZIP', f"{data.get('city', 'N/A')}, OH {data.get('zip', data.get('zip_code', 'N/A'))}"],
        ['County', data.get('county', data.get('county_name', 'N/A'))],
        ['Owner', data.get('owner', data.get('owner_name', 'N/A'))],
        ['Market Value', f"${float(data.get('market_value', data.get('assessed_value', 0))):,.2f}"],
        ['Annual Tax', f"${float(data.get('annual_tax', data.get('tax_amount', 0))):,.2f}"],
        ['Property Type', data.get('property_type', data.get('land_use', 'N/A'))],
        ['Year Built', data.get('year_built', data.get('built_year', 'N/A'))],
        ['Lot Size', data.get('lot_size', data.get('acreage', 'N/A'))],
        ['School District', data.get('school_district', data.get('district', 'N/A'))]
    ]
    
    table = Table(overview_data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('FONTSIZE',(0,0),(-1,-1),10)
    ]))
    story.append(table)
    story.append(Spacer(1,20))

    # Add data source information
    story.append(Paragraph("Data Source Information", styles['Heading2']))
    story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph("Data provided by: ReportAllUSA API", styles['Normal']))
    story.append(Paragraph("Coverage: Ohio Statewide Property Data", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Main App UI - Enhanced
# --------------------------
st.title("🏠 Ohio Property Tax Lookup Pro - All 88 Counties")
st.markdown("**Comprehensive Ohio property research with real data integration** | *10 searches per session*")

# Enhanced region information
st.info("🌟 **Now covering ALL 88 Ohio counties** with real property data from ReportAllUSA API for complete statewide coverage.")

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.stop()

# Enhanced search tabs
tab1, tab2, tab3 = st.tabs(["🔍 Search by Parcel ID", "📍 Search by Address", "🗺️ County Explorer"])

with tab1:
    st.subheader("🔍 Ohio State-wide Property Search by Parcel ID")
    st.markdown("*Search any property across all of Ohio using parcel ID - no county selection needed!*")
    
    col1, col2, col3 = st.columns([4, 2, 1])
    with col1:
        parcel_id = st.text_input(
            "Enter Ohio Parcel ID", 
            placeholder="e.g., 44327012 or multiple: 44327012;44327010;44327013", 
            help="Enter single parcel ID or multiple IDs separated by semicolons. Searches entire state of Ohio automatically."
        )
    with col2:
        county_filter = st.selectbox(
            "County Filter (Optional)",
            ["All of Ohio (Recommended)"] + [f"{info['name']}" for info in OHIO_COUNTIES.values()],
            help="Leave as 'All of Ohio' for best results, or select specific county to narrow search"
        )
    with col3:
        search_button = st.button(
            "🔍 Search Ohio", 
            type="primary", 
            disabled=(st.session_state.usage_count >= MAX_SEARCHES)
        )

    # Enhanced parcel ID search functionality
    if search_button and parcel_id:
        if st.session_state.usage_count >= MAX_SEARCHES:
            st.error("Usage limit reached!")
        elif not parcel_id.strip():
            st.error("Please enter a valid Parcel ID")
        else:
            with st.spinner("Searching Ohio state-wide property database..."):
                try:
                    # Determine county name if selected
                    county_name = None
                    if county_filter != "All of Ohio (Recommended)":
                        county_name = county_filter
                    
                    # Use comprehensive search function
                    api_response = search_ohio_property_comprehensive(parcel_id, "parcel", county_name)

                    if api_response.get('status') == "OK" and api_response.get('results'):
                        # Update usage count and history
                        st.session_state.usage_count += 1
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        search_scope = f" - {county_filter}" if county_filter != "All of Ohio (Recommended)" else " - Statewide"
                        st.session_state.search_history.append(f"{parcel_id}{search_scope} - {timestamp}")
                        
                        # Success message
                        total_found = api_response.get('total_records', len(api_response.get('results', [])))
                        st.success(f"✅ Found {total_found} Ohio property record(s)! (Search {st.session_state.usage_count}/{MAX_SEARCHES}) - Source: {api_response.get('api_source', 'ReportAllUSA')}")
                        
                        # Display results
                        results = api_response['results']
                        if len(results) == 1:
                            create_enhanced_ohio_property_cards(results[0])
                        else:
                            st.info(f"Found {len(results)} matching properties:")
                            for i, property_data in enumerate(results[:5]):  # Show top 5 results
                                county_name = property_data.get('county', property_data.get('county_name', 'N/A'))
                                address = property_data.get('address', property_data.get('property_address', 'N/A'))
                                with st.expander(f"Property {i+1}: {address} - {county_name}"):
                                    create_enhanced_ohio_property_cards(property_data)

                        # Enhanced export options
                        st.divider()
                        st.subheader("📥 Export Options")
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_buffer = create_enhanced_ohio_pdf(results[0])
                            st.download_button(
                                "📄 Download Ohio Property PDF Report", 
                                pdf_buffer.getvalue(),
                                file_name=f"ohio_property_report_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                                mime="application/pdf"
                            )
                        with col2:
                            json_str = json.dumps(results[0] if len(results) == 1 else results, indent=2)
                            st.download_button(
                                "📋 Download Complete JSON Data", 
                                json_str,
                                file_name=f"ohio_property_data_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                            
                    else:
                        error_msg = api_response.get('message', 'Property not found in Ohio records')
                        st.error(f"❌ {error_msg}")
                        st.info("💡 Please verify the Parcel ID format and try again. You can search multiple parcel IDs by separating them with semicolons (;).")
                        # Still increment usage count for failed searches
                        st.session_state.usage_count += 1
                        
                except Exception as e:
                    st.error(f"❌ Unexpected error occurred: {str(e)}")
                    st.info("💡 Please try again or contact support")
                    # Increment usage count for errors too
                    st.session_state.usage_count += 1

with tab2:
    st.subheader("📍 Address to Parcel ID Lookup")
    st.markdown("*Use this section to find parcel IDs for address-based searches*")
    
    st.info("ℹ️ **Note**: The ReportAllUSA API searches by parcel ID. Use county auditor websites below to find parcel IDs for specific addresses, then use the Parcel ID search above.")
    
    # Quick links to major Ohio county auditor websites
    st.subheader("🔗 Ohio County Auditor Property Search Links")
    
    major_counties = {
        "Cuyahoga County (Cleveland)": "https://cuyahogacounty.gov/fiscal-officer/departments/real-property/real-property-information",
        "Franklin County (Columbus)": "https://franklincountyauditor.com/",
        "Hamilton County (Cincinnati)": "https://wedge.hcauditor.org/",
        "Summit County (Akron)": "https://www.summitoh.net/",
        "Lucas County (Toledo)": "https://www.co.lucas.oh.us/377/AREIS-Information",
        "Butler County": "https://www.bcauditor.org/",
        "Stark County (Canton)": "https://www.starkcountyohio.gov/auditor",
        "Lorain County": "https://www.loraincounty.us/auditor",
        "Mahoning County (Youngstown)": "https://www.mahoningcountyoh.gov/",
        "Montgomery County (Dayton)": "https://www.mcauditor.org/"
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Major Counties:**")
        for county, url in list(major_counties.items())[:5]:
            st.markdown(f"• [{county}]({url})")
    
    with col2:
        st.markdown("**Additional Counties:**")
        for county, url in list(major_counties.items())[5:]:
            st.markdown(f"• [{county}]({url})")
    
    st.markdown("---")
    st.markdown("**💡 Tip**: Once you find the parcel ID on a county website, copy it and use the 'Search by Parcel ID' tab above for comprehensive property data.")

with tab3:
    st.subheader("🗺️ Ohio State-wide Property Data")
    st.markdown("*Comprehensive coverage across all 88 Ohio counties*")
    
    # Ohio statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Counties", "88", help="All Ohio counties supported")
    with col2:
        st.metric("Data Source", "ReportAllUSA", help="Professional property data API")
    with col3:
        st.metric("Coverage", "Statewide", help="Complete Ohio coverage")
    with col4:
        st.metric("Search Type", "Parcel ID", help="Primary search method")
    
    # Sample parcel ID formats
    st.subheader("📋 Sample Ohio Parcel ID Formats")
    st.markdown("""
    Different Ohio counties use different parcel ID formats. Here are some examples:
    
    - **Cuyahoga County**: 44327012, 44327010, 44327013
    - **Franklin County**: 010-123456-00, 010-123457-00
    - **Hamilton County**: 123-0001-0001-00, 123-0001-0002-00
    - **Summit County**: 12-34567, 12-34568
    - **Lucas County**: 12-34567-890, 12-34568-890
    
    **Multiple Search**: You can search multiple parcels at once by separating them with semicolons:
    `44327012;44327010;44327013`
    """)
    
    # Ohio regions
    st.subheader("🗺️ Ohio Regions Covered")
    regions_info = {
        "Northeast Ohio": "Cleveland, Akron, Youngstown areas - Industrial and urban properties",
        "Central Ohio": "Columbus area - State capital region with diverse property types", 
        "Southwest Ohio": "Cincinnati, Dayton areas - Major metropolitan regions",
        "Southeast Ohio": "Appalachian region - Rural and small town properties",
        "Northwest Ohio": "Toledo area - Agricultural and industrial properties"
    }
    
    for region, description in regions_info.items():
        st.markdown(f"**{region}**: {description}")

# Enhanced API Configuration Help
st.divider()
with st.expander("⚙️ ReportAllUSA API Configuration & Setup"):
    st.markdown("""
    ### Setting up ReportAllUSA API for Ohio Property Data
    
    This application uses the **ReportAllUSA API** for comprehensive Ohio property data access.
    
    #### 🔑 API Configuration
    To enable real property data, add your ReportAllUSA client key to Streamlit secrets:
    
    ```toml
    # In your Streamlit secrets.toml file
    [reportallusa]
    client = "kcuk4HJnjt"
    ```
    
    #### 🌐 API Capabilities
    - **Coverage**: All 88 Ohio counties
    - **Search Method**: Parcel ID based searches
    - **Multiple Parcels**: Search multiple properties at once
    - **Building Footprints**: Includes building polygon data when available
    - **Real-time Data**: Live property information from official sources
    
    #### 📊 API Response Format
    The API returns comprehensive property data including:
    - Property identification and location details
    - Assessment and valuation information  
    - Tax records and payment history
    - Property characteristics and building details
    - Owner information and mailing addresses
    - Geographic coordinates and boundaries
    
    #### 🔍 Search Examples
    **Single Parcel**: `44327012`
    **Multiple Parcels**: `44327012;44327010;44327013`
    **County-Specific**: Use county filter for targeted searches
    **State-wide**: Leave county as "All of Ohio" for best coverage
    
    #### 📈 Usage Guidelines
    - Each search counts toward your session limit (10 searches)
    - Multiple parcel searches count as one search
    - Failed searches still count toward the limit
    - Refresh the page to reset your search count
    
    #### 🆘 Troubleshooting
    - **"API key not configured"**: Add `[reportallusa]` section with `client = "kcuk4HJnjt"` to secrets
    - **"Property not found"**: Verify parcel ID format for the specific county
    - **"Rate limit exceeded"**: Wait a moment before trying again
    - **Multiple formats**: Try different parcel ID formats if first attempt fails
    
    #### 🔗 Getting API Access
    Visit [ReportAllUSA](https://reportallusa.com/) to sign up for API access and obtain your client key.
    """)

# Enhanced usage information
st.divider()
remaining = MAX_SEARCHES - st.session_state.usage_count
if remaining <= 2 and remaining > 0:
    st.warning(f"⚠️ {remaining} searches remaining in this session!")
elif remaining == 0:
    st.error("❌ No searches remaining. Refresh the page to reset.")
else:
    st.success(f"✅ {remaining} searches available - Ohio state-wide property data ready!")

# Enhanced footer
st.markdown(
    f"""
    <div class="custom-footer">
        Ohio Property Tax Lookup Pro - ReportAllUSA Edition | State-wide Coverage | Searches: {st.session_state.usage_count}/{MAX_SEARCHES} | 
        Real Ohio Property Data | Session: {datetime.now().strftime('%Y-%m-%d')} | 
        <a href="https://reportallusa.com/" target="_blank" style="color: #ff6b6b; text-decoration: none;">
            🌟 Powered by ReportAllUSA
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)

