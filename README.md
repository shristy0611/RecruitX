# RecruitX - AI-Powered Recruitment Matching System

RecruitX is an intelligent recruitment tool that uses AI to analyze resumes and job descriptions, providing detailed matching scores and recommendations.

## Features

- **Resume Analysis**: Extract skills, experience, education, achievements, and more from candidate resumes
- **Job Analysis**: Extract required skills, preferred skills, responsibilities, and qualifications from job descriptions
- **Intelligent Matching**: Match candidates to job descriptions with detailed scoring and recommendations
- **Detailed Reports**: Get comprehensive reports on match scores, matching/missing skills, and improvement areas

## Tech Stack

### Backend
- FastAPI (Python)
- Gemini AI API for natural language processing and analysis
- PDF/DOCX parsing for document extraction

### Frontend
- React with Vite
- TailwindCSS for styling
- Responsive design for all devices

## Setup

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd app/backend
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your Gemini API keys:
   ```
   GEMINI_API_KEY_1=your_api_key_here
   ```

5. Run the backend server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd app/frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm run dev
   ```

## Usage

1. Access the application at http://localhost:5173
2. Upload a resume to analyze its contents
3. Upload a job description to analyze its requirements
4. Match the resume against the job description to get a detailed report

## License

MIT 