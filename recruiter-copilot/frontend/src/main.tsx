import * as React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import VacancyDetails from './VacancyDetails'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/vacancy/:roleId" element={<VacancyDetails />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
) 