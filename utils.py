"""
Utility functions for TalentScout Pro
"""
import io
import PyPDF2
import docx
from PIL import Image
import google.generativeai as genai
import streamlit as st

def init_session_state():
    """Initialize all session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "Welcome to TalentScout Pro! May I have your full name to begin?"
        }]
    
    if "candidate_info" not in st.session_state:
        st.session_state.candidate_info = {
            "full_name": "",
            "email": "",
            "phone": "",
            "experience": "",
            "position": "",
            "location": "",
            "resume_text": "",
            "resume_file": None
        }
    
    if "tech_stack" not in st.session_state:
        st.session_state.tech_stack = []
    
    if "current_tech_index" not in st.session_state:
        st.session_state.current_tech_index = -1
    
    if "assessment_complete" not in st.session_state:
        st.session_state.assessment_complete = False
    
    if "final_assessment" not in st.session_state:
        st.session_state.final_assessment = None
        
    if "conversation_ended" not in st.session_state:
        st.session_state.conversation_ended = False

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded resume file"""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            return "\n".join([page.extract_text() for page in pdf_reader.pages])
        
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            return "\n".join([para.text for para in doc.paragraphs])
        
        elif uploaded_file.type.startswith('image/'):
            return "IMAGE_RESUME"
        
        return "Unsupported file type"
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return ""

def process_image_resume(image_file, model):
    """Extract text from image resume using Gemini"""
    try:
        img = Image.open(image_file)
        response = model.generate_content([
            "Extract all text from this resume. Focus on: "
            "skills, experience, education, certifications.",
            img
        ])
        return response.text
    except Exception as e:
        st.error(f"Failed to process image: {str(e)}")
        return ""

def update_candidate_info(field, value):
    """Update candidate information in session state"""
    st.session_state.candidate_info[field] = value

def reset_application():
    """Reset the application to initial state"""
    keys_to_keep = ['final_assessment']
    
    # Save final assessment if exists
    final_data = {k: st.session_state[k] for k in keys_to_keep if k in st.session_state}
    
    # Clear session state
    st.session_state.clear()
    
    # Restore final assessment
    for k, v in final_data.items():
        st.session_state[k] = v
    
    # Reinitialize
    init_session_state()
    st.rerun()