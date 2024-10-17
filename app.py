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

def create_fairy_tales_table():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fairy_tales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT,
        english_title TEXT,
        english_content TEXT,
        english_author TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Kiểm tra và thêm các cột còn thiếu
    columns_to_add = [
        ('author', 'TEXT'),
        ('english_title', 'TEXT'),
        ('english_content', 'TEXT'),
        ('english_author', 'TEXT'),
        ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    ]
    
    for column, data_type in columns_to_add:
        cursor.execute(f"PRAGMA table_info(fairy_tales)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE fairy_tales ADD COLUMN {column} {data_type}")
    
    conn.commit()
    conn.close()

# Gọi hàm này khi khởi động ứng dụng
create_fairy_tales_table()

@app.route('/api/fairy_tale', methods=['POST'])
def add_fairy_tale():
    data = request.json
    title = data['title']
    content = data['content']
    author = data.get('author', 'Unknown')

    # Dịch tiêu đề và nội dung sang tiếng Anh
    english_title = translate_text(title, 'vi', 'en')
    english_content = translate_text(content, 'vi', 'en')
    english_author = translate_text(author, 'vi', 'en')
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO fairy_tales (title, content, author, english_title, english_content)
    VALUES (?, ?, ?, ?, ?)
    ''', (title, content, author, english_title, english_content))
    conn.commit()
    conn.close()

    return jsonify({"message": "Fairy tale added successfully"}), 201

@app.route('/api/fairy_tales', methods=['GET'])
def get_fairy_tales():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, author FROM fairy_tales')
    fairy_tales = cursor.fetchall()
    conn.close()

    return jsonify([{"id": tale[0], "title": tale[1], "author": tale[2]} for tale in fairy_tales])

@app.route('/api/fairy_tale/<int:tale_id>', methods=['GET'])
def get_fairy_tale(tale_id):
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fairy_tales WHERE id = ?', (tale_id,))
        tale = cursor.fetchone()
        

        if tale:
            # Lấy tên các cột trong bảng
            cursor.execute('PRAGMA table_info(fairy_tales)')
            columns = [column[1] for column in cursor.fetchall()]
            
            # Tạo dictionary với các cột hiện có
            tale_dict = {columns[i]: tale[i] for i in range(len(tale))}
            
            # Thêm các trường còn thiếu với giá trị mặc định
            expected_fields = ["id", "title", "content", "author", "english_title", "english_content", "created_at"]
            for field in expected_fields:
                if field not in tale_dict:
                    tale_dict[field] = None
            
            return jsonify(tale_dict)
        else:
            logging.warning(f"Fairy tale with id {tale_id} not found")
            return jsonify({"error": "Fairy tale not found"}), 404
    except Exception as e:
        logging.error(f"Error fetching fairy tale: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        conn.close()

@app.route('/api/save_word', methods=['POST'])
def save_word():
    data = request.json
    word = data.get('word')
    context = data.get('context', '')
    
    if not word:
        return jsonify({"error": "No word provided"}), 400
    
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO note_word (word, context) VALUES (?, ?)', (word, context))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Word saved successfully"}), 200

@app.route('/api/random_word', methods=['GET'])
def get_random_word():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('SELECT word, context FROM note_word ORDER BY RANDOM() LIMIT 1')
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return jsonify({"word": result[0], "context": result[1]}), 200
    else:
        return jsonify({"error": "No words found"}), 404
    
def translate_fairy_tales():
    app.logger.info("Starting translation of fairy tales")
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()

    # Lấy tất cả các truyện chưa được dịch
    cursor.execute('SELECT id, title, content, author FROM fairy_tales WHERE english_title IS NULL OR english_content IS NULL OR english_title = "" OR english_content = "" OR english_author IS NULL OR english_author =""')
    untranslated_tales = cursor.fetchall()

    for tale_id,title, content, author in untranslated_tales:
        app.logger.info(f"Translating fairy tale with ID: {tale_id}")
        try:
            # Dịch nội dung
            english_title = translate_text(title, 'vi', 'en')
            english_content = translate_text(content, 'vi', 'en')
            english_author = translate_text(author, 'vi', 'en')

            # Cập nhật cơ sở dữ liệu với bản dịch
            
            cursor.execute('UPDATE fairy_tales SET english_title = ?, english_author = ?, english_content = ? WHERE id = ?', (english_title, english_author, english_content, tale_id))
            conn.commit()
            app.logger.info(f"Successfully translated and updated fairy tale with ID: {tale_id}")
        except Exception as e:
            app.logger.error(f"Error translating fairy tale with ID {tale_id}: {str(e)}")
            conn.rollback()

    conn.close()
    app.logger.info("Finished translating fairy tales")

# Gọi hàm này khi khởi động ứng dụng hoặc theo lịch trình
translate_fairy_tales()

def create_note_word_table():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS note_word
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       word TEXT NOT NULL,
                       context TEXT,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Gọi hàm này khi khởi động ứng dụng
create_note_word_table()

if __name__ == '__main__':
    app.logger.info("Starting the application")
    fetch_and_store_news()  # Lấy và lưu dữ liệu khi khởi động server
    translate_fairy_tales()  # Dịch các truyện cổ tích chưa được dịch
    app.run(debug=True)
