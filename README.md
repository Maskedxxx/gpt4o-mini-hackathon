# AI-powered Resume Personalizer Bot

## 🎯 О проекте

Resume Copilot - это инновационное решение на стыке искусственного интеллекта и HR-технологий, разработанное для автоматической персонализации резюме под требования конкретных вакансий. Наш проект решает критическую проблему на рынке труда: сложность адаптации резюме под каждую конкретную позицию и ограниченное время рекрутеров на рассмотрение каждого кандидата (в среднем 7-10 секунд).

Проект представляет собой интеллектуального Telegram-бота, который не просто анализирует резюме и вакансии, но и действует как персональный карьерный консультант, значительно повышая шансы соискателей на успешное трудоустройство.

### Ключевые преимущества
- Существенное снижение порога входа для соискателей в IT-сфере
- Экономия времени и средств на услугах рекрутинговых агентств
- Персонализированный подход к каждой вакансии
- Интеллектуальный анализ требований и автоматическая адаптация резюме
- Повышение конверсии откликов на вакансии

## 🤖 Рабочий бот

Бот доступен в Telegram: [@ai_job_job_bot](https://t.me/@ai_job_job_bot)

## 📑 Презентация проекта

(https://drive.google.com/file/d/1xAkTtZLSHQQEumSq0e9DmQm_8lFBxeK5/view?usp=sharing)

## 🎥 Демонстрация работы

(https://drive.google.com/file/d/1zNaMgXahxWqRdLUHrvZJ2Xdy4x95XkV7/view?usp=sharing)

## 💡 Функциональность

### Основной функционал
- Автоматическая авторизация через HeadHunter
- Интеллектуальный анализ существующего резюме
- GAP-анализ соответствия требованиям вакансии
- Автоматическая персонализация резюме
- Мгновенное обновление через API

### Планируемые функции
- Генерация персонализированных сопроводительных писем
- Создание планов подготовки к собеседованиям
- Анализ трендов рынка труда
- Рекомендации по развитию навыков

## 📚 История проекта

Проект был разработан с нуля в рамках хакатона, представляя собой оригинальное решение, не имеющее прямых аналогов. В ходе разработки были реализованы следующие ключевые компоненты:

### 🔄 API Интеграция
- Разработан полноценный модуль взаимодействия с API HeadHunter
- Реализованы функции получения данных резюме и вакансий
- Имплементирован механизм автоматического обновления резюме через API
- Настроена безопасная работа с токенами доступа

### 🛠 Архитектура Telegram бота
- Использован современный фреймворк aiogram с имплементацией:
  - Системы машин состояний для управления диалогом
  - Асинхронных обработчиков событий
  - Инлайн-клавиатур и callback-систем
  - Middleware для обработки пользовательских сессий
  - Системы логирования действий пользователя

### 🧠 Интеллектуальные агенты
Разработана двухуровневая система интеллектуальных агентов на базе GPT-4_mini:

1. **Агент анализа (Gap-Analysis)**
   - Получает и анализирует исходное резюме и целевую вакансию
   - Проводит детальный gap-анализ
   - Формирует структурированный отчет необходимых изменений
   - Использует Pydantic схемы для валидации данных

2. **Агент оптимизации**
   - Обрабатывает результаты gap-анализа
   - Выполняет intelligent rewriting резюме
   - Автоматически применяет необходимые изменения
   - Взаимодействует с API для обновления резюме

## 🔄 Процесс работы

### 1. Начало работы
1. Пользователь запускает бота и проходит авторизацию через HeadHunter
2. После успешной авторизации открывается доступ к основному функционалу

### 2. Персонализация резюме
1. Пользователь предоставляет ссылку на своё резюме
2. Бот автоматически получает данные резюме через API
3. Пользователь указывает целевую вакансию
4. Система анализирует требования вакансии
5. Запускается процесс интеллектуальной оптимизации

### 3. Процесс оптимизации
1. GAP-анализ выявляет области для улучшения
2. Агент оптимизации создает персонализированную версию резюме
3. Обновленное резюме автоматически загружается на HeadHunter

## 📈 Стратегия развития

### Краткосрочные планы
- Разработка функционала создания резюме с нуля
- Внедрение генерации сопроводительных писем
- Создание системы подготовки к собеседованиям

### Масштабирование
- Интеграция с дополнительными платформами (Rabota.ru, LinkedIn, Glassdoor)
- Разработка корпоративной версии для HR-отделов
- Создание партнерской программы с образовательными платформами

### Монетизация
- Внедрение модели Freemium
- Запуск системы подписок с различными уровнями доступа
- Разработка специальных тарифов для корпоративных клиентов

## 👨‍💻 Команда разработчиков

- **Немов Максим** - AI Engineer
- **Канунников Иван** - AI Engineer

## 🚀 Технологический стек

- Python 3.9+
- aiogram>=3.0
- aiohttp
- python-dotenv
- pydantic
- requests
- openai
- ngrok
- pyngrok

## ⚙️ Установка и запуск

Для запуска собственной версии бота необходимо:

1. Получить необходимые токены доступа:
   - Токен Telegram
   - Токены доступа к API HeadHunter

2. Установить зависимости:
```bash
pip install -r requirements.txt
```

3. Настроить конфигурацию в файле `.env`

## 📝 Примечание

В текущей версии бот работает с использованием персональных токенов доступа разработчиков. Для развертывания собственной версии необходимо получить соответствующие токены доступа на платформе HeadHunter.
