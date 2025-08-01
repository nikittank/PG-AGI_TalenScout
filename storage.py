"""
Data storage and persistence functions
"""
import json
import os
from datetime import datetime
import streamlit as st

def save_candidate_data():
    """Save candidate data to JSON file"""
    try:
        if not os.path.exists('candidate_data'):
            os.makedirs('candidate_data')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"candidate_data/candidate_{timestamp}.json"
        
        data = {
            "timestamp": datetime.now().isoformat(),
            "candidate_info": st.session_state.candidate_info,
            "tech_stack": st.session_state.tech_stack,
            "assessment": st.session_state.final_assessment
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    except Exception as e:
        st.error(f"Failed to save data: {str(e)}")
        return None

def load_latest_assessment():
    """Load the most recent assessment from storage"""
    try:
        if not os.path.exists('candidate_data'):
            return None
            
        files = [f for f in os.listdir('candidate_data') if f.endswith('.json')]
        if not files:
            return None
            
        latest_file = max(files)
        with open(f"candidate_data/{latest_file}", 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load assessment: {str(e)}")
        return None