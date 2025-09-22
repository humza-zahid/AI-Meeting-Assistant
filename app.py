import streamlit as st

# Page config
st.set_page_config(page_title="Hello Streamlit", page_icon="✨")

# Title
st.title("✨ My First Streamlit App")

# Text input
name = st.text_input("What's your name?", "World")

# Number input
age = st.number_input("How old are you?", min_value=1, max_value=120, value=25)

# Button
if st.button("Say Hello"):
    st.success(f"Hello {name}, you are {age} years old! 🎉")

# Show some data
st.subheader("Sample Data Table")
st.dataframe({
    "Fruit": ["Apple", "Banana", "Cherry"],
    "Count": [10, 20, 15]
})

# Chart
st.subheader("Sample Line Chart")
st.line_chart({"data": [1, 3, 2, 4, 5, 6, 7]})
