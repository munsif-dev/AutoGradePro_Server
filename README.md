# AutoGradePro Server

## Overview
AutoGradePro Server is the backend component of the AutoGradePro system, an AI-powered platform designed to automate the grading of short answers in educational settings. This Django-based REST API server handles data management, authentication, and the core AI grading functionality.

## Features

### AI-Powered Grading Engine
- Automated evaluation of short answer responses
- Integration with Ollama for semantic understanding of text
- Support for multiple answer types:
  - One-word answers (exact matching)
  - Short phrases (semantic matching using AI)
  - Lists (with configurable order sensitivity)
  - Numerical answers (with range support)

### Authentication System
- JWT-based authentication
- Role-based access control (lecturers and students)
- Secure API endpoints

### Data Management
- Comprehensive models for educational entities:
  - Users (Lecturers and Students)
  - Modules (Courses)
  - Assignments
  - Submissions
  - Marking Schemes
  - Grading Results

### File Processing
- Support for multiple file formats (TXT, PDF, DOCX)
- Intelligent parsing of student answers
- Secure file storage

### Grading Analytics
- Statistical analysis of student performance
- Score calculation and aggregation
- Pass/fail determination based on configurable thresholds

## Technical Stack

### Backend Framework
- Django
- Django REST Framework
- Django REST Framework SimpleJWT

### AI Integration
- Ollama for natural language processing
- Custom grading algorithms

### Database
- PostgreSQL (via psycopg2)

### Document Processing
- PyPDF2 for PDF parsing
- python-docx for DOCX parsing
- Custom text extraction and normalization

## API Endpoints

### Authentication
- `/api/token/` - Obtain JWT token
- `/api/token/refresh/` - Refresh JWT token

### Users
- `/api/lecturers/` - Lecturer management
- `/api/students/` - Student management

### Modules
- `/api/modules/` - Module CRUD operations

### Assignments
- `/api/assignment/` - Assignment management
- `/api/assigment-list-page/` - Paginated assignment listing with filtering

### Submissions
- `/api/submission/{assignment_id}/files/` - Get submissions for an assignment
- `/api/submission/{assignment_id}/upload/` - Upload submissions
- `/api/submission/{assignment_id}/grade/` - Grade submissions

### Marking Schemes
- `/api/assignment/{assignment_id}/marking-scheme/` - Manage marking schemes
- `/api/assignment/{assignment_id}/marking-scheme/detail/` - Get marking scheme details

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL
- Ollama (for AI grading)

### Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/AutoGradePro_Server.git
   cd AutoGradePro_Server/Server
   ```

2. Create a virtual environment
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables
   Create a `.env` file with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   DATABASE_URL=postgres://user:password@localhost:5432/autogradepro
   ```

5. Run migrations
   ```
   python manage.py migrate
   ```

6. Create a superuser
   ```
   python manage.py createsuperuser
   ```

7. Start the development server
   ```
   python manage.py runserver
   ```

## Project Structure
- `api/` - Main application code
  - `models.py` - Database models
  - `views.py` - API endpoints
  - `serializers.py` - Data serializers
  - `functions.py` - Core grading functionality
  - `urls.py` - URL routing
- `Server/` - Django project settings
- `media/` - Uploaded files storage
- `assignments/` - Assignment related files

## AI Grading Process

1. **File Parsing**: Student submissions are parsed based on file format (TXT, PDF, DOCX)
2. **Answer Extraction**: Individual answers are extracted using regex patterns
3. **Answer Evaluation**: Each answer is evaluated against the marking scheme
   - One-word answers: Exact matching (with optional case sensitivity)
   - Short phrases: AI-powered semantic matching using Ollama
   - Lists: Element matching (with optional order sensitivity)
   - Numerical: Value matching (with optional range checking)
4. **Score Calculation**: Marks are awarded based on correctness
5. **Result Storage**: Grading results are stored for future reference

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
