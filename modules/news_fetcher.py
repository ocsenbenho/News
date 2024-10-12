import requests
from bs4 import BeautifulSoup
import json
import logging

# Cấu hình logging
logging.basicConfig(filename='app.log', level=logging.INFO, 
                    format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def fetch_news():
    url = "https://thanhnien.vn/thu-tuong-quan-ngai-cac-chi-trich-thieu-cong-tam-voi-tong-thu-ky-lien-hiep-quoc-185241011181426497.htm"
    try:
        logging.info("Bắt đầu lấy dữ liệu từ %s", url)
        response = requests.get(url)
        response.raise_for_status()
        
        logging.info("Đã nhận được phản hồi từ server")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Tìm tiêu đề h1
        title = soup.find('h1')
        if title:
            title_text = title.text.strip()
            logging.info("Đã tìm thấy tiêu đề: %s", title_text)
        else:
            title_text = "Không tìm thấy tiêu đề"
            logging.warning("Không tìm thấy tiêu đề trong trang")
        
        content = soup.find('article') or soup.find('div', class_='article-content') or soup.body
        
        if content is None:
            logging.warning("Không tìm thấy nội dung trong trang")
            return {"structured_content": []}
        
        elements = content.find_all(['p', 'img'])
        
        structured_content = [
            {
                'type': 'title',
                'content': title_text,
                'position': 0
            }
        ]
        
        for idx, element in enumerate(elements, start=1):
            if element.name == 'img':
                src = element.get('src')
                if src:
                    if not src.startswith('http'):
                        src = f"{url.rstrip('/')}/{src.lstrip('/')}"
                    structured_content.append({
                        'type': 'image',
                        'content': src,
                        'position': idx
                    })
                    logging.info("Đã tìm thấy hình ảnh: %s", src)
            elif element.name == 'p' and element.text.strip():
                structured_content.append({
                    'type': 'text',
                    'content': element.text.strip(),
                    'position': idx
                })
                logging.info("Đã tìm thấy đoạn văn bản: %s", element.text.strip()[:50] + "...")
        
        logging.info("Đã tìm thấy %d phần tử", len(structured_content))
        return {"structured_content": structured_content}
    
    except requests.RequestException as e:
        logging.error("Lỗi khi lấy dữ liệu: %s", str(e))
        return {"structured_content": []}

def get_top_headlines():
    # Implement your news fetching logic here
    pass
