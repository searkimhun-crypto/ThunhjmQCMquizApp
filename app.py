import streamlit as st
import pypdf
import random
import re

st.set_page_config(page_title="Automated QCM Platform", layout="wide")

if "question_bank" not in st.session_state:
    st.session_state.question_bank = {}
if "active_quiz" not in st.session_state:
    st.session_state.active_quiz = []
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

def parse_pdf_to_qcm(file_obj):
    pdf_reader = pypdf.PdfReader(file_obj)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n"
    
    raw_questions = re.split(r'\n(?=\d+[\.\:\)])|(?=Question \d+)', full_text)
    parsed_questions = []
    
    for rq in raw_questions:
        if not rq.strip():
            continue
        lines = [line.strip() for line in rq.split('\n') if line.strip()]
        if len(lines) < 3: 
            continue
            
        question_text = "\n".join(lines[:-1]) if "ANSWER:" in lines[-1].upper() or "REPONSE:" in lines[-1].upper() else "\n".join(lines)
        choices = []
        correct_answer = None
        
        for line in lines[1:]:
            if re.match(r'^[A-D][\.\)\-\s]', line):
                choices.append(line)
            if "ANSWER:" in line.upper() or "REPONSE:" in line.upper():
                ans_match = re.search(r'(?:ANSWER|REPONSE):\s*([A-D])', line, re.IGNORECASE)
                if ans_match:
                    correct_answer = ans_match.group(1)

        if not correct_answer:
            correct_answer = "A" 
            
        if len(choices) >= 2:
            parsed_questions.append({
                "question": question_text,
                "choices": choices,
                "correct": correct_answer
            })
            
    return parsed_questions

st.title("📚 Smart QCM Exam Generator & Grader")
st.write("Upload your subject PDFs to build a database of thousands of randomized questions.")

with st.sidebar:
    st.header("⚙️ Teacher Dashboard")
    subject_input = st.text_input("1. Enter Subject Name (e.g., Biology, Physics):", value="General")
    uploaded_files = st.file_uploader("2. Upload PDF Files for this Subject:", type=["pdf"], accept_multiple_files=True)
    
    if st.button("Process & Import into Question Bank"):
        if uploaded_files:
            if subject_input not in st.session_state.question_bank:
                st.session_state.question_bank[subject_input] = []
                
            total_added = 0
            for file in uploaded_files:
                questions = parse_pdf_to_qcm(file)
                st.session_state.question_bank[subject_input].extend(questions)
                total_added += len(questions)
                
            st.success(f"Successfully added {total_added} questions to {subject_input}!")
        else:
            st.error("Please upload at least one PDF file.")

    st.write("---")
    st.header("📊 Question Bank Status")
    if st.session_state.question_bank:
        for subj, q_list in st.session_state.question_bank.items():
            st.write(f"• **{subj}**: {len(q_list)} total questions loaded")
    else:
        st.info("Question Bank is currently empty.")

st.header("📝 Student Examination Center")

if not st.session_state.question_bank:
    st.warning("Please use the sidebar dashboard to upload your PDF files and populate the question bank first.")
else:
    col1, col2 = st.columns(2)
    with col1:
        selected_subject = st.selectbox("Choose Subject to Test:", list(st.session_state.question_bank.keys()))
    with col2:
        num_questions = st.number_input("Number of Random Questions to generate:", min_value=1, max_value=100, value=5)

    if st.button("🚀 Generate New Randomized Exam"):
        available_pool = st.session_state.question_bank[selected_subject]
        if len(available_pool) < num_questions:
            num_questions = len(available_pool)
        
        st.session_state.active_quiz = random.sample(available_pool, num_questions)
        st.session_state.quiz_submitted = False
        st.rerun()

    if st.session_state.active_quiz:
        st.write("---")
        st.subheader(f"Exam Paper: {selected_subject} ({len(st.session_state.active_quiz)} Questions)")
        
        student_responses = {}
        
        for idx, q_item in enumerate(st.session_state.active_quiz):
            st.markdown(f"**Question {idx + 1}:**")
            st.text(q_item['question'])
            
            user_choice = st.radio(
                f"Select option for question {idx+1}:", 
                q_item['choices'], 
                key=f"q_{idx}",
                label_visibility="collapsed"
            )
            
            picked_letter = user_choice if user_choice else "A"
            student_responses[idx] = picked_letter
            st.write("")

        if not st.session_state.quiz_submitted:
            if st.button("Submit Exam for Auto-Correction"):
                st.session_state.quiz_submitted = True
                st.rerun()

        if st.session_state.quiz_submitted:
            st.write("---")
            correct_count = 0
            
            for idx, q_item in enumerate(st.session_state.active_quiz):
                student_ans = student_responses.get(idx)
                actual_correct = q_item['correct']
                
                if student_ans == actual_correct:
                    correct_count += 1
                    st.success(f"**Question {idx+1}: Correct!** You answered option {student_ans}.")
                else:
                    st.error(f"**Question {idx+1}: Incorrect.** You answered option {student_ans}. The correct answer was option **{actual_correct}**.")
            
            score_percentage = (correct_count / len(st.session_state.active_quiz)) * 100
            st.metric(label="Your Final Exam Score", value=f"{correct_count} / {len(st.session_state.active_quiz)}", delta=f"{score_percentage:.1f}%")
            
            if score_percentage >= 50:
                st.balloons()
