import streamlit as st
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

quiz_function = {
    "name": "create_quiz",
    "description": "Function that takes a list of questions and answers and returns a quiz",
    "parameters": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answers": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "answer": {"type": "string"},
                                    "correct": {"type": "boolean"}
                                },
                                "required": ["answer", "correct"]
                            }
                        }
                    },
                    "required": ["question", "answers"]
                }
            }
        },
        "required": ["questions"]
    }
}

st.sidebar.title("QuizGPT Settings")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
st.sidebar.markdown("[GitHub Repository](https://github.com/GTAEKI/Use_AI_Practice.git)")

st.title("QuizGPT")
topic = st.text_input("Enter a topic for the quiz", value="Rome")
difficulty = st.selectbox("Select Quiz Difficulty", options=["Easy", "Hard"])

@st.cache_data(show_spinner="Generating quiz...")
def generate_quiz(topic: str, difficulty: str, api_key: str):
    llm = ChatOpenAI(
        openai_api_key=api_key,
        temperature=0.1,
        model_name="gpt-3.5-turbo"
    ).bind(
        function_call={"name": "create_quiz"},
        functions=[quiz_function]
    )
    prompt = ChatPromptTemplate.from_messages([
        ("user", "Make a quiz about {topic} with {difficulty} difficulty.")
    ])
    chain = prompt | llm
    response = chain.invoke({"topic": topic, "difficulty": difficulty})
    return response

if st.button("Generate Quiz"):
    if not api_key:
        st.error("Please enter your OpenAI API Key in the sidebar.")
    else:
        response = generate_quiz(topic, difficulty, api_key)
        quiz_data = json.loads(response.additional_kwargs["function_call"]["arguments"])
        st.session_state.quiz = quiz_data
        st.session_state.score = 0
        st.session_state.current_question = 0

if "quiz" in st.session_state:
    quiz = st.session_state.quiz
    questions = quiz.get("questions", [])
    current_q = st.session_state.current_question

    if current_q < len(questions):
        question_item = questions[current_q]
        st.write(f"**Question {current_q + 1}:** {question_item['question']}")
        
        options = [opt["answer"] for opt in question_item["answers"]]
        user_choice = st.radio("Select an answer:", options, key=f"question_{current_q}")
        
        if st.button("Submit Answer", key=f"submit_{current_q}"):
            correct_answer = next((ans["answer"] for ans in question_item["answers"] if ans["correct"]), None)
            if user_choice == correct_answer:
                st.success("Correct!")
                st.session_state.score += 1
            else:
                st.error(f"Wrong! The correct answer is: {correct_answer}")
            st.session_state.current_question += 1
            st.experimental_rerun()
    else:
        total = len(questions)
        score = st.session_state.score
        st.write(f"Quiz Completed! Your score: {score} / {total}")
        if score == total:
            st.balloons()
        else:
            if st.button("Retry Quiz"):
                for key in ["quiz", "score", "current_question"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.experimental_rerun()
