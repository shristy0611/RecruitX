
# RecruitX Architecture Overview

This document delineates the conceptual architecture of RecruitX by Shristyverse LLC, detailing its current client-side implementation and outlining the strategic vision for its future backend system development.

## Current Architecture (Client-Side Application with Gemini API Integration)

RecruitX is currently realized as a sophisticated client-side web application, engineered for direct interaction with Google's Gemini API.

### 1. Frontend Application Layer

*   **Core Framework:** Developed using React 19 and TypeScript, leveraging modern React paradigms such as Hooks for state management and component lifecycle control.
*   **User Interface (UI) & User Experience (UX):**
    *   A dashboard-centric design paradigm, offering a holistic view of recruitment activities and analytics.
    *   Dedicated modules for managing Candidate CVs (Resumes), Job Descriptions (JDs), and initiating AI-driven analyses.
    *   Interactive and detailed score reports, featuring data visualizations for enhanced comprehension.
*   **Styling Engine:** Employs Tailwind CSS for a responsive, utility-first approach to styling, ensuring a contemporary and professional aesthetic.
*   **State Management:** Utilizes React's intrinsic state management capabilities (e.g., `useState`, `useContext`) supplemented by custom hooks for encapsulated logic.
*   **Internationalization (i18n):** Robust bilingual support (English/Japanese) for all UI elements and AI-generated analytical content, managed via a custom localization framework.
*   **Client-Side Data Persistence:** Leverages browser `localStorage` for the storage of CVs, JDs, and Match Reports. This enables data persistence across user sessions, simulating backend database interactions for demonstration and single-user scenarios.
*   **Component Modularity:** Architected with a component-based structure (e.g., `SimpleDocumentForm`, `ScoreReport`, `DashboardView`) to promote code reusability, maintainability, and scalability.
*   **Settings Management:** Allows users to configure assessment dimensions and ranking display thresholds.

### 2. AI Core (Conceptual Multi-Agent System with Agentic RAG via Gemini API)

*   **Underlying AI Engine:** Powered by Google's Gemini API, specifically utilizing the `gemini-2.5-flash-preview-04-17` model for its advanced generative capabilities.
*   **Service Orchestration Layer (`services/geminiService.ts`):**
    *   Manages all communications and interactions with the Gemini API.
    *   Dynamically constructs highly contextualized prompts based on CV content, JD specifications, active assessment dimensions, Recruiter Notes, and **simulated retrieved context from a conceptual Agentic RAG pipeline**.
    *   This layer *simulates* a **conceptual multi-agent system** primarily through sophisticated prompt engineering for the Gemini API call. The system instruction supplied to the Gemini model outlines this simulated collaborative workflow among specialized AI agents:
        1.  **Data Ingestion Agent:** (Simulated) Responsible for parsing and normalizing input CV/JD data within the prompt structure.
        2.  **(RAG) Planner Agent:** (Simulated) Conceptually analyzes the primary inputs and determines what additional information would be beneficial. This informs the structure of the prompt.
        3.  **(RAG) Query Generation Agent:** (Simulated) Conceptually formulates queries. This is not a literal query to a DB in the client-side version but helps define the kind of information to be conceptually retrieved.
        4.  **(RAG) Retrieval Agent:** (Simulated) In the *current client-side version*, its interaction with a Vector DB is purely conceptual. Its output is explicitly represented by a placeholder string (e.g., `retrieved_context_string_placeholder_for_now`) which is then injected into the prompt to simulate the presence of retrieved knowledge.
        5.  **(RAG) Formatting Agent:** (Simulated) Conceptually prepares this placeholder information into a concise format for the main Synthesis Agent.
        6.  **Recruiter Insights & Prioritization Agent:** (Simulated) Critically evaluates and integrates recruiter-provided notes AND the (simulated) `retrieved_context_string_placeholder_for_now`. This agent ensures these inputs are given high priority and directly influence subsequent analysis steps within the prompt.
        7.  **Cross-Referencing & Evidence-Gathering Agent:** Performs detailed comparison between CV and JD data, heavily weighted by Recruiter Notes and the `retrieved_context_string`, based on active assessment dimensions.
        8.  **Multi-Factor Scoring Agent:** Quantifies alignment across various dimensions, with its analysis now grounded by the `retrieved_context_string` in addition to other inputs.
        9.  **Evidence-Based Explanation & Reporting Agent (Synthesis Agent):** This is the main Gemini model. It generates human-readable justifications, the final structured report, and strategic insights, now informed by the augmented context from the RAG pipeline.
    *   The system instruction meticulously defines the strict JSON output schema that the AI must adhere to, ensuring consistent, parsable, and reliable responses.
    *   Embeds ethical considerations, such as bias mitigation and transparency, into the AI's operational directives, emphasizing the need to cite evidence from all provided sources (CV, JD, Notes, Retrieved Context).
*   **Response Processing & Validation:** Incorporates robust parsing logic to manage JSON responses from the Gemini API, including handling potential structural variations and implementing error recovery mechanisms.

## Strategic Vision for Future Backend Architecture

To transition RecruitX into a scalable, secure, and feature-rich enterprise-grade platform, a comprehensive backend system is envisioned. This future architecture will significantly expand the application's capabilities and address the demands of multi-user environments and larger data volumes.

### 1. Backend Services & Application Logic

*   **Proposed Technology Stack:**
    *   **Node.js (e.g., Express.js, NestJS):** Preferred for its JavaScript/TypeScript ecosystem, ensuring consistency with the frontend technology stack and enabling full-stack development capabilities.
    *   **Alternative: Python (e.g., FastAPI, Django):** Considered for its extensive AI/ML libraries and robust web framework options.
*   **Core Responsibilities & Features:**
    *   **Secure API Gateway:** Expose well-defined, secure RESTful or GraphQL API endpoints for all frontend interactions.
    *   **User Authentication & Authorization:** Implement industry-standard authentication and authorization.
    *   **True Multi-Agent Orchestration Engine with Agentic RAG:**
        *   Evolve the conceptual AI agents (including Planner, Query Generation, Retrieval, Formatting, and Synthesis agents) into discrete, independently deployable microservices or functional modules.
        *   The **Retrieval Agent** will interact directly with the Vector Database to fetch relevant context.
        *   The **Planner and Query Generation Agents** might themselves be LLM-driven, formulating sophisticated queries for the knowledge base.
        *   Develop an orchestrator service to manage the complex workflows and data flow between these specialized agents, feeding the augmented context to the **Synthesis Agent (Gemini or another powerful LLM)**.
    *   **Server-Side Function Calling & Tool Integration:**
        *   Enable AI agents to execute predefined server-side functions or "tools." This allows them to interact programmatically with:
            *   Internal databases (e.g., retrieving company-specific cultural information, historical hiring data from the relational DB).
            *   The Vector DB for RAG.
            *   Validated external APIs (e.g., fetching real-time market salary data, verifying technical skills against industry ontologies).
    *   **Asynchronous Task & Background Job Processing:** Implement a robust queueing system for long-running RAG processes, analyses, and report generation.
    *   **Third-Party Integration Layer:** Design for integration with ATS, HRIS, etc.

### 2. Advanced Database Architecture

A multi-modal database strategy is proposed:

*   **Relational Database (e.g., PostgreSQL, MySQL):**
    *   Primary store for structured data: user accounts, company profiles, job descriptions, candidate profiles, generated reports.
*   **Vector Database (e.g., Pinecone, Weaviate, Milvus, Qdrant):**
    *   **Crucial for RAG:** Store vector embeddings of curated knowledge base documents (skill ontologies, detailed industry role descriptions, company information, anonymized best-practice examples).
    *   Powers semantic search and retrieval for the **Retrieval Agent** in the RAG pipeline.
*   **Document Database (e.g., MongoDB, Firestore - Optional/Complementary):**
    *   May store less structured data like raw AI model responses or detailed logs.
*   **Caching Layer (e.g., Redis, Memcached):**
    *   Cache frequently accessed data and results of expensive RAG-augmented analyses.

### 3. Scalability, Reliability, & Security

*   **Containerization & Orchestration:** Docker and Kubernetes.
*   **Cloud-Native Architecture:** Leverage cloud provider services.
*   **DevSecOps Practices:** Integrate security throughout the lifecycle.
*   **Monitoring, Logging, & Alerting:** Comprehensive operational visibility.

This strategic evolution, with Agentic RAG at its core, aims to position RecruitX as a leading enterprise talent intelligence platform, delivering highly sophisticated, context-aware, and accurate AI-driven insights.
