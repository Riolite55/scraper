import streamlit as st
import threading
import time
import os
import json
import pandas as pd
from users import user_data
from send_email import send_email
from dotenv import load_dotenv
from utils_funcs import *
from send_email_without_results import *

load_dotenv()

def save_user_progress_to_file(username, progress):
    file_path = f"{username}_progress.json"
    with open(file_path, "w") as f:
        json.dump(progress, f)

def load_user_progress_from_file(username):
    file_path = f"{username}_progress.json"
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return json.load(f)
    return {"task_complete": True}

def check_credentials(username, password):
    return username in user_data and user_data[username]["password"] == user_data[username]["password"]

def check_user_task(username):
    progress = load_user_progress_from_file(username)
    return not progress.get("task_complete", True)

def save_user_progress(username, task_complete):
    progress = load_user_progress_from_file(username)
    progress["task_complete"] = task_complete
    save_user_progress_to_file(username, progress)

def extract_keywords_from_file(uploaded_file):
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return []
        if 'keywords' not in df.columns:
            st.error("The uploaded file must contain a column named 'keywords'.")
            return []
        keywords = df['keywords'].dropna().tolist()
        return keywords
    except Exception as e:
        st.error("Error reading file. Please ensure it is a valid CSV or Excel file.")
        return []

def main():
    st.title("User Login")

    if "username" not in st.session_state:
        st.session_state["username"] = ""
    if "password" not in st.session_state:
        st.session_state["password"] = ""

    st.session_state["username"] = st.text_input("Username", value=st.session_state["username"])
    st.session_state["password"] = st.text_input("Password", type="password", value=st.session_state["password"])

    if st.button("Login"):
        if check_credentials(st.session_state["username"], st.session_state["password"]):
            st.success("Login successful!")
            st.session_state["authenticated"] = True
        else:
            st.error("Invalid username or password.")

    if st.session_state.get("authenticated"):
        show_email_input_page()

def show_email_input_page():
    st.title("Search Input")

    if "email" not in st.session_state:
        st.session_state["email"] = ""
    if "selected_option" not in st.session_state:
        st.session_state["selected_option"] = ""
    
    st.session_state["email"] = st.text_input("Please Enter your email(s) (comma separated).", value=st.session_state["email"])
    
    if not st.session_state["email"]:
        st.warning("Please enter your email to proceed.")
        return

    if check_user_task(st.session_state["username"]):
        st.warning(f"A task is already running for {st.session_state['username']}. Please wait until it is complete.")
        return

    uploaded_file = st.file_uploader("Upload a file containing keywords (CSV or Excel)", type=["csv", "xlsx"])
    file_keywords = extract_keywords_from_file(uploaded_file) if uploaded_file else []

    manual_keywords = st.text_input("Enter keywords for search (comma-separated)", value="")
    manual_keywords_list = [kw.strip() for kw in manual_keywords.split(",") if kw.strip()]

    all_keywords = list(set(file_keywords + manual_keywords_list))

    dropdown_options = ["التجارة", "المقاولات", "التشغيل والصيانة والنظافة للمنشآت", "العقارات والأراضي", "الصناعة والتعدين والتدوير", "الغاز والمياه والطاقة",
                        "المناجم والبترول والمحاجر", "الإعلام والنشر والتوزيع", "الاتصالات وتقنية المعلومات",
                        "الزراعة والصيد", "الرعاية الصحية والنقاهة", "التعليم والتدريب",
                        "التوظيف والاستقدام", "الأمن والسلامة", "النقل والبريد والتخزين",
                        "المهن الاستشارية", "السياحة والمطاعم والفنادق وتنظيم المعارض",
                        "المالية والتمويل والتأمين", "الخدمات الأخرى"]

    st.session_state["selected_option"] = st.selectbox("النشاط الاساسي", dropdown_options)

    emails = [email.strip() for email in st.session_state["email"].split(",") if email.strip()]

    if st.button("Submit"):
        # Directly process the request without using a queue
        st.info("Processing your request. Please wait...")
        process_request(emails, all_keywords, st.session_state["selected_option"], st.session_state["username"])

def process_request(emails, keywords, selected_option, username):
    try:
        save_user_progress(username, False)

        # Simulate processing time
        time.sleep(5)  # Replace this with actual processing logic

        subject = f"Search Results for {', '.join(keywords)}"
        body = f"Keywords: {', '.join(keywords)}\nSelected Option: {selected_option}\nPlease find the attached results."

        get_terms_files(keywords, str(selected_option), username)
        agg_files(username)

        today_date = pd.to_datetime("today").strftime("%Y-%m-%d")
        file_name = f"tenders_{today_date}_filtered_{username}.csv"
        print("file name: ", file_name)
        
        if not os.path.isfile(file_name):
            no_results_subject = f"No Matches Found for {', '.join(keywords)}"
            no_results_body = f"Keywords: {', '.join(keywords)}\nSelected Option: {selected_option}\nPlease Try Again With Different Keywords or Main Activity."
            send_email_without_results(emails, no_results_subject, no_results_body)
            return

        send_email(emails, subject, body, username)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        save_user_progress(username, True)

if __name__ == "__main__":
    main()