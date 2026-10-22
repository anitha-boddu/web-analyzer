# Smart Web Analyzer

Smart Web Analyzer is a browser-based intelligent assistant that helps users analyze, summarize, and interact with any webpage by simply providing its URL. With built-in user login, personalized activity tracking, and AI-powered chatbot functionality, it makes understanding online content faster, easier, and smarter.

---

## ✅ Problem Statement

With the growing volume of web information, users often struggle to process, summarize, and understand lengthy webpages. There is a need for a system that can extract relevant data and provide intelligent answers based on that content, without requiring users to read through everything manually.

---

## 🌟 Proposed Solution

- A web interface where users can input any URL.
- The system extracts and summarizes meaningful content.
- AI chatbot answers questions using that page’s actual data.
- Secure login and personalized tracking of visited URLs.
- Option to filter user history based on date.
- Premium features available via a simple subscription flow.

---

## 🔑 Key Features

- Simple and responsive URL input interface  
- Intelligent webpage content extraction and summarization  
- Integrated AI chatbot trained on real-time page content  
- Secure user authentication with personalized sessions  
- Dashboard showing visited links per user  
- Filter activity by date to manage history efficiently  
- Subscription system to upgrade for premium access

---

## 🛠 Tech Stack Overview

- **Frontend**: HTML, CSS, JavaScript  
- **Backend**: Flask (Python)  
- **Database**: SQLite using SQLAlchemy ORM  
- **AI Engine**: Gemini API (Google Generative Language)  
- **Data Storage**: JSON for activity logs

---

## 🗃 Database Schema Summary

### `User` Table
- `id`: Primary key  
- `username`: Unique login ID  
- `password_hash`: Encrypted password  
- `is_subscribed`: Boolean flag  

### `VisitedURL` Table
- `id`: Primary key  
- `user_id`: Linked to user  
- `url`: Submitted URL  
- `timestamp`: When submitted  

### `Subscription` Table
- `id`: Primary key  
- `user_id`: Linked to user  
- `plan_name`, `start_date`, `end_date`, `is_active`: Subscription metadata  

---

## 🧭 User Flow

1. **User Registration/Login**
2. **URL Submission & AI Analysis**
3. **Chatbot Responds with Page-Based Answers**
4. **User History Recorded**
5. **Activity Dashboard Displays History**
6. **Date Filtering Available**
7. **Upgrade Plan for Unlimited Use**

---

## 🏃‍♂️ How to Run Locally

```bash
git clone https://github.com/yourusername/smart-web-analyzer.git
cd smart-web-analyzer
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
python application.py
