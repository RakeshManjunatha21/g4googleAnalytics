import streamlit as st
import pandas as pd
import glob
import os
import altair as alt
import google.generativeai as genai
# === Gemini LLM Setup ===
os.environ["GOOGLE_API_KEY"] = "AIzaSyBIBr01u6_BNVfYk989DXkv3FKQA928Kq8"
# # Set your Google API key in environment before running
# os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

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
    # Extract text from the first candidate
    if hasattr(response, 'candidates') and response.candidates:
        return response.candidates[0].content
    elif hasattr(response, 'text'):
        return response.text
    else:
        # Fallback to string representation
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
        st.warning(f"Failed loading {f}: {e}")

# Sidebar Executive Summary
with st.sidebar:
    st.header("Executive Summary")
    st.markdown(
        "- Desktop users dominate engagement\n"
        "- India leads, U.S. underperforms\n"
        "- Paid campaigns require restructure\n"
        "- Landing pages mixed results"
    )
    st.markdown("---")
    st.subheader("Loaded Tables")
    st.write(list(data.keys()))

# Tabs
tabs = st.tabs([
    "Audience Engagement", "Landing Pages", "Paid Search", 
    "Display Ads", "Source Attribution", "Geo Analysis", "Paid Campaigns",
    "Device Performance", "Funnel Velocity", "Overview"
])

# 1. Audience Engagement
with tabs[0]:
    st.subheader("Audience Engagement Dashboard")
    geo = data.get('Geo_Location')
    if geo is not None and not geo.empty:
        # Bounce Rate
        br = alt.Chart(geo).mark_bar().encode(
            x='country:N', y='bounceRate:Q'
        ).properties(width=600, height=300)
        st.altair_chart(br, use_container_width=True)
        # Session Duration
        sd = alt.Chart(geo).mark_line(point=True).encode(
            x='country:N', y='averageSessionDuration:Q'
        ).properties(width=600, height=300)
        st.altair_chart(sd, use_container_width=True)

        # Generate Engagement Recommendations
        top_geo = geo.sort_values('sessions', ascending=False).head(3)
        prompt = (
            f"Top 3 countries by sessions: {top_geo['country'].tolist()} "
            f"with bounce rates {top_geo['bounceRate'].tolist()}. "
            "Provide recommendations to optimize engagement."
        )
        if st.button("Generate Engagement Recommendations"):
            rec = geminiResponseFunc(prompt)
            st.markdown(rec)

        # Session Medium distribution
        if 'active_users' in data:
            act = data['active_users']
        elif 'GA4_python_output' in data:
            act = data['GA4_python_output']
        else:
            act = None

        if act is not None and not act.empty and 'sessionMedium' in act.columns:
            med = act.groupby('sessionMedium', as_index=False).agg({'activeUsers':'sum'})
            mchart = alt.Chart(med).mark_bar().encode(
                x='sessionMedium:N', y='activeUsers:Q'
            ).properties(width=600, height=300)
            st.altair_chart(mchart, use_container_width=True)
            prompt2 = (
                f"Session mediums distribution: {med.to_dict(orient='records')}. "
                "Recommend optimizing channel mix."
            )
            if st.button("Generate Channel Recommendations"):
                st.markdown(geminiResponseFunc(prompt2))
    else:
        st.warning("Geo_Location data unavailable.")

# 2. Landing Pages
with tabs[1]:
    st.subheader("Landing Page Performance (Google Traffic)")
    lp = data.get('Landing_Pages')
    if lp is not None and not lp.empty:
        scatter = alt.Chart(lp).mark_circle().encode(
            x='sessions:Q',
            y='averageSessionDuration:Q',
            size='sessionConversionRate:Q',
            color='bounceRate:Q',
            tooltip=['landingPage','sessions','bounceRate']
        ).properties(width=700, height=400)
        st.altair_chart(scatter, use_container_width=True)

        low_perf = lp.nsmallest(3, 'sessionConversionRate')['landingPage'].tolist()
        prompt = (
            f"Landing pages with lowest conversion rates: {low_perf}. "
            "Suggest improvements."
        )
        if st.button("Generate LP Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
    else:
        st.warning("Landing_Pages data missing.")

# 3. Paid Search Recommendations
with tabs[2]:
    st.subheader("Google Paid Search Recommendations")
    searches = data.get('Searches(Search_2025.01.01-2025.03.26)')
    if searches is not None and not searches.empty:
        top_keywords = searches.nlargest(5, 'Conversions')['Search'].tolist()
        st.write(f"Top 5 converting searches: {top_keywords}")
        prompt = (
            f"Given top converting keywords {top_keywords}, "
            "recommend headline and keyword expansion strategies."
        )
        if st.button("Generate Paid Search Insights"):
            st.markdown(geminiResponseFunc(prompt))
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
            f"Display ad auction insights sample: {df_head.to_dict(orient='records')}. "
            "Suggest creative targeting optimizations."
        )
        if st.button("Generate Display Ad Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
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
            alt.Chart(src).mark_bar().encode(
                x='sessionMedium:N', y='activeUsers:Q'
            ), use_container_width=True
        )
        prompt = (
            f"Channel performance: {src.to_dict(orient='records')}. "
            "Recommend reallocation of budget."
        )
        if st.button("Generate Attribution Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
    else:
        st.warning("Active users sessionMedium data missing.")

# 6. Geo Analysis
with tabs[5]:
    st.subheader("Geo Location Analysis")
    geo = data.get('Geo_Location')
    if geo is not None:
        st.dataframe(geo[['country','sessions','userConversionRate']])
        prompt = f"Geo performance sample: {geo.sort_values('sessions', ascending=False).head(3).to_dict(orient='records')}. Suggest geo-targeting strategy."
        if st.button("Generate Geo Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
    else:
        st.warning("Geo_Location data missing.")

# 7. Paid Campaign Effectiveness
with tabs[6]:
    st.subheader("Google Paid Campaign Effectiveness")
    camps = data.get('Campaigns')
    if camps is not None:
        st.dataframe(camps[['Campaign Name','Clicks','CTR','Cost']])
        prompt = f"Campaign snapshot: {camps.head(3).to_dict(orient='records')}. Provide restructure recommendations."
        if st.button("Generate Campaign Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
    else:
        st.warning("Campaigns data missing.")

# 8. Device Performance
with tabs[7]:
    st.subheader("Device Performance")
    dev = data.get('Devices(2025.01.01-2025.03.26)')
    if dev is not None:
        st.altair_chart(alt.Chart(dev).mark_bar().encode(x='Device:N', y='Clicks:Q', color='Cost:Q'), use_container_width=True)
        prompt = f"Device performance: {dev.to_dict(orient='records')}. Recommend device-specific optimizations."
        if st.button("Generate Device Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
    else:
        st.warning("Devices data missing.")

# 9. Funnel Velocity
with tabs[8]:
    st.subheader("Funnel Velocity")
    ts = data.get('Time_series(2025.01.01-2025.03.26)')
    if ts is not None:
        st.line_chart(ts.set_index('Date')[['Clicks','Impressions']])
        prompt = f"Time series trends: clicks and impressions over time. Suggest funnel acceleration tactics."
        if st.button("Generate Funnel Recommendations"):
            st.markdown(geminiResponseFunc(prompt))
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

# Footer
st.markdown("---")
st.markdown("*Generated with Streamlit | Powered by Gemini LLM & Google Analytics Data*")
