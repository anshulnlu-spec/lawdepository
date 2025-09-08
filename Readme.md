Global Law Depository (Google Cloud Platform Version)
This is an AI-powered repository of legal documents that automatically discovers, analyzes, and categorizes new content daily. It is designed for a professional, scalable deployment on Google Cloud Platform.

Architecture
Cloud Run: Hosts the live FastAPI web application.

Cloud Scheduler: Triggers the AI researcher job on a daily schedule.

Cloud Build: Automatically builds and deploys the application from this GitHub repository.

Secret Manager: Securely stores the Gemini API key.

One-Click Deployment
Simple Setup Instructions
Follow these steps to get your website live.

1. Prepare Your Google Cloud Project
Before clicking the button above, you need to do a one-time setup in your Google Cloud account.

A. Create a New Project:

Go to the Google Cloud Console.

Create a new project and give it a name (e.g., law-depository-project).

Important: Make sure your new project is selected at the top of the page.

B. Enable the 5 Necessary APIs:

In the search bar at the top, find and Enable each of these five services one by one:

Cloud Run API

Cloud Build API

Secret Manager API

Cloud Scheduler API

Artifact Registry API

C. Store Your Gemini API Key:

In the search bar, find Secret Manager.

Click Create Secret.

Name: gemini-api-key (use this exact name).

Secret value: Paste your actual Gemini API key.

Click Create Secret.

2. Deploy the Application
Once the one-time setup is complete, come back to this README.md file on GitHub.

Click the "Run on Google Cloud" button at the top.

A new window will open. Follow the on-screen prompts to:

Authorize Google Cloud to connect to your GitHub account.

Confirm the repository and branch.

Approve the deployment settings.

This will automatically create the Cloud Build trigger and deploy your website to Cloud Run. The first build may take 5-10 minutes.

3. Schedule the Daily AI Researcher
After the deployment is successful, you need to set up the daily automated job.

Go to the Cloud Run page in your Google Cloud Console and find your new service (law-depository-service). Click on it and copy its URL.

Go to the Cloud Scheduler page.

Click Create Job.

Name: daily-ai-researcher

Frequency: 0 4 * * * (This runs every day at 4 AM)

Timezone: Select your desired timezone.

Target type: HTTP

URL: Paste the URL you copied and add /run-tasks at the end (e.g., https://your-service-url.run.app/run-tasks).

HTTP method: POST

Click Create.

Congratulations! Your website is now fully deployed and automated.