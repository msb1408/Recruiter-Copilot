from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
from pathlib import Path
from functools import lru_cache
from resume_parser import ResumeParser
from resume_processor import ResumeProcessor
from openai import OpenAI

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    vacancy_id: str

# Конфиг DeepSeek
DEEPSEEK_API_KEY = ""

# Пути к JSON файлам
ALLIANCE_MATRIX_PATH = Path("alliance_matrix.json")

# Инициализация парсеров
resume_parser = ResumeParser(
    api_key=DEEPSEEK_API_KEY,
    max_retries=3,
    timeout=30
)
resume_processor = ResumeProcessor()

# Загрузка данных из JSON
@lru_cache(maxsize=1)
def get_alliance_matrix():
    try:
        with open(ALLIANCE_MATRIX_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading alliance matrix: {e}")
        return {"roles": []}

@app.get("/api/vacancies")
async def get_vacancies():
    try:
        alliance_matrix = get_alliance_matrix()
        return [
            {
                "id": role["id"],
                "title": role["name"],
                "description": role["description"]
            }
            for role in alliance_matrix["roles"]
        ]
    except Exception as e:
        print(f"Error getting vacancies: {e}")
        return []

@app.post("/api/analyze")
async def analyze(
    vacancy_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        print(f"Получен запрос: vacancy_id={vacancy_id}, filename={file.filename}")
        
        # Читаем содержимое файла
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Файл пуст")
            
        # Обрабатываем резюме
        resume_text = resume_processor.process_resume(file_content, file.filename)
        if not resume_text:
            raise HTTPException(status_code=400, detail="Не удалось извлечь текст из резюме")

        print("Текст резюме успешно извлечен")
        
        # Парсим резюме
        resume_data = resume_parser.parse(resume_text)
        if "error" in resume_data:
            raise HTTPException(status_code=400, detail=resume_data["error"])

        print("Резюме успешно распарсено")
        
        # Получаем компетенции вакансии
        vacancy_competencies = await get_vacancy_competencies(vacancy_id)
        if not vacancy_competencies:
            raise HTTPException(status_code=400, detail="Не найдены компетенции для вакансии")

        print("Компетенции вакансии получены")
        
        # Извлекаем компетенции из резюме
        candidate_competencies = extract_competencies_from_resume(resume_data)

        # Сравниваем компетенции
        comparison_result = await compare_competencies(
            candidate_competencies,
            vacancy_competencies
        )

        print("Анализ завершен успешно")
        
        return {
            "resume_data": resume_data,
            "comparison": comparison_result
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Ошибка в analyze endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_competencies_from_resume(resume_data):
    competencies = []
    
    # Извлекаем навыки из раздела skills
    if "skills" in resume_data:
        skills = resume_data["skills"]
        for category in ["programming_languages", "databases", "tools", "frameworks"]:
            if category in skills and skills[category]:
                competencies.extend(skills[category])
    
    # Извлекаем технологии из опыта работы
    if "experience" in resume_data:
        for exp in resume_data["experience"]:
            if "technologies_used" in exp and exp["technologies_used"]:
                competencies.extend(exp["technologies_used"])
    
    return list(set(competencies))  # Удаляем дубликаты

async def compare_competencies(candidate_competencies: list, vacancy_competencies: list) -> dict:
    try:
        # Создаем клиент OpenAI для сравнения компетенций
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://hubai.loe.gg/v1")
        
        prompt = f"""
        Сравни компетенции кандидата с требованиями вакансии и раздели их на три группы в формате JSON:

        {{
            "matching": [
                {{
                    "name": "название компетенции",
                    "level": "уровень владения",
                    "match": "степень соответствия требованиям",
                    "description": "описание соответствия"
                }}
            ],
            "missing": [
                {{
                    "name": "название требуемой компетенции",
                    "importance": "важность для вакансии",
                    "suggestions": ["предложения по развитию"]
                }}
            ],
            "extra": [
                {{
                    "name": "название компетенции",
                    "level": "уровень владения",
                    "relevance": "релевантность для вакансии"
                }}
            ]
        }}

        Компетенции кандидата:
        {json.dumps(candidate_competencies, ensure_ascii=False, indent=2)}

        Требования вакансии:
        {json.dumps(vacancy_competencies, ensure_ascii=False, indent=2)}
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        
        if not response.choices or not response.choices[0].message:
            return {"error": "Invalid response from LLM"}
            
        content = response.choices[0].message.content.strip()
        start = content.find('{')
        end = content.rfind('}') + 1
        if start == -1 or end == 0:
            return {"error": "Invalid JSON response"}
            
        return json.loads(content[start:end])
    except Exception as e:
        print(f"Error comparing competencies: {e}")
        return {"error": str(e)}

async def get_vacancy_competencies(vacancy_id: str) -> list:
    try:
        alliance_matrix = get_alliance_matrix()
        if not alliance_matrix or 'roles' not in alliance_matrix:
            print("Матрица альянса пуста или не содержит ролей")
            return []
            
        # Находим вакансию по ID в roles
        vacancy = alliance_matrix["roles"].get(vacancy_id)
        if not vacancy:
            print(f"Вакансия с ID {vacancy_id} не найдена")
            return []
            
        # Извлекаем компетенции из вакансии
        competencies = []
        if 'competencies' in vacancy:
            for comp in vacancy['competencies']:
                if isinstance(comp, dict) and 'name' in comp:
                    competencies.append(comp['name'])
        
        print(f"Найдены компетенции для вакансии {vacancy_id}: {competencies}")
        return competencies
    except Exception as e:
        print(f"Ошибка при получении компетенций вакансии: {e}")
        return []
