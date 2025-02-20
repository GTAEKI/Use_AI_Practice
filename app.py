import streamlit as st
from datetime import datetime


st.set_page_config(
    page_title="GPT Course",
    page_icon="🥰"
)

time = datetime.today().strftime("%H:%M:%S")
st.title(f"Now: {time}")

with st.sidebar:
    st.title("sidebar")
    st.text_input("이름 입력")

st.markdown(
    """
# Hello!

Welcome to my FullstackGPT Portfolio!

Here are the apps I made:

- [ ] [DocumentGPT](/DocumentGPT)
- [ ] [PrivateGPT](/PrivateGPT)
- [ ] [QuizGPT](/QuizGPT)
- [ ] [SiteGPT](/SiteGPT)
- [ ] [MeetingGPT](/MeetingGPT)
- [ ] [InvestorGPT](/InvestorGPT)
""")

tab_one, tab_two, tab_three = st.tabs(["A","B","C"])

with tab_one:
    st.write("a")

with tab_two:
    st.write("b")

with tab_three:
    st.write("c")