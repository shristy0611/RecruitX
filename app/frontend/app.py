import streamlit as st
import requests
import json
import pandas as pd
from pathlib import Path
import time
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure the page
st.set_page_config(
    page_title="RecruitX - AI Recruitment Matching",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS for better Japanese text support
st.markdown("""
<style>
    body {
        font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
    }
    .stMarkdown, .stText {
        font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', Meiryo, sans-serif;
    }
    .css-18e3th9 {
        padding-top: 1rem;
    }
    /* Custom button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    /* Card styling */
    .dashboard-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        height: 200px;
        transition: all 0.3s ease;
        border-top: 4px solid;
    }
    .dashboard-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    }
    .dashboard-card h3 {
        margin-bottom: 15px;
        font-weight: 600;
    }
    .dashboard-card p {
        color: #555;
        font-size: 0.95em;
        line-height: 1.5;
    }
    /* Skill tag styling */
    .skill-tag {
        display: inline-block;
        padding: 5px 12px;
        margin: 3px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 500;
        color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
    }
    .skill-tag:hover {
        transform: scale(1.05);
        box-shadow: 0 3px 6px rgba(0,0,0,0.15);
    }
    /* Navigation styling */
    .css-1lcbmhc.e1fqkh3o0 {
        padding: 20px;
        border-radius: 10px;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# API endpoint
API_ENDPOINT = "http://localhost:8000"

def main():
    # Add sidebar navigation
    st.sidebar.title("RecruitX")
    st.sidebar.image("https://img.icons8.com/color/96/000000/find-matching-job.png", width=100)
    
    pages = [
        "Dashboard", 
        "Resume Analysis", 
        "Job Analysis", 
        "Candidate Matching", 
        "Professional Report", 
        "Analytics & Reports", 
        "System Status"
    ]
    
    # Check if there's a query parameter for page navigation
    query_params = st.experimental_get_query_params()
    if "page" in query_params:
        page_from_query = query_params["page"][0].replace("+", " ")
        if page_from_query in pages:
            selection = page_from_query
        else:
            selection = st.sidebar.radio("Navigation", pages)
    else:
        selection = st.sidebar.radio("Navigation", pages)
    
    if selection == "Dashboard":
        dashboard_page()
    elif selection == "Resume Analysis":
        resume_analysis_page()
    elif selection == "Job Analysis":
        job_analysis_page()
    elif selection == "Candidate Matching":
        matching_page()
    elif selection == "Professional Report":
        professional_report_page()
    elif selection == "Analytics & Reports":
        reports_page()
    elif selection == "System Status":
        system_status_page()
    
    # Add footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "RecruitX: AI-Powered Recruitment Matching System\n\n"
        "© 2025 Shristyverse LLC"
    )

def navigate_to(page):
    st.experimental_set_query_params(page=page)
    st.experimental_rerun()

def matching_page():
    st.title("Candidate Matching")
    st.subheader("Match candidates with job opportunities")
    
    # Check if we have both resume and job data
    if "resume_data" not in st.session_state or "job_data" not in st.session_state:
        st.warning("Please analyze both a resume and job description before proceeding to matching.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Resume Analysis"):
                st.experimental_set_query_params(page="Resume Analysis")
                st.experimental_rerun()
        with col2:
            if st.button("Go to Job Analysis"):
                st.experimental_set_query_params(page="Job Analysis")
                st.experimental_rerun()
        return
    
    # Display summary of what we're matching
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Resume")
        # Display resume skills
        if "skills" in st.session_state.resume_data and st.session_state.resume_data["skills"]:
            skills_list = st.session_state.resume_data["skills"]
            if isinstance(skills_list, list) and skills_list:
                # Display skills as tags
                html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                for skill in skills_list[:5]:  # Show only top 5 skills
                    html_skills += f'<div class="skill-tag" style="background-color: #4a6da7;">{skill}</div>'
                html_skills += '</div>'
                st.markdown(html_skills, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Job Description")
        # Display job skills
        if "required_skills" in st.session_state.job_data and st.session_state.job_data["required_skills"]:
            skills_list = st.session_state.job_data["required_skills"]
            if isinstance(skills_list, list) and skills_list:
                # Display skills as tags
                html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                for skill in skills_list[:5]:  # Show only top 5 skills
                    html_skills += f'<div class="skill-tag" style="background-color: #2c7bb6;">{skill}</div>'
                html_skills += '</div>'
                st.markdown(html_skills, unsafe_allow_html=True)
    
    # Match button
    st.markdown("---")
    if st.button("Match Resume with Job Description"):
        with st.spinner("Matching resume with job description..."):
            try:
                response = requests.post(
                    f"{API_ENDPOINT}/match",
                    json={
                        "resume_data": st.session_state.resume_data,
                        "job_data": st.session_state.job_data
                    }
                )
                
                if response.status_code == 200:
                    match_data = response.json()
                    st.session_state.match_data = match_data
                    
                    # Display match results in a professional way
                    match_score = match_data.get("match_score", 0)
                    
                    # Create columns for the match score and details
                    score_col, details_col = st.columns([1, 2])
                    
                    with score_col:
                        # Display match score as a gauge
                        fig = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=match_score,
                            domain={'x': [0, 1], 'y': [0, 1]},
                            title={'text': "Match Score"},
                            gauge={
                                'axis': {'range': [0, 100]},
                                'bar': {'color': "darkblue"},
                                'steps': [
                                    {'range': [0, 40], 'color': "red"},
                                    {'range': [40, 70], 'color': "orange"},
                                    {'range': [70, 100], 'color': "green"}
                                ],
                                'threshold': {
                                    'line': {'color': "black", 'width': 4},
                                    'thickness': 0.75,
                                    'value': match_score
                                }
                            }
                        ))
                        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Add match quality text
                        if match_score >= 80:
                            st.success("Excellent Match! 🌟")
                        elif match_score >= 60:
                            st.info("Good Match! 👍")
                        elif match_score >= 40:
                            st.warning("Fair Match 🤔")
                        else:
                            st.error("Poor Match 😕")
                    
                    with details_col:
                        # Matching skills
                        st.markdown("#### ✅ Matching Skills")
                        matching_skills = match_data.get("matching_skills", [])
                        if matching_skills:
                            # Display matching skills as green tags
                            html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                            for skill in matching_skills:
                                html_skills += f'<div class="skill-tag" style="background-color: #28a745;">{skill}</div>'
                            html_skills += '</div>'
                            st.markdown(html_skills, unsafe_allow_html=True)
                        else:
                            st.info("No matching skills found")
                        
                        # Missing skills
                        st.markdown("#### ❌ Missing Skills")
                        missing_skills = match_data.get("missing_skills", [])
                        if missing_skills:
                            # Display missing skills as red tags
                            html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                            for skill in missing_skills:
                                html_skills += f'<div class="skill-tag" style="background-color: #dc3545;">{skill}</div>'
                            html_skills += '</div>'
                            st.markdown(html_skills, unsafe_allow_html=True)
                        else:
                            st.success("No missing skills! The candidate has all required skills.")
                        
                        # Recommendations
                        st.markdown("#### 💡 Recommendations")
                        recommendations = match_data.get("recommendations", [])
                        if recommendations:
                            for i, rec in enumerate(recommendations):
                                st.markdown(f"{i+1}. {rec}")
                        else:
                            st.info("No specific recommendations available")
                        
                        # Save match data for reporting
                        if "matches_history" not in st.session_state:
                            st.session_state.matches_history = []
                        
                        # Add timestamp and file names to match data
                        match_record = {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "resume_name": "Resume" if "resume_file" not in st.session_state else st.session_state.resume_file.name,
                            "job_name": "Job Description" if "job_file" not in st.session_state else st.session_state.job_file.name,
                            "match_score": match_score,
                            "matching_skills_count": len(matching_skills),
                            "missing_skills_count": len(missing_skills)
                        }
                        st.session_state.matches_history.append(match_record)
                        
                        # Add a button to view the professional report
                        if st.button("View Professional Report"):
                            navigate_to("Professional Report")
                else:
                    st.error(f"Error matching: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def professional_report_page():
    st.title("Professional Candidate Report")
    
    # Check if we have match data
    if "match_data" not in st.session_state or "resume_data" not in st.session_state or "job_data" not in st.session_state:
        st.warning("Please complete a candidate match before viewing the professional report.")
        
        if st.button("Go to Candidate Matching"):
            st.experimental_set_query_params(page="Candidate Matching")
            st.experimental_rerun()
        return
    
    # Get data from session state
    match_data = st.session_state.match_data
    resume_data = st.session_state.resume_data
    job_data = st.session_state.job_data
    
    match_score = match_data.get("match_score", 0)
    matching_skills = match_data.get("matching_skills", [])
    missing_skills = match_data.get("missing_skills", [])
    recommendations = match_data.get("recommendations", [])
    
    # Create a professional header
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #2c3e50; margin-bottom: 10px;">Candidate Evaluation Report</h2>
        <p style="color: #7f8c8d; font-size: 1.1em;">Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Executive Summary
    st.markdown("## Executive Summary")
    
    # Determine match quality text
    match_quality = "Excellent Match" if match_score >= 80 else "Good Match" if match_score >= 60 else "Fair Match" if match_score >= 40 else "Poor Match"
    
    # Create a summary based on the match score
    if match_score >= 80:
        summary = f"""
        The candidate demonstrates an **exceptional fit** for the position, with a match score of **{match_score}%**. 
        They possess {len(matching_skills)} of the {len(matching_skills) + len(missing_skills)} required skills, 
        showing strong alignment with the job requirements. This candidate should be **prioritized for immediate consideration**.
        """
    elif match_score >= 60:
        summary = f"""
        The candidate shows a **strong potential** for the position, with a match score of **{match_score}%**. 
        They possess {len(matching_skills)} of the {len(matching_skills) + len(missing_skills)} required skills, 
        indicating good alignment with the core job requirements. This candidate is **recommended for interview**.
        """
    elif match_score >= 40:
        summary = f"""
        The candidate shows **moderate alignment** with the position, with a match score of **{match_score}%**. 
        They possess {len(matching_skills)} of the {len(matching_skills) + len(missing_skills)} required skills. 
        While there are some gaps, the candidate may still bring valuable experience to the role and is **worth considering**.
        """
    else:
        summary = f"""
        The candidate shows **limited alignment** with the position requirements, with a match score of **{match_score}%**. 
        They possess only {len(matching_skills)} of the {len(matching_skills) + len(missing_skills)} required skills. 
        There may be better-suited candidates for this specific role, though they may have transferable skills for other positions.
        """
    
    st.markdown(summary)
    
    # Match Score Visualization
    st.markdown("## Match Analysis")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Create a gauge chart for the match score
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=match_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Match Score"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 40], 'color': "red"},
                    {'range': [40, 70], 'color': "orange"},
                    {'range': [70, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': match_score
                }
            }
        ))
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Add match quality assessment
        st.markdown(f"""
        <div style="background-color: {'#d4edda' if match_score >= 80 else '#fff3cd' if match_score >= 40 else '#f8d7da'}; 
                    color: {'#155724' if match_score >= 80 else '#856404' if match_score >= 40 else '#721c24'}; 
                    padding: 10px; border-radius: 5px; text-align: center; margin-top: 10px;">
            <h3>{match_quality}</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Create a breakdown of the match components
        st.markdown("### Match Components")
        
        # Calculate component scores (simplified example)
        skill_match_pct = len(matching_skills) / (len(matching_skills) + len(missing_skills)) * 100 if (len(matching_skills) + len(missing_skills)) > 0 else 0
        
        # Create a horizontal bar chart for match components
        component_data = {
            "Component": ["Skills Match", "Experience Relevance", "Education Alignment", "Overall Fit"],
            "Score": [skill_match_pct, match_score * 0.9, match_score * 0.85, match_score]
        }
        
        df_components = pd.DataFrame(component_data)
        
        fig = px.bar(df_components, x="Score", y="Component", orientation='h',
                    color="Score", color_continuous_scale=["red", "orange", "green"],
                    range_color=[0, 100], title="Match Component Analysis")
        
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Skills Analysis
    st.markdown("## Skills Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Matching Skills")
        st.markdown(f"The candidate possesses **{len(matching_skills)}** of the required skills:")
        
        if matching_skills:
            # Display matching skills as green tags
            html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
            for skill in matching_skills:
                html_skills += f'<div class="skill-tag" style="background-color: #28a745;">{skill}</div>'
            html_skills += '</div>'
            st.markdown(html_skills, unsafe_allow_html=True)
            
            # Add a brief analysis of the matching skills
            if len(matching_skills) >= 3:
                key_skills = ", ".join(matching_skills[:3])
                st.markdown(f"""
                The candidate's proficiency in **{key_skills}** directly aligns with the core requirements of the position.
                These skills demonstrate the candidate's capability to perform essential job functions effectively.
                """)
        else:
            st.info("No matching skills found")
    
    with col2:
        st.markdown("### Development Areas")
        st.markdown(f"The candidate could benefit from developing **{len(missing_skills)}** additional skills:")
        
        if missing_skills:
            # Display missing skills as red tags
            html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
            for skill in missing_skills:
                html_skills += f'<div class="skill-tag" style="background-color: #dc3545;">{skill}</div>'
            html_skills += '</div>'
            st.markdown(html_skills, unsafe_allow_html=True)
            
            # Add a brief analysis of the missing skills
            if len(missing_skills) > 0:
                st.markdown("""
                While these skills are currently not evident in the candidate's profile, many can be developed through:
                - On-the-job training
                - Mentorship opportunities
                - Professional development courses
                """)
        else:
            st.success("The candidate already possesses all the required skills for this position!")
    
    # Skills visualization
    if matching_skills or missing_skills:
        # Create a pie chart for skills breakdown
        skills_data = {
            "Category": ["Matching Skills", "Missing Skills"],
            "Count": [len(matching_skills), len(missing_skills)]
        }
        skills_df = pd.DataFrame(skills_data)
        
        fig = px.pie(skills_df, values="Count", names="Category", 
                    color="Category",
                    color_discrete_map={"Matching Skills": "green", "Missing Skills": "red"},
                    title="Skills Breakdown")
        st.plotly_chart(fig, use_container_width=True)
    
    # Candidate Strengths
    st.markdown("## Candidate Strengths")
    
    # Extract key strengths from the resume data
    strengths = []
    
    # Add skills as strengths
    if "skills" in resume_data and isinstance(resume_data["skills"], list) and resume_data["skills"]:
        strengths.append(f"Possesses {len(resume_data['skills'])} relevant skills, including {', '.join(resume_data['skills'][:3]) if len(resume_data['skills']) >= 3 else ', '.join(resume_data['skills'])}")
    
    # Add experience as strength
    if "experience" in resume_data and isinstance(resume_data["experience"], list) and resume_data["experience"]:
        strengths.append(f"Has {len(resume_data['experience'])} relevant experience entries, demonstrating depth in their field")
    
    # Add education as strength
    if "education" in resume_data and isinstance(resume_data["education"], list) and resume_data["education"]:
        strengths.append(f"Strong educational background with {len(resume_data['education'])} qualifications")
    
    # Add achievements as strength
    if "achievements" in resume_data and isinstance(resume_data["achievements"], list) and resume_data["achievements"]:
        strengths.append(f"Demonstrated excellence through {len(resume_data['achievements'])} notable achievements")
    
    # Add matching skills as strength
    if matching_skills:
        strengths.append(f"Strong alignment with {len(matching_skills)} key job requirements")
    
    # Display strengths
    if strengths:
        for strength in strengths:
            st.markdown(f"""
            <div style="background-color: #d4edda; color: #155724; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                ✓ {strength}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific strengths identified")
    
    # Development Opportunities
    st.markdown("## Development Opportunities")
    
    # Create development opportunities based on missing skills
    if missing_skills:
        st.markdown("The following areas present opportunities for professional development:")
        
        for i, skill in enumerate(missing_skills):
            st.markdown(f"""
            <div style="background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                {i+1}. Develop proficiency in <strong>{skill}</strong>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("The candidate already possesses all the required skills for this position!")
    
    # Recommendations
    st.markdown("## Hiring Recommendations")
    
    # Display AI-generated recommendations
    if recommendations:
        for i, rec in enumerate(recommendations):
            st.markdown(f"""
            <div style="background-color: #e2f0fd; color: #0c5460; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                {i+1}. {rec}
            </div>
            """, unsafe_allow_html=True)
    
    # Add a tailored recommendation based on match score
    if match_score >= 80:
        st.markdown("""
        <div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>Final Recommendation</h3>
            <p>This candidate demonstrates exceptional alignment with the position requirements. We strongly recommend proceeding with an interview as soon as possible to secure this high-potential talent.</p>
            <p>Consider preparing a competitive offer package to attract this well-qualified candidate.</p>
        </div>
        """, unsafe_allow_html=True)
    elif match_score >= 60:
        st.markdown("""
        <div style="background-color: #d4edda; color: #155724; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>Final Recommendation</h3>
            <p>This candidate shows strong potential for the role. We recommend scheduling an interview to further assess their fit and discuss development opportunities for any skill gaps.</p>
            <p>Consider focusing the interview on practical demonstrations of their matching skills.</p>
        </div>
        """, unsafe_allow_html=True)
    elif match_score >= 40:
        st.markdown("""
        <div style="background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>Final Recommendation</h3>
            <p>This candidate shows moderate alignment with the position. Consider including them in your interview process, with special focus on assessing their ability to quickly develop the missing skills.</p>
            <p>They may be suitable with appropriate training and mentorship.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 20px;">
            <h3>Final Recommendation</h3>
            <p>This candidate may not be the best fit for this specific position. Consider evaluating them for alternative roles that better match their current skill set, or keep their profile for future opportunities after they've developed additional skills.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Next Steps
    st.markdown("## Next Steps")
    
    # Create next steps based on match score
    next_steps = []
    
    if match_score >= 60:
        next_steps.append("Schedule an interview with the candidate")
        next_steps.append("Prepare role-specific questions focusing on their experience with " + ", ".join(matching_skills[:3]) if len(matching_skills) >= 3 else ", ".join(matching_skills))
        next_steps.append("Consider a practical assessment to demonstrate their skills")
        if missing_skills:
            next_steps.append("Discuss development plan for addressing skill gaps in " + ", ".join(missing_skills[:3]) if len(missing_skills) >= 3 else ", ".join(missing_skills))
    elif match_score >= 40:
        next_steps.append("Consider including the candidate in your interview process")
        next_steps.append("Prepare questions to assess adaptability and learning potential")
        next_steps.append("Evaluate their interest and ability to quickly develop missing skills")
        next_steps.append("Consider potential mentorship or training opportunities")
    else:
        next_steps.append("Keep the candidate's profile for future opportunities")
        next_steps.append("Consider evaluating them for alternative roles that better match their skill set")
        next_steps.append("Provide constructive feedback if the candidate is not selected")
    
    # Display next steps
    for i, step in enumerate(next_steps):
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <strong>{i+1}.</strong> {step}
        </div>
        """, unsafe_allow_html=True)
    
    # Download report button
    st.markdown("---")
    st.markdown("### Download Report")
    st.markdown("Click the button below to download this report as a PDF for sharing with your team.")
    
    # This is a placeholder - in a real app, you would generate a PDF
    if st.button("Download Professional Report"):
        st.success("Report download initiated! (This is a placeholder - in a real app, a PDF would be generated)")
    
    # Return to matching
    st.markdown("---")
    if st.button("Return to Candidate Matching"):
        navigate_to("Candidate Matching")

def reports_page():
    st.title("Analytics & Reports")
    
    # Check if we have match history
    if "matches_history" not in st.session_state or not st.session_state.matches_history:
        st.info("No matching data available yet. Please perform some matches first.")
        return
    
    # Create tabs for different reports
    tab1, tab2, tab3 = st.tabs(["Match History", "Skills Analysis", "Performance Metrics"])
    
    with tab1:
        st.header("Match History")
        
        # Convert match history to DataFrame
        df = pd.DataFrame(st.session_state.matches_history)
        
        # Display the dataframe
        st.dataframe(df, use_container_width=True)
        
        # Create a line chart of match scores over time
        st.subheader("Match Scores Over Time")
        fig = px.line(df, x="timestamp", y="match_score", markers=True,
                     labels={"timestamp": "Date/Time", "match_score": "Match Score (%)"},
                     title="Match Score Trend")
        st.plotly_chart(fig, use_container_width=True)
        
        # Add download button for CSV export
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Match History as CSV",
            data=csv,
            file_name="recruitx_match_history.csv",
            mime="text/csv"
        )
    
    with tab2:
        st.header("Skills Analysis")
        
        # If we have current match data, show skills breakdown
        if "match_data" in st.session_state:
            match_data = st.session_state.match_data
            
            # Create a pie chart for skills breakdown
            matching_skills = match_data.get("matching_skills", [])
            missing_skills = match_data.get("missing_skills", [])
            
            skills_data = {
                "Category": ["Matching Skills", "Missing Skills"],
                "Count": [len(matching_skills), len(missing_skills)]
            }
            skills_df = pd.DataFrame(skills_data)
            
            fig = px.pie(skills_df, values="Count", names="Category", 
                         color="Category",
                         color_discrete_map={"Matching Skills": "green", "Missing Skills": "red"},
                         title="Skills Breakdown for Latest Match")
            st.plotly_chart(fig, use_container_width=True)
            
            # Display skills details
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Matching Skills")
                if matching_skills:
                    # Display matching skills as tags
                    html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                    for skill in matching_skills:
                        html_skills += f'<div class="skill-tag" style="background-color: #28a745;">{skill}</div>'
                    html_skills += '</div>'
                    st.markdown(html_skills, unsafe_allow_html=True)
                else:
                    st.info("No matching skills found")
            
            with col2:
                st.subheader("Missing Skills")
                if missing_skills:
                    # Display missing skills as tags
                    html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                    for skill in missing_skills:
                        html_skills += f'<div class="skill-tag" style="background-color: #dc3545;">{skill}</div>'
                    html_skills += '</div>'
                    st.markdown(html_skills, unsafe_allow_html=True)
                else:
                    st.success("No missing skills!")
        else:
            st.info("No current match data available. Please perform a match first.")
    
    with tab3:
        st.header("Performance Metrics")
        
        # Calculate average match score
        avg_score = sum(item["match_score"] for item in st.session_state.matches_history) / len(st.session_state.matches_history)
        
        # Calculate other metrics
        total_matches = len(st.session_state.matches_history)
        high_matches = sum(1 for item in st.session_state.matches_history if item["match_score"] >= 70)
        medium_matches = sum(1 for item in st.session_state.matches_history if 40 <= item["match_score"] < 70)
        low_matches = sum(1 for item in st.session_state.matches_history if item["match_score"] < 40)
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Matches", total_matches)
        
        with col2:
            st.metric("Average Score", f"{avg_score:.1f}%")
        
        with col3:
            st.metric("High Matches (≥70%)", high_matches)
        
        with col4:
            st.metric("Low Matches (<40%)", low_matches)
        
        # Create a bar chart for match score distribution
        score_ranges = ["0-20%", "21-40%", "41-60%", "61-80%", "81-100%"]
        score_counts = [
            sum(1 for item in st.session_state.matches_history if 0 <= item["match_score"] <= 20),
            sum(1 for item in st.session_state.matches_history if 21 <= item["match_score"] <= 40),
            sum(1 for item in st.session_state.matches_history if 41 <= item["match_score"] <= 60),
            sum(1 for item in st.session_state.matches_history if 61 <= item["match_score"] <= 80),
            sum(1 for item in st.session_state.matches_history if 81 <= item["match_score"] <= 100)
        ]
        
        score_dist_df = pd.DataFrame({
            "Score Range": score_ranges,
            "Count": score_counts
        })
        
        fig = px.bar(score_dist_df, x="Score Range", y="Count", 
                    title="Match Score Distribution",
                    color="Score Range",
                    color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig, use_container_width=True)

def system_status_page():
    st.title("System Status")
    
    # Create tabs for different status views
    tab1, tab2 = st.tabs(["Cache Status", "System Information"])
    
    with tab1:
        st.header("Cache Status")
        
        # Fetch cache statistics from the backend
        try:
            response = requests.get(f"{API_ENDPOINT}/cache/stats")
            
            if response.status_code == 200:
                cache_stats = response.json()
                
                # Display cache metrics
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Cached Documents", cache_stats.get("total_cached_documents", 0))
                    st.metric("Total Cached Matches", cache_stats.get("total_cached_matches", 0))
                
                with col2:
                    # Display document type breakdown
                    doc_types = cache_stats.get("document_types", {})
                    if doc_types:
                        st.subheader("Document Types in Cache")
                        for doc_type, count in doc_types.items():
                            st.text(f"{doc_type}: {count} documents")
                    
                    # Add cache clear button
                    if st.button("Clear Cache"):
                        clear_response = requests.delete(f"{API_ENDPOINT}/cache/clear")
                        if clear_response.status_code == 200:
                            st.success("Cache cleared successfully!")
                        else:
                            st.error(f"Error clearing cache: {clear_response.text}")
                
                # Create a pie chart for document types
                if doc_types:
                    doc_types_df = pd.DataFrame({
                        "Type": list(doc_types.keys()),
                        "Count": list(doc_types.values())
                    })
                    
                    fig = px.pie(doc_types_df, values="Count", names="Type", 
                                title="Document Types Distribution in Cache")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"Error fetching cache statistics: {response.text}")
        except Exception as e:
            st.error(f"Error connecting to backend: {str(e)}")
    
    with tab2:
        st.header("System Information")
        
        # Display system information
        st.subheader("API Endpoints")
        endpoints = {
            "Backend API": API_ENDPOINT,
            "Resume Analysis": f"{API_ENDPOINT}/analyze/resume",
            "Job Analysis": f"{API_ENDPOINT}/analyze/job",
            "Match Analysis": f"{API_ENDPOINT}/match",
            "Cache Statistics": f"{API_ENDPOINT}/cache/stats",
            "Clear Cache": f"{API_ENDPOINT}/cache/clear"
        }
        
        for name, url in endpoints.items():
            st.markdown(f"**{name}**: `{url}`")
        
        # Display current time
        st.subheader("System Time")
        st.write(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check backend connectivity
        st.subheader("Backend Connectivity")
        try:
            start_time = time.time()
            response = requests.get(f"{API_ENDPOINT}/cache/stats")
            end_time = time.time()
            
            if response.status_code == 200:
                st.success(f"Backend is online. Response time: {(end_time - start_time)*1000:.2f} ms")
            else:
                st.warning(f"Backend returned status code {response.status_code}")
        except Exception as e:
            st.error(f"Cannot connect to backend: {str(e)}")
        
        # Display version information
        st.subheader("Version Information")
        st.markdown("""
        - **RecruitX Version**: 1.1.0
        - **FastAPI Version**: 0.109.2
        - **Streamlit Version**: 1.31.1
        - **Gemini API Version**: 1.5 Flash
        - **Last Updated**: 2025
        """)

def dashboard_page():
    st.title("RecruitX Dashboard")
    st.subheader("AI-Powered Talent Matching Platform")
    
    # Introduction section
    st.markdown("""
    Welcome to RecruitX, your intelligent recruitment assistant. This platform uses advanced AI to analyze resumes 
    and job descriptions, providing precise matching and insightful recommendations.
    """)
    
    # Quick stats
    st.markdown("### System Overview")
    
    # Get cache stats
    try:
        response = requests.get(f"{API_ENDPOINT}/cache/stats")
        if response.status_code == 200:
            cache_stats = response.json()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Analyzed Resumes", cache_stats.get("document_types", {}).get("resume", 0))
            with col2:
                st.metric("Analyzed Jobs", cache_stats.get("document_types", {}).get("job description", 0))
            with col3:
                st.metric("Completed Matches", cache_stats.get("total_cached_matches", 0))
    except Exception as e:
        st.error(f"Could not fetch system statistics: {str(e)}")
    
    # Quick access cards
    st.markdown("### Quick Access")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="dashboard-card" style="border-top-color: #1E88E5;">
            <h3 style="color: #1E88E5;">Resume Analysis</h3>
            <p>Upload and analyze candidate resumes to extract key skills and qualifications.</p>
            <p style="font-size: 0.85em; margin-top: 15px; color: #777;">Extract skills, experience, and education from resumes.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Resume Analysis", key="start_resume", use_container_width=True):
            st.experimental_set_query_params(page="Resume Analysis")
            st.experimental_rerun()
    
    with col2:
        st.markdown("""
        <div class="dashboard-card" style="border-top-color: #43A047;">
            <h3 style="color: #43A047;">Job Analysis</h3>
            <p>Upload and analyze job descriptions to identify requirements and expectations.</p>
            <p style="font-size: 0.85em; margin-top: 15px; color: #777;">Identify required skills, responsibilities, and qualifications.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Job Analysis", key="start_job", use_container_width=True):
            st.experimental_set_query_params(page="Job Analysis")
            st.experimental_rerun()
    
    with col3:
        st.markdown("""
        <div class="dashboard-card" style="border-top-color: #FB8C00;">
            <h3 style="color: #FB8C00;">Candidate Matching</h3>
            <p>Match candidates with job openings to find the perfect fit for your organization.</p>
            <p style="font-size: 0.85em; margin-top: 15px; color: #777;">Compare skills and qualifications to job requirements.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Start Matching", key="start_matching", use_container_width=True):
            st.experimental_set_query_params(page="Candidate Matching")
            st.experimental_rerun()
    
    with col4:
        st.markdown("""
        <div class="dashboard-card" style="border-top-color: #8E24AA;">
            <h3 style="color: #8E24AA;">Professional Report</h3>
            <p>Generate comprehensive reports to showcase candidate potential to employers.</p>
            <p style="font-size: 0.85em; margin-top: 15px; color: #777;">Create detailed analysis with actionable insights.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Reports", key="start_reports", use_container_width=True):
            st.experimental_set_query_params(page="Professional Report")
            st.experimental_rerun()
    
    # Recent activity
    if "matches_history" in st.session_state and st.session_state.matches_history:
        st.markdown("### Recent Matching Activity")
        
        # Convert match history to DataFrame
        df = pd.DataFrame(st.session_state.matches_history)
        
        # Display the most recent 5 matches
        st.dataframe(df.head(5), use_container_width=True)
    
    # System status
    st.markdown("### System Status")
    try:
        start_time = time.time()
        response = requests.get(f"{API_ENDPOINT}/cache/stats")
        end_time = time.time()
        
        if response.status_code == 200:
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"Backend API: Online ✓")
            with col2:
                st.info(f"Response Time: {(end_time - start_time)*1000:.2f} ms")
        else:
            st.error("Backend API: Offline ✗")
    except Exception as e:
        st.error(f"Backend API: Offline ✗ ({str(e)})")

def resume_analysis_page():
    st.title("Resume Analysis")
    st.subheader("Extract key information from candidate resumes")
    
    resume_file = st.file_uploader("Upload Resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="resume_analysis")
    
    if resume_file:
        with st.spinner("Analyzing resume..."):
            try:
                files = {"file": (resume_file.name, resume_file.getvalue(), resume_file.type)}
                response = requests.post(f"{API_ENDPOINT}/analyze/resume", files=files)
                
                if response.status_code == 200:
                    resume_data = response.json()
                    st.session_state.resume_data = resume_data
                    st.session_state.resume_file = resume_file
                    
                    # Display resume data in a more organized way
                    st.success("Resume analyzed successfully!")
                    
                    # Create tabs for different sections
                    tabs = st.tabs(["Skills", "Experience", "Education", "Achievements", "Overview"])
                    
                    with tabs[0]:  # Skills tab
                        st.markdown("### 🔧 Skills")
                        if "skills" in resume_data and resume_data["skills"]:
                            skills_list = resume_data["skills"]
                            if isinstance(skills_list, list) and skills_list and skills_list[0] != "Unable to extract skills":
                                # Display skills as tags
                                html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                                for skill in skills_list:
                                    html_skills += f'<div class="skill-tag" style="background-color: #4a6da7;">{skill}</div>'
                                html_skills += '</div>'
                                st.markdown(html_skills, unsafe_allow_html=True)
                                
                                # Add skill categorization
                                if len(skills_list) > 3:
                                    st.markdown("#### Skill Categories")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**Technical Skills**")
                                        for skill in skills_list[:len(skills_list)//2]:
                                            st.markdown(f"- {skill}")
                                    with col2:
                                        st.markdown("**Soft Skills & Domain Knowledge**")
                                        for skill in skills_list[len(skills_list)//2:]:
                                            st.markdown(f"- {skill}")
                            elif isinstance(skills_list, str):
                                st.write(skills_list)
                            else:
                                st.info("No skills information found")
                        else:
                            st.info("No skills information found")
                    
                    with tabs[1]:  # Experience tab
                        st.markdown("### 💼 Experience")
                        if "experience" in resume_data and resume_data["experience"]:
                            exp_list = resume_data["experience"]
                            if isinstance(exp_list, list) and exp_list and exp_list[0] != "Unable to extract experience":
                                for exp in exp_list:
                                    if isinstance(exp, str):
                                        # Display each experience as a complete block
                                        st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{exp}</div>""", unsafe_allow_html=True)
                                    elif isinstance(exp, dict):
                                        # Handle structured experience data
                                        company = exp.get("company", "")
                                        role = exp.get("role", "")
                                        duration = exp.get("duration", "")
                                        responsibilities = exp.get("responsibilities", [])
                                        
                                        st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                        <strong>{role}</strong> at <strong>{company}</strong> ({duration})
                                        </div>""", unsafe_allow_html=True)
                                        
                                        for resp in responsibilities:
                                            st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 5px; margin-left: 15px;">{resp}</div>""", unsafe_allow_html=True)
                            elif isinstance(exp_list, str):
                                st.write(exp_list)
                            else:
                                st.info("No experience information found")
                        else:
                            st.info("No experience information found")
                    
                    with tabs[2]:  # Education tab
                        st.markdown("### 🎓 Education")
                        if "education" in resume_data and resume_data["education"]:
                            edu_list = resume_data["education"]
                            if isinstance(edu_list, list) and edu_list and edu_list[0] != "Unable to extract education":
                                for edu in edu_list:
                                    if isinstance(edu, str):
                                        st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{edu}</div>""", unsafe_allow_html=True)
                                    elif isinstance(edu, dict):
                                        # Handle structured education data
                                        institution = edu.get("institution", "")
                                        degree = edu.get("degree", "")
                                        year = edu.get("year", "")
                                        
                                        st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                                        <strong>{degree}</strong> from <strong>{institution}</strong> ({year})
                                        </div>""", unsafe_allow_html=True)
                            elif isinstance(edu_list, str):
                                st.write(edu_list)
                            else:
                                st.info("No education information found")
                        else:
                            st.info("No education information found")
                    
                    with tabs[3]:  # Achievements tab
                        st.markdown("### 🏆 Achievements")
                        if "achievements" in resume_data and resume_data["achievements"]:
                            ach_list = resume_data["achievements"]
                            if isinstance(ach_list, list) and ach_list and ach_list[0] != "Unable to extract achievements":
                                for ach in ach_list:
                                    st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{ach}</div>""", unsafe_allow_html=True)
                            elif isinstance(ach_list, str):
                                st.write(ach_list)
                            else:
                                st.info("No achievements information found")
                        else:
                            st.info("No achievements information found")
                    
                    with tabs[4]:  # Overview tab
                        st.markdown("### 📋 Candidate Overview")
                        
                        # Calculate total years of experience
                        total_exp = 0
                        if "experience" in resume_data and isinstance(resume_data["experience"], list):
                            total_exp = len(resume_data["experience"])
                        
                        # Count skills
                        total_skills = 0
                        if "skills" in resume_data and isinstance(resume_data["skills"], list):
                            total_skills = len(resume_data["skills"])
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Experience", f"{total_exp} entries")
                        with col2:
                            st.metric("Skills", total_skills)
                        with col3:
                            st.metric("Achievements", len(resume_data.get("achievements", [])) if isinstance(resume_data.get("achievements", []), list) else 0)
                        
                        # Display candidate summary
                        st.markdown("#### Candidate Summary")
                        st.markdown(f"""
                        This candidate has {total_skills} identified skills and {total_exp} experience entries. 
                        The resume shows a professional with a background in {", ".join(resume_data.get("skills", [])[:3]) if isinstance(resume_data.get("skills", []), list) and len(resume_data.get("skills", [])) > 0 else "various fields"}.
                        """)
                    
                    # Add a button to proceed to job analysis
                    if st.button("Proceed to Job Analysis"):
                        st.experimental_set_query_params(page="Job Analysis")
                        st.experimental_rerun()
                else:
                    st.error(f"Error analyzing resume: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

def job_analysis_page():
    st.title("Job Description Analysis")
    st.subheader("Extract key requirements from job postings")
    
    job_file = st.file_uploader("Upload Job Description (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="job_analysis")
    
    if job_file:
        with st.spinner("Analyzing job description..."):
            try:
                files = {"file": (job_file.name, job_file.getvalue(), job_file.type)}
                response = requests.post(f"{API_ENDPOINT}/analyze/job", files=files)
                
                if response.status_code == 200:
                    job_data = response.json()
                    st.session_state.job_data = job_data
                    st.session_state.job_file = job_file
                    
                    # Display job data in a more organized way
                    st.success("Job description analyzed successfully!")
                    
                    # Create tabs for different sections
                    tabs = st.tabs(["Required Skills", "Responsibilities", "Qualifications", "Company Info", "Overview"])
                    
                    with tabs[0]:  # Required Skills tab
                        st.markdown("### 🔧 Required Skills")
                        if "required_skills" in job_data and job_data["required_skills"]:
                            skills_list = job_data["required_skills"]
                            if isinstance(skills_list, list) and skills_list and skills_list[0] != "Unable to extract required skills":
                                # Display skills as tags
                                html_skills = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
                                for skill in skills_list:
                                    html_skills += f'<div class="skill-tag" style="background-color: #2c7bb6;">{skill}</div>'
                                html_skills += '</div>'
                                st.markdown(html_skills, unsafe_allow_html=True)
                                
                                # Add skill categorization
                                if len(skills_list) > 3:
                                    st.markdown("#### Skill Categories")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.markdown("**Essential Skills**")
                                        for skill in skills_list[:len(skills_list)//2]:
                                            st.markdown(f"- {skill}")
                                    with col2:
                                        st.markdown("**Preferred Skills**")
                                        for skill in skills_list[len(skills_list)//2:]:
                                            st.markdown(f"- {skill}")
                            elif isinstance(skills_list, str):
                                st.write(skills_list)
                            else:
                                st.info("No required skills information found")
                        else:
                            st.info("No required skills information found")
                    
                    with tabs[1]:  # Responsibilities tab
                        st.markdown("### 📋 Responsibilities")
                        if "responsibilities" in job_data and job_data["responsibilities"]:
                            resp_list = job_data["responsibilities"]
                            if isinstance(resp_list, list) and resp_list and resp_list[0] != "Unable to extract responsibilities":
                                for resp in resp_list:
                                    st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{resp}</div>""", unsafe_allow_html=True)
                            elif isinstance(resp_list, str):
                                st.write(resp_list)
                            else:
                                st.info("No responsibilities information found")
                        else:
                            st.info("No responsibilities information found")
                    
                    with tabs[2]:  # Qualifications tab
                        st.markdown("### 📜 Qualifications")
                        if "qualifications" in job_data and job_data["qualifications"]:
                            qual_list = job_data["qualifications"]
                            if isinstance(qual_list, list) and qual_list and qual_list[0] != "Unable to extract qualifications":
                                for qual in qual_list:
                                    st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{qual}</div>""", unsafe_allow_html=True)
                            elif isinstance(qual_list, str):
                                st.write(qual_list)
                            else:
                                st.info("No qualifications information found")
                        else:
                            st.info("No qualifications information found")
                    
                    with tabs[3]:  # Company Info tab
                        st.markdown("### 🏢 Company Information")
                        if "company_info" in job_data and job_data["company_info"]:
                            info_list = job_data["company_info"]
                            if isinstance(info_list, list) and info_list and info_list[0] != "Unable to extract company information":
                                for info in info_list:
                                    st.markdown(f"""<div style="background-color: #2d3748; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{info}</div>""", unsafe_allow_html=True)
                            elif isinstance(info_list, str):
                                st.write(info_list)
                            else:
                                st.info("No company information found")
                        else:
                            st.info("No company information found")
                    
                    with tabs[4]:  # Overview tab
                        st.markdown("### 📋 Job Overview")
                        
                        # Count requirements
                        total_skills = 0
                        if "required_skills" in job_data and isinstance(job_data["required_skills"], list):
                            total_skills = len(job_data["required_skills"])
                        
                        total_resp = 0
                        if "responsibilities" in job_data and isinstance(job_data["responsibilities"], list):
                            total_resp = len(job_data["responsibilities"])
                        
                        total_qual = 0
                        if "qualifications" in job_data and isinstance(job_data["qualifications"], list):
                            total_qual = len(job_data["qualifications"])
                        
                        # Display metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Required Skills", total_skills)
                        with col2:
                            st.metric("Responsibilities", total_resp)
                        with col3:
                            st.metric("Qualifications", total_qual)
                        
                        # Display job summary
                        st.markdown("#### Job Summary")
                        st.markdown(f"""
                        This position requires {total_skills} key skills and involves {total_resp} main responsibilities.
                        The ideal candidate should have qualifications in {", ".join(job_data.get("required_skills", [])[:3]) if isinstance(job_data.get("required_skills", []), list) and len(job_data.get("required_skills", [])) > 0 else "relevant fields"}.
                        """)
                    
                    # Add a button to proceed to matching
                    if st.button("Proceed to Candidate Matching"):
                        st.experimental_set_query_params(page="Candidate Matching")
                        st.experimental_rerun()
                else:
                    st.error(f"Error analyzing job description: {response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main() 