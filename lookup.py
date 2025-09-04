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
import time

# --------------------------
# Page configuration
# --------------------------
st.set_page_config(
    page_title="Ohio Property Tax Lookup Pro - Professional Edition",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------
# Enhanced CSS Styling
# --------------------------
enhanced_css = """
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    .stApp > footer {visibility: hidden;}
    .st-emotion-cache-1629p8f {display: none;}
    button[title="View fullscreen"] {visibility: hidden;}
    .stActionButton {display: none;}
    
    /* Enhanced styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }
    
    /* Custom metrics */
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Enhanced cards */
    .property-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 25px;
        border-radius: 20px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    
    .json-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .info-card {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        color: #2d3748;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    
    .stats-card {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 5px;
        color: #2d3748;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    
    /* Enhanced footer */
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 12px 0;
        z-index: 999;
        font-weight: 500;
    }
    
    /* JSON syntax highlighting */
    .json-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        line-height: 1.4;
    }
    
    .json-key {
        color: #9cdcfe;
    }
    
    .json-string {
        color: #ce9178;
    }
    
    .json-number {
        color: #b5cea8;
    }
    
    .json-boolean {
        color: #569cd6;
    }
    
    /* Enhanced buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.2);
    }
    
    /* Enhanced selectbox */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
    }
    
    /* Enhanced text input */
    .stTextInput > div > div > input {
        border-radius: 10px;
        border: 2px solid #667eea;
        padding: 10px;
    }
    
    /* Progress bar enhancement */
    .stProgress > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Sidebar enhancements */
    .css-1d391kg {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
    }
    
    /* Tab enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 10px;
        color: #2d3748;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
"""
st.markdown(enhanced_css, unsafe_allow_html=True)

# --------------------------
# Complete Ohio Counties Database (All 88 Counties)
# --------------------------
OHIO_COUNTIES_DATABASE = {
    '01': {'code': '01', 'name': 'Adams County', 'seat': 'West Union', 'population': 27671, 'area_sq_mi': 583.91, 'founded': 1797},
    '02': {'code': '02', 'name': 'Allen County', 'seat': 'Lima', 'population': 100866, 'area_sq_mi': 404.43, 'founded': 1820},
    '03': {'code': '03', 'name': 'Ashland County', 'seat': 'Ashland', 'population': 52420, 'area_sq_mi': 424.37, 'founded': 1846},
    '04': {'code': '04', 'name': 'Ashtabula County', 'seat': 'Jefferson', 'population': 96906, 'area_sq_mi': 702.44, 'founded': 1807},
    '05': {'code': '05', 'name': 'Athens County', 'seat': 'Athens', 'population': 63218, 'area_sq_mi': 506.76, 'founded': 1805},
    '06': {'code': '06', 'name': 'Auglaize County', 'seat': 'Wapakoneta', 'population': 45922, 'area_sq_mi': 401.25, 'founded': 1848},
    '07': {'code': '07', 'name': 'Belmont County', 'seat': 'St. Clairsville', 'population': 64692, 'area_sq_mi': 537.35, 'founded': 1801},
    '08': {'code': '08', 'name': 'Brown County', 'seat': 'Georgetown', 'population': 44292, 'area_sq_mi': 491.76, 'founded': 1818},
    '09': {'code': '09', 'name': 'Butler County', 'seat': 'Hamilton', 'population': 399542, 'area_sq_mi': 467.27, 'founded': 1803},
    '10': {'code': '10', 'name': 'Carroll County', 'seat': 'Carrollton', 'population': 26460, 'area_sq_mi': 394.67, 'founded': 1833},
    '11': {'code': '11', 'name': 'Champaign County', 'seat': 'Urbana', 'population': 38907, 'area_sq_mi': 428.56, 'founded': 1805},
    '12': {'code': '12', 'name': 'Clark County', 'seat': 'Springfield', 'population': 134985, 'area_sq_mi': 399.86, 'founded': 1818},
    '13': {'code': '13', 'name': 'Clermont County', 'seat': 'Batavia', 'population': 214123, 'area_sq_mi': 451.99, 'founded': 1800},
    '14': {'code': '14', 'name': 'Clinton County', 'seat': 'Wilmington', 'population': 42019, 'area_sq_mi': 410.88, 'founded': 1810},
    '15': {'code': '15', 'name': 'Columbiana County', 'seat': 'Lisbon', 'population': 99823, 'area_sq_mi': 532.46, 'founded': 1803},
    '16': {'code': '16', 'name': 'Coshocton County', 'seat': 'Coshocton', 'population': 37003, 'area_sq_mi': 564.07, 'founded': 1810},
    '17': {'code': '17', 'name': 'Crawford County', 'seat': 'Bucyrus', 'population': 41626, 'area_sq_mi': 402.11, 'founded': 1820},
    '18': {'code': '18', 'name': 'Cuyahoga County', 'seat': 'Cleveland', 'population': 1240594, 'area_sq_mi': 458.49, 'founded': 1807},
    '19': {'code': '19', 'name': 'Darke County', 'seat': 'Greenville', 'population': 51462, 'area_sq_mi': 599.80, 'founded': 1809},
    '20': {'code': '20', 'name': 'Defiance County', 'seat': 'Defiance', 'population': 38644, 'area_sq_mi': 411.16, 'founded': 1845},
    '21': {'code': '21', 'name': 'Delaware County', 'seat': 'Delaware', 'population': 237966, 'area_sq_mi': 442.41, 'founded': 1808},
    '22': {'code': '22', 'name': 'Erie County', 'seat': 'Sandusky', 'population': 73841, 'area_sq_mi': 254.88, 'founded': 1838},
    '23': {'code': '23', 'name': 'Fairfield County', 'seat': 'Lancaster', 'population': 167762, 'area_sq_mi': 505.11, 'founded': 1800},
    '24': {'code': '24', 'name': 'Fayette County', 'seat': 'Washington Court House', 'population': 28782, 'area_sq_mi': 406.58, 'founded': 1810},
    '25': {'code': '25', 'name': 'Franklin County', 'seat': 'Columbus', 'population': 1356303, 'area_sq_mi': 539.87, 'founded': 1803},
    '26': {'code': '26', 'name': 'Fulton County', 'seat': 'Wauseon', 'population': 42028, 'area_sq_mi': 406.78, 'founded': 1850},
    '27': {'code': '27', 'name': 'Gallia County', 'seat': 'Gallipolis', 'population': 28886, 'area_sq_mi': 468.78, 'founded': 1803},
    '28': {'code': '28', 'name': 'Geauga County', 'seat': 'Chardon', 'population': 95362, 'area_sq_mi': 403.66, 'founded': 1806},
    '29': {'code': '29', 'name': 'Greene County', 'seat': 'Xenia', 'population': 172347, 'area_sq_mi': 414.88, 'founded': 1803},
    '30': {'code': '30', 'name': 'Guernsey County', 'seat': 'Cambridge', 'population': 38438, 'area_sq_mi': 522.49, 'founded': 1810},
    '31': {'code': '31', 'name': 'Hamilton County', 'seat': 'Cincinnati', 'population': 830639, 'area_sq_mi': 407.36, 'founded': 1790},
    '32': {'code': '32', 'name': 'Hancock County', 'seat': 'Findlay', 'population': 75783, 'area_sq_mi': 531.31, 'founded': 1820},
    '33': {'code': '33', 'name': 'Hardin County', 'seat': 'Kenton', 'population': 30696, 'area_sq_mi': 470.55, 'founded': 1820},
    '34': {'code': '34', 'name': 'Harrison County', 'seat': 'Cadiz', 'population': 14483, 'area_sq_mi': 403.88, 'founded': 1813},
    '35': {'code': '35', 'name': 'Henry County', 'seat': 'Napoleon', 'population': 26883, 'area_sq_mi': 416.85, 'founded': 1820},
    '36': {'code': '36', 'name': 'Highland County', 'seat': 'Hillsboro', 'population': 42713, 'area_sq_mi': 553.05, 'founded': 1805},
    '37': {'code': '37', 'name': 'Hocking County', 'seat': 'Logan', 'population': 28050, 'area_sq_mi': 423.27, 'founded': 1818},
    '38': {'code': '38', 'name': 'Holmes County', 'seat': 'Millersburg', 'population': 44223, 'area_sq_mi': 423.06, 'founded': 1824},
    '39': {'code': '39', 'name': 'Huron County', 'seat': 'Norwalk', 'population': 58565, 'area_sq_mi': 493.07, 'founded': 1815},
    '40': {'code': '40', 'name': 'Jackson County', 'seat': 'Jackson', 'population': 32653, 'area_sq_mi': 420.38, 'founded': 1816},
    '41': {'code': '41', 'name': 'Jefferson County', 'seat': 'Steubenville', 'population': 65441, 'area_sq_mi': 409.78, 'founded': 1797},
    '42': {'code': '42', 'name': 'Knox County', 'seat': 'Mount Vernon', 'population': 62721, 'area_sq_mi': 527.64, 'founded': 1808},
    '43': {'code': '43', 'name': 'Lake County', 'seat': 'Painesville', 'population': 230149, 'area_sq_mi': 228.21, 'founded': 1840},
    '44': {'code': '44', 'name': 'Lawrence County', 'seat': 'Ironton', 'population': 58240, 'area_sq_mi': 455.18, 'founded': 1815},
    '45': {'code': '45', 'name': 'Licking County', 'seat': 'Newark', 'population': 178519, 'area_sq_mi': 686.24, 'founded': 1808},
    '46': {'code': '46', 'name': 'Logan County', 'seat': 'Bellefontaine', 'population': 45657, 'area_sq_mi': 458.48, 'founded': 1817},
    '47': {'code': '47', 'name': 'Lorain County', 'seat': 'Elyria', 'population': 312964, 'area_sq_mi': 492.89, 'founded': 1822},
    '48': {'code': '48', 'name': 'Lucas County', 'seat': 'Toledo', 'population': 431279, 'area_sq_mi': 340.93, 'founded': 1835},
    '49': {'code': '49', 'name': 'Madison County', 'seat': 'London', 'population': 48845, 'area_sq_mi': 465.82, 'founded': 1810},
    '50': {'code': '50', 'name': 'Mahoning County', 'seat': 'Youngstown', 'population': 228614, 'area_sq_mi': 415.27, 'founded': 1846},
    '51': {'code': '51', 'name': 'Marion County', 'seat': 'Marion', 'population': 65359, 'area_sq_mi': 403.78, 'founded': 1824},
    '52': {'code': '52', 'name': 'Medina County', 'seat': 'Medina', 'population': 182470, 'area_sq_mi': 421.28, 'founded': 1812},
    '53': {'code': '53', 'name': 'Meigs County', 'seat': 'Pomeroy', 'population': 22210, 'area_sq_mi': 429.75, 'founded': 1819},
    '54': {'code': '54', 'name': 'Mercer County', 'seat': 'Celina', 'population': 41882, 'area_sq_mi': 463.20, 'founded': 1820},
    '55': {'code': '55', 'name': 'Miami County', 'seat': 'Troy', 'population': 109561, 'area_sq_mi': 407.84, 'founded': 1807},
    '56': {'code': '56', 'name': 'Monroe County', 'seat': 'Woodsfield', 'population': 13385, 'area_sq_mi': 456.28, 'founded': 1813},
    '57': {'code': '57', 'name': 'Montgomery County', 'seat': 'Dayton', 'population': 537309, 'area_sq_mi': 461.68, 'founded': 1803},
    '58': {'code': '58', 'name': 'Morgan County', 'seat': 'McConnelsville', 'population': 13832, 'area_sq_mi': 418.59, 'founded': 1817},
    '59': {'code': '59', 'name': 'Morrow County', 'seat': 'Mount Gilead', 'population': 35318, 'area_sq_mi': 406.06, 'founded': 1848},
    '60': {'code': '60', 'name': 'Muskingum County', 'seat': 'Zanesville', 'population': 86441, 'area_sq_mi': 664.29, 'founded': 1804},
    '61': {'code': '61', 'name': 'Noble County', 'seat': 'Caldwell', 'population': 14115, 'area_sq_mi': 398.87, 'founded': 1851},
    '62': {'code': '62', 'name': 'Ottawa County', 'seat': 'Port Clinton', 'population': 40364, 'area_sq_mi': 255.45, 'founded': 1840},
    '63': {'code': '63', 'name': 'Paulding County', 'seat': 'Paulding', 'population': 18807, 'area_sq_mi': 418.83, 'founded': 1820},
    '64': {'code': '64', 'name': 'Perry County', 'seat': 'New Lexington', 'population': 35408, 'area_sq_mi': 409.92, 'founded': 1817},
    '65': {'code': '65', 'name': 'Pickaway County', 'seat': 'Circleville', 'population': 60539, 'area_sq_mi': 501.79, 'founded': 1810},
    '66': {'code': '66', 'name': 'Pike County', 'seat': 'Waverly', 'population': 27088, 'area_sq_mi': 441.29, 'founded': 1815},
    '67': {'code': '67', 'name': 'Portage County', 'seat': 'Ravenna', 'population': 161791, 'area_sq_mi': 492.33, 'founded': 1807},
    '68': {'code': '68', 'name': 'Preble County', 'seat': 'Eaton', 'population': 40999, 'area_sq_mi': 425.33, 'founded': 1808},
    '69': {'code': '69', 'name': 'Putnam County', 'seat': 'Ottawa', 'population': 34499, 'area_sq_mi': 484.11, 'founded': 1820},
    '70': {'code': '70', 'name': 'Richland County', 'seat': 'Mansfield', 'population': 124936, 'area_sq_mi': 497.04, 'founded': 1813},
    '71': {'code': '71', 'name': 'Ross County', 'seat': 'Chillicothe', 'population': 77093, 'area_sq_mi': 689.49, 'founded': 1798},
    '72': {'code': '72', 'name': 'Sandusky County', 'seat': 'Fremont', 'population': 58896, 'area_sq_mi': 409.45, 'founded': 1820},
    '73': {'code': '73', 'name': 'Scioto County', 'seat': 'Portsmouth', 'population': 74008, 'area_sq_mi': 612.99, 'founded': 1803},
    '74': {'code': '74', 'name': 'Seneca County', 'seat': 'Tiffin', 'population': 55069, 'area_sq_mi': 551.52, 'founded': 1820},
    '75': {'code': '75', 'name': 'Shelby County', 'seat': 'Sidney', 'population': 48230, 'area_sq_mi': 409.28, 'founded': 1819},
    '76': {'code': '76', 'name': 'Stark County', 'seat': 'Canton', 'population': 374853, 'area_sq_mi': 575.99, 'founded': 1808},
    '77': {'code': '77', 'name': 'Summit County', 'seat': 'Akron', 'population': 540428, 'area_sq_mi': 412.97, 'founded': 1840},
    '78': {'code': '78', 'name': 'Trumbull County', 'seat': 'Warren', 'population': 201977, 'area_sq_mi': 618.78, 'founded': 1800},
    '79': {'code': '79', 'name': 'Tuscarawas County', 'seat': 'New Philadelphia', 'population': 92865, 'area_sq_mi': 568.92, 'founded': 1808},
    '80': {'code': '80', 'name': 'Union County', 'seat': 'Marysville', 'population': 62784, 'area_sq_mi': 437.28, 'founded': 1820},
    '81': {'code': '81', 'name': 'Van Wert County', 'seat': 'Van Wert', 'population': 28931, 'area_sq_mi': 409.61, 'founded': 1820},
    '82': {'code': '82', 'name': 'Vinton County', 'seat': 'McArthur', 'population': 12545, 'area_sq_mi': 414.32, 'founded': 1850},
    '83': {'code': '83', 'name': 'Warren County', 'seat': 'Lebanon', 'population': 242337, 'area_sq_mi': 406.86, 'founded': 1803},
    '84': {'code': '84', 'name': 'Washington County', 'seat': 'Marietta', 'population': 59711, 'area_sq_mi': 635.28, 'founded': 1788},
    '85': {'code': '85', 'name': 'Wayne County', 'seat': 'Wooster', 'population': 116903, 'area_sq_mi': 555.29, 'founded': 1808},
    '86': {'code': '86', 'name': 'Williams County', 'seat': 'Bryan', 'population': 36641, 'area_sq_mi': 421.68, 'founded': 1820},
    '87': {'code': '87', 'name': 'Wood County', 'seat': 'Bowling Green', 'population': 132248, 'area_sq_mi': 617.49, 'founded': 1820},
    '88': {'code': '88', 'name': 'Wyandot County', 'seat': 'Upper Sandusky', 'population': 21900, 'area_sq_mi': 406.92, 'founded': 1845}
}

# --------------------------
# ReportAllUSA API Configuration
# --------------------------
REPORTALLUSA_CONFIG = {
    "CLIENT_KEY": st.secrets.get("reportallusa", {}).get("client", ""),
    "BASE_URL": "https://reportallusa.com/api/parcels",
    "API_VERSION": "9",
    "TIMEOUT": 20,
    "MAX_RETRIES": 3
}

# --------------------------
# Enhanced API Functions
# --------------------------
def make_api_request(parcel_id, county_name=None, retry_count=0):
    """
    Enhanced API request with retry logic and comprehensive error handling
    """
    try:
        client_key = REPORTALLUSA_CONFIG["CLIENT_KEY"]
        if not client_key:
            return {
                "status": "ERROR",
                "message": "ReportAllUSA client key not configured. Please add [reportallusa] section with client key to secrets.",
                "error_code": "NO_API_KEY"
            }

        # Build comprehensive request parameters
        params = {
            'client': client_key,
            'v': REPORTALLUSA_CONFIG["API_VERSION"],
            'region': f"{county_name}, Ohio" if county_name else "Ohio",
            'parcel_id': parcel_id,
            'return_buildings': 'true',
            'rpp': 50
        }
        
        # Add request timestamp for tracking
        request_time = datetime.now()
        
        response = requests.get(
            REPORTALLUSA_CONFIG["BASE_URL"], 
            params=params, 
            timeout=REPORTALLUSA_CONFIG["TIMEOUT"]
        )
        
        response_time = datetime.now()
        response_duration = (response_time - request_time).total_seconds()
        
        if response.status_code == 200:
            try:
                data = response.json()
                
                if data.get('status') == 'OK':
                    return {
                        "status": "OK",
                        "results": data.get('results', []),
                        "count": data.get('count', 0),
                        "page": data.get('page', 1),
                        "rpp": data.get('rpp', 10),
                        "query": data.get('query', ''),
                        "api_source": "ReportAllUSA Professional API",
                        "request_params": params,
                        "response_time_seconds": response_duration,
                        "timestamp": request_time.isoformat(),
                        "raw_response": data
                    }
                else:
                    return {
                        "status": "NOT_FOUND",
                        "message": f"No property found with parcel ID '{parcel_id}' in Ohio.",
                        "api_response": data,
                        "request_params": params,
                        "response_time_seconds": response_duration
                    }
                    
            except json.JSONDecodeError:
                return {
                    "status": "ERROR",
                    "message": "Invalid JSON response from API",
                    "raw_response": response.text[:500],
                    "status_code": response.status_code
                }
                
        elif response.status_code == 401:
            return {
                "status": "ERROR",
                "message": "API authentication failed. Please verify your ReportAllUSA client key.",
                "error_code": "AUTH_FAILED",
                "status_code": response.status_code
            }
            
        elif response.status_code == 429:
            if retry_count < REPORTALLUSA_CONFIG["MAX_RETRIES"]:
                time.sleep(2 ** retry_count)  # Exponential backoff
                return make_api_request(parcel_id, county_name, retry_count + 1)
            else:
                return {
                    "status": "ERROR",
                    "message": "API rate limit exceeded. Maximum retries reached.",
                    "error_code": "RATE_LIMIT",
                    "status_code": response.status_code
                }
                
        else:
            return {
                "status": "ERROR",
                "message": f"API returned unexpected status code: {response.status_code}",
                "status_code": response.status_code,
                "response_text": response.text[:500]
            }
            
    except requests.exceptions.Timeout:
        if retry_count < REPORTALLUSA_CONFIG["MAX_RETRIES"]:
            return make_api_request(parcel_id, county_name, retry_count + 1)
        else:
            return {
                "status": "ERROR",
                "message": f"Request timed out after {REPORTALLUSA_CONFIG['TIMEOUT']} seconds. Maximum retries reached.",
                "error_code": "TIMEOUT"
            }
            
    except requests.exceptions.ConnectionError:
        return {
            "status": "ERROR",
            "message": "Unable to connect to ReportAllUSA API. Please check your internet connection.",
            "error_code": "CONNECTION_ERROR"
        }
        
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Unexpected error: {str(e)}",
            "error_code": "UNKNOWN_ERROR",
            "exception_type": type(e).__name__
        }

def search_multiple_parcels(parcel_ids, county_name=None):
    """
    Enhanced multiple parcel search with detailed response tracking
    """
    if isinstance(parcel_ids, str):
        parcel_ids = [pid.strip() for pid in parcel_ids.replace(",", ";").split(";")]
    
    parcel_ids_str = ";".join(parcel_ids)
    
    result = make_api_request(parcel_ids_str, county_name)
    
    if result.get("status") == "OK":
        result["search_type"] = "multiple_parcels"
        result["parcel_count"] = len(parcel_ids)
        result["parcel_ids_searched"] = parcel_ids
    
    return result

def comprehensive_property_search(search_term, county_name=None):
    """
    Main search function with enhanced capabilities
    """
    search_term = search_term.strip()
    
    if not search_term:
        return {
            "status": "ERROR",
            "message": "Please enter a valid parcel ID",
            "error_code": "EMPTY_SEARCH"
        }
    
    # Detect multiple parcel search
    if ";" in search_term or "," in search_term:
        return search_multiple_parcels(search_term, county_name)
    else:
        result = make_api_request(search_term, county_name)
        if result.get("status") == "OK":
            result["search_type"] = "single_parcel"
        return result

# --------------------------
# Session State Management
# --------------------------
if 'usage_count' not in st.session_state:
    st.session_state.usage_count = 0
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'detailed_history' not in st.session_state:
    st.session_state.detailed_history = []
if 'api_stats' not in st.session_state:
    st.session_state.api_stats = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'total_response_time': 0.0
    }

# Configuration
MAX_SEARCHES = 10

# --------------------------
# Enhanced Sidebar with Comprehensive Information
# --------------------------
with st.sidebar:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 15px; margin: 10px 0; color: white; text-align: center;'>
        <h2 style='color: white; margin: 0;'>🏠 Ohio Property Pro</h2>
        <p style='margin: 5px 0 0 0; opacity: 0.9;'>Professional Property Research</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Usage Statistics
    st.subheader("📊 Usage Analytics")
    usage_remaining = MAX_SEARCHES - st.session_state.usage_count
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Searches Left", usage_remaining, delta=None)
    with col2:
        st.metric("Searches Used", st.session_state.usage_count, delta=None)
    
    if usage_remaining > 0:
        progress_value = st.session_state.usage_count / MAX_SEARCHES
        st.progress(progress_value)
        
        if usage_remaining <= 2:
            st.error(f"⚠️ Only {usage_remaining} searches remaining!")
        elif usage_remaining <= 5:
            st.warning(f"⚠️ {usage_remaining} searches left")
        else:
            st.success(f"✅ {usage_remaining} searches available")
    else:
        st.error("❌ Search limit reached")
        st.info("Refresh page to reset")
    
    # API Performance Statistics
    if st.session_state.api_stats['total_requests'] > 0:
        st.divider()
        st.subheader("⚡ API Performance")
        
        success_rate = (st.session_state.api_stats['successful_requests'] / 
                       st.session_state.api_stats['total_requests']) * 100
        avg_response_time = (st.session_state.api_stats['total_response_time'] / 
                           st.session_state.api_stats['total_requests'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Success Rate", f"{success_rate:.1f}%")
        with col2:
            st.metric("Avg Response", f"{avg_response_time:.2f}s")
    
    # Ohio Counties Database
    st.divider()
    st.subheader("🗺️ Ohio Counties Database")
    
    # County statistics
    total_population = sum(county['population'] for county in OHIO_COUNTIES_DATABASE.values())
    total_area = sum(county['area_sq_mi'] for county in OHIO_COUNTIES_DATABASE.values())
    
    st.markdown(f"""
    <div class="stats-card">
        <h4>📈 Ohio Statistics</h4>
        <p><strong>Total Counties:</strong> 88</p>
        <p><strong>Total Population:</strong> {total_population:,}</p>
        <p><strong>Total Area:</strong> {total_area:,.0f} sq mi</p>
        <p><strong>Largest County:</strong> Ashtabula (702.44 sq mi)</p>
        <p><strong>Most Populous:</strong> Franklin ({OHIO_COUNTIES_DATABASE['25']['population']:,})</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Regional breakdown
    with st.expander("🏛️ View Counties by Region"):
        regions = {
            "Northeast Ohio (9 counties)": ['18', '28', '43', '47', '50', '67', '76', '77', '78'],
            "Central Ohio (7 counties)": ['21', '23', '25', '45', '49', '65', '80'],
            "Southwest Ohio (5 counties)": ['09', '13', '31', '68', '83'],
            "Southeast Ohio (13 counties)": ['05', '07', '27', '30', '40', '44', '56', '58', '60', '61', '71', '73', '84'],
            "Northwest Ohio (15 counties)": ['02', '20', '22', '26', '32', '35', '39', '48', '62', '69', '72', '74', '86', '87']
        }
        
        for region, county_codes in regions.items():
            st.markdown(f"**{region}:**")
            for code in county_codes:
                county = OHIO_COUNTIES_DATABASE[code]
                st.write(f"• {county['name']} - {county['seat']} (Pop: {county['population']:,})")
            st.write("")
    
    # Search History
    if st.session_state.search_history:
        st.divider()
        st.subheader("🔍 Recent Searches")
        for i, search in enumerate(st.session_state.search_history[-5:]):
            st.text(f"{i+1}. {search}")
    
    # Reset functionality
    st.divider()
    if st.button("🔄 Reset All Data", type="secondary"):
        st.session_state.usage_count = 0
        st.session_state.search_history = []
        st.session_state.detailed_history = []
        st.session_state.api_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0
        }
        st.rerun()
    
    # API Status
    st.divider()
    st.subheader("🔌 API Connection")
    
    if REPORTALLUSA_CONFIG["CLIENT_KEY"]:
        st.success("✅ ReportAllUSA Connected")
        st.caption("Professional property data enabled")
    else:
        st.error("❌ API Key Required")
        st.caption("Add client key to secrets")
    
    st.info("🌟 **Ohio Statewide Coverage**\nAll 88 counties supported")

# --------------------------
# Enhanced Property Display Functions
# --------------------------
def create_comprehensive_property_display(property_data, api_response):
    """
    Create comprehensive property display with enhanced visualizations
    """
    
    # Main property header
    st.markdown("""
    <div class="property-card">
        <h1 style='color: white; margin-bottom: 20px; text-align: center; font-size: 32px;'>
            🏠 Ohio Property Analysis Report
        </h1>
        <p style='text-align: center; font-size: 18px; opacity: 0.9;'>
            Comprehensive Property Data from ReportAllUSA Professional API
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Key metrics overview
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        parcel_id = property_data.get('parcel_id', property_data.get('parcelid', 'N/A'))
        st.metric("Parcel ID", parcel_id)
    
    with col2:
        county = property_data.get('county', property_data.get('county_name', 'N/A'))
        st.metric("County", county)
    
    with col3:
        market_value = property_data.get('market_value', property_data.get('assessed_value', 0))
        try:
            market_value = float(market_value) if market_value else 0
            st.metric("Market Value", f"${market_value:,.0f}")
        except:
            st.metric("Market Value", "N/A")
    
    with col4:
        annual_tax = property_data.get('annual_tax', property_data.get('tax_amount', 0))
        try:
            annual_tax = float(annual_tax) if annual_tax else 0
            st.metric("Annual Tax", f"${annual_tax:,.0f}")
        except:
            st.metric("Annual Tax", "N/A")
    
    with col5:
        property_type = property_data.get('property_type', property_data.get('land_use', 'N/A'))
        st.metric("Property Type", property_type)
    
    st.divider()
    
    # Detailed property information in organized sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Property Details", 
        "💰 Financial Information", 
        "📍 Location Data", 
        "🏛️ Tax Information", 
        "📊 Complete JSON Response"
    ])
    
    with tab1:
        st.subheader("🏠 Property Characteristics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>🏘️ Basic Information</h4>
            """, unsafe_allow_html=True)
            
            fields = [
                ('Property Address', property_data.get('address', property_data.get('property_address', 'N/A'))),
                ('City', property_data.get('city', property_data.get('municipality', 'N/A'))),
                ('ZIP Code', property_data.get('zip', property_data.get('zip_code', 'N/A'))),
                ('Year Built', property_data.get('year_built', property_data.get('built_year', 'N/A'))),
                ('Lot Size', property_data.get('lot_size', property_data.get('acreage', 'N/A')))
            ]
            
            for label, value in fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🏗️ Building Details</h4>
            """, unsafe_allow_html=True)
            
            building_fields = [
                ('Square Feet', property_data.get('square_feet', property_data.get('sqft', 'N/A'))),
                ('Bedrooms', property_data.get('bedrooms', property_data.get('beds', 'N/A'))),
                ('Bathrooms', property_data.get('bathrooms', property_data.get('baths', 'N/A'))),
                ('Stories', property_data.get('stories', property_data.get('floors', 'N/A'))),
                ('Building Type', property_data.get('building_type', property_data.get('structure_type', 'N/A')))
            ]
            
            for label, value in building_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="info-card">
                <h4>👤 Ownership Information</h4>
            """, unsafe_allow_html=True)
            
            owner_fields = [
                ('Owner Name', property_data.get('owner', property_data.get('owner_name', 'N/A'))),
                ('Mailing Address', property_data.get('mailing_address', property_data.get('owner_address', 'N/A'))),
                ('Owner Occupied', property_data.get('owner_occupied', 'Unknown')),
                ('Deed Date', property_data.get('deed_date', property_data.get('sale_date', 'N/A'))),
                ('Sale Price', property_data.get('sale_price', property_data.get('last_sale_price', 'N/A')))
            ]
            
            for label, value in owner_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.subheader("💰 Financial Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>💵 Assessed Values</h4>
            """, unsafe_allow_html=True)
            
            # Create value breakdown
            land_value = property_data.get('land_value', property_data.get('lot_value', 0))
            building_value = property_data.get('building_value', property_data.get('improvement_value', 0))
            total_value = property_data.get('total_value', property_data.get('assessed_value_total', 0))
            
            try:
                land_value = float(land_value) if land_value else 0
                building_value = float(building_value) if building_value else 0
                total_value = float(total_value) if total_value else 0
                
                st.write(f"**Land Value:** ${land_value:,.2f}")
                st.write(f"**Building Value:** ${building_value:,.2f}")
                st.write(f"**Total Assessed:** ${total_value:,.2f}")
                
                if total_value > 0:
                    land_pct = (land_value / total_value) * 100
                    building_pct = (building_value / total_value) * 100
                    st.write(f"**Land %:** {land_pct:.1f}%")
                    st.write(f"**Building %:** {building_pct:.1f}%")
                    
            except:
                st.write("Value data not available")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🏛️ Tax Analysis</h4>
            """, unsafe_allow_html=True)
            
            tax_fields = [
                ('Annual Tax', property_data.get('annual_tax', property_data.get('tax_amount', 'N/A'))),
                ('Tax Year', property_data.get('tax_year', datetime.now().year)),
                ('Tax Rate', property_data.get('tax_rate', property_data.get('millage_rate', 'N/A'))),
                ('School District', property_data.get('school_district', property_data.get('district', 'N/A'))),
                ('Tax Status', property_data.get('tax_status', property_data.get('delinquent_status', 'N/A')))
            ]
            
            for label, value in tax_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.subheader("📍 Geographic Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>🗺️ Location Details</h4>
            """, unsafe_allow_html=True)
            
            location_fields = [
                ('Full Address', property_data.get('full_address', property_data.get('address', 'N/A'))),
                ('Street Number', property_data.get('street_number', property_data.get('house_number', 'N/A'))),
                ('Street Name', property_data.get('street_name', 'N/A')),
                ('City', property_data.get('city', property_data.get('municipality', 'N/A'))),
                ('State', property_data.get('state', 'Ohio')),
                ('ZIP Code', property_data.get('zip_code', property_data.get('postal_code', 'N/A'))),
                ('County', property_data.get('county', property_data.get('county_name', 'N/A')))
            ]
            
            for label, value in location_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🌐 Coordinates & Boundaries</h4>
            """, unsafe_allow_html=True)
            
            # Coordinates
            lat = property_data.get('latitude', property_data.get('lat'))
            lng = property_data.get('longitude', property_data.get('lng', property_data.get('lon')))
            
            if lat and lng:
                st.write(f"**Latitude:** {lat}")
                st.write(f"**Longitude:** {lng}")
                st.write(f"**Coordinates:** {lat}, {lng}")
            else:
                st.write("**Coordinates:** Not available")
            
            # Additional geographic data
            geo_fields = [
                ('Census Tract', property_data.get('census_tract', 'N/A')),
                ('Census Block', property_data.get('census_block', 'N/A')),
                ('School District', property_data.get('school_district', 'N/A')),
                ('Fire District', property_data.get('fire_district', 'N/A')),
                ('Police District', property_data.get('police_district', 'N/A'))
            ]
            
            for label, value in geo_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab4:
        st.subheader("🏛️ Comprehensive Tax Information")
        
        # Tax breakdown
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div class="info-card">
                <h4>💸 Current Tax Information</h4>
            """, unsafe_allow_html=True)
            
            current_tax_fields = [
                ('Tax Year', property_data.get('tax_year', datetime.now().year)),
                ('Annual Tax', property_data.get('annual_tax', property_data.get('tax_amount', 'N/A'))),
                ('Tax Status', property_data.get('tax_status', 'N/A')),
                ('Payment Status', property_data.get('payment_status', 'N/A')),
                ('Due Date', property_data.get('tax_due_date', 'N/A'))
            ]
            
            for label, value in current_tax_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="info-card">
                <h4>🏫 Tax Districts</h4>
            """, unsafe_allow_html=True)
            
            district_fields = [
                ('School District', property_data.get('school_district', 'N/A')),
                ('Library District', property_data.get('library_district', 'N/A')),
                ('Fire District', property_data.get('fire_district', 'N/A')),
                ('Park District', property_data.get('park_district', 'N/A')),
                ('Special Districts', property_data.get('special_districts', 'N/A'))
            ]
            
            for label, value in district_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="info-card">
                <h4>📊 Tax Calculations</h4>
            """, unsafe_allow_html=True)
            
            calc_fields = [
                ('Millage Rate', property_data.get('millage_rate', property_data.get('tax_rate', 'N/A'))),
                ('Effective Rate', property_data.get('effective_tax_rate', 'N/A')),
                ('Exemptions', property_data.get('exemptions', property_data.get('tax_exemptions', 'N/A'))),
                ('Deductions', property_data.get('deductions', 'N/A')),
                ('Net Taxable', property_data.get('net_taxable_value', 'N/A'))
            ]
            
            for label, value in calc_fields:
                st.write(f"**{label}:** {value}")
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab5:
        st.subheader("📊 Complete API Response")
        
        st.markdown("""
        <div class="json-card">
            <h3 style='color: white; margin-bottom: 15px;'>🔍 Full JSON Response from ReportAllUSA API</h3>
            <p style='opacity: 0.9;'>Complete raw data returned by the API for this property search</p>
        </div>
        """, unsafe_allow_html=True)
        
        # API metadata
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Response Time", f"{api_response.get('response_time_seconds', 0):.2f}s")
        with col2:
            st.metric("Records Found", api_response.get('count', 0))
        with col3:
            st.metric("API Version", api_response.get('request_params', {}).get('v', 'N/A'))
        with col4:
            st.metric("Search Type", api_response.get('search_type', 'single_parcel'))
        
        # Request parameters
        st.subheader("📤 Request Parameters")
        if 'request_params' in api_response:
            st.json(api_response['request_params'])
        
        # Full property data
        st.subheader("📥 Property Data Response")
        st.json(property_data)
        
        # Complete API response
        st.subheader("🔧 Complete API Response")
        if 'raw_response' in api_response:
            st.json(api_response['raw_response'])
        else:
            st.json(api_response)
        
        # Download options for JSON
        st.subheader("💾 Download Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            property_json = json.dumps(property_data, indent=2)
            st.download_button(
                "📄 Download Property Data",
                property_json,
                file_name=f"property_data_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            full_response_json = json.dumps(api_response.get('raw_response', api_response), indent=2)
            st.download_button(
                "📋 Download Full Response",
                full_response_json,
                file_name=f"full_api_response_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col3:
            # Create comprehensive report
            comprehensive_data = {
                "search_metadata": {
                    "timestamp": api_response.get('timestamp'),
                    "response_time": api_response.get('response_time_seconds'),
                    "search_type": api_response.get('search_type'),
                    "api_source": api_response.get('api_source')
                },
                "request_parameters": api_response.get('request_params', {}),
                "property_data": property_data,
                "full_api_response": api_response.get('raw_response', api_response)
            }
            
            comprehensive_json = json.dumps(comprehensive_data, indent=2)
            st.download_button(
                "📊 Download Comprehensive Report",
                comprehensive_json,
                file_name=f"comprehensive_report_{parcel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def create_enhanced_pdf_report(property_data, api_response):
    """
    Create enhanced PDF report with comprehensive property information
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    # Enhanced title
    title_style = ParagraphStyle(
        'EnhancedTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.darkblue,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    story.append(Paragraph("Ohio Property Analysis Report", title_style))
    story.append(Paragraph("Professional Property Research via ReportAllUSA API", styles['Normal']))
    story.append(Spacer(1, 20))

    # Property summary table
    parcel_id = property_data.get('parcel_id', property_data.get('parcelid', 'N/A'))
    
    summary_data = [
        ['Property Information', 'Details', 'Additional Data'],
        ['Parcel ID', parcel_id, f"Search Date: {datetime.now().strftime('%Y-%m-%d')}"],
        ['Property Address', property_data.get('address', 'N/A'), f"API Response Time: {api_response.get('response_time_seconds', 0):.2f}s"],
        ['City, State ZIP', f"{property_data.get('city', 'N/A')}, OH {property_data.get('zip', 'N/A')}", f"Records Found: {api_response.get('count', 0)}"],
        ['County', property_data.get('county', 'N/A'), f"Search Type: {api_response.get('search_type', 'N/A')}"],
        ['Owner', property_data.get('owner', 'N/A'), f"API Source: {api_response.get('api_source', 'N/A')}"],
        ['Market Value', f"${float(property_data.get('market_value', 0)):,.2f}", f"Year Built: {property_data.get('year_built', 'N/A')}"],
        ['Annual Tax', f"${float(property_data.get('annual_tax', 0)):,.2f}", f"Property Type: {property_data.get('property_type', 'N/A')}"],
        ['Lot Size', property_data.get('lot_size', 'N/A'), f"Square Feet: {property_data.get('square_feet', 'N/A')}"],
        ['School District', property_data.get('school_district', 'N/A'), f"Tax Year: {property_data.get('tax_year', 'N/A')}"]
    ]
    
    table = Table(summary_data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.navy),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,0),12),
        ('BOTTOMPADDING',(0,0),(-1,0),12),
        ('BACKGROUND',(0,1),(-1,-1),colors.beige),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('FONTSIZE',(0,1),(-1,-1),10)
    ]))
    story.append(table)
    story.append(Spacer(1,30))

    # Additional sections
    story.append(Paragraph("Detailed Property Analysis", styles['Heading2']))
    story.append(Spacer(1,10))
    
    # Financial information
    financial_data = [
        ['Financial Information', 'Value'],
        ['Land Value', f"${float(property_data.get('land_value', 0)):,.2f}"],
        ['Building Value', f"${float(property_data.get('building_value', 0)):,.2f}"],
        ['Total Assessed Value', f"${float(property_data.get('total_value', 0)):,.2f}"],
        ['Annual Property Tax', f"${float(property_data.get('annual_tax', 0)):,.2f}"],
        ['Tax Rate/Millage', property_data.get('tax_rate', 'N/A')],
        ['Effective Tax Rate', property_data.get('effective_tax_rate', 'N/A')]
    ]
    
    financial_table = Table(financial_data, colWidths=[3*inch, 2*inch])
    financial_table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('FONTNAME',(0,0),(0,-1),'Helvetica-Bold'),
        ('ALIGN',(0,0),(-1,-1),'LEFT'),
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('FONTSIZE',(0,0),(-1,-1),10)
    ]))
    story.append(financial_table)
    story.append(Spacer(1,20))

    # API information
    story.append(Paragraph("Data Source Information", styles['Heading2']))
    story.append(Paragraph(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Data source: {api_response.get('api_source', 'ReportAllUSA API')}", styles['Normal']))
    story.append(Paragraph(f"API response time: {api_response.get('response_time_seconds', 0):.2f} seconds", styles['Normal']))
    story.append(Paragraph(f"Search type: {api_response.get('search_type', 'Property lookup')}", styles['Normal']))
    story.append(Paragraph("Coverage: Ohio statewide property database", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --------------------------
# Main Application Interface
# --------------------------
st.markdown("""
<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            padding: 30px; border-radius: 25px; margin: 20px 0; color: white; text-align: center;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);'>
    <h1 style='color: white; margin-bottom: 15px; font-size: 42px; font-weight: 700;'>
        🏠 Ohio Property Tax Lookup Pro
    </h1>
    <h2 style='color: white; margin-bottom: 10px; font-size: 24px; font-weight: 400; opacity: 0.9;'>
        Professional Edition - Parcel Number Search Only
    </h2>
    <p style='font-size: 18px; opacity: 0.8; margin: 0;'>
        Comprehensive Ohio property research with ReportAllUSA Professional API | 10 searches per session
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced feature highlights
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="stats-card">
        <h4>🗺️ Complete Coverage</h4>
        <p><strong>All 88 Ohio Counties</strong></p>
        <p>Statewide property database access</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="stats-card">
        <h4>🔍 Parcel Search Only</h4>
        <p><strong>Professional Focus</strong></p>
        <p>Precise parcel ID based searches</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="stats-card">
        <h4>📊 Full JSON Response</h4>
        <p><strong>Complete Data Access</strong></p>
        <p>Raw API response included</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="stats-card">
        <h4>⚡ Real-Time Data</h4>
        <p><strong>ReportAllUSA API</strong></p>
        <p>Live property information</p>
    </div>
    """, unsafe_allow_html=True)

# Usage limit check
if st.session_state.usage_count >= MAX_SEARCHES:
    st.error("❌ Maximum usage reached (10 searches). Please refresh the page to reset your session.")
    st.info("💡 **Tip:** Use the reset button in the sidebar or refresh your browser to start a new session.")
    st.stop()

# Enhanced search interface
st.markdown("""
<div class="info-card">
    <h2>🔍 Professional Parcel Number Search</h2>
    <p>Enter Ohio parcel numbers for comprehensive property analysis. Supports single or multiple parcel searches across all 88 Ohio counties.</p>
</div>
""", unsafe_allow_html=True)

# Search form
col1, col2, col3 = st.columns([5, 2, 1])

with col1:
    parcel_input = st.text_input(
        "Enter Ohio Parcel Number(s)",
        placeholder="e.g., 44327012 or multiple: 44327012;44327010;44327013",
        help="Enter single parcel ID or multiple IDs separated by semicolons. Searches entire Ohio state automatically.",
        key="parcel_search"
    )

with col2:
    county_filter = st.selectbox(
        "County Filter (Optional)",
        ["All of Ohio (Recommended)"] + [f"{county['name']}" for county in OHIO_COUNTIES_DATABASE.values()],
        help="Leave as 'All of Ohio' for best results, or select specific county to narrow search"
    )

with col3:
    search_button = st.button(
        "🔍 Search Properties",
        type="primary",
        disabled=(st.session_state.usage_count >= MAX_SEARCHES),
        use_container_width=True
    )

# Search execution
if search_button and parcel_input:
    if st.session_state.usage_count >= MAX_SEARCHES:
        st.error("❌ Search limit reached!")
    elif not parcel_input.strip():
        st.error("❌ Please enter a valid parcel number")
    else:
        with st.spinner("🔍 Searching Ohio statewide property database..."):
            try:
                # Determine county filter
                county_name = None
                if county_filter != "All of Ohio (Recommended)":
                    county_name = county_filter
                
                # Execute search
                search_start_time = time.time()
                api_response = comprehensive_property_search(parcel_input, county_name)
                search_end_time = time.time()
                
                # Update API statistics
                st.session_state.api_stats['total_requests'] += 1
                if 'response_time_seconds' in api_response:
                    st.session_state.api_stats['total_response_time'] += api_response['response_time_seconds']
                
                if api_response.get('status') == "OK" and api_response.get('results'):
                    # Update usage and history
                    st.session_state.usage_count += 1
                    st.session_state.api_stats['successful_requests'] += 1
                    
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    search_scope = f" - {county_filter}" if county_filter != "All of Ohio (Recommended)" else " - Statewide"
                    search_entry = f"{parcel_input}{search_scope} - {timestamp}"
                    st.session_state.search_history.append(search_entry)
                    
                    # Store detailed history
                    detailed_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'parcel_input': parcel_input,
                        'county_filter': county_filter,
                        'results_count': api_response.get('count', 0),
                        'response_time': api_response.get('response_time_seconds', 0),
                        'search_type': api_response.get('search_type', 'unknown')
                    }
                    st.session_state.detailed_history.append(detailed_entry)
                    
                    # Success message with enhanced details
                    total_found = api_response.get('count', len(api_response.get('results', [])))
                    response_time = api_response.get('response_time_seconds', 0)
                    
                    st.success(f"""
                    ✅ **Search Successful!** Found {total_found} property record(s) 
                    | Search {st.session_state.usage_count}/{MAX_SEARCHES} 
                    | Response time: {response_time:.2f}s 
                    | Source: {api_response.get('api_source', 'ReportAllUSA')}
                    """)
                    
                    # Display results
                    results = api_response['results']
                    
                    if len(results) == 1:
                        # Single property result
                        create_comprehensive_property_display(results[0], api_response)
                        
                        # Enhanced export options
                        st.divider()
                        st.markdown("""
                        <div class="info-card">
                            <h3>📥 Export & Download Options</h3>
                            <p>Download comprehensive property reports and data in multiple formats</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            pdf_buffer = create_enhanced_pdf_report(results[0], api_response)
                            st.download_button(
                                "📄 Download PDF Report",
                                pdf_buffer.getvalue(),
                                file_name=f"ohio_property_report_{parcel_input.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        
                        with col2:
                            property_json = json.dumps(results[0], indent=2)
                            st.download_button(
                                "📋 Download Property JSON",
                                property_json,
                                file_name=f"property_data_{parcel_input.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                        
                        with col3:
                            full_response_json = json.dumps(api_response, indent=2)
                            st.download_button(
                                "🔧 Download Full API Response",
                                full_response_json,
                                file_name=f"full_api_response_{parcel_input.replace(';', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json",
                                use_container_width=True
                            )
                    
                    else:
                        # Multiple property results
                        st.info(f"🏠 Found {len(results)} matching properties. Displaying detailed information for each:")
                        
                        for i, property_data in enumerate(results[:10]):  # Limit to 10 results for performance
                            county_name = property_data.get('county', property_data.get('county_name', 'N/A'))
                            address = property_data.get('address', property_data.get('property_address', 'N/A'))
                            parcel_id = property_data.get('parcel_id', property_data.get('parcelid', 'N/A'))
                            
                            with st.expander(f"🏠 Property {i+1}: {address} - {county_name} (Parcel: {parcel_id})", expanded=(i==0)):
                                create_comprehensive_property_display(property_data, api_response)
                
                else:
                    # Handle errors and not found cases
                    st.session_state.usage_count += 1
                    st.session_state.api_stats['failed_requests'] += 1
                    
                    error_msg = api_response.get('message', 'Property not found in Ohio records')
                    error_code = api_response.get('error_code', 'UNKNOWN')
                    
                    st.error(f"❌ **Search Failed:** {error_msg}")
                    
                    if error_code == "NO_API_KEY":
                        st.info("🔑 **Setup Required:** Please configure your ReportAllUSA client key in the secrets configuration.")
                    elif error_code == "NOT_FOUND":
                        st.info("💡 **Search Tips:** Verify the parcel ID format. Different Ohio counties use different formats. You can search multiple parcel IDs by separating them with semicolons (;).")
                    elif error_code == "RATE_LIMIT":
                        st.info("⏱️ **Rate Limit:** The API is temporarily limiting requests. Please wait a moment before trying again.")
                    else:
                        st.info("🔧 **Troubleshooting:** Please verify your input and try again. Check the API configuration help in the sidebar for more information.")
                    
                    # Show error details for debugging
                    with st.expander("🔍 Error Details (for debugging)"):
                        st.json(api_response)
                        
            except Exception as e:
                st.session_state.usage_count += 1
                st.session_state.api_stats['failed_requests'] += 1
                
                st.error(f"❌ **Unexpected Error:** {str(e)}")
                st.info("💡 Please try again or contact support if the problem persists.")
                
                # Show exception details
                with st.expander("🔍 Technical Details"):
                    st.write(f"**Exception Type:** {type(e).__name__}")
                    st.write(f"**Error Message:** {str(e)}")

# Enhanced parcel ID format examples
st.divider()
st.markdown("""
<div class="info-card">
    <h3>📋 Ohio Parcel ID Format Examples</h3>
    <p>Different Ohio counties use various parcel ID formats. Here are examples from major counties:</p>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    **Northeast Ohio:**
    - **Cuyahoga County:** 44327012, 44327010
    - **Summit County:** 12-34567, 12-34568  
    - **Lake County:** 123-456-789, 123-456-790
    """)

with col2:
    st.markdown("""
    **Central Ohio:**
    - **Franklin County:** 010-123456-00, 010-123457-00
    - **Delaware County:** 308-123456-00, 308-123457-00
    - **Fairfield County:** 141-123456-000, 141-123457-000
    """)

with col3:
    st.markdown("""
    **Southwest Ohio:**
    - **Hamilton County:** 123-0001-0001-00, 123-0001-0002-00
    - **Butler County:** 123456789, 123456790
    - **Warren County:** 12-123-45-678-900, 12-123-45-678-901
    """)

st.markdown("""
**💡 Multiple Search Example:** `44327012;010-123456-00;123-0001-0001-00`

**🔍 Search Tips:**
- Use exact parcel ID formats as they appear in county records
- Multiple parcels can be searched simultaneously using semicolon separation
- Leave county filter as "All of Ohio" for best results across different formats
- Each search (single or multiple parcels) counts as one usage toward your 10-search limit
""")

# Enhanced API configuration help
st.divider()
with st.expander("⚙️ ReportAllUSA API Configuration & Professional Setup"):
    st.markdown("""
    ### 🔧 Professional API Configuration
    
    This application uses the **ReportAllUSA Professional API** for comprehensive Ohio property data access.
    
    #### 🔑 API Setup Instructions
    
    **Step 1: Obtain API Access**
    - Visit [ReportAllUSA](https://reportallusa.com/) to sign up for professional API access
    - Choose a plan that meets your property research needs
    - Obtain your unique client key from your account dashboard
    
    **Step 2: Configure Streamlit Secrets**
    Add your client key to your Streamlit secrets configuration:
    
    ```toml
    # In your .streamlit/secrets.toml file
    [reportallusa]
    client = "your_client_key_here"
    ```
    
    #### 🌐 Professional API Capabilities
    
    **Coverage & Scope:**
    - ✅ All 88 Ohio counties supported
    - ✅ Statewide property database access
    - ✅ Real-time data from official sources
    - ✅ Historical property information
    - ✅ Building footprint data when available
    
    **Search Features:**
    - 🔍 Single parcel ID searches
    - 🔍 Multiple parcel batch searches (semicolon separated)
    - 🔍 County-specific filtering options
    - 🔍 Comprehensive property data retrieval
    - 🔍 Building polygon geometry data
    
    **Data Types Included:**
    - 📊 Property identification and location details
    - 📊 Current and historical assessment values
    - 📊 Tax records and payment information
    - 📊 Property characteristics and building details
    - 📊 Owner information and mailing addresses
    - 📊 Geographic coordinates and boundaries
    - 📊 Zoning and land use classifications
    - 📊 School and tax district information
    
    #### 📈 Usage Guidelines & Best Practices
    
    **Session Management:**
    - Each user session allows 10 property searches
    - Multiple parcel searches count as one search
    - Failed searches still count toward the limit
    - Refresh the page to reset your search count
    - Use the sidebar reset button to clear all data
    
    **Search Optimization:**
    - Use exact parcel ID formats from county records
    - Leave county filter as "All of Ohio" for maximum compatibility
    - Batch multiple parcels in a single search when possible
    - Verify parcel ID formats if searches fail
    
    **Performance Monitoring:**
    - API response times are tracked and displayed
    - Success rates are calculated and shown in sidebar
    - Request parameters are logged for debugging
    - Complete API responses are available for download
    
    #### 🆘 Troubleshooting Guide
    
    **Common Issues & Solutions:**
    
    **"API key not configured"**
    - ✅ Add `[reportallusa]` section with `client = "your_key"` to secrets
    - ✅ Verify the client key is correct and active
    - ✅ Check that secrets.toml file is properly formatted
    
    **"Property not found"**
    - ✅ Verify parcel ID format matches county standards
    - ✅ Try searching without county filter (use "All of Ohio")
    - ✅ Check for typos or extra characters in parcel ID
    - ✅ Confirm the property exists in Ohio
    
    **"Rate limit exceeded"**
    - ✅ Wait 30-60 seconds before retrying
    - ✅ The application automatically retries with exponential backoff
    - ✅ Consider upgrading your API plan for higher limits
    
    **"Request timeout"**
    - ✅ Check your internet connection
    - ✅ The application automatically retries failed requests
    - ✅ Large batch searches may take longer to process
    
    #### 🔗 Additional Resources
    
    **API Documentation:**
    - [ReportAllUSA API Docs](https://reportallusa.com/api-documentation)
    - [Ohio Property Data Guide](https://reportallusa.com/ohio-property-guide)
    - [Parcel ID Format Reference](https://reportallusa.com/parcel-formats)
    
    **Support & Contact:**
    - Technical Support: [ReportAllUSA Support](https://reportallusa.com/support)
    - API Status Page: [ReportAllUSA Status](https://status.reportallusa.com)
    - Community Forum: [ReportAllUSA Community](https://community.reportallusa.com)
    
    #### 💼 Professional Features
    
    This application provides professional-grade features for property research:
    
    - **Complete JSON Access:** Full API response data available
    - **Batch Processing:** Multiple parcel searches in single request
    - **Performance Monitoring:** Response time and success rate tracking
    - **Export Options:** PDF reports, JSON data, and comprehensive reports
    - **Error Handling:** Automatic retries and detailed error reporting
    - **Usage Analytics:** Session tracking and search history
    - **County Database:** Complete Ohio county information and statistics
    """)

# Enhanced usage information and footer
st.divider()

# Current session status
remaining = MAX_SEARCHES - st.session_state.usage_count
col1, col2, col3 = st.columns(3)

with col1:
    if remaining <= 2 and remaining > 0:
        st.warning(f"⚠️ **{remaining} searches remaining** in this session!")
    elif remaining == 0:
        st.error("❌ **No searches remaining.** Refresh page to reset.")
    else:
        st.success(f"✅ **{remaining} searches available** - Professional Ohio property data ready!")

with col2:
    if st.session_state.api_stats['total_requests'] > 0:
        success_rate = (st.session_state.api_stats['successful_requests'] / 
                       st.session_state.api_stats['total_requests']) * 100
        st.info(f"📊 **API Success Rate:** {success_rate:.1f}%")

with col3:
    st.info(f"🕒 **Session Started:** {datetime.now().strftime('%H:%M:%S')}")

# Enhanced footer
st.markdown(
    f"""
    <div class="custom-footer">
        🏠 Ohio Property Tax Lookup Pro - Professional Edition | 
        ReportAllUSA API Integration | 
        Searches: {st.session_state.usage_count}/{MAX_SEARCHES} | 
        All 88 Ohio Counties | 
        Session: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
        <a href="https://reportallusa.com/" target="_blank" style="color: #ffd700; text-decoration: none; font-weight: 600;">
            ⭐ Powered by ReportAllUSA Professional API
        </a>
    </div>
    """, 
    unsafe_allow_html=True
)

