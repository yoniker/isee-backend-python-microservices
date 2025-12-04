# iSee Backend Service

Backend infrastructure for the iSee mobile application, responsible for serving the API, managing image uploads, and running deep learning inference using PyTorch.

## Security Note
**This repository is a snapshot of a formerly private codebase.**
*   Legacy configuration files may contain hardcoded credentials from early development.
*   **All exposed keys have been revoked.**
*   Production environments should use Environment Variables or AWS Secrets Manager.

## Technology Stack
*   **Framework:** Python (Flask)
*   **AI/ML:** PyTorch (Inference Engine)
*   **Infrastructure:** AWS ECS, Docker
*   **Storage:** AWS S3
*   **Database:** PostgreSQL

## Project Overview
*   **API Layer:** Flask-based REST API handling user requests and authentication.
*   **Inference:** PyTorch models integrated directly for real-time image processing.
*   **Deployment:** Containerized using Docker and orchestrated via Amazon ECS for scalability.
