from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import json
from datetime import datetime

application = Flask(__name__)
application.secret_key = 'secret'

application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(application)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_subscribed = db.Column(db.Boolean, default=False)

with application.app_context():
    db.create_all()

def log_visited_url(url):
    user_id = session.get("user_id")
    if not user_id:
        return

    entry = {
        "user_id": user_id,
        "url": url,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open("visited_urls.json", "r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=2)
    except FileNotFoundError:
        with open("visited_urls.json", "w") as f:
            json.dump([entry], f, indent=2)

@application.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('url_input'))
    return redirect(url_for('login'))

@application.route('/url-input')
def url_input():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('url_input.html')

@application.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error='Username already exists!')
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['username'] = username
            session['user_id'] = user.id
            session['paid'] = user.is_subscribed
            session.pop('message_count', None)
            return redirect(url_for('url_input'))
        return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

@application.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@application.route('/pricing')
def pricing():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_subscribed = session.get('paid', False)
    return render_template('pricing.html', is_subscribed=user_subscribed)

@application.route('/pay', methods=['POST'])
def handle_payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('payment_20'))

@application.route('/payment20', methods=['GET', 'POST'])
def payment_20():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    if request.method == 'POST':
        if user:
            user.is_subscribed = True
            db.session.commit()
            session['paid'] = True
            session.pop('message_count', None)
            return render_template('payment20.html', success=True, is_subscribed=True)
        return render_template('payment20.html', error="User not found.", is_subscribed=user.is_subscribed)

    return render_template('payment20.html', is_subscribed=user.is_subscribed if user else False)

@application.route('/payment-success', methods=['POST'])
def payment_success():
    if 'username' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        if user:
            user.is_subscribed = True
            db.session.commit()
            session['paid'] = True
            session.pop('message_count', None)
            return jsonify({'message': 'Subscription updated successfully!', 'is_subscribed': True})
    return jsonify({'message': 'Unauthorized'}), 401

@application.route('/payment')
def payment():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('payment.html')

@application.route('/features')
def features():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('features.html')

@application.route('/documentation')
def documentation():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('documentation.html')

@application.route('/activity')
def activity():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    selected_date = request.args.get('date')  # Format: YYYY-MM-DD

    try:
        with open("visited_urls.json", "r") as f:
            visited_urls = json.load(f)
    except FileNotFoundError:
        visited_urls = []

    # Filter URLs by user_id
    visited_urls = [entry for entry in visited_urls if entry.get("user_id") == user_id]

    if selected_date:
        visited_urls = [
            entry for entry in visited_urls
            if entry.get("timestamp", "").startswith(selected_date)
        ]

    return render_template("activity.html", visited_urls=visited_urls, selected_date=selected_date)

def extract_webpage_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for tag in soup(['script', 'style', 'noscript']):
            tag.decompose()

        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})

        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        content = ' '.join(chunk for chunk in chunks if chunk)

        if len(content) > 3000:
            content = content[:3000] + "..."

        return {
            'title': title.get_text().strip() if title else "No title",
            'description': meta_desc.get('content', '') if meta_desc else '',
            'content': content,
            'url': url
        }

    except Exception as e:
        print(f"Error extracting webpage content: {e}")
        return {
            'title': 'External webpage',
            'description': 'Could not extract content',
            'content': f'Viewing: {url}, but unable to read content.',
            'url': url
        }

import os

API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL = "gemini-1.5-flash"

def is_question_related(user_query, webpage_content):
    user_keywords = user_query.lower().split()
    content_lower = webpage_content.lower()
    match_count = sum(1 for word in user_keywords if word in content_lower or SequenceMatcher(None, word, content_lower).ratio() > 0.6)
    return match_count > 0

@application.route('/start', methods=['POST'])
def start():
    if 'username' not in session:
        return redirect(url_for('login'))
    url = request.form['url']
    session['url'] = url
    session['webpage_info'] = extract_webpage_content(url)
    log_visited_url(url)
    session.pop('message_count', None)
    return redirect(url_for('chat'))

@application.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))
    user_subscribed = session.get('paid', False)
    message_count = session.get('message_count', 0)
    return render_template('chat.html',
                           url=session.get('url'),
                           webpage_info=session.get('webpage_info'),
                           is_subscribed=user_subscribed,
                           message_count=message_count)

@application.route('/chat', methods=['POST'])
def get_reply():
    if 'username' not in session:
        return jsonify({"reply": "Session expired. Please log in again."}), 401

    user = User.query.filter_by(id=session['user_id']).first()
    if not user or not user.is_subscribed:
        message_count = session.get('message_count', 0)
        if message_count >= 5:
            return jsonify({"limit_reached": True, "message": "Message limit reached. Please subscribe to continue."})
        session['message_count'] = message_count + 1

    message = request.json['message'].strip()
    lower_message = message.lower()
    webpage_info = session.get('webpage_info', {})
    content = webpage_info.get('content', '').lower()

    if lower_message in ['hi', 'hello', 'hey']:
        return jsonify({"reply": "Hello! Tell me your queries related to the website."})

    if not is_question_related(lower_message, content):
        return jsonify({"reply": "This question is not related to the content of the entered website."})

    context_prompt = f"""
You are analyzing a webpage:
Title: {webpage_info.get('title', 'N/A')}
URL: {webpage_info.get('url', 'N/A')}
Description: {webpage_info.get('description', 'N/A')}
Content: {webpage_info.get('content', 'No content extracted.')}
User Question: {message}
"""
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}",
            json={"contents": [{"parts": [{"text": context_prompt}]}]}
        )
        response.raise_for_status()
        data = response.json()
        if 'candidates' in data and data['candidates'] and \
           'content' in data['candidates'][0] and 'parts' in data['candidates'][0]['content'] and \
           data['candidates'][0]['content']['parts']:
            reply = data['candidates'][0]['content']['parts'][0]['text']
        else:
            reply = "Sorry, the AI did not return a valid response."
    except requests.exceptions.RequestException as req_e:
        print(f"Gemini API Network Error: {req_e}")
        reply = "Sorry, I'm having trouble connecting to the AI service."
    except Exception as e:
        print(f"Gemini API Processing Error: {e}")
        reply = "Sorry, an unexpected error occurred while processing your request."

    current_message_count = session.get('message_count', 0)
    is_limit_reached_now = not user.is_subscribed and current_message_count >= 5

    return jsonify({"reply": reply, "limit_reached": is_limit_reached_now})

@application.route('/new-chat')
def new_chat():
    session.pop('url', None)
    session.pop('webpage_info', None)
    session.pop('message_count', None)
    return redirect(url_for('url_input'))

if __name__ == '__main__':
    application.run(debug=True)
