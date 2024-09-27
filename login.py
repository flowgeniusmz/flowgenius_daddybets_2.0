import streamlit as st
from supabase import create_client, Client
import jwt
import datetime
import json

def main():
    st.title("Login")

    # Supabase credentials from Streamlit secrets
    SUPABASE_URL = st.secrets.supabase.url
    SUPABASE_KEY = st.secrets.supabase.api_key_admin

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        # Validate user against Supabase 'users' table
        data = supabase.table('users').select('*').eq('username', username).eq('password', password).execute()
        if data.data:
            user = data.data[0]
            st.success("Login successful!")
            st.session_state['logged_in'] = True
            st.session_state['user'] = user

            # Generate JWT token with 'username'
            payload = {
                'username': user['username'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expires in 1 hour
            }
            token = jwt.encode(payload, st.secrets.jwt.secret_key, algorithm='HS256')

            # Redirect the parent window to the chat page with token
            # st.write(f"""
            #     <script>
            #     window.top.location.href = "https://daddybetsgpt.com/chat?token={token}";
            #     </script>
            # """, unsafe_allow_html=True)
            st.write(f"""
                <script>
                window.parent.postMessage({json.dumps({'type': 'loginSuccess', 'token': token})}, 'https://daddybetsgpt.com');
                </script>
            """, unsafe_allow_html=True)
        else:
            st.error("Invalid username or password.")

if __name__ == "__page__":
    main()
