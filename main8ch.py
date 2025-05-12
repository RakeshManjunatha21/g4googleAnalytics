# app.py
import os
import json
import streamlit as st
import pandas as pd
# from dotenv import load_dotenv
import google.generativeai as genai
from streamlit_chat import message

# ── LOAD SECRETS ───────────────────────────────────────────────────────────────
# load_dotenv()
GEMINI_API_KEY = "AIzaSyBIBr01u6_BNVfYk989DXkv3FKQA928Kq8"
genai.configure(api_key=GEMINI_API_KEY)

# ── GEMINI CALL WRAPPER ─────────────────────────────────────────────────────────
def gemini_response(prompt: str) -> str:
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.types.GenerationConfig(temperature=0.2)
    )
    resp = model.generate_content(prompt)
    # pick first candidate
    return (
        resp.candidates[0].content.parts[0].text
        if hasattr(resp, "candidates") else resp.text
    )

# ── LOAD GA4 EXCEL (all sheets) ────────────────────────────────────────────────
@st.cache_data
def load_all_sheets(path: str) -> dict:
    return pd.read_excel(path, sheet_name=None)

data = load_all_sheets("GA4_Full_Report_Apr2023_Mar2024_V3.xlsx")

# ── PREPARE SCHEMA + DATA JSON ─────────────────────────────────────────────────
# 1) Build simple sheet→columns summary
schema_info = []
for sheet, df in data.items():
    cols = df.columns.tolist()
    schema_info.append(f"• {sheet}: columns = {cols}")
schema_text = "\n".join(schema_info)

# 2) Convert entire dataset to JSON
#    (this can be large—ensure your deployment can handle it)
data_json = json.dumps(
    {sheet: df.to_dict(orient="records") for sheet, df in data.items()},
    indent=None
)

# ── STREAMLIT CHAT UI ─────────────────────────────────────────────────────────
# st.set_page_config(page_title="GA4 Full-Data Chat", layout="wide")
st.title("💬 Google Analytics Chat Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

# display existing history
for idx, (role, txt) in enumerate(st.session_state.history):
    message(txt, is_user=(role=="user"), key=f"msg_{role}_{idx}")

# get user input
query = st.chat_input("Ask any question about your Google Analytics…", key="input_1")
json_file_path = "combined_data_mod_v2.json"
with open(json_file_path, "r", encoding="utf-8") as f:
    data_loaded_adward = json.load(f)


if query:
    # record user
    st.session_state.history.append(("user", query))
    message(query, is_user=True, key=f"msg_user_{len(st.session_state.history)}")

    # build the full prompt
    prompt = f"""
    You are a highly intelligent GA4 and Google Ads analytics assistant.

    Your role is to deliver **precise, actionable, and insight-rich answers** to the user's question, using **only the data provided**. 
    Think and respond like an experienced growth consultant or performance marketer—able to translate raw data into meaningful insights, strategic takeaways, and optimization opportunities.

    **Guidelines to follow:**
    - Always ground your answers in the data, but do not expose or mention sheet names, column names, or JSON structures.
    - Never use phrases like “according to the data” or “based on the dataset.”
    - Prioritize **business-relevant takeaways** over technical summaries or statistics.
    - Every response must reflect **practical recommendations**, **clear performance insights**, or **opportunities for improvement**.
    - Use a confident, conversational tone—as if presenting insights to a marketing team or decision-maker.
    - Support your response with **specific data points** (e.g., actual values, trends, comparisons) to justify your conclusions, but **do not reveal underlying data structures**.

    ---

    **User Question:**  
    {query}

    **Data to use (Google Analytics - JSON):**  
    {data_json}

    **Data to use (Google Ads - JSON):**  
    {data_loaded_adward}
    """


    # get the model’s answer
    answer = gemini_response(prompt).strip()

    # record assistant
    st.session_state.history.append(("assistant", answer))
    message(answer, is_user=False, key=f"msg_assistant_{len(st.session_state.history)}")
