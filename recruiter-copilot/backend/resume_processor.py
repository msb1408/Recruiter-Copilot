import json
import re
import fitz
import docx2pdf
from pathlib import Path
import os
import tempfile
from typing import Optional

class ResumeProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)

    def process_resume(self, file_content: bytes, filename: str) -> Optional[str]:
        """Обрабатывает загруженное резюме и возвращает извлеченный текст."""
        try:
            # Сохраняем файл во временную директорию
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Извлекаем текст из файла
            text = self._extract_text(temp_file_path)
            
            # Удаляем временный файл
            os.unlink(temp_file_path)
            
            return text
        except Exception as e:
            print(f"Ошибка при обработке резюме: {e}")
            return None

    def _extract_text(self, filepath: str) -> Optional[str]:
        """Извлекает текст из файла резюме."""
        text = ""
        filepath = Path(filepath)

        if filepath.suffix.lower() == '.docx':
            try:
                # Конвертируем DOCX в PDF
                pdf_path = filepath.with_suffix('.pdf')
                docx2pdf.convert(str(filepath), str(pdf_path))
                
                # Читаем PDF
                doc = fitz.open(str(pdf_path))
                for page in doc:
                    text += page.get_text()
                doc.close()
                
                # Удаляем временный PDF файл
                os.unlink(pdf_path)
            except Exception as e:
                print(f"Ошибка при чтении DOCX файла {filepath}: {e}")
                return None

        elif filepath.suffix.lower() == '.pdf':
            try:
                doc = fitz.open(str(filepath))
                for page in doc:
                    text += page.get_text()
                doc.close()
            except Exception as e:
                print(f"Ошибка при чтении PDF файла {filepath}: {e}")
                return None
        
        else:
            print(f"Формат файла {filepath} не поддерживается. Поддерживаемые форматы: .pdf, .docx")
            return None

        return self._clean_text(text)

    def _clean_text(self, text: str) -> str:
        """Очищает извлеченный текст."""
        # Удаляем лишние пробелы и переносы строк
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Удаляем специальные символы, оставляя только буквы, цифры и основные знаки препинания
        text = re.sub(r'[^\w\s.,!?-]', ' ', text)
        
        # Удаляем множественные пробелы
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip() 