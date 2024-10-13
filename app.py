from flask import Flask, jsonify, render_template, request, send_from_directory, redirect, url_for, Response
from flask_cors import CORS
from modules.translation import translate_text
from modules.news_fetcher import fetch_news
from modules.phonetic import get_phonetic_transcriptions
import json
from googletrans import Translator
from modules.news_fetcher import get_top_headlines
import logging
from logging.handlers import RotatingFileHandler
import sqlite3
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Cấu hình logging cho server
server_handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
server_handler.setLevel(logging.INFO)
app.logger.addHandler(server_handler)
app.logger.setLevel(logging.INFO)

# Cấu hình logging cho JavaScript
js_logger = logging.getLogger('javascript')
js_handler = RotatingFileHandler('js.log', maxBytes=10000, backupCount=1)
js_handler.setLevel(logging.INFO)
js_logger.addHandler(js_handler)
js_logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/api/translate', methods=['POST'])
def translate():
    app.logger.info("Received translation request")
    data = request.json
    text = data['text']
    source_language = data.get('source_language', 'vi')
    target_language = data.get('target_language', 'en')
    
    app.logger.info(f"Translating from {source_language} to {target_language}")
    translated_text = translate_text(text, source_language, target_language)
    
    app.logger.info("Translation completed")
    return jsonify({
        'translated_text': translated_text,
        'source_language': source_language,
        'target_language': target_language
    })

@app.route('/api/news')
def get_news():
    app.logger.info("Fetching news from database")
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY position")
    news = c.fetchall()
    conn.close()
    
    news_list = [{'id': row[0], 'type': row[1], 'content': row[2], 'position': row[3], 'title': row[4]} for row in news]

    app.logger.info(f"Retrieved {len(news_list)} news items")
    response = jsonify(news_list)
    response.headers['Content-Type'] = 'application/json; charset=utf-8'
    return response

@app.route('/api/log', methods=['POST'])
def log_js():
    log_data = request.json
    js_logger.info(f"JavaScript log: {log_data['message']}")
    return jsonify({"status": "Log received"}), 200

@app.route('/')
def index():
    app.logger.info("Rendering index page")
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    app.logger.info(f"Serving static file: {path}")
    return send_from_directory('static', path)

# Hàm để lấy và lưu trữ dữ liệu
def fetch_and_store_news():
    app.logger.info("Starting fetch_and_store_news")
    news_data = fetch_news()
    app.logger.info(f"Fetched news data: {news_data}")
    structured_content = news_data.get('structured_content', [])

    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    app.logger.info("Creating news table if not exists")
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT,
                  content TEXT,
                  position INTEGER,
                  title TEXT)''')

    app.logger.info("Deleting existing news data")
    c.execute("DELETE FROM news")

    title = next((item['content'] for item in structured_content if item['type'] == 'title'), "No title")
    app.logger.info(f"Title found: {title}")
    for item in structured_content:
        app.logger.info(f"Inserting item: {item}")
        c.execute("INSERT INTO news (type, content, position, title) VALUES (?, ?, ?, ?)",
                  (item['type'], item['content'], item['position'], title))

    conn.commit()
    conn.close()
    app.logger.info("Finished fetch_and_store_news")

@app.route('/log')
def get_log():
    app.logger.info("Retrieving log content")
    with open('app.log', 'r', encoding='utf-8') as f:
        log_content = f.read()
    return Response(log_content, mimetype='text/plain; charset=utf-8')

@app.route('/api/get_translation', methods=['POST'])
def get_translation():
    app.logger.info("Received request for stored translation")
    data = request.json
    url = data['url']

    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT translated_content FROM news WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()

    if result:
        app.logger.info("Translation found in database")
        return jsonify({'translated_content': result[0]})
    else:
        app.logger.warning("Translation not found in database")
        return jsonify({'error': 'Translation not found'}), 404

if __name__ == '__main__':
    app.logger.info("Starting the application")
    fetch_and_store_news()  # Lấy và lưu dữ liệu khi khởi động server
    app.run(debug=True)
