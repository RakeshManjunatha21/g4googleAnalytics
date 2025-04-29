import streamlit as st
import pandas as pd
import glob
import os
import altair as alt

# Page config
st.set_page_config(
    page_title="Google Marketing Operations Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("Google Marketing Operations Insights")
st.markdown("Deep Dive into Engagement, Landing Pages, Campaigns, and Funnel Efficiency")

# Load all datasets from a folder
DATA_PATH = os.getcwd() # adjust path to your dataset directory
files = glob.glob(os.path.join(DATA_PATH, "*.*"))
if not files:
    st.error(f"No files found in {DATA_PATH}. Please check the path and file names.")
data = {}
for f in files:
    name = os.path.basename(f)
    try:
        if f.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(f, engine='openpyxl')
        elif f.lower().endswith('.csv'):
            df = pd.read_csv(f)
        else:
            continue
        key = os.path.splitext(name)[0]
        data[key] = df
    except Exception as e:
        st.warning(f"Could not load {name}: {e}")

# Show loaded dataset keys for debugging
with st.sidebar:
    st.header("Executive Summary")
    st.markdown(
        "- Desktop users dominate Google engagement\n"
        "- India traffic strong, U.S. underperforms\n"
        "- Landing Pages: mixed performance\n"
        "- Paid campaigns need restructure"
    )
    st.markdown("---")
    st.subheader("Data Loaded")
    st.write(list(data.keys()))

# Tabs for analytics
tabs = st.tabs([
    "Audience Engagement", "Landing Pages", "Paid Search Recommendations", 
    "Display Ads", "Source Attribution", "Geo Analysis", "Paid Campaigns", 
    "Funnel Velocity", "Overview"
])

# 3. Audience Engagement Dashboard
with tabs[0]:
    st.subheader("Audience Engagement Dashboard")
    geo = data.get('Geo_Location')
    if geo is None or geo.empty:
        st.warning("Geo_Location dataset is missing or empty. Check data keys and contents.")
    else:
        br_chart = alt.Chart(geo).mark_bar().encode(
            x='country:N', y='bounceRate:Q', tooltip=['country','bounceRate']
        ).properties(width=600, height=300)
        st.altair_chart(br_chart, use_container_width=True)

        sd_chart = alt.Chart(geo).mark_line(point=True).encode(
            x='country:N', y='averageSessionDuration:Q', tooltip=['country','averageSessionDuration']
        ).properties(width=600, height=300)
        st.altair_chart(sd_chart, use_container_width=True)

        geo['returningUsers'] = geo['sessions'] - geo['newUsers']
        user_df = pd.melt(
            geo[['country','newUsers','returningUsers']],
            id_vars=['country'],
            value_vars=['newUsers','returningUsers'],
            var_name='User Type',
            value_name='Count'
        )
        countries = user_df['country'].unique().tolist()
        default_countries = countries[:2]
        selected = st.multiselect(
            "Select countries for comparison",
            options=countries,
            default=default_countries
        )
        if selected:
            filtered = user_df[user_df['country'].isin(selected)]
            bar_users = alt.Chart(filtered).mark_bar().encode(
                x=alt.X('country:N', title='Country'),
                y=alt.Y('Count:Q', title='User Count'),
                color=alt.Color('User Type:N', title='User Type'),
                tooltip=['country','User Type','Count']
            ).properties(width=700, height=400)
            st.altair_chart(bar_users, use_container_width=True)

# 4. Landing Page Performance
with tabs[1]:
    st.subheader("Landing Page Performance (Google Traffic)")
    lp = data.get('Landing_Pages')
    if lp is None or lp.empty:
        st.warning("Landing_Pages dataset is missing or empty.")
    else:
        chart = alt.Chart(lp).mark_circle(size=100).encode(
            x='sessions:Q',
            y='averageSessionDuration:Q',
            size='sessionConversionRate:Q',
            color='bounceRate:Q',
            tooltip=['landingPage','sessions','bounceRate','averageSessionDuration']
        ).interactive().properties(width=700, height=400)
        st.altair_chart(chart, use_container_width=True)
        st.markdown("**Strengths:** Homepage, Contact Us strong. Career pages weak.")
        st.markdown("**Checklist:** Clear H1, proof, fast load, 3 fields max.")

# 5. Paid Search Recommendations
with tabs[2]:
    st.subheader("Google Paid Search Recommendations")
    st.markdown("**Keywords Strategy:** Intent-based, Long-tail")
    st.markdown("**Headline Examples:**")
    st.code("Headline 1: Fast, Secure Cloud Migrations")
    st.code("Headline 2: Cut Downtime by 30%")

# 6. Display Ad Recommendations
with tabs[3]:
    st.subheader("Display Ad Recommendations")
    st.markdown("**Targeting:** Remarketing, Intent audiences")
    st.markdown("**Creative Tips:** Bold message, Proof visuals, Dynamic elements for remarketing")

# 7. Source Attribution
with tabs[4]:
    st.subheader("Source/Medium Attribution")
    # Use active_users dataset for Source/Medium
    act = data.get('active_users') or data.get('GA4_python_output')
    if act is None or act.empty or 'sessionMedium' not in act.columns:
        st.warning("active_users dataset missing or 'sessionMedium' column not found. Check data keys.")
    else:
        src = act.groupby('sessionMedium', as_index=False).agg({'activeUsers':'sum'})
        bar = alt.Chart(src).mark_bar().encode(
            x='sessionMedium:N',
            y='activeUsers:Q',
            tooltip=['sessionMedium','activeUsers']
        ).properties(width=600, height=300)
        st.altair_chart(bar, use_container_width=True)
        st.markdown("Direct/Organic outperform Display. Shift to Search + Remarketing.")

# 8. Geo Location Analysis
with tabs[5]:
    st.subheader("Geo Location Analysis")
    if geo is None or geo.empty:
        st.warning("Geo_Location dataset is missing or empty.")
    else:
        st.dataframe(
            geo[['country','sessions','bounceRate','userConversionRate']]
            .sort_values('sessions', ascending=False)
        )
        st.markdown("Launch India-specific campaigns.")

# 9. Paid Campaign Effectiveness
with tabs[6]:
    st.subheader("Google Paid Campaign Effectiveness")
    camps = data.get('Campaigns')
    if camps is None or camps.empty:
        st.warning("Campaigns dataset is missing or empty.")
    else:
        camp_chart = alt.Chart(camps).mark_bar().encode(
            x='Campaign Name:N',
            y='Clicks:Q',
            color='CTR:Q',
            tooltip=['Campaign Name','Clicks','CTR']
        ).properties(width=800, height=300)
        st.altair_chart(camp_chart, use_container_width=True)
        st.markdown("Restructure by intent; pause inactive accounts.")

# 10. Funnel Velocity
# 10. Funnel Velocity
with tabs[7]:
    st.subheader("Funnel Velocity")
    st.markdown("Install Scroll Depth Events. Setup Event Goals in GA4.")

# 11. Overall Recommendations
with tabs[8]:
    st.subheader("Overall Recommendations")
    st.markdown(
        "- Desktop-first Design\n"
        "- Pause/refine U.S. targeting\n"
        "- Align LP Storytelling\n"
        "- Tighten UTM tagging\n"
        "- Build Remarketing Audiences"
    )

# Footer
st.markdown("---")
st.markdown("*Generated with Streamlit | Google Analytics Data*")