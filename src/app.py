import streamlit as st
import asyncio
import json
from pathlib import Path
from agents.orchestrator import OrchestratorAgent

# Page config
st.set_page_config(
    page_title="RecruitX - AI-Powered Recruitment Matching",
    page_icon="🎯",
    layout="wide"
)

# Title and description
st.title("🎯 RecruitX")
st.markdown("""
AI-powered recruitment matching system that:
- Processes job descriptions and resumes
- Extracts key information using Gemini and FLAIR
- Matches candidates using semantic similarity
- Provides detailed insights and recommendations
""")

# Initialize session state
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = OrchestratorAgent()
    
if 'processing' not in st.session_state:
    st.session_state.processing = False

# File upload section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Job Description")
    jd_file = st.file_uploader("Upload Job Description (PDF/DOCX)", type=['pdf', 'docx'])
    
with col2:
    st.subheader("Resumes")
    resume_files = st.file_uploader("Upload Resumes (PDF/DOCX)", type=['pdf', 'docx'], accept_multiple_files=True)

# Process files when uploaded
if jd_file and resume_files:
    if not st.session_state.processing and st.button("Process and Match"):
        st.session_state.processing = True
        
        # Create data directory if it doesn't exist
        data_dir = Path("data/uploads")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded files
        jd_path = data_dir / jd_file.name
        with open(jd_path, "wb") as f:
            f.write(jd_file.getvalue())
            
        resume_paths = []
        for resume in resume_files:
            resume_path = data_dir / resume.name
            with open(resume_path, "wb") as f:
                f.write(resume.getvalue())
            resume_paths.append(str(resume_path))
        
        # Create request for orchestrator
        request = {
            "jd_path": str(jd_path),
            "resume_paths": resume_paths
        }
        
        with st.spinner("Processing documents and matching candidates..."):
            try:
                # Run orchestrator
                result = asyncio.run(
                    st.session_state.orchestrator.run(json.dumps(request))
                )
                
                # Display results
                st.markdown("## Results")
                st.text(result)
                
                # Clean up uploaded files
                jd_path.unlink()
                for path in resume_paths:
                    Path(path).unlink()
                    
            except Exception as e:
                st.error(f"Error during processing: {str(e)}")
                
            finally:
                st.session_state.processing = False
                
# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit, Gemini, and FLAIR") 