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
DATA_PATH = os.getcwd()  # adjust path as needed
files = glob.glob(os.path.join(DATA_PATH, "*.*"))
data = {}
for f in files:
    name = os.path.basename(f)
    if f.lower().endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(f)
        except:
            df = pd.read_excel(f, engine='openpyxl')
    elif f.lower().endswith('.csv'):
        df = pd.read_csv(f)
    else:
        continue
    key = os.path.splitext(name)[0]
    data[key] = df

# Sidebar for executive summary
with st.sidebar:
    st.header("Executive Summary")
    st.markdown("- Desktop users dominate Google engagement\n- India traffic strong, U.S. underperforms\n- Landing Pages: mixed performance\n- Paid campaigns need restructure")

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
    if geo is not None:
        # Bounce Rate by Country
        br_chart = alt.Chart(geo).mark_bar().encode(
            x='country:N', y='bounceRate:Q', tooltip=['country','bounceRate']
        ).properties(width=600, height=300)
        st.altair_chart(br_chart, use_container_width=True)

        # Avg Session Duration
        sd_chart = alt.Chart(geo).mark_line(point=True).encode(
            x='country:N', y='averageSessionDuration:Q', tooltip=['country','averageSessionDuration']
        ).properties(width=600, height=300)
        st.altair_chart(sd_chart, use_container_width=True)

        # New vs Returning Users
        geo['returningUsers'] = geo['sessions'] - geo['newUsers']
        rows = geo[['country','newUsers','returningUsers']].set_index('country')
        selected = st.multiselect("Select country", rows.index.tolist(), default=['India','United States'])
        for c in selected:
            counts = rows.loc[c]
            pie = alt.Chart(counts.reset_index()).mark_arc().encode(
                theta=alt.Theta(field=counts.name, type='quantitative'),
                color='index:N',
                tooltip=['index','value']
            ).properties(title=f"New vs Returning for {c}", width=300, height=300)
            st.altair_chart(pie)

# 4. Landing Page Performance
with tabs[1]:
    st.subheader("Landing Page Performance (Google Traffic)")
    lp = data.get('Landing_Pages')
    if lp is not None:
        chart = alt.Chart(lp).mark_circle(size=100).encode(
            x='sessions:Q', y='averageSessionDuration:Q', size='sessionConversionRate:Q',
            color='bounceRate:Q', tooltip=['landingPage','sessions','bounceRate','averageSessionDuration']
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
    cr = data.get('Custom_Report')
    if cr is not None:
        src = cr.groupby('sessionMedium').agg({'screenPageViews':'sum'}).reset_index()
        bar = alt.Chart(src).mark_bar().encode(
            x='sessionMedium:N', y='screenPageViews:Q', tooltip=['sessionMedium','screenPageViews']
        ).properties(width=600, height=300)
        st.altair_chart(bar, use_container_width=True)
        st.markdown("Direct/Organic outperform Display. Shift to Search + Remarketing.")

# 8. Geo Location Analysis
with tabs[5]:
    st.subheader("Geo Location Analysis")
    if geo is not None:
        st.dataframe(geo[['country','sessions','bounceRate','userConversionRate']].sort_values('sessions', ascending=False))
        st.markdown("Launch India-specific campaigns.")

# 9. Paid Campaign Effectiveness
with tabs[6]:
    st.subheader("Google Paid Campaign Effectiveness")
    camps = data.get('Campaigns')
    if camps is not None:
        camp_chart = alt.Chart(camps).mark_bar().encode(
            x='Campaign Name:N', y='Clicks:Q', color='CTR:Q', tooltip=['Campaign Name','Clicks','CTR']
        ).properties(width=800, height=300)
        st.altair_chart(camp_chart, use_container_width=True)
        st.markdown("Restructure by intent; pause inactive accounts.")

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
