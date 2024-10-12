from modules.translation import translate_text
import sqlite3
import requests
from bs4 import BeautifulSoup

def fetch_news_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Lấy tiêu đề h1
    title = soup.find('h1').text.strip() if soup.find('h1') else "Không tìm thấy tiêu đề"
    
    # Lấy nội dung (giả sử nội dung nằm trong thẻ có class là 'article-content')
    content = soup.find(class_='article-content').text.strip() if soup.find(class_='article-content') else "Không tìm thấy nội dung"
    
    return title, content

def fetch_and_translate_news(url):
    # Fetch news content
    title, content = fetch_news_content(url)
    
    # Translate title and content
    translated_title = translate_text(title, 'vi', 'en')
    translated_content = translate_text(content, 'vi', 'en')
    
    # Save to database (you might need to modify your database schema)
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO news (url, original_title, original_content, translated_title, translated_content)
    VALUES (?, ?, ?, ?, ?)
    ''', (url, title, content, translated_title, translated_content))
    conn.commit()
    conn.close()

    return title, content, translated_title, translated_content
