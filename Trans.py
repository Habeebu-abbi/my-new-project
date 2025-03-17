import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from authlib.integrations.requests_client import OAuth2Session
from io import BytesIO
import matplotlib.pyplot as plt

# 🔹 Google OAuth Credentials (Loaded from Streamlit Secrets)
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]

# 🔹 Allowed Emails (Loaded from Streamlit Secrets)
ALLOWED_EMAILS = st.secrets["ALLOWED_EMAILS"].split(",")  # Convert to list

# 🔹 Metabase credentials (Loaded from Streamlit Secrets)
METABASE_URL = st.secrets["METABASE_URL"]
METABASE_USERNAME = st.secrets["METABASE_USERNAME"]
METABASE_PASSWORD = st.secrets["METABASE_PASSWORD"]

# Initialize OAuth2 session
oauth = OAuth2Session(
    CLIENT_ID, CLIENT_SECRET, redirect_uri=REDIRECT_URI, scope=["openid", "email", "profile"]
)

# Function to handle authentication
def login():
    auth_url, state = oauth.create_authorization_url("https://accounts.google.com/o/oauth2/auth")
    st.session_state["oauth_state"] = state
    st.markdown(f"[Login with Google]({auth_url})")

def fetch_token():
    if "code" in st.query_params:
        try:
            # Construct the full authorization response URL
            authorization_response = f"{REDIRECT_URI}?{requests.compat.urlencode(st.query_params)}"
            
            # Fetch the token using the full authorization response
            token = oauth.fetch_token(
                "https://oauth2.googleapis.com/token",
                authorization_response=authorization_response,
                grant_type="authorization_code"  # Explicitly specify the grant type
            )
            
            # Fetch user info
            user_info = oauth.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
            st.session_state["user"] = user_info
            return user_info
        except Exception as e:
            st.error(f"❌ OAuth Error: {e}")
            st.error(f"Query Params: {st.query_params}")
            return None
    return None

# 🔹 Check if user is authenticated
if "user" not in st.session_state:
    st.session_state["user"] = None

if not st.session_state["user"]:
    login()
    user_info = fetch_token()
else:
    user_info = st.session_state["user"]

# 🔹 Restrict access to specific emails
if user_info:
    email = user_info.get("email", "")
    st.write(f"Authenticated Email: {email}")  # Debugging: Print the email
    
    # Check if the email is in the allowed list
    if email in ALLOWED_EMAILS:
        st.success(f"✅ Welcome, {email}!")
    else:
        st.error(f"❌ Access Denied! Your email ({email}) is not allowed.")
        st.stop()
else:
    st.warning("⚠️ Please log in to access the app.")
    st.stop()

# 🔹 Fetch data from Metabase
def get_metabase_session():
    login_url = f"{METABASE_URL}/api/session"
    credentials = {"username": METABASE_USERNAME, "password": METABASE_PASSWORD}

    try:
        response = requests.post(login_url, json=credentials)
        response.raise_for_status()
        return response.json().get("id")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Metabase Authentication Failed! Error: {e}")
        return None

def fetch_metabase_data(query_id):
    session_token = get_metabase_session()
    if not session_token:
        return None

    query_url = f"{METABASE_URL}/api/card/{query_id}/query/json"
    headers = {"X-Metabase-Session": session_token}

    try:
        response = requests.post(query_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Debugging: Print the raw data
        st.write("Raw Data from Metabase:")
        st.write(data)
        
        # Check if the response contains an error
        if "error" in data:
            st.error(f"❌ Metabase Query Error: {data['error']}")
            return None
        
        # Ensure the data is in the expected format
        if not isinstance(data, dict) or not all(isinstance(v, list) for v in data.values()):
            st.error("❌ Unexpected data format returned from Metabase.")
            return None
        
        # Ensure all columns have the same length
        max_length = max(len(v) for v in data.values())
        for key in data:
            data[key] = data[key] + [None] * (max_length - len(data[key]))
        
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

# Function to convert DataFrame to PNG
def dataframe_to_image(df, title="Table"):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.axis('tight')
    ax.axis('off')

    # Set the title
    ax.set_title(title, fontsize=14, fontweight="bold", pad=20)

    # Create the table
    table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

    # Adjust the table properties
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.auto_set_column_width([i for i in range(len(df.columns))])

    # Save the figure to a BytesIO object
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=300)
    img_buffer.seek(0)
    return img_buffer

# Streamlit UI
st.title("📊 Metabase Data Viewer & Driver Analysis")
st.sidebar.header("🔍 Query Settings")

# User inputs Query IDs
query_id_1 = st.sidebar.number_input("Enter Metabase Query ID (First Dataset)", min_value=1, value=3021, step=1)
query_id_2 = st.sidebar.number_input("Enter Metabase Query ID (Second Dataset)", min_value=1, value=3023, step=1)
query_id_3 = st.sidebar.number_input("Enter Metabase Query ID (Third Dataset)", min_value=1, value=3036, step=1)
query_id_4 = st.sidebar.number_input("Enter Metabase Query ID (Fourth Dataset)", min_value=1, value=3003, step=1)

# Fetch data for each query ID
df_1 = fetch_metabase_data(query_id_1)
df_2 = fetch_metabase_data(query_id_2)
df_3 = fetch_metabase_data(query_id_3)
df_4 = fetch_metabase_data(query_id_4)

# Display data for each query ID
if df_1 is not None:
    st.write("### 🔹 Data from Query ID 1")
    st.dataframe(df_1)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_1, title="Data from Query ID 1")

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="query_1_data.png",
        mime="image/png"
    )

    # Example: Plotting with Plotly
    if not df_1.empty:
        st.write("### Example Plot for Query ID 1")
        fig = px.bar(df_1, x=df_1.columns[0], y=df_1.columns[1], title="Sample Bar Chart for Query ID 1")
        st.plotly_chart(fig)
else:
    st.warning(f"⚠️ No data available for Query ID {query_id_1}.")

if df_2 is not None:
    st.write("### 🔹 Data from Query ID 2")
    st.dataframe(df_2)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_2, title="Data from Query ID 2")

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="query_2_data.png",
        mime="image/png"
    )

    # Example: Plotting with Plotly
    if not df_2.empty:
        st.write("### Example Plot for Query ID 2")
        fig = px.bar(df_2, x=df_2.columns[0], y=df_2.columns[1], title="Sample Bar Chart for Query ID 2")
        st.plotly_chart(fig)
else:
    st.warning(f"⚠️ No data available for Query ID {query_id_2}.")

if df_3 is not None:
    st.write("### 🔹 Data from Query ID 3")
    st.dataframe(df_3)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_3, title="Data from Query ID 3")

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="query_3_data.png",
        mime="image/png"
    )

    # Example: Plotting with Plotly
    if not df_3.empty:
        st.write("### Example Plot for Query ID 3")
        fig = px.bar(df_3, x=df_3.columns[0], y=df_3.columns[1], title="Sample Bar Chart for Query ID 3")
        st.plotly_chart(fig)
else:
    st.warning(f"⚠️ No data available for Query ID {query_id_3}.")

if df_4 is not None:
    st.write("### 🔹 Data from Query ID 4")
    st.dataframe(df_4)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_4, title="Data from Query ID 4")

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="query_4_data.png",
        mime="image/png"
    )

    # Example: Plotting with Plotly
    if not df_4.empty:
        st.write("### Example Plot for Query ID 4")
        fig = px.bar(df_4, x=df_4.columns[0], y=df_4.columns[1], title="Sample Bar Chart for Query ID 4")
        st.plotly_chart(fig)
else:
    st.warning(f"⚠️ No data available for Query ID {query_id_4}.")
