# 🚀 FaceConnect API & Frontend

This is a full-stack, scalable web application that replicates core features of a social media platform like Facebook. It is built with a Flask backend and a vanilla JavaScript frontend.

The application includes real-time features using WebSockets (Socket.IO) and is designed with a modern, maintainable project structure after being refactored from a single-file script.

## ✨ Features

* **Authentication:** User registration, login, and logout with JWT.
* **Social Feed:** A main feed of posts from friends.
* **Posts:** Create, read, edit, and delete posts.
* **Reactions:** React to posts with "like", "love", "haha", "wow", "sad", or "angry".
* **Comments:** Create, read, edit, and delete nested comments.
* **Friend System:** Send, accept, and reject friend requests; follow/unfollow users.
* **Stories:** Post 24-hour expiring stories (text-based).
* **Real-time Chat:** Live messaging and online status indicators via Socket.IO.
* **Notifications:** Real-time notifications for likes, comments, friend requests, etc.
* **Search:** Search for users and posts.
* **Profile:** View and update user profiles, including profile pictures.

## 🛠️ Tech Stack

* **Backend:**
    * **Flask:** Micro web framework for the API.
    * **Flask-SQLAlchemy:** ORM for database operations (using SQLite).
    * **Flask-JWT-Extended:** For handling JSON Web Token authentication.
    * **Flask-SocketIO:** For real-time WebSocket communication.
    * **eventlet:** A high-performance server that supports WebSockets.
    * **Flask-Limiter:** For API rate limiting.
* **Frontend:**
    * **HTML5:** The main structure.
    * **CSS3:** All custom styling for the UI.
    * **Vanilla JavaScript (ES6+):** For all client-side logic, API fetching, and DOM manipulation.
* **Database:**
    * **SQLite:** Default database for ease of development.

## 📁 Project Structure
clonee/
├── backend/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── friends.py
│   │   ├── main.py
│   │   ├── messaging.py
│   │   ├── notifications.py
│   │   ├── posts.py
│   │   ├── profile.py
│   │   └── stories.py
│   ├── sockets/
│   │   ├── __init__.py
│   │   └── handlers.py
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── helpers.py
│   └── models.py
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   └── templates/
│       └── index.html
│
├── .env
├── .gitignore
├── db_init.py
├── facebook.db           <-- (This is created when you run db_init.py)
├── README.md
├── requirements.txt
└── run.py

## 🚀 How to Run

### 1. Prerequisites

* Python 3.8+
* `pip` (Python package installer)

### 2. Setup

1.  **Clone the repository (or create the files):**
    
    git clone [https://your-repo-url.com/faceconnect.git](https://your-repo-url.com/faceconnect.git)
    cd faceconnect_project
    

2.  **Create a virtual environment (Recommended):**
    
    python -m venv venv
    

3.  **Activate the virtual environment:**
    * **On Windows:** `.\venv\Scripts\activate`
    * **On Mac/Linux:** `source venv/bin/activate`

4.  **Install dependencies:**
    Make sure you have `eventlet` in your `requirements.txt` file, then run:
    
    pip install -r requirements.txt
    

5.  **Create your `.env` file:**
    Create a file named `.env` in the root directory and add your secret keys. Use a Python terminal (`import secrets; secrets.token_hex(32)`) to generate secure random keys.
    
    SECRET_KEY='YOUR_FIRST_LONG_RANDOM_STRING_HERE'
    JWT_SECRET_KEY='YOUR_SECOND_DIFFERENT_RANDOM_STRING_HERE'
    SQLALCHEMY_DATABASE_URI='sqlite:///facebook.db'
    

### 3. Initialize the Database

Before running the app for the first time, you must create the database tables.

python db_init.py

### 4. Run the Server
Start the application using the main run.py script.

python run.py

### 5. Access the App
Open your web browser and go to the URL provided in the terminal: http://127.0.0.1:5000

*** ctrl + c = quit ***
