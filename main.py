"""
Main TalentScout Pro application
"""
import streamlit as st
import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils import (
    init_session_state,
    extract_text_from_file,
    process_image_resume,
    update_candidate_info,
    reset_application
)
from storage import save_candidate_data, load_latest_assessment

SYSTEM_PROMPT = """
You are **TalentBot Pro**, an advanced AI hiring assistant conducting technical screenings for a tech recruitment agency.

### PHASE 1: INFORMATION COLLECTION
1. Politely greet the candidate and give a short summary of your purpose.
2. Ask for the following information, one at a time:
   - Full name  
   - Email address  
   - Phone number  
   - Years of relevant experience  
   - Desired position/role  
   - Current location (City, Country)  
3. Ask them to upload their resume (if possible).  
4. Request a comma-separated list of technical skills (programming languages, frameworks, tools, databases).

If a candidate provides unexpected or unclear inputs at any stage:
- Politely rephrase the question or give a simple example to clarify what is needed.
- If confusion continues, ask:  
  _"Would you like me to repeat the question or explain it in a simpler way?"_

### PHASE 2: TECHNICAL ASSESSMENT  
For each declared skill:
1. Ask **1 conceptual question** to test understanding.  
2. Ask **2 practical questions** to check hands-on knowledge.  
3. Ask **1 problem-solving question** to see how they apply their skills.  

Rules:
- Ask **only one question at a time**.
- **Wait for the candidate's answer** before moving to the next.
- Use the **experience level** to decide question difficulty.
- If a response is unclear or unrelated, say:  
  _"Thanks for your answer. Could you clarify or give an example?"_  
- If a candidate says something confusing, respond with:  
  _"I'm not sure I understood that. Would you like to try rephrasing it?"_

### PHASE 3: FINAL EVALUATION
Once all questions are answered:
1. Thank the candidate for their time.
2. Let them know that the team will review their responses.
3. Generate a short summary including:
   - Candidate details
   - Tech stack
   - List of asked questions with brief evaluation
   - Overall impression or recommendation (if asked)

### BEHAVIOR RULES:
- Always stay professional, friendly, and supportive.
- Maintain a clear and simple tone.
- Handle any confusion or mistakes politely.
- Use fallback prompts when needed to handle unexpected replies.
- If the user types exit keywords like "stop", "quit", or "end", politely say goodbye and end the conversation.


"""

# Updated UI Configuration
st.set_page_config(
    page_title="TalentScout Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Initialize Gemini
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash"))
except Exception as e:
    st.error(f"Failed to initialize Gemini: {str(e)}")
    st.stop()

# Initialize session state
init_session_state()

def get_ai_response(prompt):
    """Get response from Gemini AI"""
    try:
        # Check if we need to process an image resume
        if (st.session_state.candidate_info['resume_text'] == "IMAGE_RESUME" and 
            st.session_state.candidate_info['resume_file']):
            text = process_image_resume(
                st.session_state.candidate_info['resume_file'], 
                model
            )
            update_candidate_info('resume_text', text)
            return "Thank you for your resume. I've extracted the information. Now, could you please list your technical skills (comma separated)?"
        
        # Prepare conversation context
        messages = [{"role": "user", "parts": [SYSTEM_PROMPT]}]
        
        # Add message history (last 20 messages)
        for msg in st.session_state.messages[-40:]:
            messages.append({
                "role": msg["role"], 
                "parts": [msg["content"]]
            })
        
        # Add current prompt
        messages.append({"role": "user", "parts": [prompt]})
        
        # Generate response
        response = model.generate_content(messages)
        return response.text
        
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}. Please try again."

def generate_final_summary():
    """Generate a final summary of the conversation"""
    if not st.session_state.messages:
        return None
        
    # Prepare condensed conversation
    conversation = "\n".join(
        f"{msg['role']}: {msg['content']}" 
        for msg in st.session_state.messages
    )
    
    prompt = f"""
    Create a concise summary of this technical screening conversation:
    
    {conversation}
    
    Based on the answers provided by the candidate across all sessions, 
    create a final evaluation. Start by extracting the candidate's key 
    details including their full name, email address, phone number, the 
    role they applied for, and a list of their technical skills. Then, 
    evaluate each technology or tool they mentioned (such as Python, React, 
    etc.) and assign a proficiency score out of 10 based on the depth and 
    quality of their responses. After scoring the tech stack, write a brief 
    summary outlining the candidate's strengths — areas where they demonstrated 
    strong knowledge, clear thinking, or practical experience — and also mention 
    their weaknesses, such as lack of clarity, shallow understanding, or incomplete answers.

    Ensure the tone is clear, concise, and professional. 
    The final assessment should give hiring managers a quick but complete 
    overview of the candidate's technical abilities and overall fit for the role.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate summary: {str(e)}"

# Custom styling to prevent sidebar from collapsing
st.markdown("""
<style>
    /* Make sidebar permanently expanded and wider */
    section[data-testid="stSidebar"] {
        min-width: 600px !important;
        max-width: 600px !important;
        width: 600px !important;
    }
    
    /* Remove the collapse button completely */
    button[title="Collapse sidebar"] {
        display: none !important;
    }
    
    /* Adjust main content area */
    .main .block-container {
        padding-left: 2rem;
        padding-right: 2rem;
        max-width: calc(100% - 600px);
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 12px 16px;
        margin-bottom: 8px;
        border-radius: 8px;
    }
    
    /* Chat input positioning */
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 20px;
        width: calc(100% - 620px);
    }
    
    /* Summary section styling */
    .summary-container {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 8px;
        margin-top: 1rem;
    }
    
    /* Sidebar section headers */
    .sidebar .stSubheader {
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application layout with summary on left sidebar"""
    # Permanent left sidebar - now with summary display
    with st.sidebar:
        st.header("📋 Candidate Assessment")
        
        # Display final summary if available
        if hasattr(st.session_state, 'final_summary'):
            st.subheader("Final Assessment Summary")
            with st.container():
                st.markdown(st.session_state.final_summary)
            st.markdown("---")
        
        # Resume upload section
        if not st.session_state.candidate_info['resume_file']:
            st.subheader("Upload Resume")
            uploaded_file = st.file_uploader(
                " ",
                type=["pdf", "docx", "png", "jpg", "jpeg"],
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                update_candidate_info('resume_file', uploaded_file)
                text = extract_text_from_file(uploaded_file)
                update_candidate_info('resume_text', text)
                st.rerun()
        
        # Technical skills display
        if st.session_state.tech_stack:
            st.subheader("Technical Skills")
            for skill in st.session_state.tech_stack:
                st.markdown(f"- {skill}")
        
        # Action buttons at bottom
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start New Screening", use_container_width=True):
                reset_application()
        with col2:
            if st.button("Download Report", 
                       disabled=not hasattr(st.session_state, 'final_summary'),
                       use_container_width=True):
                pass  # Handled in main area
        
        if st.button("Generate Summary", 
                    disabled=len(st.session_state.messages) == 0,
                    key="generate_btn",
                    use_container_width=True):
            summary = generate_final_summary()
            if summary:
                st.session_state.final_summary = summary
                st.session_state.conversation_ended = True
                st.rerun()

    # Main chat area
    st.header("TalentScout Pro - AI Screening Assistant")
    
    # Chat display area
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Fixed chat input at bottom
    if not st.session_state.conversation_ended:
        if prompt := st.chat_input("Type your answer here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.spinner("Thinking..."):
                response = get_ai_response(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()

if __name__ == "__main__":
    main()
