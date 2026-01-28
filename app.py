import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="KhataBook AI", page_icon="💰")
st.title("💰 AI Munim Ji")

# --- 2. KEY REPAIR (Sabse Zaruri Hissa) ---
try:
    if "google_creds" in st.secrets:
        # Secrets se data nikala
        creds_dict = dict(st.secrets["google_creds"])
        
        # --- MAGIC REPAIR START ---
        # Ye line check karegi ki key tuti hui hai ya judi hui
        raw_key = creds_dict["private_key"]
        
        # 1. Agar key mein "\n" likha hua hai text ki tarah, to use asli enter banao
        fixed_key = raw_key.replace("\\n", "\n")
        
        # 2. Wapas dictionary mein daal do
        creds_dict["private_key"] = fixed_key
        # --- MAGIC REPAIR END ---
        
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Secrets nahi mile!")
        st.stop()
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# --- 3. GOOGLE SHEETS CONNECTION ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Expenses").sheet1
except Exception as e:
    st.error(f"Login Fail hua: {e}")
    st.stop()

# --- 4. AI SETUP ---
genai.configure(api_key=gemini_key)
def analyze_expense(image):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Extract: Date, Item, Category, Amount, PaymentMode. Return JSON."
    try:
        response = model.generate_content([prompt, image])
        return json.loads(response.text.replace("```json","").replace("```",""))
    except:
        return None

# --- 5. APP UI ---
cam_img = st.camera_input("Bill Scan Karo")
if cam_img:
    if st.button("Save Bill"):
        with st.spinner("Munim ji hisaab laga rahe hain..."):
            img = Image.open(cam_img)
            data = analyze_expense(img)
            if data:
                sheet.append_row([data.get('Date'), data.get('Item'), data.get('Category'), data.get('Amount'), data.get('PaymentMode')])
                st.balloons()
                st.success("Hisaab Likh Diya! 🎉")
            else:
                st.error("Bill saaf nahi aaya.")
