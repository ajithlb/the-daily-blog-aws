# The Daily Blog — Flask + AWS starter project

A GitHub-ready starter implementation based on the website shown in the supplied project demo. It includes account registration/login, a blog feed, post details, and a create-post page. Optional Amazon SNS notifications can be enabled when a new post is published.

> **Important:** This is a clean starter implementation created from the demo/context, not a recovery of the original source code from the screen recording. Review and adapt it to match your actual AWS deployment before presenting it as your exact project.

## Features

- Flask application with responsive HTML/CSS templates
- User registration and login with Werkzeug password hashing
- Create and view blog posts
- SQLite database for local development
- Optional SNS notifications using `boto3`
- Environment-based configuration; no AWS keys stored in source code
- Procfile for platforms that support Gunicorn

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = "replace-this-with-a-long-random-secret"
python app.py
```

Open http://127.0.0.1:5000.

A sample post is seeded on the first run. A demo account is also seeded for local testing:

- Username: `demo`
- Password: `DemoPassword123!`

Delete the demo account and sample content before deploying publicly. Do not use the demo password in production.

## Optional Amazon SNS notifications

1. Create an SNS topic in the AWS region you intend to use.
2. Configure subscriptions and confirm them where required.
3. Give the application's **IAM role** permission to call `sns:Publish` on that topic ARN.
4. Set `AWS_REGION` and `SNS_TOPIC_ARN` as environment variables in your runtime.
5. Use an IAM role (for example, an Elastic Beanstalk instance profile) rather than hardcoding AWS access keys.

When SNS is not configured, the app continues to work locally and skips notifications.

## AWS deployment notes

This starter can be adapted for AWS Elastic Beanstalk. Before production use:

- Set a strong `FLASK_SECRET_KEY` in the platform environment.
- Replace SQLite with Amazon RDS for multi-instance/production deployments; SQLite is intended for local demonstration only.
- Configure HTTPS, secure session cookies, CSRF protection, input validation, and rate limiting.
- Use an IAM role with least-privilege permissions.
- If storing uploaded images/files in S3, use a private bucket and presigned URLs; this starter does not currently implement file uploads or S3 storage.
- Configure CloudWatch logs/alarms and test the deployment.

## Suggested GitHub upload

Create a new GitHub repository named `the-daily-blog-aws`, extract this ZIP, then run:

```bash
git init
git add .
git commit -m "Initial commit: The Daily Blog Flask AWS project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/the-daily-blog-aws.git
git push -u origin main
```

Never commit `.env`, AWS access keys, passwords, or other secrets.
