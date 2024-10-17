console.log("Script is running");

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

let translatedParagraphs = {};
let phoneticTranscriptions = {};

// Hàm để lưu log
async function saveLog(message) {
    console.log(message);
    try {
        await fetch('/api/log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });
    } catch (error) {
        console.error('Error saving log:', error);
    }
}

async function processData(data) {
    await saveLog("Creating article elements with data: " + JSON.stringify(data));

    if (data.structured_content && Array.isArray(data.structured_content)) {
        data.structured_content.forEach((item, index) => {
            if (item.type === 'image') {
                const img = document.createElement('img');
                img.src = item.content;
                img.alt = "Article image";
                img.className = "article-image";
                articleContent.appendChild(img);
            } else if (item.type === 'text') {
                const paragraphElement = document.createElement('div');
                paragraphElement.className = 'paragraph';
                paragraphElement.innerHTML = `
                    <p id="text-${index}">${item.content}</p>
                    <select id="language-select-${index}" class="language-select">
                        <option value="vi">Vietnamese</option>
                        <option value="en">English</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                        <option value="es">Spanish</option>
                    </select>
                    <button onclick="translateParagraph(${index})" data-paragraph-id="${index}" class="translate-button">Translate</button>
                    <button id="phonetic-button-${index}" onclick="togglePhonetic(${index})" class="phonetic-button" style="display: none;">Toggle Phonetic</button>
                    <div id="translation-status-${index}" class="translation-status"></div>
                    <div id="translation-${index}" class="translation"></div>
                `;
                articleContent.appendChild(paragraphElement);
            }
        });
    } else {
        articleContent.innerHTML = '<p>No content available.</p>';
    }
}




async function translateParagraph(paragraphId) {
    const textElement = document.getElementById(`text-${paragraphId}`);
    const text = textElement.textContent;
    const targetLanguage = document.getElementById(`language-select-${paragraphId}`).value;
    const statusElement = document.getElementById(`translation-status-${paragraphId}`);
    const translationElement = document.getElementById(`translation-${paragraphId}`);
    const translateButton = document.querySelector(`[data-paragraph-id="${paragraphId}"]`);
    const phoneticButton = document.getElementById(`phonetic-button-${paragraphId}`);

    if (translatedParagraphs[paragraphId]) {
        translationElement.style.display = 'none';
        statusElement.textContent = '';
        translateButton.textContent = 'Translate';
        phoneticButton.style.display = 'none';
        translatedParagraphs[paragraphId] = false;
        return;
    }

    statusElement.textContent = 'Translating...';
    translateButton.disabled = true;

    try {
        const response = await fetch('/api/translate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text, target_language: targetLanguage }),
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(`Server error: ${data.error || response.statusText}`);
        }
        
        if (!data || !data.translated_text) {
            throw new Error("Invalid response from server");
        }
        
        let translationHtml = '<div class="translation-container">';
        const words = data.translated_text.split(' ');
        words.forEach((word, index) => {
            translationHtml += `<span class="word">${word}</span> `;
        });
        translationHtml += '</div>';
        
        translationElement.innerHTML = translationHtml;
        translationElement.style.display = 'block';
        statusElement.textContent = 'Translation complete';
        translateButton.textContent = 'Hide Translation';
        phoneticButton.style.display = 'inline-block';
        translatedParagraphs[paragraphId] = true;
        phoneticTranscriptions[paragraphId] = data.phonetic_transcriptions;
    } catch (error) {
        console.error('Translation error:', error);
        statusElement.textContent = `Translation failed: ${error.message}`;
        translationElement.style.display = 'none';
    } finally {
        translateButton.disabled = false;
    }
}

function togglePhonetic(paragraphId) {
    const translationElement = document.getElementById(`translation-${paragraphId}`);
    const phoneticContainer = document.getElementById(`phonetic-${paragraphId}`);
    
    if (phoneticContainer) {
        phoneticContainer.remove();
    } else {
        const phoneticHtml = '<div id="phonetic-' + paragraphId + '" class="phonetic-container">';
        const words = translationElement.querySelector('.translation-container').innerText.split(' ');
        words.forEach((word, index) => {
            const phonetic = phoneticTranscriptions[paragraphId][index] || '';
            phoneticHtml += `<span class="phonetic">${phonetic}</span> `;
        });
        phoneticHtml += '</div>';
        translationElement.insertAdjacentHTML('beforeend', phoneticHtml);
    }
}

function attachTranslateEvents() {
    const translateButtons = document.querySelectorAll('.translate-button');
    translateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const paragraphId = this.dataset.paragraphId;
            translateParagraph(paragraphId);
        });
    });
}

// Thêm hàm để tải nội dung bài viết
function loadArticleContent() {
    fetch('/api/news')
        .then(response => response.json())
        .then(data => {
            const articleContent = document.getElementById('article-content');
            let contentHtml = `
                <h1>${data.title}</h1>
                <div class="summary">${data.summary}</div>
            `;
            
            data.content.forEach((part, index) => {
                if (part.type === 'text') {
                    contentHtml += `
                        <p>
                            <span id="text-${index}">${part.content}</span>
                            <button class="translate-button" data-paragraph-id="${index}">Translate</button>
                            <select id="language-select-${index}" class="language-select">
                                <option value="en">English</option>
                                <option value="vi">Vietnamese</option>
                                <option value="fr">French</option>
                                <option value="de">German</option>
                                <option value="ja">Japanese</option>
                            </select>
                            <div id="translation-status-${index}" class="translation-status"></div>
                            <div id="translation-${index}" class="translation"></div>
                        </p>
                    `;
                } else if (part.type === 'image') {
                    contentHtml += `
                        <figure>
                            <img src="${part.src}" alt="Article image">
                            ${part.caption ? `<figcaption>${part.caption}</figcaption>` : ''}
                        </figure>
                    `;
                }
            });
            
            articleContent.innerHTML = contentHtml;
            attachTranslateEvents();
        })
        .catch(error => {
            console.error('Error:', error);
            const articleContent = document.getElementById('article-content');
            articleContent.innerHTML = '<p>Error loading news.</p>';
        });
}

// Gọi hàm loadArticleContent khi trang được tải
document.addEventListener('DOMContentLoaded', loadArticleContent);

function createArticleElements(data) {
    const articleContainer = document.getElementById('article-container');
    articleContainer.innerHTML = ''; // Clear existing content

    // Add title
    const titleElement = document.createElement('h1');
    titleElement.className = 'article-title';
    titleElement.textContent = data[0].title;
    articleContainer.appendChild(titleElement);

    data.forEach((item, index) => {
        if (item.type === 'title') return; // Skip title, as we've already added it

        const element = document.createElement('div');
        element.className = 'article-item';

        switch(item.type) {
            case 'image':
                element.innerHTML = `<img src="${item.content}" alt="Article image" class="article-image" data-id="${item.id}" data-position="${item.position}">`;
                break;
            case 'text':
                element.innerHTML = `
                    <p class="article-text" data-id="${item.id}" data-position="${item.position}">${item.content}</p>
                    <button onclick="translateParagraph(${index})" class="translate-button">Translate to English</button>
                    <div id="translation-${index}" class="translation"></div>
                `;
                break;
            default:
                console.log(`Unknown type: ${item.type}`);
        }

        articleContainer.appendChild(element);
    });
}

function fetchNews() {
    console.log("Fetching news...");
    fetch('/api/news')
        .then(response => {
            console.log("Response received:", response);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Parsed data:", data);
            createArticleElements(data);
        })
        .catch(error => {
            console.error('Error fetching news:', error);
            const errorContainer = document.getElementById('error-container');
            errorContainer.textContent = `Error fetching news: ${error.message}`;
        });
}

// Call fetchNews when the page loads
document.addEventListener('DOMContentLoaded', fetchNews);

function translateToEnglish(text, apiUrl = '/api/translate') {
    return fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text, target_language: 'en' }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.translated_text) {
            return data.translated_text;
        } else {
            throw new Error('Translation failed');
        }
    });
}

function translateParagraph(index) {
    const paragraph = document.querySelector(`.article-text[data-position="${index}"]`);
    const translationDiv = document.getElementById(`translation-${index}`);
    const translateButton = translationDiv.previousElementSibling;

    if (translationDiv.style.display === 'block') {
        translationDiv.style.display = 'none';
        translateButton.textContent = 'Translate to English';
    } else {
        translateButton.disabled = true;
        translateButton.textContent = 'Translating...';
        translateToEnglish(paragraph.textContent)
            .then(translation => {
                translationDiv.textContent = translation;
                translationDiv.style.display = 'block';
                translateButton.textContent = 'Hide Translation';
            })
            .catch(error => {
                console.error('Translation error:', error);
                translationDiv.textContent = 'Translation failed. Please try again.';
                translationDiv.style.display = 'block';
            })
            .finally(() => {
                translateButton.disabled = false;
            });
    }
}

function showTranslation(url) {
    fetch('/api/get_translation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.translated_content) {
            document.getElementById('content').innerHTML = data.translated_content;
        } else {
            console.error('Translation not found');
        }
    })
    .catch(error => console.error('Error:', error));
    
}

function fetchFairyTales() {
    console.log('Fetching fairy tales');
    fetch('/api/fairy_tales')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Fairy tales data received:', data);
            const fairyTalesList = document.getElementById('fairy-tales-list');
            fairyTalesList.innerHTML = '';
            if (data.length === 0) {
                fairyTalesList.innerHTML = '<li>Không có truyện cổ tích nào.</li>';
            } else {
                data.forEach(tale => {
                    const li = document.createElement('li');
                    const a = document.createElement('a');
                    a.href = '#';
                    a.textContent = tale.title;
                    a.addEventListener('click', function(e) {
                        e.preventDefault();
                        showFairyTale(tale.id);
                    });
                    li.appendChild(a);
                    li.appendChild(document.createTextNode(` by ${tale.author}`));
                    fairyTalesList.appendChild(li);
                });
            }
        })
        .catch(error => {
            console.error('Error fetching fairy tales:', error);
            const fairyTalesList = document.getElementById('fairy-tales-list');
            fairyTalesList.innerHTML = '<li>Lỗi khi tải truyện cổ tích. Vui lòng thử lại sau.</li>';
        });
}

function showFairyTale(taleId) {
    console.log('Showing fairy tale with ID:', taleId);
    fetch(`/api/fairy_tale/${taleId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fairy tale data received:', data);
            document.getElementById('fairy-tales-list').style.display = 'none';
            const contentDiv = document.getElementById('fairy-tale-content');
            contentDiv.style.display = 'block';
            
            // Cập nhật tiêu đề
            document.getElementById('fairy-tale-title').textContent = data.title || 'Không có tiêu đề';
            document.getElementById('fairy-tale-english-title').textContent = data.english_title || 'No title';
            
            // Cập nhật tác giả
            document.getElementById('fairy-tale-author').textContent = `Tác giả: ${data.author || 'Không rõ'}`;
            document.getElementById('fairy-tale-english-author').textContent = `Author: ${data.english_author || 'Unknown'}`;
            
            // Xử lý văn bản có định dạng
            document.getElementById('fairy-tale-content-vi').innerHTML = formatText(data.content || 'Không có nội dung.');
            document.getElementById('fairy-tale-content-en').innerHTML = formatText(data.english_content || 'No content available.');
        })
        .catch(error => {
            console.error('Error fetching fairy tale:', error);
            const errorContainer = document.getElementById('error-container');
            errorContainer.textContent = `Error fetching fairy tale: ${error.message}`;
        });
}

function formatText(text) {
    // Thay thế xuống dòng bằng thẻ <p>
    return text.split('\n').map(paragraph => `<p>${paragraph}</p>`).join('');
}

function showFairyTalesList() {
    document.getElementById('fairy-tale-content').style.display = 'none';
    document.getElementById('fairy-tales-list').style.display = 'block';
}

// Định nghĩa các biến toàn cục
let articleContainer, fairyTalesContainer, fairyTalesLink, newsLink;

// Hàm khởi tạo
function initializeApp() {
    articleContainer = document.getElementById('article-container');
    fairyTalesContainer = document.getElementById('fairy-tales-container');
    fairyTalesLink = document.getElementById('fairy-tales-link');
    newsLink = document.getElementById('news-link');
    const hamburger = document.getElementById('hamburger');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.overlay');

    // Kiểm tra xem các elements có tồn tại không
    if (!articleContainer || !fairyTalesContainer || !fairyTalesLink || !newsLink || !hamburger || !sidebar || !overlay) {
        console.error('One or more required elements are missing');
        return;
    }

    // Thêm event listeners
    fairyTalesLink.addEventListener('click', function(e) {
        e.preventDefault();
        showFairyTales();
    });

    newsLink.addEventListener('click', function(e) {
        e.preventDefault();
        showNews();
    });

    hamburger.addEventListener('click', function() {
        sidebar.style.left = sidebar.style.left === '0px' ? '-250px' : '0px';
        overlay.style.display = overlay.style.display === 'block' ? 'none' : 'block';
    });

    overlay.addEventListener('click', function() {
        sidebar.style.left = '-250px';
        overlay.style.display = 'none';
    });

    // Khởi đầu với tin tức
    showNews();
}

// Hàm hiển thị phần truyện cổ tích
function showFairyTales() {
    console.log('Showing fairy tales');
    articleContainer.style.display = 'none';
    fairyTalesContainer.style.display = 'block';
    document.getElementById('fairy-tale-content').style.display = 'none';
    document.getElementById('fairy-tales-list').style.display = 'block';
    fetchFairyTales();
}

// Hàm hiển thị phần tin tức
function showNews() {
    console.log('Showing news');
    fairyTalesContainer.style.display = 'none';
    articleContainer.style.display = 'block';
    fetchNews();
}

// Gọi hàm khởi tạo khi trang đã tải xong
document.addEventListener('DOMContentLoaded', initializeApp);

document.getElementById('fairy-tale-content-en').addEventListener('mouseup', function() {
    const selectedText = window.getSelection().toString().trim();
    if (selectedText) {
        const context = this.innerText;
        saveWord(selectedText, context);
    }
});

function saveWord(word, context) {
    fetch('/api/save_word', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ word: word, context: context }),
    })
    .then(response => response.json())
    .then(data => console.log('Word saved:', data))
    .catch(error => console.error('Error saving word:', error));
}

let currentWord = '';
let currentContext = '';

function showFlashCard() {
    document.getElementById('flash-card').style.display = 'block';
    getRandomWord();
}

function getRandomWord() {
    fetch('/api/random_word')
        .then(response => response.json())
        .then(data => {
            currentWord = data.word;
            currentContext = data.context;
            document.getElementById('word-display').textContent = currentWord;
            document.getElementById('context-display').style.display = 'none';
            document.getElementById('context-display').textContent = currentContext;
        })
        .catch(error => console.error('Error fetching random word:', error));
}

document.getElementById('show-context').addEventListener('click', function() {
    document.getElementById('context-display').style.display = 'block';
});

document.getElementById('next-word').addEventListener('click', getRandomWord);

// Thêm nút để hiển thị flash card
const flashCardButton = document.createElement('button');
flashCardButton.textContent = 'Show Flash Cards';
flashCardButton.addEventListener('click', showFlashCard);
document.querySelector('.container').appendChild(flashCardButton);
