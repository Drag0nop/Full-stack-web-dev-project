# Autonomous Codebase Documenter

AI-powered documentation generator that automatically creates comprehensive README files for GitHub repositories and uploaded codebases using Google's Gemini AI.

## Features

- 🔐 **User Authentication** - Secure login/register with JWT tokens
- 📁 **GitHub Analysis** - Analyze any public GitHub repository
- 📤 **File Upload** - Upload ZIP/TAR.GZ codebases for analysis
- 🤖 **AI-Powered** - Generates professional README files using Gemini AI
- 📊 **History Tracking** - View all your past analyses
- 📈 **Statistics** - Track completed, in-progress, and failed analyses

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **MongoDB** - NoSQL database for user data and analyses
- **Google Gemini API** - AI model for README generation
- **Pydantic** - Data validation
- **JWT** - Authentication
- **bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Semantic markup
- **JavaScript (Vanilla)** - Client-side logic
- **Tailwind CSS** - Utility-first styling
- **Glassmorphism Design** - Modern UI aesthetics

## Project Structure

```
.
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
│   └── dashboard.html       # Main dashboard
│
└── README.md                # This file
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB (local or Atlas)
- Node.js (optional, for Tailwind CDN)
- Google Gemini API Key

### 1. Clone the Repository

```bash
git clone <repository-url>
cd autonomous-codebase-documenter
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your MongoDB URI and Gemini API key
```

### 3. Frontend Setup

No build step required! The frontend uses Tailwind CSS via CDN.

### 4. Run MongoDB

**Local MongoDB:**
```bash
mongod
```

**MongoDB Atlas:**
Use your connection string in the `.env` file.

### 5. Start the Application

```bash
# From the backend directory
python main.py
```

The server will start at `http://localhost:8000`

### 6. Access the Application

Open your browser and navigate to:
- **Login Page:** `http://localhost:8000/`
- **Dashboard:** `http://localhost:8000/dashboard`

**Demo Credentials:**
- Email: `demo@mail.com`
- Password: `password`

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Gemini API Key (Get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your-gemini-api-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/forgot-password` | Request password reset |
| GET | `/api/auth/profile` | Get current user profile |
| PUT | `/api/auth/profile` | Update user profile |
| POST | `/api/auth/change-password` | Change password |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze/github` | Analyze GitHub repository |
| POST | `/api/analyze/upload` | Upload and analyze file |
| GET | `/api/analyze/history` | Get analysis history |
| GET | `/api/analyze/{id}` | Get specific analysis |
| GET | `/api/analyze/{id}/status` | Get analysis status |
| DELETE | `/api/analyze/{id}` | Delete analysis |
| GET | `/api/analyze/stats` | Get user statistics |

## How to Use

### Analyze a GitHub Repository

1. Login to your account
2. Paste the GitHub repository URL in the input field
3. Click "Analyze"
4. Wait for the AI to generate the README
5. View or download the generated documentation

### Upload a Codebase

1. Login to your account
2. Drag & drop or browse for a ZIP/TAR.GZ file
3. Click "Upload & Analyze"
4. Wait for processing
5. View or download the README

## AI README Generation

The Gemini AI agent generates comprehensive README files including:

- Project overview and description
- Features and capabilities
- Installation instructions
- Usage examples
- Project structure
- Technologies used
- Contributing guidelines
- License information
- Acknowledgments

## Supported File Formats

- ZIP archives (`.zip`)
- Gzipped TAR archives (`.tar.gz`, `.tgz`)
- TAR archives (`.tar`)

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- CORS protection
- Input validation with Pydantic
- Secure file upload handling

## Troubleshooting

### MongoDB Connection Issues

```bash
# Check MongoDB is running
mongosh

# Verify connection in .env
MONGO_URI=mongodb://localhost:27017
```

### Gemini API Issues

- Ensure `GEMINI_API_KEY` is set correctly
- Check API quota at https://makersuite.google.com
- Verify network connectivity

### Port Already in Use

```bash
# Change port in .env or run command
PORT=8001
python main.py
```

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## Support

For issues and questions, please open an issue on GitHub.

## Recent Updates

- History now uses pagination with 5 analyses per page.
- A default admin account is created on startup: `admin@example.com` / `admin123`.
- Admin users can open `/admin.html` to view the total user count and registered user details.
- The dashboard includes a README Intelligence option that summarizes a GitHub repository README and suggests future improvements.

---

Built with ❤️ using FastAPI, MongoDB, and Google Gemini AI
