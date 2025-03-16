import streamlit as st
import os
from pathlib import Path
from typing import List, Dict, Any
import tempfile
import sqlite3

from ..utils.document_parser import DocumentParser
from ..models.entity_extractor import EntityExtractor
from ..models.matching_engine import MatchingEngine

# Initialize components
document_parser = DocumentParser()
entity_extractor = EntityExtractor()
matching_engine = MatchingEngine()

def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file to temporary directory and return path."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        return tmp_file.name

def process_document(file_path: str) -> Dict[str, Any]:
    """Process a document and return its ID and entities."""
    # Parse document
    doc_info = document_parser.parse_document(file_path)
    
    # Store document in database
    conn = sqlite3.connect(Path(__file__).parent.parent.parent / 'data' / 'prototype.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Documents (file_name, file_type, parsed_text)
        VALUES (?, ?, ?)
    ''', (
        os.path.basename(file_path),
        doc_info['file_type'],
        doc_info['text']
    ))
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # Extract entities
    entities = entity_extractor.extract_entities(doc_info['text'], doc_id)
    
    return {
        'id': doc_id,
        'entities': entities
    }

def main():
    st.title("RecruitX - AGI-Level Recruitment Matching")
    st.write("Upload job descriptions and resumes to find the best matches.")
    
    # File upload section
    st.header("Upload Documents")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Description")
        jd_file = st.file_uploader("Upload JD", type=['pdf', 'docx'])
        
    with col2:
        st.subheader("Resumes")
        resume_files = st.file_uploader("Upload Resumes", type=['pdf', 'docx'], accept_multiple_files=True)
    
    if jd_file and resume_files:
        if st.button("Find Matches"):
            with st.spinner("Processing documents..."):
                # Process job description
                jd_path = save_uploaded_file(jd_file)
                jd_info = process_document(jd_path)
                
                # Process resumes
                resume_ids = []
                for resume_file in resume_files:
                    resume_path = save_uploaded_file(resume_file)
                    resume_info = process_document(resume_path)
                    resume_ids.append(resume_info['id'])
                
                # Find matches
                matches = matching_engine.find_matches(jd_info['id'], resume_ids)
                
                # Display results
                st.header("Matching Results")
                
                for match in matches:
                    with st.expander(f"Match Score: {match['score']:.2f}"):
                        match_details = matching_engine.get_match_details(match['match_id'])
                        if match_details:
                            st.write(f"**Resume:** {match_details['resume_file_name']}")
                            st.write(f"**Insight:** {match_details['insight']}")
                            
                            # Display entities
                            st.subheader("Key Entities")
                            entities = entity_extractor.get_document_entities(match_details['resume_id'])
                            for entity in entities:
                                st.write(f"- {entity['entity_type']}: {entity['entity_value']}")

if __name__ == "__main__":
    main() 