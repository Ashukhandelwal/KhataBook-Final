import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import json
from PIL import Image

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Smart Munim Debug", page_icon="🐞", layout="centered")
st.title("🐞 Munim Ji (Debug Mode)")
st.info("Ye mode humein batayega ki AI ke dimaag mein kya chal raha hai.")

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

# --- 3. AI LOGIC (With Spy) ---
def analyze_expense(content, input_type):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = """
    Extract expense data. Return ONLY a JSON object.
    Keys: "Date", "Item", "Category", "Amount" (int/float), "PaymentMode".
    Example: {"Date": "29/01/2026", "Item": "Burger", "Category": "Food", "Amount": 250, "PaymentMode": "UPI"}
    """
    try:
        # AI se baat karte hain
        if input_type == "image":
            response = model.generate_content([prompt, content])
        else:
            response = model.generate_content([prompt, f"Text: {content}"])
        
        # --- JASOOS CODE (Spy) ---
        # Hum screen par print karenge ki AI ne kya bola
        st.text("AI Raw Response (Debug):")
        st.code(response.text) 
        # -------------------------

        # Safai Abhiyaan (JSON Cleaning)
        clean_text = response.text
        # Backticks hatate hain
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
        
        # Agar AI ne koi faltu text likha hai to sirf { } wala hissa nikalenge
        start = clean_text.find("{")
        end = clean_text.rfind("}") + 1
        if start != -1 and end != -1:
            clean_text = clean_text[start:end]

        return json.loads(clean_text)

    except Exception as e:
        st.error(f"⚠️ Parsing Error: {e}")
        return None

# --- 4. UI ---
tab1, tab2 = st.tabs(["📂 Upload (Best)", "✍️ Type"])

with tab1:
    uploaded_file = st.file_uploader("Gallery se Bill/Note chuno", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_column_width=True)
        if st.button("Analyze", type="primary"):
            data = analyze_expense(image, "image")
            if data:
                sheet.append_row([data.get('Date'), data.get('Item'), data.get('Category'), data.get('Amount'), data.get('PaymentMode')])
                st.balloons()
                st.success("✅ Saved Successfully!")
            else:
                st.error("❌ Data save nahi hua. Upar 'AI Raw Response' check karo.")

with tab2:
    txt = st.text_input("Likho (e.g. 100rs Chai)")
    if st.button("Add"):
        data = analyze_expense(txt, "text")
        if data:
            sheet.append_row(list(data.values()))
            st.success("✅ Saved!")

# --- 5. Data ---
try:
    df = pd.DataFrame(sheet.get_all_records())
    st.dataframe(df.tail(3))
except:
    pass
