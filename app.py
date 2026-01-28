import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image
from datetime import datetime

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="KhataBook AI", page_icon="💰", layout="centered")

# --- 2. SECRETS SETUP ---
try:
    if "google_creds" in st.secrets:
        creds_dict = dict(st.secrets["google_creds"])
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("⚠️ Secrets nahi mile! Streamlit settings check karo.")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# --- 3. CONNECTION ---
genai.configure(api_key=gemini_key)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

SHEET_NAME = "Expenses"
try:
    sheet = client.open(SHEET_NAME).sheet1
except:
    st.error(f"❌ Error: '{SHEET_NAME}' naam ki Sheet nahi mili! Naam check kar.")
    st.stop()

# --- 4. AI LOGIC ---
def analyze_expense(input_type, content):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    You are an expert accountant. Extract expense details into JSON.
    Fields: 'Date' (DD/MM/YYYY), 'Item' (Short name), 'Category' (Food/Travel/Bills/Misc), 
    'Amount' (Number only), 'PaymentMode' (UPI/Cash).
    Output STRICTLY JSON.
    """
    try:
        if input_type == "text":
            response = model.generate_content([prompt, f"User Input: {content}"])
        elif input_type == "image":
            response = model.generate_content([prompt, content])
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return None

# --- 5. UI LAYOUT ---
st.title("💰 AI Munim Ji")

tab1, tab2 = st.tabs(["📝 Likho", "📸 Scan Bill"])

with tab1:
    text_val = st.chat_input("Aaj kya kharcha hua?")
    if text_val:
        with st.chat_message("user"):
            st.write(text_val)
        with st.spinner("Likh raha hu..."):
            data = analyze_expense("text", text_val)
            if data:
                sheet.append_row([data['Date'], data['Item'], data['Category'], data['Amount'], data['PaymentMode']])
                st.success(f"✅ Saved: ₹{data['Amount']} - {data['Item']}")
            else:
                st.error("Samajh nahi aaya.")

with tab2:
    cam_img = st.camera_input("Bill ki photo lo")
    if cam_img:
        img = Image.open(cam_img)
        if st.button("Save Bill"):
            with st.spinner("Scanning..."):
                data = analyze_expense("image", img)
                if data:
                    sheet.append_row([data['Date'], data['Item'], data['Category'], data['Amount'], data['PaymentMode']])
                    st.success(f"✅ Saved: ₹{data['Amount']}")
                else:
                    st.error("Photo saaf nahi hai.")

# --- 6. DASHBOARD ---
st.divider()
st.subheader("📊 Live Hisaab")
try:
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        st.metric("Total Kharcha", f"₹{df['Amount'].sum()}" if 'Amount' in df.columns else "0")
        st.dataframe(df.tail(5))
except:
    st.info("Abhi register khali hai.")
