import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Smart Munim", page_icon="💳", layout="centered")
st.title("💳 Smart Munim Ji")

# --- 2. CONNECTION ---
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

# --- 3. AI LOGIC (FIXED MODEL) ---
def analyze_expense(content, input_type):
    # YAHAN CHANGE KIYA HAI: 'latest' version use karenge
    model = genai.GenerativeModel("gemini-1.5-flash-latest")
    
    prompt = """
    Extract expense details into a SINGLE JSON Object.
    Rules:
    1. 'Date': Format DD/MM/YYYY.
    2. 'Item': Combine items if multiple (e.g. "Burger + Coke").
    3. 'Category': Food/Travel/Bills/Misc.
    4. 'Amount': Grand Total (Number only).
    5. 'PaymentMode': Cash/UPI/Card.
    
    Output JSON: {"Date": "...", "Item": "...", "Category": "...", "Amount": 0, "PaymentMode": "..."}
    """
    try:
        if input_type == "image":
            response = model.generate_content([prompt, content])
        else:
            response = model.generate_content([prompt, f"Text: {content}"])
            
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        if start != -1 and end != -1:
            clean_text = clean_text[start:end]
            
        return json.loads(clean_text)
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# --- 4. APP UI ---
tab1, tab2, tab3 = st.tabs(["📂 Gallery", "📸 Camera", "✍️ Type"])

with tab1:
    st.caption("Best for Mobile: Gallery se photo upload karein")
    uploaded_file = st.file_uploader("Upload Bill", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview", use_column_width=True)
        if st.button("Save (Upload)", type="primary"):
            with st.spinner("Analyzing..."):
                data = analyze_expense(image, "image")
                if data:
                    sheet.append_row(list(data.values()))
                    st.balloons()
                    st.success(f"✅ Saved: ₹{data.get('Amount')} ({data.get('Item')})")

with tab2:
    cam_img = st.camera_input("Camera")
    if cam_img:
        image = Image.open(cam_img)
        if st.button("Save (Camera)"):
            with st.spinner("Analyzing..."):
                data = analyze_expense(image, "image")
                if data:
                    sheet.append_row(list(data.values()))
                    st.balloons()
                    st.success(f"✅ Saved: ₹{data.get('Amount')}")

with tab3:
    txt = st.text_input("Manual Entry")
    if st.button("Save Text"):
        data = analyze_expense(txt, "text")
        if data:
            sheet.append_row(list(data.values()))
            st.success("✅ Saved!")

st.divider()
try:
    df = pd.DataFrame(sheet.get_all_records())
    if not df.empty:
        st.dataframe(df.tail(3))
except:
    pass
