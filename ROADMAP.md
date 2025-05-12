# RecruitX – End-to-End Roadmap (Local Docker ≈ AWS)

> **Goal:** Deliver a SOTA, multi-agent JD ⇄ CV matching platform that runs today on a single laptop (Docker Compose) while mirroring the AWS production topology for a drop-in future migration.

---

## 0 · Key Non-Functional Requirements
| Topic | Target |
|-------|--------|
| Accuracy KPI | ≥ 85 % good/excellent matches (manual eval) |
| Latency | ≤ 2 s p95 for match request after extraction |
| Throughput | 10 req/s burst → 100 req/s (autoscale) |
| Cost | ≤ $0.02 per JD–CV pair |
| Availability | 99.9 % |
| Compliance | GDPR delete-on-demand, SOC2 ready |

---

## 1 · Tech-Stack Summary
| Tier | Stack | Rationale |
|------|-------|-----------|
| Frontend | **Next.js 14**, React 18, TS | SSR, file uploads, auth |
| API Gateway | Next.js Route Handlers + **tRPC** | End-to-end types |
| Workers / Agents | **LangChainJS**, **CrewAI** running in Node18 | Multi-agent orchestration |
| LLMs | Gemini flash-lite / flash, GPT-3.5 fallback | Accuracy + cost |
| DB | PostgreSQL 15 + **pgvector** (via Prisma) | Relational + embeddings |
| Cache & Queue | Redis 7 + BullMQ | Rate-limit & async jobs |
| Object Store | S3 (prod) / **MinIO** (local) | File blobs & extractions |
| AWS Emulation | **LocalStack** | S3, SQS, SES, Lambda parity |
| Observability | Grafana, Prometheus, Loki, Tempo | Full telemetry |
| CI/CD | GitHub Actions → Docker, **Terraform** modules | IaC + pipelines |

---

## 2 · System Architecture
`Next.js → API → Redis queue → Workers / Agents → Postgres/pgvector → Object Store`

```
             +---------------+
 FRONTEND    |  Next.js 14   |
             +------+--------+
                    | tRPC
                    v
             +------+--------+          async via Redis
  API        |  Gateway      |<---------------------+
             +------+--------+                      |
                    |                                |
   +----------------v-------------------+            |
   |       Workers / Agents Layer       |            |
   |------------------------------------|            |
   | 1 File-Ingest-Svc   (S3)           |      publish job
   | 2 Extraction-Agent (Unstructured)  |<-------------+
   | 3 Review UI (Monaco)               |
   | 4 Matching-Agents (LLMs)           |
   | 5 Report-Agent (react-pdf)         |
   +------------------------------------+
                    |
                    v
             +------+--------+
             |  Postgres     |
             +------+--------+
                    |
                    v
             +------+--------+
             |  pgvector     |
             +---------------+
```

---

## 3 · Local-Docker Infrastructure (AWS Parity)
All services are orchestrated with **docker-compose** to mimic AWS resources:

| AWS Service | Docker Image | Usage |
|-------------|--------------|-------|
| RDS (Postgres) | `postgres:15-alpine` | DB & pgvector |
| ElastiCache | `redis:7-alpine` | cache, BullMQ queue |
| S3 | `minio/minio` OR LocalStack S3 | raw files, reports |
| SQS | LocalStack | async event bus (future decoupling) |
| SES | LocalStack | email previews |
| Lambda | LocalStack | playground for agent inference |
| CloudWatch | Grafana + Loki | logs, metrics |
| ECR | Local registry (`registry:2`) | container pushes |

### docker-compose.yaml (excerpt)
```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: recruitpro
    ports: ["5432:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  localstack:
    image: localstack/localstack:latest
    environment:
      SERVICES: s3,sqs,lambda,ses
      EDGE_PORT: 4566
    ports: ["4566:4566"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9090"
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio123
    ports:
      - "9000:9000"
      - "9090:9090"

  app:
    build: . # your Next.js / workers image
    env_file: .env
    depends_on: [postgres, redis, localstack, minio]
    ports: ["3000:3000"]
```

> **Tip:** Keep compose file in `infra/docker-compose.yaml`.  Use **dotenv-compose** to inject secrets per environment.

---

## 4 · AWS Production Blueprint (future)
* Terraform modules in `infra/aws/` provision:
  * VPC with 2 AZs
  * RDS Postgres 15 + pgvector extension
  * ElastiCache Redis cluster
  * S3 bucket `recruitx-prod-files`
  * ECR repo `recruitx/app`
  * Fargate ECS service w/ ALB
  * SQS queues: `extract_text`, `match_job`
  * SES domain-verified identity
  * CloudWatch Container Insights, X-Ray tracing
* Secrets in AWS Secrets Manager (Gemini keys etc.)
* CI pipeline pushes tagged image to ECR, runs `terraform apply` (with plan approval).

### Parity Rules
| Local (Compose) | AWS (Prod) |
|-----------------|------------|
| minio           | S3 |
| localstack SQS  | SQS |
| docker network  | VPC |
| mounted `.env`  | Secrets Manager |

---

## 5 · LLM Key Rotation & Fallback
Located in `/lib/llm.ts` – same code local & prod.  Keys stored as comma-separated secret string → split into array.

---

## 6 · CI / CD Pipeline
1. **Pre-commit:** ESLint, Prettier, Husky, commitlint.
2. **GitHub Actions:**
   - `build`: pnpm install → test → type-check → docker build.
   - `push-local`: `docker compose up -d --build` (for PR preview via ngrok).
   - `push-aws`: on `main` tag → login to ECR → push → TF plan/apply.
3. **Monitoring:** Post-deploy smoke (Playwright) + k6 perf job.

---

## 7 · Security & Compliance
* HTTPS everywhere (mkcert locally, ACM in AWS)
* Helmet, rate-limit by IP + JWT subject
* OWASP ZAP scan in CI
* S3 bucket policy: private, encryption SSE-S3 (prod)
* GDPR delete route & DB cascade

---

## 8 · Testing Matrix
| Layer | Tool | Notes |
|-------|------|-------|
| Unit | Vitest / Jest | extractors, utils |
| Contract | Pact | tRPC schema | 
| Agent Prompts | Spectral tests + jsonschema validation | guardrail |
| E2E | Playwright | upload → PDF report |
| Load | k6 | 100 rps for 10 min |

---

## 9 · Timeline (8 Weeks)
| Week | Deliverables |
|------|--------------|
| 1 | Repo scaffold, docker-compose infra, auth flow |
| 2 | File upload → S3/MinIO, extraction worker |
| 3 | Review UI, key-rotation lib |
| 4 | Matching agents (skills / culture) |
| 5 | Reporting agent, PDF & dashboard |
| 6 | Observability stack (Grafana + Loki) |
| 7 | Security audit, load tests, staging ECS (optional) |
| 8 | Prod readiness, Terraform reviewed, docs |

---

## 10 · Future Extensions
* Semantic search for candidate pool (pgvector + ANN)
* Chatbot interface for recruiters (“Ask this JD…”) using RAG
* Auto-redaction of PII in extracted text (presidio-analyzer)
* Multi-tenant isolation via row-level security

---

© 2025 RecruitX  •  Crafted for scalability & AWS parity ✨
