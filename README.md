# RecruitX

An advanced AI-powered recruitment platform with multi-agent capabilities and a privacy-first architecture.

## Project Status (May 2025)

RecruitX has successfully completed Phase 0 (Foundation) and Phase 1 (Core Multi-Agent System), with all essential components implemented and operational.

### Current Capabilities

- **Dual AI Model Support**: Choose between Gemma 3 (local) and Gemini (cloud) for all operations
- **Multi-Agent System**: Complete implementation of all specialized recruitment agents
- **Privacy-First Design**: All processing happens locally with no external dependencies
- **Modern React UI**: Beautiful interface with glass-card design system

## Architecture

RecruitX uses a modular, privacy-first architecture:

### Backend
- **Weaviate Vector Database**: Privacy-first implementation for semantic search
- **Redis Message Broker**: Powers inter-agent communication
- **FastAPI**: Provides endpoints for all recruitment operations

### Agents
1. **Screening Agent**: Resume parsing and job matching capabilities
2. **Sourcing Agent**: Candidate discovery with semantic search
3. **Matching Agent**: Advanced matching with explainable results
4. **Engagement Agent**: Conversational capabilities with memory
5. **Agent Orchestration**: Redis-based coordination layer

## Setup

### Prerequisites
- Node.js 18+
- Python 3.10+
- Docker and Docker Compose
- Docker Desktop with Models support (for Gemma 3)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/recruitx.git
   cd recruitx
   ```

2. Install backend dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Install frontend dependencies:
   ```bash
   cd src/ui
   npm install
   ```

4. Start infrastructure services:
   ```bash
   docker-compose up -d
   ```

5. Set up Gemma 3 model:
   ```bash
   # Get a Hugging Face token from https://huggingface.co/settings/tokens
   export HF_TOKEN="your_huggingface_token"
   
   # Start the Gemma 3 model
   ./start_model.sh
   ```

6. Start the backend server:
   ```bash
   python main.py
   ```

7. Start the frontend:
   ```bash
   cd src/ui
   npm run dev
   ```

## Usage

Navigate to `http://localhost:5173` to access the RecruitX platform. The UI provides access to:

- **AI Chat**: Interact with the recruitment AI assistant
- **Resume Analyzer**: Parse and analyze candidate resumes
- **Job Uploader**: Create and manage job descriptions
- **Sourcing**: Discover candidates based on job requirements
- **Matching**: Match candidates to jobs with detailed scoring
- **Engagement**: Interact with candidates through automated messaging

## Development Roadmap

Current development status:

- ✅ **Phase 0**: Foundation (Completed May 2025)
  - Weaviate vector database with privacy-first implementation
  - Knowledge base operations (add, get, search, delete)
  - Screening agent with resume parsing and job matching
  - FastAPI with endpoints for job management and resume analysis

- ✅ **Phase 1**: Core Multi-Agent System (Completed May 2025)
  - Agent Orchestration layer with Redis-based message passing
  - Sourcing Agent for candidate discovery
  - Matching Agent with explainable results
  - Engagement Agent with conversational capabilities

- 🔄 **Phase 2**: Advanced Capabilities (In Progress)
  - Enhanced matching algorithms
  - Analytics dashboard
  - Advanced explainability features

- ⏳ **Phase 3**: Enterprise Features (Planned)
  - Scalability enhancements
  - Additional integrations
  - Enterprise deployment options

## License

This project is proprietary and confidential.
