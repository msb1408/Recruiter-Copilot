# Recruiter Copilot
ИИ-ассистент по подбору персонала.

Это прототип.
Анализирует и структурирует резюме кандидата, исходя из описания вакансии, выводит совпадающие, отсутствующие и дополнительные компетенции. Все модули масштабируемы. Работает на LLM Deepseek. 

В качестве описания вакансий используется Матрица компетенций Альянса.

Планируется:
- улучшение структуризации резюме и вакансии для большей наглядности, добавление фильтров
- добавление процента совпадения
- создание рекомендательной системы вакансий
- создание SQL БД с вузами, направлениями обучения и соотвествующими компетенциями
- интеграция hh.ru и других сайтов по поиску работы
- анализ компетенций на основе ссылок в резюме
- собственный NLP-модуль и улучшенная версия сайта: соискатель сам загружает резюме на выбранные вакансии, а рекрутеру приходят 2 версии резюме: проанализированная и сырая.
