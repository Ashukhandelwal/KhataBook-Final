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

# --- 2. SECRETS SETUP (Fixed) ---
try:
    if "google_creds" in st.secrets:
        creds_dict = dict(st.secrets["google_creds"])
        
        # --- YE WALI LINE IMPORTANT HAI (Error Fix) ---
        # Ye private key ko theek karta hai taaki login fail na ho
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
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
    st.error(f"❌ Error: '{SHEET_NAME}' naam ki Sheet nahi mili! Google Sheet ka naam check kar.")
    st.stop()

# --- 4. AI LOGIC ---
def analyze_expense(input_type, content):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    You are an expert accountant. Extract expense details into JSON.
    Fields: 'Date' (DD/MM/YYYY), 'Item' (Short name), 'Category' (Food/Travel/Bills/Misc), 
    'Amount' (Number only), 'PaymentMode' (UPI/Cash).
    If Date is not clear, use today's date.
    Output STRICTLY JSON. Do not use Markdown formatting.
    """
    try:
        if input_type == "text":
            response = model.generate_content([prompt, f"User Input: {content}"])
        elif input_type == "image":
            response = model.generate_content([prompt, content])
        
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except Exception as e:
        return None

# --- 5. UI LAYOUT ---
st.title("💰 AI Munim Ji")
st.caption("Kharcha likho nahi, bas bata do!")

tab1, tab2 = st.tabs(["📝 Likho (Chat)", "📸 Scan Bill"])

with tab1:
    text_val = st.chat_input("Aaj kya kharcha hua? (e.g. 100 ka petrol)")
    if text_val:
        with st.chat_message("user"):
            st.write(text_val)
        with st.spinner("Munim ji likh rahe hain..."):
            data = analyze_expense("text", text_val)
            if data:
                sheet.append_row([data.get('Date'), data.get('Item'), data.get('Category'), data.get('Amount'), data.get('PaymentMode')])
                st.success(f"✅ Likh liya: ₹{data.get('Amount')} - {data.get('Item')}")
            else:
                st.error("Samajh nahi aaya, dobara likho.")

with tab2:
    cam_img = st.camera_input("Bill ki photo lo")
    if cam_img:
        img = Image.open(cam_img)
        if st.button("Save Bill"):
            with st.spinner("Bill padh raha hu..."):
                data = analyze_expense("image", img)
                if data:
                    sheet.append_row([data.get('Date'), data.get('Item'), data.get('Category'), data.get('Amount'), data.get('PaymentMode')])
                    st.balloons()
                    st.success(f"✅ Saved: ₹{data.get('Amount')} ({data.get('Item')})")
                else:
                    st.error("Bill saaf nahi hai.")

# --- 6. DASHBOARD ---
st.divider()
st.subheader("📊 Live Hisaab")
try:
    records = sheet.get_all_records()
    if records:
        df = pd.DataFrame(records)
        # Amount ko number mein convert karte hain taaki jod sakein
        if 'Amount' in df.columns:
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
            total = df['Amount'].sum()
            st.metric("Total Kharcha", f"₹{int(total)}")
            st.dataframe(df.tail(5))
        else:
             st.write("Sheet mein 'Amount' column nahi mila.")
    else:
        st.info("Abhi register khali hai.")
except Exception as e:
    st.info("Data load ho raha hai... (ya Sheet khali hai)")
