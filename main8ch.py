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
if query:
    # record user
    st.session_state.history.append(("user", query))
    message(query, is_user=True, key=f"msg_user_{len(st.session_state.history)}")

    # build the full prompt
    prompt = f"""
    You are a highly intelligent GA4 analytics assistant.

    Your job is to provide **precise, actionable, and insight-driven answers** to the user’s question using only the data provided. 
    You must behave like an expert data analyst or growth consultant—interpreting trends, identifying opportunities, and suggesting next steps without exposing raw technical details.

    **Rules to follow:**
    - Do not mention sheet names, column names, or JSON structure in your answer.
    - Do not say “according to the data” or “based on the dataset.”
    - Assume the user expects **practical business insights** or **performance improvement ideas**, not raw stats.
    - Focus on delivering value. Offer **clear recommendations**, **root cause ideas**, or **strategic observations**.
    - Speak naturally, like a consultant summarizing findings, not like a system referencing files.

    ---

    **User Question:**  
    {query}

    **Data to use (JSON):**  
    {data_json}
    """

    # get the model’s answer
    answer = gemini_response(prompt).strip()

    # record assistant
    st.session_state.history.append(("assistant", answer))
    message(answer, is_user=False, key=f"msg_assistant_{len(st.session_state.history)}")
