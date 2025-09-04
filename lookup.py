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
    
    /* Premium link styling - Light Blue Theme */
    .premium-link {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        padding: 15px 20px;
        border-radius: 10px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(33,150,243,0.3);
    }
    
    .premium-link a {
        color: white !important;
        text-decoration: none !important;
        font-weight: bold;
        font-size: 16px;
    }
    
    .premium-link a:hover {
        text-decoration: underline !important;
    }
    
    /* JSON Card Styling */
    .json-card {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid #2196F3;
        box-shadow: 0 2px 8px rgba(33,150,243,0.2);
    }
    
    .json-card h4 {
        color: #1565C0;
        margin-bottom: 10px;
        font-weight: bold;
    }
    
    .json-field {
        margin: 5px 0;
        padding: 3px 0;
        border-bottom: 1px solid rgba(33,150,243,0.1);
    }
    
    .json-field:last-child {
        border-bottom: none;
    }
    
    .field-label {
        font-weight: bold;
        color: #1565C0;
        display: inline-block;
        min-width: 120px;
    }
    
    .field-value {
        color: #424242;
        margin-left: 10px;
    }
    
    /* Address highlight styling */
    .address-highlight {
        background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 6px 20px rgba(25,118,210,0.4);
        text-align: center;
    }
    
    .address-highlight h3 {
        color: white;
        margin-bottom: 15px;
        font-size: 24px;
    }
    
    .address-text {
        font-size: 18px;
        font-weight: bold;
        margin: 8px 0;
    }
    
    /* Mailing address styling */
    .mailing-address {
        background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 12px rgba(66,165,245,0.3);
    }
    
    .mailing-address h4 {
        color: white;
        margin-bottom: 10px;
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
                "message": "ReportAllUSA client key not configured. Please set client key in [reportallusa] section of secrets.",
                "raw_response": None
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
                    "query_info": data.get('query', ''),
                    "raw_response": data  # Include raw JSON response
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": f"No property found with parcel ID '{parcel_id}' in Ohio.",
                    "raw_response": data
                }
        elif response.status_code == 401:
            return {
                "status": "ERROR", 
                "message": "API authentication failed. Please check your ReportAllUSA client key.",
                "raw_response": None
            }
        elif response.status_code == 429:
            return {
                "status": "ERROR", 
                "message": "API rate limit exceeded. Please try again later.",
                "raw_response": None
            }
        else:
            return {
                "status": "ERROR", 
                "message": f"API returned status code: {response.status_code}. Response: {response.text[:200]}",
                "raw_response": None
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "ERROR", 
            "message": "Request timed out. The ReportAllUSA API may be experiencing delays.",
            "raw_response": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "ERROR", 
            "message": "Connection error. Unable to reach ReportAllUSA API.",
            "raw_response": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "ERROR", 
            "message": f"Request error: {str(e)}",
            "raw_response": None
        }
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Unexpected error: {str(e)}",
            "raw_response": None
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
                "message": "ReportAllUSA client key not configured.",
                "raw_response": None
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
                    "query_info": data.get('query', ''),
                    "raw_response": data  # Include raw JSON response
                }
            else:
                return {
                    "status": "NOT_FOUND",
                    "message": "No properties found for the provided parcel IDs in Ohio.",
                    "raw_response": data
                }
        else:
            return {
                "status": "ERROR", 
                "message": f"API error: {response.status_code}",
                "raw_response": None
            }
            
    except Exception as e:
        return {
            "status": "ERROR", 
            "message": f"Multiple parcel search error: {str(e)}",
            "raw_response": None
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
            "message": "Address search not directly supported. Please use parcel ID search for Ohio properties.",
            "raw_response": None
        }

# --------------------------
# Enhanced Property Display Functions with Full JSON Cards
# --------------------------
def create_json_field_card(title, fields, data):
    """Create a card for a group of JSON fields"""
    card_html = f"""
    <div class='json-card'>
        <h4>{title}</h4>
    """
    
    for field_key, field_label in fields.items():
        value = data.get(field_key, 'N/A')
        if value is not None and value != '':
            # Format numeric values
            if field_key in ['mkt_val_land', 'mkt_val_bldg', 'mkt_val_tot', 'sale_price'] and str(value).replace('.', '').isdigit():
                try:
                    value = f"${float(value):,.2f}"
                except:
                    pass
            elif field_key in ['bldg_sqft'] and str(value).isdigit():
                try:
                    value = f"{int(value):,} sq ft"
                except:
                    pass
            elif field_key in ['acreage', 'acreage_calc'] and str(value).replace('.', '').isdigit():
                try:
                    value = f"{float(value):.3f} acres"
                except:
                    pass
            
            card_html += f"""
            <div class='json-field'>
                <span class='field-label'>{field_label}:</span>
                <span class='field-value'>{value}</span>
            </div>
            """
    
    card_html += "</div>"
    return card_html

def create_enhanced_ohio_property_cards(data):
    """Create enhanced property display cards for Ohio property data with full JSON response"""
    
    # Highlighted Address Section
    property_address = data.get('address', data.get('property_address', data.get('street_address', 'N/A')))
    city = data.get('addr_city', data.get('city', data.get('municipality', 'N/A')))
    zip_code = data.get('addr_zip', data.get('zip', data.get('zip_code', data.get('postal_code', 'N/A'))))
    zip_plus_four = data.get('addr_zipplusfour', '')
    full_zip = f"{zip_code}-{zip_plus_four}" if zip_plus_four else zip_code
    
    st.markdown(f"""
    <div class='address-highlight'>
        <h3>📍 Property Address</h3>
        <div class='address-text'>{property_address}</div>
        <div class='address-text'>{city}, OH {full_zip}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Mailing Address Section
    mail_address1 = data.get('mail_address1', 'N/A')
    mail_address3 = data.get('mail_address3', 'N/A')
    
    if mail_address1 != 'N/A' or mail_address3 != 'N/A':
        st.markdown(f"""
        <div class='mailing-address'>
            <h4>📮 Mailing Address</h4>
            <div>{mail_address1}</div>
            <div>{mail_address3}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Main property overview with gradient cards (Light Blue Theme)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Market Value - Light Blue gradient
        market_value = data.get('mkt_val_tot', data.get('market_value', data.get('assessed_value', data.get('appraised_value', 0))))
        try:
            market_value = float(market_value) if market_value else 0
        except:
            market_value = 0
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #42A5F5 0%, #1E88E5 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(66,165,245,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>💰 Market Value</h4>
            <div style='font-size: 24px; font-weight: bold; margin-bottom: 10px;'>${market_value:,.0f}</div>
            <div style='font-size: 12px; opacity: 0.9;'>Total Market Value</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Parcel Information - Medium Blue gradient
        parcel_id = data.get('parcel_id', data.get('parcelid', data.get('parcel_number', 'N/A')))
        county_name = data.get('county_name', data.get('county', 'N/A'))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(33,150,243,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>📋 Parcel Info</h4>
            <div style='margin-bottom: 12px;'><strong>Parcel ID:</strong><br><span style='font-size: 14px; font-weight: bold;'>{parcel_id}</span></div>
            <div><strong>County:</strong><br><span style='font-size: 14px;'>{county_name}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Property Details - Light Blue gradient
        land_use_class = data.get('land_use_class', data.get('property_type', data.get('land_use', data.get('property_class', 'N/A'))))
        bldg_sqft = data.get('bldg_sqft', data.get('square_feet', data.get('sqft', 'N/A')))
        acreage = data.get('acreage', data.get('lot_size', data.get('lot_area', 'N/A')))
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(100,181,246,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>🏘️ Property Info</h4>
            <div style='margin-bottom: 12px;'><strong>Type:</strong><br><span style='font-size: 14px; font-weight: bold;'>{land_use_class}</span></div>
            <div style='margin-bottom: 12px;'><strong>Building Sq Ft:</strong><br><span style='font-size: 14px;'>{bldg_sqft}</span></div>
            <div><strong>Acreage:</strong><br><span style='font-size: 14px;'>{acreage}</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Owner Information - Dark Blue gradient
        owner = data.get('owner', data.get('owner_name', data.get('property_owner', 'N/A')))
        school_district = data.get('school_district', data.get('district', 'N/A'))
        owner_occupied = data.get('owner_occupied', 'N/A')
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1976D2 0%, #1565C0 100%); 
                    padding: 20px; border-radius: 15px; margin: 10px 5px; color: white; 
                    box-shadow: 0 6px 20px rgba(25,118,210,0.3); text-align: center;'>
            <h4 style='color: white; margin-bottom: 15px;'>👤 Owner Info</h4>
            <div style='margin-bottom: 12px;'><strong>Owner:</strong><br><span style='font-size: 12px; font-weight: bold;'>{owner}</span></div>
            <div style='margin-bottom: 12px;'><strong>Owner Occupied:</strong><br><span style='font-size: 14px;'>{owner_occupied}</span></div>
            <div><strong>School District:</strong><br><span style='font-size: 11px;'>{school_district}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

# --------------------------
# Sidebar JSON Cards Function
# --------------------------
def display_json_cards_in_sidebar(data):
    """Display comprehensive JSON data in organized cards in the sidebar"""
    
    with st.sidebar:
        st.subheader("📊 Complete Property Data")
        
        # Basic Property Information
        basic_fields = {
            'parcel_id': 'Parcel ID',
            'county_id': 'County ID',
            'county_name': 'County Name',
            'muni_name': 'Municipality',
            'census_place': 'Census Place',
            'state_abbr': 'State',
            'robust_id': 'Robust ID'
        }
        st.markdown(create_json_field_card("🏛️ Basic Information", basic_fields, data), unsafe_allow_html=True)
        
        # Address Information
        address_fields = {
            'address': 'Full Address',
            'addr_number': 'Address Number',
            'addr_street_name': 'Street Name',
            'addr_street_type': 'Street Type',
            'addr_city': 'City',
            'addr_zip': 'ZIP Code',
            'addr_zipplusfour': 'ZIP+4',
            'census_zip': 'Census ZIP'
        }
        st.markdown(create_json_field_card("📍 Address Details", address_fields, data), unsafe_allow_html=True)
        
        # Mailing Address
        mail_fields = {
            'mail_address1': 'Mail Address Line 1',
            'mail_address3': 'Mail Address Line 3',
            'mail_addressnumber': 'Mail Address Number',
            'mail_streetname': 'Mail Street Name',
            'mail_streetnameposttype': 'Mail Street Type',
            'mail_placename': 'Mail Place Name',
            'mail_statename': 'Mail State',
            'mail_zipcode': 'Mail ZIP Code'
        }
        st.markdown(create_json_field_card("📮 Mailing Address", mail_fields, data), unsafe_allow_html=True)
        
        # Owner Information
        owner_fields = {
            'owner': 'Owner Name',
            'owner_occupied': 'Owner Occupied'
        }
        st.markdown(create_json_field_card("👤 Owner Details", owner_fields, data), unsafe_allow_html=True)
        
        # Financial Information
        financial_fields = {
            'trans_date': 'Transaction Date',
            'sale_price': 'Sale Price',
            'mkt_val_land': 'Market Value - Land',
            'mkt_val_bldg': 'Market Value - Building',
            'mkt_val_tot': 'Market Value - Total'
        }
        st.markdown(create_json_field_card("💰 Financial Data", financial_fields, data), unsafe_allow_html=True)
        
        # Property Characteristics
        property_fields = {
            'bldg_sqft': 'Building Sq Ft',
            'land_use_code': 'Land Use Code',
            'land_use_class': 'Land Use Class',
            'acreage': 'Acreage',
            'acreage_calc': 'Calculated Acreage',
            'buildings': 'Number of Buildings',
            'zoning': 'Zoning'
        }
        st.markdown(create_json_field_card("🏠 Property Details", property_fields, data), unsafe_allow_html=True)
        
        # Location Information
        location_fields = {
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'elevation': 'Elevation',
            'ngh_code': 'Neighborhood Code',
            'census_block': 'Census Block',
            'census_tract': 'Census Tract'
        }
        st.markdown(create_json_field_card("🗺️ Location Data", location_fields, data), unsafe_allow_html=True)
        
        # Administrative Information
        admin_fields = {
            'school_district': 'School District',
            'muni_id': 'Municipality ID',
            'usps_residential': 'USPS Classification',
            'last_updated': 'Last Updated',
            'county_link': 'County Link'
        }
        st.markdown(create_json_field_card("🏛️ Administrative", admin_fields, data), unsafe_allow_html=True)
        
        # Land Cover Information
        if 'land_cover' in data and data['land_cover']:
            land_cover_html = """
            <div class='json-card'>
                <h4>🌱 Land Cover</h4>
            """
            for cover_type, percentage in data['land_cover'].items():
                land_cover_html += f"""
                <div class='json-field'>
                    <span class='field-label'>{cover_type}:</span>
                    <span class='field-value'>{percentage}</span>
                </div>
                """
            land_cover_html += "</div>"
            st.markdown(land_cover_html, unsafe_allow_html=True)
        
        # Crop Cover Information
        if 'crop_cover' in data and data['crop_cover']:
            crop_cover_html = """
            <div class='json-card'>
                <h4>🌾 Crop Cover</h4>
            """
            for crop_type, percentage in data['crop_cover'].items():
                crop_cover_html += f"""
                <div class='json-field'>
                    <span class='field-label'>{crop_type}:</span>
                    <span class='field-value'>{percentage}</span>
                </div>
                """
            crop_cover_html += "</div>"
            st.markdown(crop_cover_html, unsafe_allow_html=True)

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
        ['City, State ZIP', f"{data.get('addr_city', data.get('city', 'N/A'))}, OH {data.get('addr_zip', data.get('zip', 'N/A'))}"],
        ['County', data.get('county_name', data.get('county', 'N/A'))],
        ['Owner', data.get('owner', data.get('owner_name', 'N/A'))],
        ['Market Value Total', f"${float(data.get('mkt_val_tot', data.get('market_value', 0))):,.2f}"],
        ['Market Value Land', f"${float(data.get('mkt_val_land', 0)):,.2f}"],
        ['Market Value Building', f"${float(data.get('mkt_val_bldg', 0)):,.2f}"],
        ['Land Use Class', data.get('land_use_class', data.get('property_type', 'N/A'))],
        ['Building Sq Ft', data.get('bldg_sqft', 'N/A')],
        ['Acreage', data.get('acreage', 'N/A')],
        ['School District', data.get('school_district', 'N/A')]
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
    
    # Premium subscription link
    st.markdown("""
    <div class='premium-link'>
        <h4 style='color: white; margin-bottom: 10px;'>🚀 Get Premium Access</h4>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Upgrade to Premium for Unlimited Searches
        </a>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Recent searches
    if st.session_state.search_history:
        st.subheader("🕒 Recent Searches")
        for search in st.session_state.search_history[-5:]:  # Show last 5 searches
            st.text(search)
    
    st.divider()
    
    # Reset usage button
    if st.button("🔄 Reset Usage Count", help="Reset your search count to start over"):
        st.session_state.usage_count = 0
        st.session_state.search_history = []
        st.session_state.cached_results = {}
        st.rerun()

# --------------------------
# Main App UI - Enhanced
# --------------------------
st.title("🏠 Ohio Property Tax Lookup Pro - All 88 Counties")
st.markdown("**Comprehensive Ohio property research with real data integration** | *10 searches per session*")

# Enhanced region information
st.info("🌟 **Now covering ALL 88 Ohio counties** with real property data from ReportAllUSA API for complete statewide coverage.")

# Premium subscription banner
st.markdown("""
<div class='premium-link'>
    <h4 style='color: white; margin-bottom: 10px;'>🚀 Need More Searches?</h4>
    <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
        Get Premium Access for Unlimited Property Searches
    </a>
</div>
""", unsafe_allow_html=True)

# Check usage limit
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset.")
    st.info("💡 **Tip:** Refresh the page or use the reset button in the sidebar to start over.")
    st.markdown("""
    <div class='premium-link'>
        <h4 style='color: white; margin-bottom: 10px;'>🚀 Want Unlimited Access?</h4>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Upgrade to Premium - No Search Limits!
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Main search interface (removed tabs, keeping only parcel search)
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
                        # Display comprehensive JSON cards in sidebar
                        display_json_cards_in_sidebar(results[0])
                    else:
                        st.info(f"Found {len(results)} matching properties:")
                        for i, property_data in enumerate(results[:5]):  # Show top 5 results
                            county_name = property_data.get('county_name', property_data.get('county', 'N/A'))
                            address = property_data.get('address', property_data.get('property_address', 'N/A'))
                            with st.expander(f"Property {i+1}: {address} - {county_name}"):
                                create_enhanced_ohio_property_cards(property_data)
                        
                        # Display JSON cards for first result in sidebar
                        if results:
                            display_json_cards_in_sidebar(results[0])

                    # Enhanced export options with JSON Raw Response
                    st.divider()
                    st.subheader("📥 Export Options")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        pdf_buffer = create_enhanced_ohio_pdf(results[0])
                        st.download_button(
                            "📄 Download PDF Report", 
                            pdf_buffer.getvalue(),
                            file_name=f"ohio_property_report_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", 
                            mime="application/pdf"
                        )
                    with col2:
                        json_str = json.dumps(results[0] if len(results) == 1 else results, indent=2)
                        st.download_button(
                            "📋 Download Property JSON", 
                            json_str,
                            file_name=f"ohio_property_data_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                            mime="application/json"
                        )
                    with col3:
                        # Raw API Response JSON
                        if api_response.get('raw_response'):
                            raw_json_str = json.dumps(api_response['raw_response'], indent=2)
                            st.download_button(
                                "🔧 Download Raw API Response", 
                                raw_json_str,
                                file_name=f"raw_api_response_{parcel_id.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 
                                mime="application/json"
                            )
                    
                    # Display Raw JSON Response
                    if api_response.get('raw_response'):
                        st.divider()
                        st.subheader("🔧 Raw API Response")
                        with st.expander("View Raw JSON Response from ReportAllUSA API", expanded=False):
                            st.json(api_response['raw_response'])
                            
                else:
                    error_msg = api_response.get('message', 'Property not found in Ohio records')
                    st.error(f"❌ {error_msg}")
                    st.info("💡 Please verify the Parcel ID format and try again. You can search multiple parcel IDs by separating them with semicolons (;).")
                    
                    # Show raw response even for errors if available
                    if api_response.get('raw_response'):
                        with st.expander("View Raw API Response", expanded=False):
                            st.json(api_response['raw_response'])
                    
                    # Still increment usage count for failed searches
                    st.session_state.usage_count += 1
                    
            except Exception as e:
                st.error(f"❌ Unexpected error occurred: {str(e)}")
                st.info("💡 Please try again or contact support")
                # Increment usage count for errors too
                st.session_state.usage_count += 1

# Footer with premium link
st.divider()
st.markdown("""
<div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin: 20px 0;'>
    <h4>🚀 Ready for More?</h4>
    <p>Get unlimited property searches, advanced features, and priority support with our Premium subscription.</p>
    <div class='premium-link'>
        <a href='https://aipropiq.com/product/monthsubscription/' target='_blank'>
            Start Your Premium Subscription Today
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# Custom footer
st.markdown("""
<div class='custom-footer'>
    <p>Ohio Property Tax Lookup Pro - Powered by ReportAllUSA API | 
    <a href='https://aipropiq.com/product/monthsubscription/' target='_blank' style='color: #2196F3;'>Get Premium Access</a></p>
</div>
""", unsafe_allow_html=True)

