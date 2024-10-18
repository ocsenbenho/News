Import và Cấu hình:
Import các module cần thiết từ Flask và các module tùy chỉnh.
Cấu hình logging cho server và JavaScript.
Các route API:
/api/translate: Dùng để dịch văn bản.
/api/news: Lấy tin tức từ cơ sở dữ liệu.
/api/log: Ghi log từ JavaScript.
/api/get_translation: Lấy bản dịch đã lưu.
/api/fairy_tale: Thêm truyện cổ tích mới.
/api/fairy_tales: Lấy danh sách truyện cổ tích.
/api/fairy_tale/<int:tale_id>: Lấy chi tiết một truyện cổ tích.
/api/save_word: Lưu từ vựng.
/api/random_word: Lấy một từ vựng ngẫu nhiên.
Các hàm hỗ trợ:
fetch_and_store_news(): Lấy và lưu tin tức vào cơ sở dữ liệu.
create_fairy_tales_table(): Tạo bảng truyện cổ tích trong cơ sở dữ liệu.
translate_fairy_tales(): Dịch các truyện cổ tích chưa được dịch.
create_note_word_table(): Tạo bảng lưu từ vựng.
Xử lý cơ sở dữ liệu:
Sử dụng SQLite để lưu trữ tin tức, truyện cổ tích và từ vựng.
Xử lý đa ngôn ngữ:
Hỗ trợ dịch thuật giữa tiếng Việt và tiếng Anh cho truyện cổ tích.
Logging:
Cấu hình logging chi tiết cho cả server và JavaScript.
Khởi động ứng dụng:
Khi khởi động, ứng dụng sẽ lấy và lưu tin tức, dịch các truyện cổ tích chưa được dịch.
