from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import asyncio
import fitz  # PyMuPDF
from docx import Document
import io
import tempfile
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("recruitx-api")

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="RecruitX API", description="AI-Powered Recruitment Matching System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize Gemini API keys
GEMINI_API_KEYS = [os.getenv(f"GEMINI_API_KEY_{i}") for i in range(1, 11)]
current_key_index = 0

def get_next_api_key():
    global current_key_index
    key = GEMINI_API_KEYS[current_key_index]
    current_key_index = (current_key_index + 1) % len(GEMINI_API_KEYS)
    return key

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from different file formats"""
    logger.info(f"Extracting text from file: {file.filename}")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    file_extension = file.filename.lower().split('.')[-1]
    
    if file_extension == 'pdf':
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(content)
            temp_file.flush()
            try:
                pdf_document = fitz.open(temp_file.name)
                text = ""
                for page_num in range(len(pdf_document)):
                    text += pdf_document[page_num].get_text()
                pdf_document.close()
                return text
            finally:
                os.unlink(temp_file.name)
    
    elif file_extension == 'docx':
        doc = Document(io.BytesIO(content))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    
    elif file_extension == 'txt':
        return content.decode('utf-8')
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {file_extension}")

async def analyze_document(content: str, doc_type: str) -> dict:
    """Analyze document content using Gemini API"""
    logger.info(f"Analyzing document of type: {doc_type}")
    try:
        # Mock response for testing
        if os.getenv("TESTING") == "true":
            logger.info("Using mock response for testing")
            if doc_type == "resume":
                return {
                    "skills": ["Python", "Django", "Flask", "SQL"],
                    "experience": ["Software Developer - 5 years"],
                    "education": ["Bachelor's in Computer Science"],
                    "achievements": ["Led development of enterprise application"],
                    "key_strengths": ["Fast learner", "Team player", "Problem solver"],
                    "development_areas": ["Could improve cloud expertise"]
                }
            else:
                return {
                    "required_skills": ["Python", "Django", "Database"],
                    "responsibilities": ["Develop web applications"],
                    "qualifications": ["Bachelor's degree in Computer Science"],
                    "job_benefits": ["Competitive salary", "Remote work"],
                    "company_culture": ["Collaborative", "Innovative"]
                }
        
        # Real API integration
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if doc_type == "resume":
            prompt = """Analyze this resume in detail and extract in JSON format:
            {
                "skills": [list of technical and soft skills with proficiency levels where indicated],
                "experience": [list of work experiences with key responsibilities and achievements],
                "education": [list of educational qualifications with relevant details],
                "achievements": [list of notable achievements and accomplishments],
                "key_strengths": [list of the candidate's key strengths based on the resume],
                "development_areas": [potential areas for professional development]
            }
            IMPORTANT: Your response MUST be a valid JSON object with no additional text.
            Content: """ + content
        else:
            prompt = """Analyze this job description in detail and extract in JSON format:
            {
                "required_skills": [list of required skills with importance level],
                "preferred_skills": [list of preferred but not required skills],
                "responsibilities": [list of key responsibilities and expectations],
                "qualifications": [list of required qualifications and experience],
                "job_benefits": [list of benefits and perks offered],
                "company_culture": [list of company culture aspects mentioned]
            }
            IMPORTANT: Your response MUST be a valid JSON object with no additional text.
            Content: """ + content
        
        # Get response from Gemini API
        try:
            response_obj = await asyncio.to_thread(lambda: model.generate_content(prompt))
            response_text = response_obj.text
            
            # Log the raw response for debugging
            logger.info(f"Raw Gemini API response: {response_text[:200]}...")
            
            # Clean the response to ensure it's valid JSON
            # First, find the first '{' and the last '}'
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                json_str = response_text[first_brace:last_brace+1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error after cleanup: {str(e)}")
                    # Fall through to the general error case
            
            # If we can't find valid JSON brackets or parsing fails, try parsing the raw response
            try:
                return json.loads(response_text.strip())
            except json.JSONDecodeError:
                # Return a structured error response
                return {
                    "error": "Invalid response from Gemini API",
                    "message": "Could not parse API response as JSON",
                    "content_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "document_type": doc_type
                }
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}")
            return {
                "error": f"Gemini API error: {str(api_error)}",
                "document_type": doc_type,
                "success": False
            }
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Error analyzing document: {str(e)}")
        return {
            "error": f"Error analyzing document: {str(e)}",
            "document_type": doc_type,
            "success": False
        }

@app.post("/analyze/resume")
async def analyze_resume(file: UploadFile = File(...)):
    """Analyze a resume file"""
    logger.info(f"Received resume analysis request for file: {file.filename}")
    text_content = await extract_text_from_file(file)
    result = await analyze_document(text_content, "resume")
    logger.info(f"Resume analysis completed: {json.dumps(result)[:100]}...")
    return result

@app.post("/analyze/job")
async def analyze_job(file: UploadFile = File(...)):
    """Analyze a job description file"""
    logger.info(f"Received job description analysis request for file: {file.filename}")
    text_content = await extract_text_from_file(file)
    result = await analyze_document(text_content, "job description")
    logger.info(f"Job analysis completed: {json.dumps(result)[:100]}...")
    return result

@app.post("/match")
async def match_resume_job(request: dict):
    """Match a resume against a job description"""
    logger.info(f"Received matching request: {json.dumps(request)[:100]}...")
    try:
        resume_data = request.get("resume_data", {})
        job_data = request.get("job_data", {})
        
        # Use text directly if provided in the data objects
        resume_text = resume_data.get("text", "")
        job_text = job_data.get("text", "")
        
        # Set default empty objects if anything is missing
        if not resume_text and not resume_data:
            resume_data = {}
        if not job_text and not job_data:
            job_data = {}
        
        # Mock response for testing
        if os.getenv("TESTING") == "true":
            logger.info("Using mock response for matching")
            return {
                "match_score": 85,
                "matching_skills": ["Python", "Django"],
                "missing_skills": ["AWS", "React"],
                "score_explanation": "Mockup score calculation based on skill overlap...",
                "recommendations": [
                    "Consider learning AWS to improve cloud expertise.",
                    "React is a valuable front-end skill mentioned in the job description."
                ]
            }
        
        # Real API integration
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash-002')
        
        prompt = f"""Compare this resume and job description and provide a detailed matching analysis in JSON format:
        Resume: {resume_text if resume_text else json.dumps(resume_data)}
        Job Description: {job_text if job_text else json.dumps(job_data)}
        
        I need a comprehensive and detailed analysis of the match between this candidate and job. 
        
        Return ONLY a JSON with the following format and no additional text:
        {{
            "match_score": (0-100, calculate this based on overall skill and qualification match),
            "score_explanation": (detailed explanation of how you arrived at the match score with specific evidence),
            "matching_skills": [detailed list of skills found in both resume and job with specific evidence],
            "missing_skills": [detailed list of skills in job description but not in resume],
            "recommendations": [detailed, actionable recommendations for the candidate to improve their match for this job],
            "matching_experience": (analysis of how the candidate's experience aligns with job requirements),
            "matching_education": (analysis of how the candidate's education aligns with job requirements),
            "strengths": [areas where the candidate is particularly strong for this role],
            "areas_for_improvement": [specific areas where the candidate could improve for this role]
        }}
        """
        
        try:
            response_obj = await asyncio.to_thread(lambda: model.generate_content(prompt))
            response_text = response_obj.text
            
            # Log the raw response for debugging
            logger.info(f"Raw Gemini API match response: {response_text[:200]}...")
            
            # Clean the response to ensure it's valid JSON
            # First, find the first '{' and the last '}'
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                json_str = response_text[first_brace:last_brace+1]
                try:
                    result = json.loads(json_str)
                    logger.info(f"Match completed: {json.dumps(result)[:100]}...")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error after cleanup: {str(e)}")
                    # Fall through to the general error case
            
            # If we can't find valid JSON brackets or parsing fails, try parsing the raw response
            try:
                result = json.loads(response_text.strip())
                logger.info(f"Match completed: {json.dumps(result)[:100]}...")
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return a structured error response
                logger.error(f"Error parsing Gemini API response: {response_text[:100]}...")
                return {
                    "error": "Invalid response from Gemini API",
                    "match_score": 0,
                    "matching_skills": [],
                    "missing_skills": [],
                    "content_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                }
        except Exception as api_error:
            # Handle any API-specific exceptions
            logger.error(f"Gemini API error in match: {str(api_error)}")
            return {
                "error": f"Gemini API error: {str(api_error)}",
                "match_score": 0,
                "matching_skills": [],
                "missing_skills": [],
                "success": False
            }
    except Exception as e:
        # Handle any other exceptions
        logger.error(f"Error matching resume to job: {str(e)}")
        return {
            "error": f"Error matching resume to job: {str(e)}",
            "match_score": 0,
            "matching_skills": [],
            "missing_skills": []
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check endpoint called")
    return {"status": "ok", "testing_mode": os.getenv("TESTING") == "true"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting RecruitX API server")
    uvicorn.run(app, host="0.0.0.0", port=8000) 