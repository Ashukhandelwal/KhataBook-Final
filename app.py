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

# --- 2. BULLETPROOF CONNECTION ---
try:
    if "google_json" in st.secrets:
        # Direct JSON string padhenge -> No formatting errors!
        creds_dict = json.loads(st.secrets["google_json"])
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Secrets mein 'google_json' nahi mila!")
        st.stop()
        
    # Scope define karte hain
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Connect karte hain
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Expenses").sheet1

except json.JSONDecodeError:
    st.error("Secrets mein JSON sahi se paste nahi hua. Check karo brackets { } pure hain ya nahi.")
    st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. AI SETUP ---
genai.configure(api_key=gemini_key)
def analyze_expense(image):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "Extract: Date, Item, Category, Amount, PaymentMode. Return JSON."
    try:
        response = model.generate_content([prompt, image])
        return json.loads(response.text.replace("```json","").replace("```",""))
    except:
        return None

# --- 4. APP UI ---
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
