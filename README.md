# Autonomous Codebase Documenter

AI-powered documentation generator that can generate README files from codebases, summarize existing GitHub READMEs, track per-user usage history, and provide admin-side analytics.

## Features

<<<<<<< HEAD
- Secure login and role-based admin access
- Generate README files from public GitHub repositories
- Upload ZIP codebases and generate README files from them
- Read an existing repository README and get a summary plus improvement suggestions
- Paginated user history with action-type labels
- User stats for total actions, README generations, README summaries, and failures
- Admin search, user list view, and per-user usage analytics
=======
- 🔐 **User Authentication** - Secure login/register with JWT tokens
- 📁 **GitHub Analysis** - Analyze any public GitHub repository
- 📤 **File Upload** - Upload ZIP/TAR.GZ codebases for analysis
- 🤖 **AI-Powered** - Generates professional README files using Gemini AI
- 📊 **History Tracking** - View all your past analyses
- 📈 **Statistics** - Track completed, and failed analyses
>>>>>>> aba8a7f827d7d6cd7202132daaaaf78eae19cfe8

## Tech Stack

### Backend

- FastAPI
- MongoDB
- Google Gemini API
- Pydantic Settings
- JWT authentication
- bcrypt password hashing

### Frontend

- HTML5 / CSS3
- Vanilla JavaScript
- Tailwind CSS
- Three.js

## Project Structure

```text
.
<<<<<<< HEAD
|-- backend/
|   |-- app/
|   |   |-- main.py
|   |   |-- core/
|   |   |-- database/
|   |   |-- models/
|   |   |-- routes/
|   |   `-- services/
|   |-- run.py
|   `-- .env
|-- frontend/
|   |-- index.html
|   |-- dashboard.html
|   `-- admin.html
`-- README.md
=======
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── database.py          # MongoDB connection management
│   ├── models.py            # Pydantic data models
│   ├── ai_agent.py          # Gemini AI agent for README generation
│   ├── routes/
│   │   ├── auth.py          # Authentication endpoints
│   │   └── analysis.py      # Analysis endpoints
│   ├── uploads/             # Temporary file storage
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment variables template
│
├── frontend/
│   ├── index.html           # Login/Register page
│   ├── dashboard.html       # Main dashboard
│   └── admin.html
│
└── README.md                # This file
>>>>>>> aba8a7f827d7d6cd7202132daaaaf78eae19cfe8
```

## Setup

### Prerequisites

- Python 3.9+
<<<<<<< HEAD
- MongoDB local or Atlas
- A valid Gemini API key
=======
- MongoDB (local or Atlas)
- HTML/CSS/JS
- Google Gemini API Key
>>>>>>> aba8a7f827d7d6cd7202132daaaaf78eae19cfe8

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env` and configure:

```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=code_documenter
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
```

### Run

```bash
cd backend
python run.py
```

The app will be available at:

- Login: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard.html`
- Admin: `http://localhost:8000/admin.html`

### Default Admin

- Email: `admin@example.com`
- Password: `admin123`

## Main Flows

### Generate README From Repository Code

1. Open the dashboard.
2. Paste a public GitHub repository URL.
3. Click `Generate README`.
4. Review or download the generated output.

### Generate README From Uploaded Codebase

1. Upload a `.zip` codebase.
2. Click `Upload & Analyze`.
3. Review or download the generated output.

### Read Existing README

1. Open the `Read Existing README` section.
2. Paste a GitHub repository URL.
3. Click `Summarize`.
4. Review the summary and suggested improvements.

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analysis/github` | Generate README from GitHub repo |
| POST | `/api/analysis/upload` | Generate README from uploaded ZIP |
| GET | `/api/analysis/history` | Get paginated history and user stats |
| POST | `/api/analysis/readme/intelligence` | Summarize an existing GitHub README |
| POST | `/api/analysis/github/readme-summary` | Legacy README summary endpoint |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | Get non-admin users with usage stats |

## AI README Generation

The GitHub README generation flow is optimized to reduce token usage:

- shallow clone of the repository
- lightweight AST and symbol extraction
- compact structural summary sent to Gemini
- fallback model handling for supported Gemini models

Generated output typically includes:

- Project overview
- Architecture summary
- Key components
- Data flow
- Setup and usage notes
- Improvements and future work

## Dashboard and Admin Notes

- History uses pagination with 5 items per page.
- Dashboard stats break down `Generate README`, `README Summary`, and `Failed`.
- README summary actions are saved into history and included in stats.
- Admin can search users and open per-user usage analytics.

## Troubleshooting

### Gemini API

- Ensure `GEMINI_API_KEY` is valid and not expired.
- Restart the backend after changing `.env`.
- Check Gemini quota and rate limits.
- Verify outbound access to `generativelanguage.googleapis.com`.

### MongoDB

- Ensure MongoDB is running or Atlas credentials are correct.
- Verify `MONGO_URI` and `DB_NAME` in `backend/.env`.

## License

<<<<<<< HEAD
MIT
=======
This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Support

For issues and questions, please open an issue on GitHub.

---
>>>>>>> aba8a7f827d7d6cd7202132daaaaf78eae19cfe8
