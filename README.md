# 🚀 FaceConnect API & Frontend

This is a full-stack, scalable web application that replicates core features of a social media platform like Facebook. It is built with a Flask backend and a vanilla JavaScript frontend.

The application includes real-time features using WebSockets (Socket.IO) and is designed with a modern, maintainable project structure.

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
    * **Flask-Limiter:** For API rate limiting.
    * **Pyngrok:** To expose the local server to the internet.
* **Frontend:**
    * **HTML5:** The main structure.
    * **CSS3:** All custom styling for the UI.
    * **Vanilla JavaScript (ES6+):** For all client-side logic, API fetching, and DOM manipulation.
* **Database:**
    * **SQLite:** Default database for ease of development.

## 📁 Project Structure