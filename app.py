import streamlit as st
import pandas as pd
import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Title of the app
st.title("Live Quiz App")

# Collect user email for identification
user_email = st.sidebar.text_input("Enter your email to track your quiz results:", "")

# Make email input compulsory
if not user_email:
    st.sidebar.warning("⚠️ Email is required to proceed. Please enter your email.")
    st.stop()  # Stop execution if email is not provided
else:
    st.sidebar.success(f"Welcome, {user_email}!")

# Sidebar for topic selection using checkboxes
st.sidebar.header("Quiz Topics")
quiz_files = [file for file in os.listdir() if file.endswith('.csv')]  # List all CSV files in the directory

# Initialize session state for tracking the selected topic
if 'selected_topic' not in st.session_state:
    st.session_state.selected_topic = None

# Create a dictionary to store the state of each checkbox
selected_topics = {}
for file in quiz_files:
    topic_name = os.path.splitext(file)[0]  # Remove the .csv extension for display
    # Check if this topic is the currently selected one
    is_selected = st.sidebar.checkbox(
        topic_name,
        value=(st.session_state.selected_topic == topic_name),
        key=topic_name
    )
    
    # If this checkbox is selected, update the session state
    if is_selected:
        if st.session_state.selected_topic != topic_name:
            st.session_state.selected_topic = topic_name  # Update the selected topic
            # Uncheck other checkboxes by rerunning the app
            st.experimental_rerun()
    selected_topics[topic_name] = is_selected

# Get the selected file based on the session state
selected_file = None
if st.session_state.selected_topic:
    selected_file = f"{st.session_state.selected_topic}.csv"

# Handle cases where no topic is selected
if not selected_file:
    st.info("Please select a quiz topic from the sidebar.")
else:
    # Path to the selected CSV file
    csv_file_path = selected_file

    # Check if the selected CSV file exists
    if not os.path.exists(csv_file_path):
        st.error(f"File '{csv_file_path}' not found in the current directory.")
    else:
        try:
            # Load the selected CSV file into a DataFrame
            df = pd.read_csv(csv_file_path)

            # Check if the CSV has the required columns
            required_columns = ['question', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
            if not all(column in df.columns for column in required_columns):
                st.error(f"CSV must contain the following columns: {', '.join(required_columns)}")
            else:
                st.success(f"Quiz loaded for topic: {os.path.splitext(csv_file_path)[0]}!")

                # Initialize session state for quiz
                if 'user_answers' not in st.session_state:
                    st.session_state.user_answers = {}

                # Display all questions
                st.subheader("Answer the following questions:")
                for idx, row in df.iterrows():
                    question_key = f"q_{idx}"
                    options = [row['option1'], row['option2'], row['option3'], row['option4']]
                    selected_option = st.radio(
                        f"**Q{idx + 1}: {row['question']}**",
                        options,
                        key=question_key
                    )
                    st.session_state.user_answers[idx] = selected_option

                # Submit button
                if st.button("Submit"):
                    # Calculate score and prepare feedback
                    score = 0
                    feedback = []

                    for idx, row in df.iterrows():
                        user_answer = st.session_state.user_answers.get(idx, None)
                        correct_answer = row['correct_answer']
                        is_correct = user_answer == correct_answer
                        score += int(is_correct)

                        feedback.append({
                            "Question": row['question'],
                            "Your Answer": user_answer,
                            "Correct Answer": correct_answer,
                            "Result": "Correct" if is_correct else "Incorrect"
                        })

                        # Log the response to Firebase
                        db.collection('responses').add({
                            'email': user_email,
                            'question': row['question'],
                            'user_answer': user_answer,
                            'correct_answer': correct_answer,
                            'is_correct': is_correct,
                            'timestamp': firestore.SERVER_TIMESTAMP
                        })

                    # Log the overall score to Firebase
                    db.collection('scores').add({
                        'email': user_email,
                        'score': score,
                        'total_questions': len(df),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    })

                    # Display results
                    st.subheader("Quiz Results")
                    st.write(f"Your final score is: {score} / {len(df)}")

                    # Display detailed feedback with highlighting
                    st.subheader("Detailed Feedback")

                    # Define a function to apply conditional formatting
                    def color_result(val):
                        color = 'green' if val == 'Correct' else 'red'
                        return f'background-color: {color}'

                    # Create a DataFrame for feedback
                    feedback_df = pd.DataFrame(feedback)

                    # Apply the styling to the "Result" column
                    styled_feedback_df = feedback_df.style.applymap(color_result, subset=['Result'])

                    # Display the styled table
                    st.table(styled_feedback_df)

                    # Reset session state for a new quiz
                    st.session_state.user_answers = {}

        except Exception as e:
            st.error(f"Error parsing the CSV file: {e}")