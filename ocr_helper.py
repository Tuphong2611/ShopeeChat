from PIL import ImageGrab
import pytesseract

# Đảm bảo bạn đã cài đúng đường dẫn tới tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def read_text_from_screen_area(bbox=(100, 100, 600, 400)):
    """
    Chụp màn hình vùng bbox và đọc text bằng OCR
    bbox: (left, top, right, bottom)
    """
    image = ImageGrab.grab(bbox)
    text = pytesseract.image_to_string(image, lang='vie')
    return text.strip()

if __name__ == "__main__":
    print("📷 Đang OCR vùng màn hình...")
    print(read_text_from_screen_area())
