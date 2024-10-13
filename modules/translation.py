import re
import sqlite3
from googletrans import Translator
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

translator = Translator()
DB_PATH = 'news.db'

def get_db_connection():
    logger.info("Establishing database connection")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    logger.info("Creating translations table if not exists")
    # Tạo bảng nếu chưa tồn tại
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS translations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_text TEXT NOT NULL,
        translated_text TEXT NOT NULL,
        source_language TEXT NOT NULL,
        target_language TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    logger.info("Database connection established and table created/verified")
    return conn

def translate_text(text, source_language='vi', target_language='en'):
    logger.info(f"Starting translation from {source_language} to {target_language}")
    conn = get_db_connection()
    cursor = conn.cursor()

    logger.debug(f"Translating: '{text[:50]}...' from {source_language} to {target_language}")

    # Kiểm tra xem bản dịch đã tồn tại chưa
    logger.info("Checking for existing translation in database")
    cursor.execute('''
        SELECT translated_text 
        FROM translations 
        WHERE original_text = ? AND source_language = ? AND target_language = ?
    ''', (text, source_language, target_language))
    
    result = cursor.fetchone()
    
    if result:
        logger.info("Found existing translation in database")
        translated_text = result['translated_text']
    else:
        logger.info("No existing translation found. Proceeding with new translation")
        try:
            logger.debug("Translating with Google Translate")
            translation = translator.translate(text, src=source_language, dest=target_language)
            translated_text = translation.text
            
            logger.debug("Post-processing translation")
            translated_text = post_process_translation(translated_text)
            
            logger.debug(f"Translated text: '{translated_text[:50]}...'")
            
            # Lưu bản dịch vào DB
            logger.info("Saving translation to database")
            cursor.execute('''
                INSERT INTO translations (original_text, translated_text, source_language, target_language)
                VALUES (?, ?, ?, ?)
            ''', (text, translated_text, source_language, target_language))
            logger.debug(f"Executing INSERT query with values: {text[:50]}..., {translated_text[:50]}..., {source_language}, {target_language}")
            
            conn.commit()
            logger.info(f"Translation saved to database. Row count: {cursor.rowcount}")
        except sqlite3.Error as e:
            logger.error(f"Error saving to database: {str(e)}")
        except Exception as e:
            logger.error(f"Translation error: {str(e)}")

    conn.close()
    logger.info("Database connection closed")
    
    return translated_text

def post_process_translation(text):
    logger.info("Starting post-processing of translated text")
    # Loại bỏ dấu chấm không cần thiết
    logger.debug("Removing unnecessary periods")
    text = re.sub(r'\.\s+([a-z])', r' \1', text)
    
    # Sửa lỗi "relevant senior level"
    #logger.debug("Fixing 'relevant senior level' phrase")
    #text = text.replace("conferences. relevant senior level", "relevant high-level conferences")
    
    # Các quy tắc xử lý khác có thể được thêm vào đây
    
    logger.info("Post-processing completed")
    return text
