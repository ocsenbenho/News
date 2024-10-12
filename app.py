from flask import Flask, jsonify, render_template, request, send_from_directory, redirect, url_for
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

@app.route('/api/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        app.logger.info(f"Received translation request: {data}")
        
        text = data.get('text')
        target_language = data.get('target_language', 'en')
        
        if not text:
            raise ValueError("No text provided for translation")
        
        app.logger.info(f"Translating text: '{text}' to {target_language}")
        translated_text = translate_text(text, target_language)
        
        app.logger.info(f"Translated text: '{translated_text}'")
        
        if not translated_text:
            raise ValueError("Translation failed")
        
        response_data = {
            'translated_text': translated_text,
            'show_ipa': True,  # Đảm bảo điều này được đặt thành True
            'show_articles': False,
            'translit_original': '',
            'translit_translation': ''
        }
        
        if target_language == 'en':
            try:
                phonetic_transcriptions = get_phonetic_transcriptions(translated_text)
                app.logger.info(f"Phonetic transcriptions: {phonetic_transcriptions}")  # Log để debug
                response_data['phonetic_transcriptions'] = phonetic_transcriptions
            except Exception as e:
                app.logger.error(f"Error generating phonetic transcriptions: {str(e)}")
                response_data['phonetic_transcriptions'] = []
        
        app.logger.info(f"Sending response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        app.logger.error(f"Error in translate route: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/news')
def get_news():
    conn = sqlite3.connect('news.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY position")
    news = c.fetchall()
    conn.close()
    
    news_list = [{'id': row[0], 'type': row[1], 'content': row[2], 'position': row[3]} for row in news]

    respone = jsonify(news_list)
    respone.headers['Content-Type'] = 'application/json; charset=utf-8'
    return respone

@app.route('/api/log', methods=['POST'])
def log_js():
    log_data = request.json
    js_logger.info(log_data['message'])
    return jsonify({"status": "Log received"}), 200

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# Hàm để lấy và lưu trữ dữ liệu
def fetch_and_store_news():
    news_data = fetch_news()
    structured_content = news_data.get('structured_content', [])

    conn = sqlite3.connect('news.db')
    c = conn.cursor()

    # Tạo bảng nếu nó chưa tồn tại
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  type TEXT,
                  content TEXT,
                  position INTEGER)''')

    # Xóa dữ liệu cũ
    c.execute("DELETE FROM news")

    # Lưu dữ liệu mới
    for item in structured_content:
        c.execute("INSERT INTO news (type, content, position) VALUES (?, ?, ?)",
                  (item['type'], item['content'], item['position']))

    conn.commit()
    conn.close()

if __name__ == '__main__':
    fetch_and_store_news()  # Lấy và lưu dữ liệu khi khởi động server
    app.run(debug=True)
