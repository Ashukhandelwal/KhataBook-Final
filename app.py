import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- PAGE SETUP ---
st.set_page_config(page_title="Smart Munim", page_icon="💳")
st.title("💳 Smart Munim Ji (Final v1)")

# --- CONNECTION ---
try:
    if "google_json" in st.secrets:
        creds_dict = json.loads(st.secrets["google_json"])
        gemini_key = st.secrets["GEMINI_API_KEY"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Expenses").sheet1
        genai.configure(api_key=gemini_key)
    else:
        st.error("Secrets missing!")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- AI LOGIC (Auto-Fallback) ---
def analyze_expense(content, input_type):
    # Pehle Latest Model Try karenge
    model_name = "gemini-1.5-flash"
    
    prompt = """
    Extract expense details into JSON.
    Fields: Date (DD/MM/YYYY), Item, Category, Amount (Number), PaymentMode.
    If Date missing, use today.
    Output ONLY JSON: {"Date": "...", "Item": "...", "Category": "...", "Amount": 0, "PaymentMode": "..."}
    """
    
    try:
        model = genai.GenerativeModel(model_name)
        if input_type == "image":
            response = model.generate_content([prompt, content])
        else:
            response = model.generate_content([prompt, f"Text: {content}"])
            
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        # Cleaning braces
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        if start != -1 and end != -1:
            clean_text = clean_text[start:end]
            
        return json.loads(clean_text)
        
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- UI ---
tab1, tab2 = st.tabs(["📂 Upload Bill", "✍️ Manual"])

with tab1:
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_column_width=True)
        if st.button("Save Expense", type="primary"):
            with st.spinner("Processing..."):
                data = analyze_expense(image, "image")
                if data:
                    sheet.append_row(list(data.values()))
                    st.balloons()
                    st.success(f"✅ Saved: ₹{data.get('Amount')} - {data.get('Item')}")

with tab2:
    txt = st.text_input("Type here (e.g. 50rs Chips)")
    if st.button("Save Text"):
        data = analyze_expense(txt, "text")
        if data:
            sheet.append_row(list(data.values()))
            st.success("✅ Saved!")

# --- DATA ---
try:
    df = pd.DataFrame(sheet.get_all_records())
    if not df.empty:
        st.divider()
        st.dataframe(df.tail(3))
except:
    pass
