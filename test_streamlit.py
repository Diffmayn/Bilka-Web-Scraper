import streamlit as st

st.title("Bilka Price Monitor - Test")
st.write("If you can see this, Streamlit is working!")

st.header("Test Features")
st.metric("Test Metric", 42)
st.success("✅ Basic functionality working!")

if st.button("Test Button"):
    st.write("Button clicked!")

st.sidebar.header("Sidebar Test")
st.sidebar.write("Sidebar is working!")