import streamlit as st
import pandas as pd
import os
import time
import random
import csv
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="Quiz: Test Your Numpy Knowledge on Streamlit",
    page_icon="🗒️",
)

# Session state initialization
if 'quiz_state' not in st.session_state:
    st.session_state.update({
        'quiz_state': 'not_started',
        'admin_logged_in': False,
        'current_question': 0,
        'user_answers': {},
        'shuffled_options': {},
        'question_feedback': [],
        'quiz_duration': 0,
        'final_score': 0
    })

st.title("🗒️ Quiz: Test Your Numpy Knowledge on Streamlit")
st.markdown("""
Self-Assessment: W3Schools NumPy Topics (February 19, 2025)

Key Topics from W3Schools NumPy Module

https://www.w3schools.com/python/numpy/numpy_ufunc.asp

NumPy ufunc ufun Intro, ufunc Create Function, ufunc Simple Arithmetic, ufunc Rounding Decimals, ufunc Logs, ufunc Summations, ufunc Products, ufunc Differences, ufunc Finding LCM, ufunc Finding GCD, ufunc Trigonometric, ufunc Hyperbolic, ufunc Set Operations
""")
QUESTIONS_FILE = "numpy4.csv"

# --- Main Quiz Logic ---
def load_questions():
    """Load questions with caching and validation"""
    try:
        df = pd.read_csv(QUESTIONS_FILE)
        required_columns = ['question', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
        
        if not all(col in df.columns for col in required_columns):
            st.error("Invalid question format in database")
            return None
            
        return df.sample(frac=1).reset_index(drop=True)  # Shuffle questions
    except FileNotFoundError:
        st.error("Question database not found")
        return None

def display_question():
    """Display current question with stable shuffled options"""
    idx = st.session_state.current_question
    row = st.session_state.quiz_df.iloc[idx]
    
    # Generate consistent shuffled options for this question
    if idx not in st.session_state.shuffled_options:
        options = [row['option1'], row['option2'], row['option3'], row['option4']]
        random.shuffle(options)
        st.session_state.shuffled_options[idx] = options
    
    options = st.session_state.shuffled_options[idx]
    
    with st.expander(f"Question {idx + 1}", expanded=True):
        st.markdown(f"#### {row['question']}")
        
        # Display options as buttons
        cols = st.columns(2)
        for i, option in enumerate(options):
            with cols[i % 2]:
                btn_type = "primary" if st.session_state.user_answers.get(idx) == option else "secondary"
                if st.button(
                    option,
                    key=f"q{idx}_opt{i}",
                    use_container_width=True,
                    type=btn_type
                ):
                    st.session_state.user_answers[idx] = option

# --- Quiz Interface ---
if st.session_state.quiz_state == 'not_started':
    if st.button("🚀 Start Quiz"):
        st.session_state.quiz_df = load_questions()
        if st.session_state.quiz_df is not None:
            st.session_state.quiz_state = 'in_progress'
            st.session_state.start_time = time.time()
            st.rerun()

if st.session_state.quiz_state == 'in_progress':
    # Quiz progress
    current_q = st.session_state.current_question
    total_q = len(st.session_state.quiz_df)
    
    # Display progress
    progress = (current_q + 1) / total_q
    st.progress(progress, text=f"Question {current_q + 1} of {total_q}")
    
    # Display current question
    display_question()
    
    # Navigation controls
    col1, col2 = st.columns([8, 1.2])
    with col1:
        if current_q > 0:
            st.button("Previous", on_click=lambda: st.session_state.update({"current_question": current_q - 1}))
    with col2:    
        if current_q < total_q - 1:
            st.button("Next ", on_click=lambda: st.session_state.update({"current_question": current_q + 1}))
        else:
            if st.button("Submit", type="primary"):
                # Calculate results
                question_feedback = []
                for idx in range(total_q):
                    row = st.session_state.quiz_df.iloc[idx]
                    user_answer = st.session_state.user_answers.get(idx)
                    correct_answer = row['correct_answer']
                    
                    # Verify answer exists in shuffled options
                    shuffled = st.session_state.shuffled_options.get(idx, [])
                    actual_correct = correct_answer in shuffled
                    
                    is_correct = (user_answer == correct_answer) if actual_correct else False
                    result = "Correct" if is_correct else "Incorrect"
                    
                    question_feedback.append({
                        'Question': row['question'],
                        'Your Answer': user_answer or "Not answered",
                        'Correct Answer': correct_answer,
                        'Result': result
                    })
                
                # Update session state
                st.session_state.question_feedback = question_feedback
                st.session_state.quiz_duration = time.time() - st.session_state.start_time
                st.session_state.final_score = sum(1 for fb in question_feedback if fb['Result'] == "Correct")
                st.session_state.quiz_state = 'completed'
                st.rerun()

elif st.session_state.quiz_state == 'completed':
    # Display results
    st.balloons()
    st.subheader("📝 Quiz Results Summary")
    
    # Score and time
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f" **Final Score:**  \n{st.session_state.final_score}/{len(st.session_state.quiz_df)}")
    with col2:
        mins = int(st.session_state.quiz_duration // 60)
        secs = int(st.session_state.quiz_duration % 60)
        st.markdown(f"**Time Taken:**  \n{mins} minutes {secs} seconds")
    
    # Detailed feedback
    st.subheader("Detailed Feedback")
    
    # Styling function for results
    def color_result(val):
        color = 'green' if val == 'Correct' else 'red'
        return f'background-color: {color}; color: white'
    
    # Create and display styled results table
    feedback_df = pd.DataFrame(st.session_state.question_feedback)
    styled_feedback = feedback_df.style.applymap(color_result, subset=['Result'])
    st.table(styled_feedback)
    
    # Restart button
    if st.button("🔄 Take Quiz Again"):
        st.session_state.quiz_state = 'not_started'
        st.session_state.current_question = 0
        st.session_state.user_answers = {}
        st.session_state.shuffled_options = {}
        st.session_state.question_feedback = []
        st.rerun()
