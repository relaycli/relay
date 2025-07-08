# Relay
SDK and CLI for email management

## What you get
- Production ready backend with user authentication
- Cloud-backed DB
- Coming soon: beautiful documentation

## What it's built with
- Builds: docker images stored on GitHub
- Continuous deployment: GitHub Workflows, orchestrated with Docker, using Traefik as proxy
- Database: Postgres DB hosted on Supabase, migration using alembic
- Backend framework: FastAPI
- Services: email using Resend

## 1min setup
- Click on "Use this template" and "Create a new repository"
- Boot a small VM and set up a S3 storage with your cloud provider
- Configure your DNS to point the subdomain "api.yourdomain.com" to your instance
- Signup to an account on Supabase, Resend and Codecov. Optionally also on Logfire, Sentry and PostHog
- in your GitHub repository, add the following secret: codecov token, ssh prod host + user + key, secrets .env

## Roadmap
- [ ] Add documentation using Mintlify
