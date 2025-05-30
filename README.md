# RecruitX by Shristyverse LLC

**RecruitX: Precision Talent Intelligence**

RecruitX is an advanced AI-powered recruitment assistant developed by Shristyverse LLC. It is engineered to enhance the hiring process by providing intelligent, data-driven matching of candidate CVs (Resumes) with Job Descriptions (JDs). RecruitX delivers detailed scoring, insightful explanations, and a sophisticated, user-friendly interface to empower recruiters in making faster, more informed, and equitable talent acquisition decisions.

## Core Capabilities

*   **Executive Dashboard:** Provides a strategic overview of recruitment activities, including key metrics (Managed CVs, Managed JDs, Analyses Performed) and immediate access to recent analysis reports with enhanced filtering options (dimensions used, score threshold, date range).
*   **Document Management:** Streamlined uploading and management of CVs and Job Descriptions. Supports `.txt`, `.pdf`, `.docx`, and `.xlsx` file formats, alongside direct text input. Includes bulk upload functionality integrated into list views.
*   **AI-Powered Analysis & Scoring:** Utilizes Google's Gemini API for nuanced candidate-job matching.
    *   **Customizable Assessment Dimensions:** Recruiters can activate/deactivate and customize the AI's evaluation criteria from a predefined list of dimensions (e.g., Skills Assessment, Experience Alignment, Professionalism & Collaboration, etc.). Prompt guidance for each dimension can be tailored.
    *   **Comprehensive Scoring Model:** Delivers an overall match score and granular assessments for each active dimension.
*   **Actionable Explanations:** Articulates the rationale behind AI-generated scores through clear, evidence-based explanations, emphasizing how Recruiter Notes and retrieved contextual information (from RAG) influenced the outcome.
*   **Recruiter Insights Prioritization:** Enables recruiters to append contextual notes to CVs and JDs. The AI is programmed to assign high priority to these insights.
*   **Advanced Agentic RAG Integration (Conceptual Simulation):** The system's client-side implementation *simulates* the integration of knowledge from an external, curated knowledge base. This is achieved through sophisticated prompt engineering, where the *concept* of an Agentic Retrieval Augmented Generation pipeline is used to structure the interaction with the Gemini API. This allows the AI to conceptually access relevant definitions, benchmarks, and detailed context, leading to more accurate and deeply informed analyses.
*   **Bilingual Support:** Offers full interface and AI report generation in both English and Japanese.
*   **Conceptual Multi-Agent AI Framework (Simulated):** The AI's analytical process is modeled on a collaborative team of specialized virtual agents (e.g., Data Ingestion, RAG Agents for planning and retrieval, Recruiter Insights Integration, Scoring Engine, Reporting). In the current client-side version, these interactions are *simulated* via prompt engineering to guide the Gemini API, ensuring a structured and thorough evaluation.
*   **Client-Side Data Persistence:** Leverages `localStorage` for the persistence of CVs, JDs, match reports, and application settings, enabling users to retain their data across browser sessions (simulating database interaction for demonstration and single-user contexts).
*   **Ethical AI Framework:** Designed with an emphasis on objectivity and transparency, aiming to mitigate bias in the AI's analytical outputs. The system requires AI to explain its reasoning for scores based on textual evidence.
*   **Sophisticated User Interface:** A clean, responsive, and professional interface built with React and Tailwind CSS, designed for optimal user experience.
*   **Structured Data Views & Editing:** Provides AI-generated structured summaries of CVs and JDs, which are editable by the user, enhancing data review and refinement.
*   **Nexus Ranking:** Features "Top Candidate Matches" for jobs and "Best Job Fits" for candidates based on a configurable score threshold, facilitating quick identification of high-potential pairings.

## Technology Stack

*   **Frontend:** React 19, TypeScript
*   **Styling:** Tailwind CSS
*   **AI Engine:** Google Gemini API (`gemini-2.5-flash-preview-04-17`) via `@google/genai` SDK. The system is designed to incorporate inputs from a conceptual Agentic RAG pipeline to enrich the context provided to the Gemini model.
*   **Charting & Visualization:** Recharts
*   **File Parsing:** `pdf.js` (for PDF), `mammoth` (for DOCX), `xlsx` (for Excel).
*   **Localization:** Custom React hooks for robust English/Japanese language support.
*   **Data Persistence (Client-Side):** Browser `localStorage`.

## Project Setup & Execution

RecruitX is architected as a client-side application that interfaces directly with the Google Gemini API.

**Prerequisites:**

*   A modern web browser (e.g., Chrome, Firefox, Edge, Safari - latest versions recommended).
*   A valid Google Gemini API Key.

**Configuration:**

1.  **Repository Acquisition:**
    ```bash
    # If using Git
    git clone https://github.com/shristy0611/RecruitX.git 
    cd RecruitX
    ```
    Alternatively, ensure all project files are co-located in a dedicated directory.

2.  **API Key Integration:**
    *   For local development using Vite (which is the recommended setup for this project), the application expects the Gemini API Key to be available as `import.meta.env.VITE_GOOGLE_GENAI_API_KEY`. This is typically set in a `.env.local` file at the project root (see "API Keys Setup" section below).
    *   The `services/geminiService.ts` file uses `import.meta.env.VITE_GOOGLE_GENAI_API_KEY` to access the key.
    *   If deploying to a specific platform (e.g., AI Developer Hub) that might use `process.env.API_KEY`, ensure that this environment variable is correctly made available to the application, potentially requiring adjustments in how the key is accessed in `services/geminiService.ts` or through build process configurations. For standard local development, `VITE_GOOGLE_GENAI_API_KEY` is the correct variable.
    *   **The application will not prompt for an API key or provide a UI for its input if the key is not found or is invalid.** It will fall back to mock implementations as described in the "API Keys Setup" section.

**Application Launch & Local Development:**

The application's `index.html` uses an `importmap` for ES module resolution and dynamically loads React and other dependencies from CDNs (`esm.sh`). The core logic, including Gemini API interactions, resides in TypeScript (`.tsx`) files.

*   **Local Development with Vite:**
    1.  Ensure you have Node.js and npm installed.
    2.  Install project dependencies:
        ```bash
        npm install
        ```
    3.  Set up your `VITE_GOOGLE_GENAI_API_KEY` in a `.env.local` file as described in "API Keys Setup".
    4.  Run the development server:
        ```bash
        npm run dev
        ```
        This will typically start the application on `http://localhost:5173` (or the next available port).
*   **Note on `process.env.API_KEY`:** The previous mentions of `process.env.API_KEY` were relevant to specific deployment contexts. For local development with Vite, `import.meta.env.VITE_GOOGLE_GENAI_API_KEY` and the `.env.local` file method is the standard.

Once the API key is accessible to the application's JavaScript context, `index.html` (when served by Vite) can be opened in a browser.

## Strategic Vision & Future Enhancements

RecruitX is envisioned as the foundation for a comprehensive, enterprise-grade talent intelligence platform. Future development trajectories include:

*   **Robust Backend Infrastructure:**
    *   Technologies: Node.js (Express/NestJS) or Python (FastAPI/Django).
    *   Features: Secure user authentication, role-based access control, scalable API architecture.
*   **Dedicated Database Systems:**
    *   Relational (e.g., PostgreSQL): For structured data like user profiles, job specifications, and analytical reports.
    *   Vector (e.g., Pinecone, Weaviate): **Crucial for the Agentic RAG system**, storing embeddings of curated knowledge (skill definitions, industry benchmarks, company data).
*   **True Multi-Agent System Implementation:** Evolve the conceptual AI agents (including RAG agents) into independently deployable microservices.
*   **Server-Side Function Calling & Tool Integration:** Empower AI agents to interact with external APIs, internal knowledge bases (via RAG), and proprietary data sources for enriched analysis.
*   **Advanced Predictive Analytics & Reporting:** Equip recruiters with sophisticated tools for trend analysis, talent pool insights, and recruitment process optimization.
*   **ATS & HRIS Integration:** Ensure seamless connectivity with leading Applicant Tracking Systems and Human Resource Information Systems.
*   **Personalized Candidate Experience Portal:** Offer candidates a platform to track application status and receive relevant updates.

## Contribution Guidelines

We encourage contributions to RecruitX. Please consult our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to participate.

## Code of Conduct

All participants in the RecruitX project are expected to adhere to the [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). By contributing, you agree to uphold these standards.

## Licensing

RecruitX is distributed under the MIT License. Refer to the [LICENSE](LICENSE) file for comprehensive details.

## API Keys Setup

### Google Gemini API

This application uses Google's Gemini API for AI features. To enable these features:

1. Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a `.env.local` file in the project root with the following content:

```
VITE_GOOGLE_GENAI_API_KEY=your-api-key-here
```
**Note:** The `VITE_` prefix is necessary for Vite to expose the variable to the client-side code during local development.

Without a valid API key, the application will use mock implementations for AI features.

---

© 2024 Shristyverse LLC, Okegawa city, Japan. All rights reserved.
