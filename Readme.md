# Legal Docs Service

This repository contains the source code and deployment configuration for the **Legal Docs Service**, a FastAPI application deployed on Google Cloud Run.

---

## Features

* FastAPI backend served with Uvicorn.
* PostgreSQL database connection (via SQLAlchemy & psycopg2).
* Configuration management with `config.py` and `.env` (for local dev).
* Secure secret management using **Google Secret Manager** for production (`DB_USER`).
* Automated build and deployment with **Cloud Build** and `cloudbuild.yaml`.

---

## Local Development

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/legal-docs-service.git
   cd legal-docs-service
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run locally:

   ```bash
   uvicorn main:app --reload
   ```

App will be available at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## Deployment

This project uses **Google Cloud Build** to build and deploy to **Cloud Run**.

### Pre-requisites

* Google Cloud project: `gen-lang-client-0486914658`
* Enable the following APIs:

  * Cloud Run
  * Cloud Build
  * Artifact Registry
  * Secret Manager
* Secret in Secret Manager: `legal-docs-db-user`
* Service account permissions:

  * `roles/run.admin`
  * `roles/secretmanager.secretAccessor`

### Deploying Manually

To build and deploy manually from local:

```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_SERVICE_NAME=legal-docs-service,_REGION=us-central1,_PROJECT_ID=gen-lang-client-0486914658,_REPOSITORY=legal-docs-repo,_IMAGE_TAG=latest,_SECRET_NAME=legal-docs-db-user
```

### Deploying via GitHub Trigger

1. Connect your GitHub repo to Google Cloud Build.
2. Create a trigger:

   * Event: Push to `main` (or your default branch).
   * Configuration file: `cloudbuild.yaml`
   * Substitutions (set in trigger UI):

     * \`\_SERVIC
