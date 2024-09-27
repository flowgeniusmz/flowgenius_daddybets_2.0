import streamlit as st
from openai import OpenAI
import jwt
from supabase import create_client, Client
from config import pagesetup as ps

def main():
    st.title("Chat with AI Assistant")

    # Retrieve the token from st.query_params
    token = st.query_params.get('token')

    if token is None:
        st.warning("User not authenticated. Please log in.")
        # Redirect to login page
        st.write("""
            <script>
            window.top.location.href = "https://daddybetsgpt.com/login";
            </script>
        """, unsafe_allow_html=True)
        return
    else:
        try:
            # Decode the JWT token
            payload = jwt.decode(token, st.secrets.jwt.secret_key, algorithms=['HS256'])
            username = payload['username']
            # If the token is expired, jwt.decode will raise an exception
        except jwt.ExpiredSignatureError:
            st.warning("Session expired. Please log in again.")
            st.write("""
                <script>
                window.top.location.href = "https://daddybetsgpt.com/login";
                </script>
            """, unsafe_allow_html=True)
            return
        except jwt.InvalidTokenError:
            st.warning("Invalid token. Please log in again.")
            st.write("""
                <script>
                window.top.location.href = "https://daddybetsgpt.com/login";
                </script>
            """, unsafe_allow_html=True)
            return

        # Fetch user details from Supabase
        SUPABASE_URL = st.secrets.supabase.url
        SUPABASE_KEY = st.secrets.supabase.api_key_admin
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        data = supabase.table('users').select('*').eq('username', username).execute()
        if data.data:
            st.session_state['logged_in'] = True
            st.session_state['user'] = data.data[0]
        else:
            st.warning("User not found. Please log in again.")
            st.write("""
                <script>
                window.top.location.href = "https://daddybetsgpt.com/login";
                </script>
            """, unsafe_allow_html=True)
            return

        # Proceed with chat functionality
        # Initialize OpenAI API
        oaiclient = OpenAI(api_key=st.secrets.openai.api_key)
        

        if 'messages' not in st.session_state:
            st.session_state['messages'] = []

        chatcontainer = ps.get_styled_container()
        promptcontainer = st.container(border=False)

        # Display previous messages
        with chatcontainer:
            for message in st.session_state['messages']:
                with st.chat_message(message['role']):
                    st.write(message['content'])

        # Chat input
        with promptcontainer:
            if prompt := st.chat_input("Type your message"):
                with st.chat_message("user"):
                    st.write(prompt)
                st.session_state['messages'].append({"role": "user", "content": prompt})

            with chatcontainer:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = oaiclient.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=st.session_state['messages'],
                            max_tokens=150
                        )
                        assistant_message = response['choices'][0]['message']['content']
                        st.write(assistant_message)
                        st.session_state['messages'].append({"role": "assistant", "content": assistant_message})

if __name__ == "__page__":
    main()
