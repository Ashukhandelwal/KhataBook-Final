import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Smart Munim", page_icon="💳", layout="centered")
st.title("💳 Smart Munim Ji")
st.caption("Kharcha photo se ya likh kar save karein.")

# --- 2. CONNECTION SETUP ---
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
        st.error("Secrets missing! Please check Streamlit settings.")
        st.stop()
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. AI BRAIN (Fixed Model Name) ---
def analyze_expense(content, input_type):
    # Ab server update ho gaya hai, to ye naam perfect chalega
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = """
    Extract expense details into a SINGLE JSON Object.
    
    Rules:
    1. 'Date': Format DD/MM/YYYY. If not found, use today's date.
    2. 'Item': Keep it short. If multiple items, join with + (e.g. "Burger + Fries").
    3. 'Category': Choose one (Food/Travel/Bills/Misc/Shopping).
    4. 'Amount': Grand Total only. Number format (no symbols).
    5. 'PaymentMode': Cash/UPI/Card/Online.
    
    Output STRICTLY JSON: {"Date": "...", "Item": "...", "Category": "...", "Amount": 0, "PaymentMode": "..."}
    """
    
    try:
        with st.spinner("Munim ji hisaab laga rahe hain... 🧠"):
            if input_type == "image":
                response = model.generate_content([prompt, content])
            else:
                response = model.generate_content([prompt, f"Text: {content}"])
            
            # JSON Cleaning
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != -1:
                clean_text = clean_text[start:end]
                
            return json.loads(clean_text)
            
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# --- 4. APP UI (3 Options) ---
tab1, tab2, tab3 = st.tabs(["📂 Upload (Mobile)", "📸 Camera", "✍️ Type"])

# OPTION 1: GALLERY UPLOAD (Mobile ke liye Best)
with tab1:
    uploaded_file = st.file_uploader("Gallery se Bill chuno", type=["jpg", "png", "jpeg", "pdf"], label_visibility="collapsed")
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Bill Preview", use_column_width=True)
        
        if st.button("Hisaab Save Karo (Upload)", type="primary"):
            data = analyze_expense(image, "image")
            if data:
                sheet.append_row(list(data.values()))
                st.balloons()
                st.success(f"✅ Saved: ₹{data.get('Amount')} - {data.get('Item')}")

# OPTION 2: CAMERA INPUT (Laptop/Direct)
with tab2:
    cam_img = st.camera_input("Direct Photo Khicho")
    if cam_img:
        image = Image.open(cam_img)
        if st.button("Hisaab Save Karo (Cam)"):
            data = analyze_expense(image, "image")
            if data:
                sheet.append_row(list(data.values()))
                st.balloons()
                st.success(f"✅ Saved: ₹{data.get('Amount')}")

# OPTION 3: MANUAL ENTRY
with tab3:
    txt = st.text_input("Likh ke batao (e.g. 50rs Auto)")
    if st.button("Add Text"):
        data = analyze_expense(txt, "text")
        if data:
            sheet.append_row(list(data.values()))
            st.success(f"✅ Added: {txt}")

# --- 5. RECENT DATA ---
st.divider()
try:
    df = pd.DataFrame(sheet.get_all_records())
    if not df.empty:
        st.caption("📋 Haal hi ke kharche:")
        st.dataframe(df.tail(3))
except:
    pass
