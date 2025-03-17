import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from authlib.integrations.requests_client import OAuth2Session

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

# 🔹 Fetch data from Metabase (Example)
def get_metabase_session():
    login_url = f"{METABASE_URL}/api/session"
    credentials = {"username": METABASE_USERNAME, "password": METABASE_PASSWORD}

    try:
        response = requests.post(login_url, json=credentials)
        response.raise_for_status()
        return response.json().get("id")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Authentication Failed! Error: {e}")
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
        if not data:
            st.warning("⚠️ Query returned no data.")
            return None
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
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
        if not data:
            st.warning("⚠️ Query returned no data.")
            return None
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

QUERY_ID = 123  # Change to your Metabase Query ID
df = fetch_metabase_data(QUERY_ID)

if df is not None:
    st.dataframe(df)

# Function to convert DataFrame to PNG
def dataframe_to_image(df, title="App Not Deployed - Real Time Data"):
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
query_id_3 = st.sidebar.number_input("Enter Metabase Query ID (First Dataset)", min_value=1, value=3036, step=1)
query_id_4 = st.sidebar.number_input("Enter Metabase Query ID (First Dataset)", min_value=1, value=3003, step=1)
query_id_2 = st.sidebar.number_input("Enter Metabase Query ID (Second Dataset)", min_value=1, value=3023, step=1)

# Fetch data
df_1 = fetch_metabase_data(query_id_1)
df_3 = fetch_metabase_data(query_id_3)
df_4 = fetch_metabase_data(query_id_4)
df_2 = fetch_metabase_data(query_id_2)

## ------------------- QUERY 1: VEHICLE SCHEDULE DATA -------------------
if df_1 is not None:
    st.write("### 🔹 App Not Deployed - Real Time Data")
    st.dataframe(df_1)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_1)

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="app_not_deployed_real_time_data_1.png",
        mime="image/png"
    )

    # Bar Chart: Customer-wise Total Vehicle Count
    st.subheader("📊 Customer-wise count of \"Not App Deployed\" for today")
    df_1['Total Vehicles'] = pd.to_numeric(df_1['Total Vehicles'], errors='coerce')
    df_customer_vehicles = df_1.groupby('Customer')['Total Vehicles'].sum().reset_index()
    
    fig_customer_bar = px.bar(
        df_customer_vehicles, 
        x='Customer', 
        y='Total Vehicles', 
        title="Total Vehicle Count per Customer", 
        color='Total Vehicles', 
        text_auto=True
    )
    st.plotly_chart(fig_customer_bar, key="plotly_chart_1")  # ✅ Added unique key
else:
    st.warning(f"⚠️ No data found for Query ID {query_id_1}.")

## ------------------- QUERY 3: VEHICLE SCHEDULE DATA -------------------
if df_3 is not None:
    st.write("### 🔹 Accepted Trips - Real Time Data")  # Differentiate title
    st.dataframe(df_3)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_3)

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="accepted_trips_real_time_data.png",  # Unique filename
        mime="image/png"
    )

    # Bar Chart: Customer-wise Total Vehicle Count
    st.subheader("📊 Customer-wise count of \"Accepted trip\" for today")
    df_3['Total Vehicles'] = pd.to_numeric(df_3['Total Vehicles'], errors='coerce')  # Corrected reference
    df_customer_vehicles = df_3.groupby('Customer')['Total Vehicles'].sum().reset_index()  # Corrected reference
    
    fig_customer_bar = px.bar(
        df_customer_vehicles, 
        x='Customer', 
        y='Total Vehicles', 
        title="Total Vehicle Count per Customer", 
        color='Total Vehicles', 
        text_auto=True
    )
    st.plotly_chart(fig_customer_bar, key="plotly_chart_3")  # ✅ Added unique key
else:
    st.warning(f"⚠️ No data found for Query ID {query_id_3}.")

# Check if both dataframes exist
if df_1 is not None and df_3 is not None:
    # Remove existing "Grand Total" rows from df_1 and df_3
    df_1["Duty Type"] = df_1["Duty Type"].astype(str)
    df_3["Duty Type"] = df_3["Duty Type"].astype(str)

    df_1_filtered = df_1[df_1["Duty Type"] != "Grand Total"].copy()
    df_3_filtered = df_3[df_3["Duty Type"] != "Grand Total"].copy()

    # Add Status column
    df_1_filtered["Status"] = "New"
    df_3_filtered["Status"] = "Accepted"

    # Ensure 'Total Vehicles' is numeric
    df_1_filtered["Total Vehicles"] = pd.to_numeric(df_1_filtered["Total Vehicles"], errors="coerce")
    df_3_filtered["Total Vehicles"] = pd.to_numeric(df_3_filtered["Total Vehicles"], errors="coerce")

    # Compute grand total for Total Vehicles
    total_vehicles_sum = df_1_filtered["Total Vehicles"].sum() + df_3_filtered["Total Vehicles"].sum()

    # Combine DataFrames
    df_combined = pd.concat([df_1_filtered, df_3_filtered], ignore_index=True)

    # Create a single Grand Total row at the bottom (without unnecessary columns)
    grand_total_row = pd.DataFrame({
        "Duty Type": [""],  
        "Customer": [""],
        "Hub": [""],
        "Spocs": [""],
        "Driver": [""],
        "Scheduled At Time": [""],
        "Started At Time": [""],
        "Total Vehicles": [total_vehicles_sum],  # Only keeping total sum
        "Status": [""]
    })

    # Append only one Grand Total row at the end
    df_combined = pd.concat([df_combined, grand_total_row], ignore_index=True)

    # Ensure that there are no duplicate or misplaced Grand Total rows
    df_combined = df_combined[~df_combined["Customer"].str.contains("Grand Total", na=False)]

    # Display the cleaned-up DataFrame
    st.write("### 🔹 Combined Vehicle Schedule Data")
    st.dataframe(df_combined)

    # Convert DataFrame to PNG
    img_buffer = dataframe_to_image(df_combined)

    # PNG Download Button
    st.download_button(
        label="📷 Download Table as PNG",
        data=img_buffer,
        file_name="combined_vehicle_schedule_data.png",
        mime="image/png"
    )

if df_4 is not None and df_2 is not None:
    # Convert "Scheduled At" from string to datetime (correct format)
    df_4["Scheduled At"] = pd.to_datetime(df_4["Scheduled At"], format="%d-%b-%Y", errors="coerce").dt.date
    df_2["Scheduled At"] = pd.to_datetime(df_2["Scheduled At"], format="%d-%b-%Y", errors="coerce").dt.date

    # Remove NaN values after conversion
    df_4 = df_4.dropna(subset=["Scheduled At"])
    df_2 = df_2.dropna(subset=["Scheduled At"])

    # Get the current month and year
    current_month = pd.Timestamp.today().month
    current_year = pd.Timestamp.today().year

    # Filter only current month data
    df_4 = df_4[df_4["Scheduled At"].apply(lambda x: x.month == current_month and x.year == current_year)]
    df_2 = df_2[df_2["Scheduled At"].apply(lambda x: x.month == current_month and x.year == current_year)]

    # Count vehicles per date
    deployed_vehicles = df_4.groupby("Scheduled At")["Vehicle"].count().reset_index(name="Deployed Vehicles")
    non_deployed_vehicles = df_2.groupby("Scheduled At")["Vehicle"].count().reset_index(name="Non-Deployed Vehicles")

    # Merge both counts
    merged_df = pd.merge(deployed_vehicles, non_deployed_vehicles, on="Scheduled At", how="outer").fillna(0)

    # Calculate App Deployment %
    merged_df["Total Vehicles"] = merged_df["Deployed Vehicles"] + merged_df["Non-Deployed Vehicles"]
    merged_df["App Deployment%"] = (merged_df["Deployed Vehicles"] / merged_df["Total Vehicles"]) * 100

    # Calculate the overall average App Deployment%
    overall_average_deployment = merged_df["App Deployment%"].mean()

    # Convert percentages to integer format and append '%'
    merged_df["App Deployment%_str"] = merged_df["App Deployment%"].astype(int).astype(str) + "%"

    # Display result in Streamlit
    st.subheader("📊 App Deployment Analysis")
    st.dataframe(merged_df[["Scheduled At", "Deployed Vehicles", "Non-Deployed Vehicles", "Total Vehicles", "App Deployment%_str"]])

    # Display overall average separately
    st.markdown(f"**📊 Overall Average Deployment%:** {int(overall_average_deployment)}%")
    
    # Convert 'Scheduled At' to the desired format
    merged_df["Scheduled At"] = pd.to_datetime(merged_df["Scheduled At"]).dt.strftime("%d %B")


    # Set the formatted column as the index and plot the bar chart
    st.subheader("📊 App Deployment% Over Time")
    st.bar_chart(merged_df.set_index("Scheduled At")["App Deployment%"])



## ------------------- QUERY 2: TRIP DATA -------------------
if df_2 is not None:
    st.write("### 🚚 Current month's raw data for \"App Not Deployed\"")
    st.dataframe(df_2)

    # Bar Chart: Number of Trips per Hub
    st.subheader("📊 Number of Trips per Hub")
    df_hub_trips = df_2.groupby('Hub').size().reset_index(name='Trip Count')
    fig_hub_bar = px.bar(
        df_hub_trips, 
        x='Hub', 
        y='Trip Count', 
        title="Trips per Hub", 
        color='Trip Count', 
        text_auto=True
    )
    st.plotly_chart(fig_hub_bar)

    # Count Unique Drivers and Their Trip Counts
    st.subheader("🚛 Driver-wise Trip Count for \"App Not Deployed\" in the Current Month")
    df_driver_trips = df_2.groupby('Driver').size().reset_index(name='Total Trips')
    st.dataframe(df_driver_trips)

    # Bar Chart: Driver-wise Trip Count
    fig_driver_bar = px.bar(
        df_driver_trips, 
        x='Driver', 
        y='Total Trips', 
        title="Trips per Driver", 
        color='Total Trips', 
        text_auto=True
    )
    st.plotly_chart(fig_driver_bar)

    # SPOC-wise Trip Count
    st.subheader("👤 SPOC-wise Trip Count \"App Not Deployed\" in the Current Month")
    if 'Spoc' in df_2.columns:
        df_spoc_trips = df_2.groupby('Spoc').size().reset_index(name='Total Trips')
        st.dataframe(df_spoc_trips)

        # Bar Chart: SPOC-wise Trip Count
        fig_spoc_bar = px.bar(
            df_spoc_trips, 
            x='Spoc', 
            y='Total Trips', 
            title="Trips per SPOC", 
            color='Total Trips', 
            text_auto=True
        )
        st.plotly_chart(fig_spoc_bar)
    else:
        st.warning("⚠️ No 'Spoc' column found in the dataset.")
else:
    st.warning(f"⚠️ No data found for Query ID {query_id_2}.")

## ------------------- DRIVERS WHO DID NOT DEPLOY THE APP (YESTERDAY & TODAY) -------------------
if df_1 is not None and df_2 is not None:
    if 'Driver' in df_1.columns and 'Driver' in df_2.columns:
        st.success("✅ 'Driver' column exists in both datasets.")
        
        if 'Scheduled At' in df_2.columns:
            st.success("✅ 'Scheduled At' column exists in Query 3023.")
            df_2['Scheduled At'] = pd.to_datetime(df_2['Scheduled At'], errors='coerce')
            yesterday = (pd.Timestamp.today() - pd.Timedelta(days=1)).date()
            df_2_yesterday = df_2[df_2['Scheduled At'].dt.date == yesterday]
            
            drivers_3021 = set(df_1['Driver'].dropna().unique())
            drivers_3023_yesterday = set(df_2_yesterday['Driver'].dropna().unique())
            
            common_drivers = sorted(drivers_3021.intersection(drivers_3023_yesterday))
            
            if common_drivers:
                st.subheader("🚚 Drivers who have not deployed the app yesterday and today")
                st.write(common_drivers)
            else:
                st.warning("⚠️ No matching drivers found for yesterday's data.")
        else:
            st.warning("⚠️ 'Scheduled At' column not found in Query 3023.")
    else:
        st.warning("⚠️ 'Driver' column not found in one of the datasets.")
if df_2 is not None:
    if {'Customer', 'Driver', 'Spoc', 'Scheduled At'}.issubset(df_2.columns):
        st.subheader("📅 Drivers who have not deployed the app in the last 7 days")
        
        # Define last 7 days
        last_7_days = [(pd.Timestamp.today() - pd.Timedelta(days=i)).date() for i in range(6, -1, -1)]
        
        # Ensure 'Scheduled At' column is in datetime format
        df_2['Scheduled At'] = pd.to_datetime(df_2['Scheduled At'], errors='coerce')

        # Convert 'Scheduled At' to date before filtering
        df_filtered = df_2[df_2['Scheduled At'].dt.date.isin(last_7_days)]
        
        # Create pivot table for last 7 days
        df_pivot = df_filtered.pivot_table(
            index=['Customer', 'Driver', 'Spoc'], 
            columns='Scheduled At', 
            aggfunc='size', 
            fill_value=0
        ).reset_index()
        
        # Rename columns
        df_pivot.columns.name = None
        df_pivot.rename(columns=lambda x: str(x) if isinstance(x, pd.Timestamp) else x, inplace=True)

        # Add Grand Total row
        total_row = df_pivot.select_dtypes(include=['number']).sum()
        total_row['Customer'] = 'Grand Total'
        total_row['Driver'] = ''
        total_row['Spoc'] = ''
        df_pivot = pd.concat([df_pivot, pd.DataFrame([total_row])], ignore_index=True)

        # Display Pivot Table
        st.dataframe(df_pivot)

        # Melt the pivot table to long format for visualization
        df_melted = df_pivot.melt(id_vars=['Customer', 'Driver', 'Spoc'], var_name='Date', value_name='Count')

        # Remove Grand Total row from visualization
        df_melted = df_melted[df_melted['Customer'] != 'Grand Total']

        fig = px.bar(
            df_melted, 
            x='Date',
            y='Count',
            color='Driver',
            barmode='group',
            title="📊 Driver Schedule Count Over the Last 7 Days",
            labels={'Date': 'Scheduled Date', 'Count': 'Number of Assignments'},
            height=500
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)


        # ------------------- CURRENT DATE DATA -------------------
        st.subheader("📆 Drivers who have not deployed the app today after trip completion")

        # Filter data for today
        today_date = pd.Timestamp.today().date()
        df_today = df_2[df_2['Scheduled At'].dt.date == today_date]

        # Count occurrences of (Customer, Driver, Spoc)
        df_today_summary = df_today.groupby(['Customer', 'Driver', 'Spoc']).size().reset_index(name='Count')

        # Add Grand Total row
        total_count = df_today_summary['Count'].sum()
        grand_total_row = pd.DataFrame([{'Customer': 'Grand Total', 'Driver': '', 'Spoc': '', 'Count': total_count}])
        # Append Grand Total to the dataframe
        df_today_summary = pd.concat([df_today_summary, grand_total_row], ignore_index=True)
        # Display Today's Data
        st.dataframe(df_today_summary)

    else:
        st.warning("⚠️ Required columns ('Customer', 'Driver', 'Spoc', 'Scheduled At') not found in dataset.")
