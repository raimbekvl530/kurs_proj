#  Kurs Project — Чат в реальном времени на Django

**Kurs Project** — это курсовая работа, реализующая веб-приложение чата в реальном времени с использованием Django и WebSocket. Проект демонстрирует навыки работы с современными веб-технологиями и архитектурой клиент-сервер.



## Технологии и зависимости

Проект построен на следующих технологиях:

- **Python 3.10+**
- **Django 4.2.1**
- **Django Channels 4.0.0**
- **Django REST Framework 3.14.0**
- **Channels Redis**
- **Redis**
- **ASGI**

Полный список зависимостей — в `requirements.txt`.

---

## Установка и запуск

1. Клонировать репозиторий:

   ```bash
   git clone https://github.com/raimbekvl530/kurs_project.git
   cd kurs_project

2. установка зависимости
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt


3. Миграции
python manage.py migrate

4. запуск
python manage.py runserver

5.проверка
http://localhost:8000


Структура проекта
chat/ — логика чата: модели, views, routing

kurs_project/ — конфигурация проекта

templates/ — HTML-шаблоны

static/ — CSS и JavaScript

requirements.txt — зависимости

Особенности реализации
Используется WebSocket и Redis для обмена сообщениями в реальном времени

Система аутентификации пользователей

Возможность общения в разных комнатах

Хранение истории сообщений

Простое и чистое UI-оформлениe
