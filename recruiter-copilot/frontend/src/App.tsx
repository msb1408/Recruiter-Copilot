import { useState, useEffect } from 'react'
import type { ChangeEvent } from 'react'
import './App.css'

interface Role {
  id: string
  name: string
  description: string
  competencies: Array<{
    id: string
    name: string
    group: string
    level: string
    required_level_name: string
    relevant_industries: string[]
  }>
}

interface AnalysisResult {
  resume_data: {
    personal_data: {
      full_name: string
      date_of_birth: string
      contacts: {
        email: string
        phones: string[]
        telegram: string | null
        linkedin: string | null
      }
    }
    education: Array<{
      university: string
      degree: string
      specialization: string
      start_date: string
      end_date: string | null
      gpa: number | null
    }>
    experience: Array<{
      company: string
      position: string
      start_date: string
      end_date: string | null
      description: string
      technologies_used: string[]
    }>
    skills: {
      programming_languages: string[]
      databases: string[]
      tools: string[]
      frameworks: string[]
    }
    additional: {
      github: string | null
      portfolio: string | null
      languages: string[]
      certificates: string[]
    }
  }
  comparison: {
    matching: Array<{
      name: string
      level: string
      match: string
      description: string
    }>
    missing: Array<{
      name: string
      importance: string
      suggestions: string[]
    }>
    extra: Array<{
      name: string
      level: string
      relevance: string
    }>
  }
}

function App() {
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/alliance_matrix.json')
      .then(response => response.json())
      .then(data => {
        // Преобразуем объект ролей в массив
        const rolesArray = Object.entries(data.roles).map(([id, role]: [string, any]) => ({
          id,
          name: role.name,
          description: role.description,
          competencies: role.competencies
        }))
        setRoles(rolesArray)
      })
      .catch(error => console.error('Error loading roles:', error))
  }, [])

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setResumeFile(e.target.files[0])
    }
  }

  const handleAnalyze = async () => {
    if (!resumeFile || !selectedRole) {
      setError('Пожалуйста, выберите файл резюме и вакансию')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const formData = new FormData()
      formData.append('file', resumeFile)
      formData.append('vacancy_id', selectedRole)

      console.log('Отправка запроса:', {
        filename: resumeFile.name,
        vacancyId: selectedRole
      })

      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        console.error('Ошибка сервера:', errorData)
        throw new Error(errorData.detail || `Ошибка сервера: ${response.status}`)
      }

      const data = await response.json()
      console.log('Получен ответ:', data)
      setResult(data)
    } catch (error) {
      console.error('Ошибка:', error)
      setError(error instanceof Error ? error.message : 'Произошла ошибка при анализе резюме')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container">
      <h1>Recruiter Copilot</h1>
      <p className="subtitle">Ваш помощник по подбору персонала</p>
      
      <div className="file-upload">
        <h2>Импортируйте резюме</h2>
        <input
          type="file"
          id="resume-upload"
          accept=".pdf,.docx"
          onChange={handleFileChange}
        />
        <label htmlFor="resume-upload">
          {resumeFile ? resumeFile.name : 'Выберите файл (PDF или DOCX)'}
        </label>
      </div>

      <div className="vacancy-select">
        <h2>Выберите вакансию</h2>
        <select 
          value={selectedRole} 
          onChange={(e) => setSelectedRole(e.target.value)}
        >
          <option value="">Выберите вакансию</option>
          {roles.map(role => (
            <option key={role.id} value={role.id}>
              {role.name}
            </option>
          ))}
        </select>
        {selectedRole && (
          <a 
            href={`/vacancy/${selectedRole}`} 
            target="_blank" 
            rel="noopener noreferrer"
            className="details-link"
          >
            Подробнее о вакансии
          </a>
        )}
      </div>

      <button 
        onClick={handleAnalyze}
        disabled={loading || !resumeFile || !selectedRole}
        className="analyze-button"
      >
        {loading ? 'Анализ...' : 'Анализировать резюме'}
      </button>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {result && (
        <div className="result-section">
          {/* Блок 1: Персональные данные */}
          <div className="result-block">
            <h3>Персональные данные</h3>
            <div className="personal-info">
              <p><strong>ФИО:</strong> {result.resume_data.personal_data.full_name}</p>
              <p><strong>Дата рождения:</strong> {result.resume_data.personal_data.date_of_birth}</p>
              <p><strong>Телефон:</strong> {result.resume_data.personal_data.contacts.phones.join(', ')}</p>
              <p><strong>Email:</strong> {result.resume_data.personal_data.contacts.email}</p>
              <p><strong>Telegram:</strong> {result.resume_data.personal_data.contacts.telegram || 'Не указан'}</p>
              <p><strong>LinkedIn:</strong> {result.resume_data.personal_data.contacts.linkedin || 'Не указан'}</p>
            </div>
          </div>

          {/* Блок 2: Образование */}
          <div className="result-block">
            <h3>Образование</h3>
            {result.resume_data.education.map((edu, index) => (
              <div key={index} className="education-item">
                <p><strong>Учебное заведение:</strong> {edu.university}</p>
                <p><strong>Степень:</strong> {edu.degree}</p>
                <p><strong>Специальность:</strong> {edu.specialization}</p>
                <p><strong>Период:</strong> {edu.start_date} - {edu.end_date || 'Настоящее время'}</p>
                {edu.gpa && <p><strong>Средний балл:</strong> {edu.gpa}</p>}
              </div>
            ))}
          </div>

          {/* Блок 3: Опыт работы */}
          <div className="result-block">
            <h3>Опыт работы</h3>
            {result.resume_data.experience.map((exp, index) => (
              <div key={index} className="experience-item">
                <p><strong>Компания:</strong> {exp.company}</p>
                <p><strong>Должность:</strong> {exp.position}</p>
                <p><strong>Период:</strong> {exp.start_date} - {exp.end_date || 'Настоящее время'}</p>
                <p><strong>Описание:</strong> {exp.description}</p>
                <div className="technologies">
                  <strong>Используемые технологии:</strong>
                  <ul>
                    {exp.technologies_used.map((tech, i) => (
                      <li key={i}>{tech}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>

          {/* Блок 4: Компетенции */}
          <div className="result-block">
            <h3>Карта компетенций</h3>
            
            {/* Совпадающие компетенции */}
            <div className="competencies-section matching">
              <h4>Совпадающие компетенции</h4>
              {result.comparison.matching.map((comp, index) => (
                <div key={index} className="competency-item">
                  <p><strong>{comp.name}</strong> (уровень: {comp.level})</p>
                  <p>Совпадение: {comp.match}</p>
                  <p>{comp.description}</p>
                </div>
              ))}
            </div>

            {/* Отсутствующие компетенции */}
            <div className="competencies-section missing">
              <h4>Отсутствующие компетенции</h4>
              {result.comparison.missing.map((comp, index) => (
                <div key={index} className="competency-item">
                  <p><strong>{comp.name}</strong></p>
                  <p>Важность: {comp.importance}</p>
                  <div className="suggestions">
                    <strong>Предложения по развитию:</strong>
                    <ul>
                      {comp.suggestions.map((sugg, i) => (
                        <li key={i}>{sugg}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            {/* Дополнительные компетенции */}
            <div className="competencies-section extra">
              <h4>Дополнительные компетенции</h4>
              {result.comparison.extra.map((comp, index) => (
                <div key={index} className="competency-item">
                  <p><strong>{comp.name}</strong> (уровень: {comp.level})</p>
                  <p>Релевантность: {comp.relevance}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Блок 5: Дополнительная информация */}
          <div className="result-block">
            <h3>Дополнительная информация</h3>
            <div className="additional-info">
              {result.resume_data.skills.programming_languages.length > 0 && (
                <div className="skills">
                  <h4>Программирование</h4>
                  <ul>
                    {result.resume_data.skills.programming_languages.map((skill, index) => (
                      <li key={index}>{skill}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.resume_data.skills.databases.length > 0 && (
                <div className="skills">
                  <h4>Базы данных</h4>
                  <ul>
                    {result.resume_data.skills.databases.map((skill, index) => (
                      <li key={index}>{skill}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.resume_data.skills.tools.length > 0 && (
                <div className="skills">
                  <h4>Инструменты</h4>
                  <ul>
                    {result.resume_data.skills.tools.map((skill, index) => (
                      <li key={index}>{skill}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.resume_data.skills.frameworks.length > 0 && (
                <div className="skills">
                  <h4>Фреймворки</h4>
                  <ul>
                    {result.resume_data.skills.frameworks.map((skill, index) => (
                      <li key={index}>{skill}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.resume_data.additional.languages.length > 0 && (
                <div className="languages">
                  <h4>Языки</h4>
                  <ul>
                    {result.resume_data.additional.languages.map((lang, index) => (
                      <li key={index}>{lang}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {result.resume_data.additional.certificates.length > 0 && (
                <div className="certificates">
                  <h4>Сертификаты</h4>
                  <ul>
                    {result.resume_data.additional.certificates.map((cert, index) => (
                      <li key={index}>{cert}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App 