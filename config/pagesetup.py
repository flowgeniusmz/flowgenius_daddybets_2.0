import streamlit as st
from streamlit_extras.stylable_container import stylable_container as sc

def display_background_image():
    # Set the Streamlit image for branding as the background with transparency
    background_image = 'https://storage.googleapis.com/production-domaincom-v1-0-8/048/1724048/4RBifvGs/dfc737c8f0d640cfa7e8623583bfcf5e'
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0.90)), url({background_image});
            background-size: cover;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def get_page_styling():
    with open("assets/styling/style.css" ) as css:
        st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)


def container_styled2(varKey):
    styledcontainer = sc(
        key=varKey,
        css_styles="""
        {
            border: 2px solid rgba(0, 0, 0, 0.2); /* Changed border color to a subtle grey */
            background-color: rgba(40, 94, 159, 0.75); /* Adjusted transparency for better visibility */
            border-radius: 0.5rem;
            padding: 1em; /* Added padding for better spacing */
            overflow: hidden; /* Keeps the content within the borders */
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2); /* Soft shadow for a 3D effect */
            transition: 0.3s; /* Smooth transition for hover effects */
            box-sizing: border-box;
        }
        """
    )


    return styledcontainer

def container_styled3(varKey):
    styledcontainer = sc(
        key=varKey,
        css_styles="""
        {
            border: 2px solid rgba(0, 0, 0, 0.2); /* Changed border color to a subtle grey */
            background-color: rgba(255, 255, 255, 0.75); /* Adjusted transparency for better visibility */
            border-radius: 0.5rem;
            padding: 1em; /* Added padding for better spacing */
            overflow: hidden; /* Keeps the content within the borders */
            box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2); /* Soft shadow for a 3D effect */
            transition: 0.3s; /* Smooth transition for hover effects */
            box-sizing: border-box;
        }
        """
    )


    return styledcontainer

def get_styled_container(border: bool=False, height: int=None):
    outer = container_styled2(varKey="outer")
    with outer:
        inner = container_styled3(varKey="inner")
        with inner:
            if height is not None:
                cont = st.container(border=border, height=height)
            else:
                cont = st.container(border=border)
    return cont
           
