import re
import pronouncing
from nltk.tokenize import word_tokenize
import nltk
from pyphonetics import Metaphone
from nltk import pos_tag

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

metaphone = Metaphone()

# Bảng chuyển đổi từ ARPAbet sang X-SAMPA
arpa_to_xsampa = {
    'AA': 'A', 'AE': '{', 'AH': 'V', 'AO': 'O', 'AW': 'aU', 'AY': 'aI',
    'B': 'b', 'CH': 'tS', 'D': 'd', 'DH': 'D', 'EH': 'E', 'ER': '3`',
    'EY': 'eI', 'F': 'f', 'G': 'g', 'HH': 'h', 'IH': 'I', 'IY': 'i',
    'JH': 'dZ', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'N',
    'OW': 'oU', 'OY': 'OI', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'S',
    'T': 't', 'TH': 'T', 'UH': 'U', 'UW': 'u', 'V': 'v', 'W': 'w',
    'Y': 'j', 'Z': 'z', 'ZH': 'Z'
}

def arpa_to_xsampa(arpa):
    xsampa = []
    for phone in arpa.split():
        # Xử lý trường hợp có số ở cuối (biểu thị trọng âm)
        base_phone = ''.join([c for c in phone if not c.isdigit()])
        if base_phone in arpa_to_xsampa:
            xsampa.append(arpa_to_xsampa[base_phone])
        else:
            xsampa.append(base_phone)
    return ' '.join(xsampa)

def ensure_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('taggers/averaged_perceptron_tagger')
    except LookupError:
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')

def simple_tokenize(text):
    # Tách từ đơn giản bằng cách sử dụng regular expression
    return re.findall(r'\b\w+\b', text.lower())

def get_phonetic_transcriptions(text):
    words = text.split()
    phonetic_transcriptions = []
    for word in words:
        pronunciations = pronouncing.phones_for_word(word.lower())
        if pronunciations:
            # Lấy phát âm đầu tiên nếu có nhiều phát âm
            xsampa = arpa_to_xsampa(pronunciations[0])
            phonetic_transcriptions.append(xsampa)
        else:
            phonetic_transcriptions.append('')
    return phonetic_transcriptions
