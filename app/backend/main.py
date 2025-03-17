from fastapi import FastAPI, HTTPException, UploadFile, File, Query
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
from pydantic import BaseModel
from typing import Optional

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

# Language detection helper
async def detect_language(text):
    """Attempt to detect if the text is primarily English or Japanese"""
    # Simple heuristic: Count Japanese characters vs English
    japanese_chars = sum(1 for char in text if ord(char) > 0x3000)
    if japanese_chars > len(text) * 0.3:  # If more than 30% are Japanese characters
        return "ja"
    return "en"

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text from different file formats"""
    logger.info(f"Extracting text from file: {file.filename}")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    
    # Save to a temp file for processing
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(content)
        temp_path = temp.name
    
    # Process based on file extension
    file_extension = file.filename.lower().split('.')[-1]
    extracted_text = ""
    
    try:
        if file_extension == 'pdf':
            doc = fitz.open(temp_path)
            for page in doc:
                extracted_text += page.get_text()
        elif file_extension in ['docx', 'doc']:
            doc = Document(temp_path)
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
        else:
            # For text files or if format not recognized, try to decode as text
            try:
                extracted_text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Unsupported file format")
    finally:
        # Clean up temp file
        os.unlink(temp_path)
    
    return extracted_text

class AnalysisRequest(BaseModel):
    language: Optional[str] = "en"

async def analyze_document(content: str, doc_type: str, language: str = "en") -> dict:
    """Analyze document content using Gemini API with language support"""
    logger.info(f"Analyzing document of type: {doc_type} in language: {language}")
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
        
        # Detect document language if not specified
        doc_language = language
        if language == "auto":
            doc_language = await detect_language(content)
            logger.info(f"Detected document language: {doc_language}")
        
        # Real API integration
        api_key = get_next_api_key()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Choose prompt based on document type and language
        if doc_type == "resume":
            if doc_language == "ja":
                prompt = """この履歴書を詳細に分析し、以下のJSON形式で情報を抽出してください。全てのフィールドについての情報を必ず含めてください：
                {
                    "skills": [技術的なスキルとソフトスキルのリスト、レベルが示されている場合はそれも含む],
                    "experience": [仕事経験の詳細リスト、会社名、役職、主な責任と成果を含む],
                    "education": [教育資格の詳細リスト、学校名、学位、専攻を含む],
                    "achievements": [注目すべき成果や業績のリスト],
                    "key_strengths": [履歴書に基づく候補者の主な強みのリスト],
                    "development_areas": [職業能力開発の可能性のある分野]
                }
                
                全てのフィールドについて、できるだけ詳細な情報を提供してください。特に、experience、education、achievementsのフィールドを空にしないでください。
                情報が不足している場合でも、履歴書から読み取れる部分的な情報を使って回答してください。

                重要：回答は追加テキストなしの有効なJSONオブジェクトでなければなりません。
                内容：""" + content
            else:
                prompt = """Analyze this resume in detail and extract in JSON format. INCLUDE INFORMATION FOR ALL FIELDS:
                {
                    "skills": [list of technical and soft skills with proficiency levels where indicated],
                    "experience": [detailed list of work experiences with company name, position/title, key responsibilities and achievements],
                    "education": [detailed list of educational qualifications with institution name, degree, major],
                    "achievements": [list of notable achievements and accomplishments],
                    "key_strengths": [list of the candidate's key strengths based on the resume],
                    "development_areas": [potential areas for professional development]
                }
                
                Please provide detailed information for ALL fields. DO NOT leave the experience, education, or achievements fields empty.
                Even if information is limited, use whatever partial information is available in the resume.
                
                IMPORTANT: Your response MUST be a valid JSON object with no additional text.
                Content: """ + content
        else:  # job description
            if doc_language == "ja":
                prompt = """この求人情報を詳細に分析し、以下のJSON形式で情報を抽出してください：
                {
                    "required_skills": [必須スキルのリスト、重要度レベル付き],
                    "preferred_skills": [優遇されるが必須ではないスキルのリスト],
                    "responsibilities": [主な責任と期待事項のリスト],
                    "qualifications": [必要な資格と経験のリスト],
                    "job_benefits": [提供される福利厚生と特典のリスト],
                    "company_culture": [言及されている企業文化の側面のリスト]
                }
                重要：回答は追加テキストなしの有効なJSONオブジェクトでなければなりません。
                内容：""" + content
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
            }
    except Exception as e:
        logger.error(f"Document analysis error: {str(e)}")
        return {"error": f"Analysis failed: {str(e)}"}

@app.post("/analyze/resume")
async def analyze_resume(file: UploadFile = File(...), language: str = Query("en", description="Language for analysis response: en, ja, or auto")):
    """Analyze a resume/CV document"""
    try:
        content = await extract_text_from_file(file)
        raw_result = await analyze_document(content, "resume", language)
        logger.info(f"Resume analysis raw data keys: {list(raw_result.keys())}")
        
        # Transform the response to match frontend's expected format
        # Process skills safely to handle different formats from AI response
        skills_details = []
        if "skills" in raw_result:
            logger.info(f"Skills type: {type(raw_result['skills'])}")
            if isinstance(raw_result["skills"], list):
                for skill in raw_result["skills"]:
                    if isinstance(skill, dict):
                        # If this is a full skill object with details
                        if "skill" in skill:
                            skills_details.append(skill["skill"])
                        else:
                            # Keep the full skill object as is
                            skills_details.append(skill)
                    elif isinstance(skill, str):
                        skills_details.append(skill)
            # Handle nested skills structure that might appear in Japanese
            elif isinstance(raw_result["skills"], dict):
                if "items" in raw_result["skills"]:
                    if isinstance(raw_result["skills"]["items"], list):
                        for item in raw_result["skills"]["items"]:
                            if isinstance(item, str):
                                skills_details.append(item)
                # Handle other dictionary structures
                for key, value in raw_result["skills"].items():
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, str):
                                skills_details.append(item)
                            elif isinstance(item, dict) and "skill" in item:
                                skills_details.append(item["skill"])
        
        # Process experience safely with more flexible approach
        experience_details = []
        experience_keys = ["experience", "work_experience", "職歴", "実務経験"]
        for exp_key in experience_keys:
            if exp_key in raw_result:
                logger.info(f"Found experience under key: {exp_key}, type: {type(raw_result[exp_key])}")
                if isinstance(raw_result[exp_key], list):
                    for exp in raw_result[exp_key]:
                        if isinstance(exp, dict):
                            # Try various possible field names
                            for field in ["position", "title", "role", "job", "description", "company"]:
                                if field in exp:
                                    detail = exp[field]
                                    if "company" in exp and field != "company":
                                        detail = f"{detail} at {exp['company']}"
                                    experience_details.append(detail)
                                    break
                            else:
                                # If no specific field found, use the whole dict as string
                                experience_details.append(str(exp))
                        elif isinstance(exp, str):
                            experience_details.append(exp)
                elif isinstance(raw_result[exp_key], dict):
                    # Handle nested structure
                    for company, details in raw_result[exp_key].items():
                        if isinstance(details, list):
                            for detail in details:
                                experience_details.append(f"{detail} at {company}")
                        else:
                            experience_details.append(f"{details} at {company}")
        
        # Process education safely with more flexible approach
        education_details = []
        education_keys = ["education", "educational_background", "学歴", "教育"]
        for edu_key in education_keys:
            if edu_key in raw_result:
                logger.info(f"Found education under key: {edu_key}, type: {type(raw_result[edu_key])}")
                if isinstance(raw_result[edu_key], list):
                    for edu in raw_result[edu_key]:
                        if isinstance(edu, dict):
                            # Try various possible field names
                            for field in ["degree", "institution", "school", "university", "qualification", "description"]:
                                if field in edu:
                                    detail = edu[field]
                                    if "institution" in edu and field != "institution":
                                        detail = f"{detail} at {edu['institution']}"
                                    education_details.append(detail)
                                    break
                            else:
                                # If no specific field found, use the whole dict as string
                                education_details.append(str(edu))
                        elif isinstance(edu, str):
                            education_details.append(edu)
                elif isinstance(raw_result[edu_key], dict):
                    # Handle nested structure
                    for institution, details in raw_result[edu_key].items():
                        if isinstance(details, list):
                            for detail in details:
                                education_details.append(f"{detail} at {institution}")
                        else:
                            education_details.append(f"{details} at {institution}")
        
        # Process achievements safely with more flexible approach
        achievements_details = []
        achievement_keys = ["achievements", "accomplishments", "projects", "notable_projects", "業績", "成果", "プロジェクト"]
        for ach_key in achievement_keys:
            if ach_key in raw_result:
                logger.info(f"Found achievements under key: {ach_key}, type: {type(raw_result[ach_key])}")
                if isinstance(raw_result[ach_key], list):
                    for ach in raw_result[ach_key]:
                        if isinstance(ach, dict):
                            # Try various possible field names
                            for field in ["achievement", "accomplishment", "description", "project", "title"]:
                                if field in ach:
                                    achievements_details.append(ach[field])
                                    break
                            else:
                                # If no specific field found, use the whole dict as string
                                achievements_details.append(str(ach))
                        elif isinstance(ach, str):
                            achievements_details.append(ach)
                elif isinstance(raw_result[ach_key], dict):
                    # Handle nested structure
                    for project_name, details in raw_result[ach_key].items():
                        if isinstance(details, list):
                            for detail in details:
                                achievements_details.append(f"{project_name}: {detail}")
                        else:
                            achievements_details.append(f"{project_name}: {details}")
        
        # Check for key_strengths and development_areas as alternative sources
        if not achievements_details:
            strength_keys = ["key_strengths", "strengths", "強み"]
            for key in strength_keys:
                if key in raw_result and isinstance(raw_result[key], list):
                    achievements_details.extend([f"Strength: {s}" for s in raw_result[key]])
        
        transformed_result = {
            "skills": {"details": skills_details},
            "experience": {"details": experience_details},
            "education": {"details": education_details},
            "achievements": {"details": achievements_details}
        }
        
        logger.info(f"Transformed resume result: experience={len(experience_details)}, education={len(education_details)}, achievements={len(achievements_details)}")
        return transformed_result
    except Exception as e:
        logger.error(f"Resume analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/job")
async def analyze_job(file: UploadFile = File(...), language: str = Query("en", description="Language for analysis response: en, ja, or auto")):
    """Analyze a job description document"""
    try:
        content = await extract_text_from_file(file)
        raw_result = await analyze_document(content, "job description", language)
        logger.info(f"Job analysis completed: {json.dumps(raw_result)[:100]}...")
        
        # Transform the response to match frontend's expected format
        # Handle different possible data structures for skills
        required_skills_details = []
        if "required_skills" in raw_result:
            if isinstance(raw_result["required_skills"], list):
                for skill in raw_result["required_skills"]:
                    if isinstance(skill, dict) and "skill" in skill:
                        required_skills_details.append(skill["skill"])
                    elif isinstance(skill, str):
                        required_skills_details.append(skill)
        
        preferred_skills_details = []
        if "preferred_skills" in raw_result:
            if isinstance(raw_result["preferred_skills"], list):
                for skill in raw_result["preferred_skills"]:
                    if isinstance(skill, dict) and "skill" in skill:
                        preferred_skills_details.append(skill["skill"])
                    elif isinstance(skill, str):
                        preferred_skills_details.append(skill)
        
        # Safely process responsibilities
        responsibilities = []
        if "responsibilities" in raw_result and isinstance(raw_result["responsibilities"], list):
            for resp in raw_result["responsibilities"]:
                if isinstance(resp, dict) and "responsibility" in resp:
                    responsibilities.append(resp["responsibility"])
                elif isinstance(resp, str):
                    responsibilities.append(resp)
        
        # Safely process qualifications
        qualifications = []
        if "qualifications" in raw_result and isinstance(raw_result["qualifications"], list):
            for qual in raw_result["qualifications"]:
                if isinstance(qual, dict) and "qualification" in qual:
                    qualifications.append(qual["qualification"])
                elif isinstance(qual, str):
                    qualifications.append(qual)
        
        # Safely process company culture and job benefits
        company_culture = []
        job_benefits = []
        
        if "company_culture" in raw_result:
            if isinstance(raw_result["company_culture"], list):
                for item in raw_result["company_culture"]:
                    if isinstance(item, dict) and "culture" in item:
                        company_culture.append(item["culture"])
                    elif isinstance(item, str):
                        company_culture.append(item)
        
        if "job_benefits" in raw_result:
            if isinstance(raw_result["job_benefits"], list):
                for item in raw_result["job_benefits"]:
                    if isinstance(item, dict) and "benefit" in item:
                        job_benefits.append(item["benefit"])
                    elif isinstance(item, str):
                        job_benefits.append(item)
        
        # Combine company info safely
        company_info = company_culture + job_benefits
        
        transformed_result = {
            "required_skills": {"details": required_skills_details},
            "preferred_skills": {"details": preferred_skills_details},
            "responsibilities": {"details": responsibilities},
            "qualifications": {"details": qualifications},
            "company_info": {"details": company_info}
        }
        
        return transformed_result
    except Exception as e:
        logger.error(f"Job analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class MatchRequest(BaseModel):
    resume_data: dict
    job_data: dict
    language: Optional[str] = "en"

@app.post("/match")
async def match_resume_job(request: MatchRequest):
    """Match a resume against a job description"""
    logger.info(f"Received matching request: {json.dumps(request.dict())[:100]}...")
    try:
        resume_data = request.resume_data
        job_data = request.job_data
        language = request.language
        
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
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Choose prompt based on language
        if language == "ja":
            prompt = f"""この履歴書と求人情報を比較し、詳細なマッチング分析をJSON形式で提供してください：
            履歴書: {resume_text if resume_text else json.dumps(resume_data, ensure_ascii=False)}
            求人情報: {job_text if job_text else json.dumps(job_data, ensure_ascii=False)}
            
            この候補者と求人の間のマッチについて包括的で詳細な分析が必要です。
            
            以下の形式の有効なJSONのみを返し、追加のテキストは含めないでください：
            {{
                "match_score": (0-100、全体的なスキルと資格のマッチに基づいてこれを計算してください),
                "score_explanation": (マッチスコアにどのようにたどり着いたかの詳細な説明、具体的な証拠を含む),
                "matching_skills": [履歴書と求人の両方に見られるスキルの詳細なリスト、具体的な証拠を含む],
                "missing_skills": [求人情報にあるが履歴書にないスキルの詳細なリスト],
                "recommendations": [この求人に対するマッチを改善するための、候補者への詳細で実行可能な推奨事項],
                "matching_experience": (候補者の経験が求人要件とどのように一致するかの分析),
                "matching_education": (候補者の学歴が求人要件とどのように一致するかの分析),
                "strengths": [この求人における候補者の強みのリスト],
                "areas_for_improvement": [この求人に関する候補者の改善すべき分野のリスト]
            }}
            """
        else:
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
                "strengths": [list of the candidate's strengths for this job position],
                "areas_for_improvement": [list of areas where the candidate could improve for this job position]
            }}
            """
        
        # Get response from Gemini API
        try:
            response_obj = await asyncio.to_thread(lambda: model.generate_content(prompt))
            response_text = response_obj.text
            
            # Log the raw response for debugging
            logger.info(f"Raw Gemini API match response: {response_text[:200]}...")
            
            # Clean the response to ensure it's valid JSON
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            
            if first_brace != -1 and last_brace != -1:
                json_str = response_text[first_brace:last_brace+1]
                try:
                    result = json.loads(json_str)
                    logger.info(f"Match completed: {json.dumps(result)[:100]}...")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {str(e)}")
            
            # If we can't find valid JSON brackets or parsing fails, try parsing the raw response
            try:
                result = json.loads(response_text.strip())
                logger.info(f"Match completed (alternative parsing): {json.dumps(result)[:100]}...")
                return result
            except json.JSONDecodeError:
                # Return a structured error response
                error_response = {
                    "error": "Invalid response from Gemini API",
                    "message": "Could not parse API response as JSON",
                    "content_preview": response_text[:200] + "..." if len(response_text) > 200 else response_text
                }
                logger.error(f"Match failed: {json.dumps(error_response)}")
                return error_response
        except Exception as api_error:
            logger.error(f"Gemini API error during matching: {str(api_error)}")
            return {"error": f"API error: {str(api_error)}"}
    except Exception as e:
        logger.error(f"Match error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    logger.info("Health check endpoint called")
    return {"status": "ok", "testing": os.getenv("TESTING", "false")}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting RecruitX API server")
    uvicorn.run(app, host="0.0.0.0", port=8000) 