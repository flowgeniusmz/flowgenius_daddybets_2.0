import streamlit as st
from config import pagesetup as ps

st.set_page_config(page_title="DaddyBetsGPT", page_icon="👨‍💻", layout="wide")
ps.get_page_styling()
ps.display_background_image()

# Define pages using st.Page
login_page = st.Page("login.py", title="Login", icon="🔑", url_path="login")
register_page = st.Page("register.py", title="Register", icon="📝", url_path="register")
create_page = st.Page("create.py", title="Create Account", icon="🔧", url_path="create")
chat_page = st.Page("chat.py", title="Chat", icon="💬", url_path="chat")
account_page = st.Page("account.py", title="Account", icon="👤", url_path="account")

# Configure navigation using st.navigation
pages = [login_page, register_page, create_page, chat_page, account_page]
selected_page = st.navigation(pages, position="hidden")

# Run the selected page
selected_page.run()
