import streamlit as st
import pandas as pd
import glob
import os
import altair as alt
import google.generativeai as genai
import json

# === Gemini LLM Setup ===
os.environ["GOOGLE_API_KEY"] = "AIzaSyBIBr01u6_BNVfYk989DXkv3FKQA928Kq8"

def bardLLMInitialize():
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=32000,
            temperature=0.2
        )
    )

def geminiResponseFunc(prompt: str) -> str:
    model = bardLLMInitialize()
    response = model.generate_content(prompt)
    if hasattr(response, 'candidates') and response.candidates:
        print(f"Response candidates: {response.candidates}")
        return response.candidates[0].content.parts[0].text
    elif hasattr(response, 'text'):
        print(f"Response text: {response.text}")
        return response.text
    else:
        return str(response)

# === Streamlit App ===
st.set_page_config(
    page_title="Google Marketing Operations Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Google Marketing Operations Insights")
st.markdown(
    "Deep Dive into Engagement, Landing Pages, Campaigns, Funnel Efficiency, "
    "and Strategic Recommendations"
)

# Load data
DATA_PATH = os.getcwd()
files = glob.glob(os.path.join(DATA_PATH, "*.*"))
if not files:
    st.error(f"No files found in {DATA_PATH}. Please verify the path and contents.")

data = {}
for f in files:
    try:
        if f.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(f, engine='openpyxl')
        else:
            df = pd.read_csv(f)
        key = os.path.splitext(os.path.basename(f))[0]
        data[key] = df
    except Exception as e:
        pass

# print(f"Loaded data keys: {list(data.keys())}")
# print("-------------------")
# print(f"Loaded data: {data}")
# print("-------------------")

# Tabs
tabs = st.tabs([
    "Audience Engagement", "Landing Pages", "Paid Search", 
    "Display Ads", "Source Attribution", "Geo Analysis", "Paid Campaigns",
    "Device Performance", "Funnel Velocity", "Overview"
])

# Helper to format recommendations
# def display_recommendations(text: str):
#     lines = [l.strip() for l in text.split('\n') if l.strip()]
#     bullets = '\n'.join(f"- {l}" for l in lines)
#     st.markdown(bullets)
def display_recommendations(text):
    try:
        # Ensure the input is a string
        if not isinstance(text, str):
            text = str(text)

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if lines:
            st.markdown("### Recommendations:")
            for line in lines:
                st.markdown(f"- {line}")
        else:
            st.info("No recommendations to display.")
    
    except Exception as e:
        st.error(f"An error occurred while displaying recommendations: {e}")

# 1. Audience Engagement
with tabs[0]:
    st.subheader("Audience Engagement Dashboard")
    geo = data.get('Geo_Location')
    if geo is not None and not geo.empty:
        st.altair_chart(
            alt.Chart(geo).mark_bar().encode(x='country:N', y='bounceRate:Q'),
            use_container_width=True
        )
        st.altair_chart(
            alt.Chart(geo).mark_line(point=True).encode(x='country:N', y='averageSessionDuration:Q'),
            use_container_width=True
        )

        top_geo = geo.sort_values('sessions', ascending=False).head(3)
        prompt = (
            f"Top 3 countries by sessions: {top_geo['country'].tolist()} "
            f"with bounce rates {top_geo['bounceRate'].tolist()}. "
            "Provide data-driven recommendations to optimize engagement. in a short bullet list format."
        )
        if st.button("Generate Engagement Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Engagement Recommendations"):
                display_recommendations(rec)

        # Select active_users dataset explicitly
        if 'active_users' in data:
            act = data['active_users']
        elif 'GA4_python_output' in data:
            act = data['GA4_python_output']
        else:
            act = None

        if act is not None and not act.empty and 'sessionMedium' in act.columns:
            med = act.groupby('sessionMedium', as_index=False).agg({'activeUsers':'sum'})
            st.altair_chart(
                alt.Chart(med).mark_bar().encode(x='sessionMedium:N', y='activeUsers:Q'),
                use_container_width=True
            )
            prompt2 = (
                f"Session mediums distribution: {med.to_dict(orient='records')}. "
                "Recommend optimization and budget reallocation. in a short bullet list format."
            )
            if st.button("Generate Channel Recommendations"):
                rec2 = geminiResponseFunc(prompt2)
                with st.expander("Channel Mix Recommendations"):
                    display_recommendations(rec2)
    else:
        st.warning("Geo_Location data unavailable.")

# 2. Landing Pages
with tabs[1]:
    st.subheader("Landing Page Performance (Google Traffic)")
    lp = data.get('Landing_Pages')
    if lp is not None and not lp.empty:
        st.altair_chart(
            alt.Chart(lp).mark_circle().encode(
                x='sessions:Q', y='averageSessionDuration:Q',
                size='sessionConversionRate:Q', color='bounceRate:Q',
                tooltip=['landingPage','sessions','bounceRate']
            ), use_container_width=True
        )
        low_perf = lp.nsmallest(3, 'sessionConversionRate')['landingPage'].tolist()
        prompt = (
            f"Landing pages with lowest conversion rates: {low_perf}. "
            "Suggest design and content improvements. in a short bullet list format."
        )
        if st.button("Generate LP Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Landing Page Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Landing_Pages data missing.")

# 3. Paid Search
with tabs[2]:
    st.subheader("Google Paid Search Recommendations")
    searches = data.get('Searches(Search_2025.01.01-2025.03.26)')
    if searches is not None and not searches.empty:
        top_keywords = searches.nlargest(5, 'Conversions')['Search'].tolist()
        st.write(f"Top converting searches: {top_keywords}")
        prompt = (
            f"Given top converting keywords {top_keywords}, recommend headlines, bids, "
            "and expansion strategies. in a short bullet list format."
        )
        if st.button("Generate Paid Search Insights"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Paid Search Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Searches data absent.")

# 4. Display Ads
with tabs[3]:
    st.subheader("Display Ad Recommendations")
    ins = data.get('Auction_insights(Compare_metrics_2025.01.01-2025.03.26)')
    if ins is not None and not ins.empty:
        df_head = ins[['Advertiser Name','Overlap rate','Top of page rate']].head()
        st.dataframe(df_head)
        prompt = (
            f"Display ad auction metrics sample: {df_head.to_dict(orient='records')}. "
            "Provide creative and targeting optimizations. in a short bullet list format."
        )
        if st.button("Generate Display Ad Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Display Ad Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Auction insights data missing.")

# 5. Source Attribution
with tabs[4]:
    st.subheader("Source/Medium Attribution")
    if 'active_users' in data:
        act = data['active_users']
    elif 'GA4_python_output' in data:
        act = data['GA4_python_output']
    else:
        act = None

    if act is not None and not act.empty and 'sessionMedium' in act.columns:
        src = act.groupby('sessionMedium', as_index=False).agg({'activeUsers':'sum'})
        st.altair_chart(
            alt.Chart(src).mark_bar().encode(x='sessionMedium:N', y='activeUsers:Q'),
            use_container_width=True
        )
        prompt = (
            f"Channel performance: {src.to_dict(orient='records')}. "
            "Suggest budget allocation adjustments. in a short bullet list format."
        )
        if st.button("Generate Attribution Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Attribution Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Active users sessionMedium data missing.")

# 6. Geo Analysis
with tabs[5]:
    st.subheader("Geo Location Analysis")
    geo = data.get('Geo_Location')
    if geo is not None and not geo.empty:
        st.dataframe(
            geo[['country','sessions','userConversionRate']]
            .sort_values('sessions', ascending=False)
        )
        prompt = (
            f"Top regions: {geo.sort_values('sessions', ascending=False).head(3).to_dict(orient='records')}. "
            "Recommend targeted campaigns."
        )
        if st.button("Generate Geo Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Geo Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Geo_Location data missing.")

# 7. Paid Campaign Effectiveness
with tabs[6]:
    st.subheader("Google Paid Campaign Effectiveness")
    camps = data.get('Campaigns')
    if camps is not None and not camps.empty:
        st.dataframe(camps[['Campaign Name','Clicks','CTR','Cost']])
        prompt = (
            f"Sample campaigns: {camps.head(3).to_dict(orient='records')}. "
            "Provide restructure recommendations. in a short bullet list format."
        )
        if st.button("Generate Campaign Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Campaign Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Campaigns data missing.")

# 8. Device Performance
with tabs[7]:
    st.subheader("Device Performance")
    dev = data.get('Devices(2025.01.01-2025.03.26)')
    if dev is not None and not dev.empty:
        st.altair_chart(
            alt.Chart(dev).mark_bar().encode(x='Device:N', y='Clicks:Q', color='Cost:Q'),
            use_container_width=True
        )
        prompt = (
            f"Device performance: {dev.to_dict(orient='records')}. "
            "Suggest device-specific optimizations. in a short bullet list format."
        )
        if st.button("Generate Device Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Device Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Devices data missing.")

# 9. Funnel Velocity
with tabs[8]:
    st.subheader("Funnel Velocity")
    ts = data.get('Time_series(2025.01.01-2025.03.26)')
    if ts is not None and not ts.empty:
        st.line_chart(ts.set_index('Date')[['Clicks','Impressions']])
        prompt = (
            "Time series trends for clicks and impressions. "
            "Provide funnel acceleration tactics. in a short bullet list format."
        )
        if st.button("Generate Funnel Recommendations"):
            rec = geminiResponseFunc(prompt)
            with st.expander("Funnel Recommendations"):
                display_recommendations(rec)
    else:
        st.warning("Time series data missing.")

# 10. Overview
with tabs[9]:
    st.subheader("Overall Recommendations")
    st.markdown(
        "- Emphasize desktop-first enhancements\n"
        "- Refine U.S. targeting; invest in India\n"
        "- Optimize channel mix based on data\n"
        "- Improve low-converting landing pages\n"
        "- Implement event goals and advanced tracking"
    )

# Sidebar Executive Summary

from streamlit_chat import message

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Main header
st.markdown(
    "<h2 style='text-align: center; color: #4A90E2;'>Chat Assistant</h2><hr>",
    unsafe_allow_html=True,
)

# Container for chat history
chat_container = st.container()

# Display chat history
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        is_user = msg["role"] == "user"
        message(
            msg["content"],
            is_user=is_user,
            key=f"msg_{i}",
            avatar_style="thumbs",  # Optional: change avatar style
            seed="user" if is_user else "ai",
        )

# Chat input
prompt = st.chat_input("Type your message here...")
root_folder = "All Informations Aspire"

# Store all extracted data
all_data = {}

# Function to read a file and return its content as a DataFrame
def read_file(file_path):
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
        return pd.read_excel(file_path)
    return None

# Traverse through all files in the folder and subfolders
for root, dirs, files in os.walk(root_folder):
    for file in files:
        if file.endswith(('.csv', '.xlsx', '.xls')):
            file_path = os.path.join(root, file)
            try:
                df = read_file(file_path)
                if df is not None:
                    # Use file name (without extension) as key
                    file_key = os.path.relpath(file_path, root_folder)
                    all_data[file_key] = df.to_dict(orient='records')
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

# Convert the entire dataset to JSON format
output_json = json.dumps(all_data, indent=2)

if prompt:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True, key=f"user_{len(st.session_state.messages)}")
    # Static data context (you can make this dynamic later)
    marketing_context = F"""
    You are a senior marketing operations analyst with access to Google Ads and Google Analytics data.

    The user has already provided surface-level KPIs and executive summaries. 
    Focus on strategy-impacting findings like stage mismatches, creative-geo gaps, funnel leaks, tagging issues, conversion delays, and underused high-performers. Base insights on detailed metrics. Be sharp, specific, and action-oriented—avoid generic advice. based only on Provided data Google Ads and Google Analytics data.
    in a very short answer, Your response is Strictly based on the below data for the user-query: {prompt}
    while generating the response, please do not use any other data or information outside the provided data.
    The data is in JSON format, and you can use it to extract insights and generate recommendations.
    Strictly Don't include Which file the data is coming from, just use the data to answer the user query.
    Strictly Don't include the terms in response like "Based on the provided data" or "According to the data" or "The provided data".

    If User query is related to dates or last 30days, then you have to calculated the result and provide insights.

    Generate insights based on the user query using the following data:

    Raw Dataset below:
    Use the below data to answer the user query.
    The data is in JSON format, and you can use it to extract insights and generate recommendations.
    The datasets are as follows:
    {output_json}
    another dataset is as follows:
    {data}

    The response should be in a short format and should be based on the data provided.


    """

    # Combine user input with prompt context
    full_prompt = f"{marketing_context}\n\nUser query: {prompt}"

    # Call your model with the combined input
    llm_response = geminiResponseFunc(full_prompt)

    # response = llm_response
    st.session_state.messages.append({"role": "assistant", "content": llm_response})
    message(llm_response, is_user=False, key=f"assistant_{len(st.session_state.messages)}")
