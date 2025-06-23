# # 🚀 Draft Mode - Setup Guide
A retro-styled blog draft management system built with Flask. This guide will walk you through setting up the project from scratch.
# 📋 Prerequisites
* Python 3.8 or higher
* pip (Python package installer)
* Git (optional, for version control)

⠀🛠️ Initial Setup
### 1. Clone or Download the Project

### bash
*# If using Git*
git clone <your-repository-url>
cd flask-app

*# Or if you downloaded the files*
cd path/to/your/flask-app
### 2. Create and Activate Virtual Environment
**On macOS/Linux:**

### bash
*# Create virtual environment*
python3 -m venv venv

*# Activate virtual environment*
source venv/bin/activate

*# Verify activation (you should see (venv) in your prompt)*
which python
**On Windows:**

### bash
*# Create virtual environment*
python -m venv venv

*# Activate virtual environment*
venv\Scripts\activate

*# Verify activation (you should see (venv) in your prompt)*
where python
### 3. Install Dependencies

### bash
*# Upgrade pip first*
pip install --upgrade pip

*# Install all required packages*
pip install -r requirements.txt
### 4. Set Up Environment Variables (Optional but Recommended)
Create a .env file in your project root:

### bash
*# Create .env file*
touch .env  *# On macOS/Linux*
*# OR*
echo. > .env  *# On Windows*
Add the following content to .env:

### env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///draft_mode_dev.db
FLASK_ENV=development
FLASK_APP=app.py
### 5. Initialize Database Migrations

### bash
*# Initialize migration repository (run once)*
flask db init

*# Create initial migration*
flask db migrate -m "Initial migration with users, drafts, and versions"

*# Apply migration to create database tables*
flask db upgrade
### 6. Verify Directory Structure
Your project should look like this:

flask-app/
├── app.py                    # Main application
├── config.py                 # Configuration classes
├── models.py                 # Database models
├── requirements.txt          # Dependencies
├── .env                      # Environment variables (you created this)
├── migrations/               # Database migration files (created by flask db init)
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── routes/
│   ├── __init__.py
│   ├── auth.py              # Authentication routes
│   ├── main.py              # Main routes
│   ├── drafts.py            # Draft management
│   └── api.py               # API endpoints
├── utils/
│   ├── __init__.py
│   └── decorators.py        # Utility decorators
├── templates/               # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── dashboard.html
│   ├── create_draft.html
│   ├── edit_draft.html
│   ├── compare.html
│   ├── public_view.html
│   ├── 404.html
│   └── 500.html
└── draft_mode_dev.db        # SQLite database (created after first run)
# 🚀 Running the Application
### Start the Development Server

### bash
*# Make sure your virtual environment is activated*
*# You should see (venv) in your terminal prompt*

*# Run the application*
python app.py

*# Alternative method using Flask CLI*
flask run
You should see output like:

* Running on http://127.0.0.1:5000
* Debug mode: on
### Open in Browser
Navigate to http://localhost:5000 or http://127.0.0.1:5000
# 🔧 Development Workflow
### Making Database Changes
When you modify the models in models.py:

### bash
*# Create a new migration*
flask db migrate -m "Description of your changes"

*# Apply the migration*
flask db upgrade
### Adding New Features
**1** **Routes**: Add new routes to appropriate blueprint files in routes/
**2** **Templates**: Add HTML templates to templates/
**3** **Models**: Modify models.py and create migrations
**4** **Static Files**: Add CSS/JS to a new static/ directory if needed

⠀Stopping the Server
Press Ctrl+C in the terminal where the server is running.
### Deactivating Virtual Environment

### bash
deactivate
# 🧪 Testing the Application
### Create Your First Account
1 Go to http://localhost:5000
2 Click "Sign Up"
3 Create an account with:
	* Name: Your Name
	* Email: ~[test@example.com](mailto:test@example.com)~
	* Password: password123

⠀Test Core Features
**1** **Create a Draft**: Click "New Draft" and create your first blog post
**2** **Version Management**: Create multiple versions of your draft
**3** **Preview**: Test the live markdown preview
**4** **Sharing**: Generate a public share link
**5** **Comparison**: Compare different versions

⠀🐛 Troubleshooting
### Common Issues
**"Module not found" errors**

### bash
*# Make sure virtual environment is activated*
source venv/bin/activate  *# macOS/Linux*
*# OR*
venv\Scripts\activate     *# Windows*

*# Reinstall dependencies*
pip install -r requirements.txt
**Database errors**

### bash
*# Reset database (WARNING: This deletes all data)*
rm draft_mode_dev.db
rm -rf migrations/  *# Optional: reset migrations*
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
**Port already in use**

### bash
*# Run on different port*
flask run --port 5001
**Permission errors on Windows**

### bash
*# Run terminal as Administrator or use:*
python -m pip install -r requirements.txt
### Environment Issues
**Virtual environment not working**

### bash
*# Remove and recreate virtual environment*
rm -rf venv  *# or rmdir /s venv on Windows*
python -m venv venv
source venv/bin/activate  *# or venv\Scripts\activate on Windows*
pip install -r requirements.txt
# 📝 Development Tips
### Useful Commands

### bash
*# See all Flask commands*
flask --help

*# See database migration history*
flask db history

*# Downgrade database (rollback)*
flask db downgrade

*# See current migration*
flask db current

*# Install new package and update requirements*
pip install package-name
pip freeze > requirements.txt
### IDE Setup
**VS Code Extensions:**
* Python
* Flask-Snippets
* Jinja2

⠀**PyCharm:**
* Enable Flask support in project settings

⠀Git Setup (Recommended)

### bash
*# Initialize git repository*
git init

*# Create .gitignore file*
echo "venv/
*.pyc
__pycache__/
instance/
.env
draft_mode_dev.db" > .gitignore

*# Initial commit*
git add .
git commit -m "Initial commit: Draft Mode setup"
# 🚀 Production Deployment
For production deployment, you'll need to:
1 Set FLASK_ENV=production in environment variables
2 Use a proper database (PostgreSQL, MySQL)
3 Set a secure SECRET_KEY
4 Use a production WSGI server (Gunicorn, uWSGI)
5 Configure reverse proxy (Nginx, Apache)

⠀
# 🎉 You're Ready!
Your Draft Mode application is now set up and running! Start by creating your first draft and exploring the retro-styled interface.
**Need help?** Check the troubleshooting section above or review the code comments for implementation details.
Happy writing! ✍️

