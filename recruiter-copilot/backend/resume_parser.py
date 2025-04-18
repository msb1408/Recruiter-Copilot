import json
from collections import OrderedDict
from openai import OpenAI
import time
from typing import Optional, Dict, Any

class ResumeParser:
    def __init__(self, api_key: str, max_retries: int = 3, timeout: int = 30):
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.system_prompt = """Ты — профессиональный парсер резюме с безупречной точностью. Анализируй предоставленное резюме и ВОЗВРАЩАЙ ТОЛЬКО JSON без пояснений.
Требования к анализу:
1. Извлекай ВСЕ данные, включая неочевидные (например, подразумеваемые навыки в описании опыта)
2. Если информация отсутствует — указывай null
3. Сохраняй оригинальные формулировки из текста

Формат JSON (сохраняй порядок!):
{
  "personal_data": {
    "full_name": "строка",
    "date_of_birth": "DD.MM.YYYY",
    "contacts": {
      "email": "строка",
      "phones": ["массив строк"],
      "telegram": "строка/null",
      "linkedin": "строка/null"
    }
  },
  "education": [
    {
      "university": "строка",
      "degree": "строка",
      "specialization": "строка",
      "start_date": "MM.YYYY",
      "end_date": "MM.YYYY/null(если 'настоящее время')",
      "gpa": "число/null"
    }
  ],
  "skills": {
    "programming_languages": ["массив"],
    "databases": ["массив"],
    "tools": ["массив"],
    "frameworks": ["массив"]
  },
  "experience": [
    {
      "company": "строка",
      "position": "строка",
      "start_date": "MM.YYYY",
      "end_date": "MM.YYYY/null",
      "description": "строка",
      "technologies_used": ["массив"]
    }
  ],
  "additional": {
    "github": "строка/null",
    "portfolio": "строка/null",
    "languages": ["массив"],
    "certificates": ["массив"]
  }
}"""

    def parse(self, raw_text: str) -> Dict[str, Any]:
        """Парсит резюме с повторными попытками при ошибках."""
        for attempt in range(self.max_retries):
            try:
                response = self._call_api(raw_text)
                if not response.choices:
                    return self._error_template("Нет ответа от API")
                return self._process_response(response)
            except Exception as e:
                print(f"Попытка {attempt + 1} из {self.max_retries} не удалась: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Экспоненциальная задержка
                else:
                    return self._error_template(f"Ошибка системы: {str(e)}")

    def _call_api(self, text: str):
        """Вызывает API с настройками таймаута."""
        client = OpenAI(
            api_key=self.api_key,
            base_url="https://hubai.loe.gg/v1",
            timeout=self.timeout
        )
        
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"Резюме для анализа:\n{text}"}
                ],
                stream=False,
                temperature=0.1,
                max_tokens=2000
            )
            return response
        except Exception as e:
            raise Exception(f"Ошибка при вызове API: {str(e)}")

    def _process_response(self, response) -> Dict[str, Any]:
        """Обрабатывает ответ от API."""
        try:
            if not response.choices or not response.choices[0].message:
                return self._error_template("Пустой ответ от API")
                
            content = response.choices[0].message.content.strip()
            if not content:
                return self._error_template("Пустое содержимое ответа")

            start = content.find('{')
            end = content.rfind('}') + 1
            if start == -1 or end == 0:
                return self._error_template("Неверный JSON в ответе")
            json_str = content[start:end]
            
            result = json.loads(json_str, object_pairs_hook=OrderedDict)
            validated = self._validate_structure(result)
            return validated
        except json.JSONDecodeError as e:
            return self._error_template(f"Ошибка парсинга JSON: {str(e)}")
        except Exception as e:
            return self._error_template(f"Ошибка валидации: {str(e)}")

    def _validate_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Валидирует структуру данных."""
        template = OrderedDict([
            ("personal_data", OrderedDict([
                ("full_name", None),
                ("date_of_birth", None),
                ("contacts", OrderedDict([
                    ("email", None),
                    ("phones", []),
                    ("telegram", None),
                    ("linkedin", None)
                ]))
            ])),
            ("education", [OrderedDict([
                ("university", None),
                ("degree", None),
                ("specialization", None),
                ("start_date", None),
                ("end_date", None),
                ("gpa", None)
            ])]),
            ("skills", OrderedDict([
                ("programming_languages", []),
                ("databases", []),
                ("tools", []),
                ("frameworks", [])
            ])),
            ("experience", [OrderedDict([
                ("company", None),
                ("position", None),
                ("start_date", None),
                ("end_date", None),
                ("description", None),
                ("technologies_used", [])
            ])]),
            ("additional", OrderedDict([
                ("github", None),
                ("portfolio", None),
                ("languages", []),
                ("certificates", [])
            ]))
        ])
        
        return self._merge_structures(template, data)

    def _merge_structures(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Объединяет шаблон с данными."""
        if data is None:
            return template
            
        if isinstance(template, OrderedDict) and isinstance(data, dict):
            merged = OrderedDict()
            for key in template:
                merged[key] = self._merge_structures(template[key], data.get(key, None))
            return merged
        elif isinstance(template, list) and isinstance(data, list):
            if not data:
                return template
            if len(template) == 0:
                return data
            return [self._merge_structures(template[0], item) for item in data]
        else:
            return data if data is not None else template

    def _error_template(self, message: str) -> Dict[str, Any]:
        """Возвращает шаблон с ошибкой."""
        return OrderedDict([
            ("error", message),
            ("data", None)
        ]) 