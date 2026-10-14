# PEER SURE

Peer Supported Substance Use Research and Education web application, built by the [Data Lab at Marquette University](https://www.cs.mu.edu/~praveen/Research-include1.html).

PEER SURE pairs people in recovery with peer support specialists (mentors), supports regular check-ins, and gives mentors a dashboard of mentee progress over time. Mentors can also draft forum replies with generative AI, then review that text before posting.

## Demo

Watch a walkthrough of the app:

**[Project demo (Vimeo)](https://vimeo.com/1020239730)**

## Features

- **Accounts and roles.** Register as a mentee or mentor, join one or more organizations, and (for mentees) link a mentor by email.
- **Weekly check-in.** Mentees complete a short organization-specific survey and can add a free-text comment.
- **Onboarding surveys.** Profile flow includes Past Medical and Family History (PMHx) and Demographic surveys.
- **Progress tracker.** Mentors view Plotly charts of weekly scores, filter by date range, mentee, and question, and watch behavior change over time.
- **Forum.** Organization-scoped posts and comments, including anonymous posts. Authors can edit or delete their own posts.
- **AI-assisted replies.** Mentors can generate a suggested comment from a post’s context, then edit it before sending.
- **Password reset.** Email-based reset through the Gmail API.
- **Admin export.** Django admin actions export posts and comments to CSV.

After login, mentees land on Check-In, mentors land on Progress-Tracker, and users with multiple organizations pick an organization first.

## Tech stack

| Layer | Tools |
| --- | --- |
| Backend | Django 5, Python 3.11 |
| UI | Django templates, Bootstrap 4, Crispy Forms |
| Charts | Plotly, pandas |
| Databases | SQLite (local), Azure Database for PostgreSQL (production) |
| Static files | WhiteNoise |
| Email | Gmail API (`google-api-python-client`) |
| Deploy | Azure App Service via GitHub Actions |

Django apps:

- `users` — registration, profiles, organizations, password reset
- `survey` — check-in and related surveys
- `vizual` — mentor progress dashboard
- `feed` — forum posts, comments, AI reply helper
- `APIs` — generative AI wrapper used by the forum

## Local setup

**Requirements:** Python 3.11+, pip

1. Clone the repository and create a virtual environment:

   ```bash
   git clone https://github.com/sajjadIslam2619/peer_sure_app.git
   cd peer_sure_app
   python -m venv venv
   ```

   On Windows (PowerShell):

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   On macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Add a Django secret key. Create `secret_key.txt` in the project root with a single secret string (no quotes).

4. Apply migrations and start the server (defaults to development / SQLite):

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

5. Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

Create organizations, survey categories, surveys, questions, and options in Django admin (`/admin/`) so check-in and onboarding surveys are available for each organization.

### Environment

| Variable | Purpose |
| --- | --- |
| `DJANGO_ENV_PEER_SURE` | `dev` (default) uses SQLite and `DEBUG=True`. `prod` uses PostgreSQL and `DEBUG=False`. |
| `DB_PASS_PEER_SURE_APP` | PostgreSQL password when `DJANGO_ENV_PEER_SURE=prod`. |

Password-reset email needs Gmail API credentials in `users/credentials.json` (and a generated `users/token.json` after first auth). Those files are not required to browse the rest of the app locally.

## Production

The app is deployed to Azure App Service (`peer-sure-app.azurewebsites.net`). Pushes to `main` run [`.github/workflows/main_peer-sure-app.yml`](.github/workflows/main_peer-sure-app.yml), which installs dependencies and deploys the Python app.

Production expects:

- `DJANGO_ENV_PEER_SURE=prod`
- `DB_PASS_PEER_SURE_APP` set in Azure Application Settings
- `secret_key.txt` available on the host

## Project layout

```
peer_sure_app/     Django project settings and URL routing
users/             Auth, profiles, organizations, Gmail backend
survey/            Check-in surveys and responses
vizual/            Mentor dashboard and Plotly charts
feed/              Forum, comments, AI reply endpoint
APIs/              Generative AI helper
.github/workflows/ Azure deploy pipeline
```

## Support

Contact: [mudatalab@gmail.com](mailto:mudatalab@gmail.com)
