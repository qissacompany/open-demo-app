import streamlit as st

bucket_key = st.secrets["client_bucket"]['BUCKET_idkey']
bucket_secret = st.secrets["client_bucket"]['BUCKET_secretkey']
bucket_url = st.secrets["client_bucket"]['BUCKET_url']
bucket_name = st.secrets["client_bucket"]['BUCKET_name']

#LOCAT
username_input_text = ["Käyttäjätunnus","Username"]
password_input_text = ["Salasana","Password"]
incorrect_warning = ["Käyttäjä tai tunnus on väärin","User not known or password incorrect"]
testuser_max_error = ['Testikäyttömäärä on ylittynyt!','Test usage limit reached!']

#simple auth
def check_password(lin=0):
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input(username_input_text[lin], on_change=password_entered, key="username")
        st.text_input(password_input_text[lin], type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(username_input_text[lin], on_change=password_entered, key="username")
        st.text_input(password_input_text[lin], type="password", on_change=password_entered, key="password")
        st.error(incorrect_warning[lin])
        return False
    else:
        # Password correct.
        return True

def check_test_query_count(max=10,lin=0):
    if 'test_count' not in st.session_state:
        st.session_state.test_count = 0
    if st.session_state.test_count < max:
        st.session_state.test_count += 1
        return True
    else:
        st.warning(testuser_max_error[lin])
        return False
