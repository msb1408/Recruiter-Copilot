import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

interface Role {
  id: string
  name: string
  description: string
  competencies: Array<{
    id: string
    name: string
    group: string
    required_level_code: number | null
    required_level_name: string | null
    relevant_industries: string[]
  }>
}

export default function VacancyDetails() {
  const { roleId } = useParams()
  const [role, setRole] = useState<Role | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/alliance_matrix.json')
      .then(response => response.json())
      .then(data => {
        // Ищем вакансию в объекте roles по ключу
        const roleData = data.roles[roleId || '']
        if (roleData) {
          setRole({
            id: roleId || '',
            name: roleData.name,
            description: roleData.description,
            competencies: roleData.competencies
          })
        }
        setLoading(false)
      })
      .catch(error => {
        console.error('Error fetching role details:', error)
        setLoading(false)
      })
  }, [roleId])

  if (loading) {
    return <div>Загрузка...</div>
  }

  if (!role) {
    return <div>Вакансия не найдена</div>
  }

  return (
    <div className="vacancy-details">
      <h1>{role.name}</h1>
      <div className="description">
        <h2>Описание</h2>
        <p>{role.description}</p>
      </div>

      <div className="competencies">
        <h2>Требуемые компетенции</h2>
        {role.competencies.map(comp => (
          <div key={comp.id} className="competency">
            <h3>{comp.name}</h3>
            <p><strong>Группа:</strong> {comp.group}</p>
            {comp.required_level_name && (
              <p><strong>Требуемый уровень:</strong> {comp.required_level_name}</p>
            )}
            {comp.relevant_industries.length > 0 && (
              <p><strong>Отрасли:</strong> {comp.relevant_industries.join(', ')}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
} 