# Arenda - Система управления арендой коммерческой недвижимости

Полнофункциональная CRM-система для управления коммерческой недвижимостью с публичным каталогом, системой обработки заявок, управлением договорами и платежами.

## 🚀 Основные возможности

### MVP (Версия 1.0)

✅ **Управление объектами недвижимости**
- Иерархическая структура: Компания → Объект → Здание → Помещение
- Карточки объектов с полной информацией
- Фотогалереи и медиа-файлы

✅ **Управление арендаторами**
- База арендаторов (физлица и юрлица)
- Контактные лица
- История взаимодействий

✅ **Договоры аренды**
- Создание и управление договорами
- График платежей
- Статусы договоров

✅ **Платежи**
- Загрузка платежных документов
- Двухэтапное подтверждение платежей
- Автоматический расчет задолженностей и пени
- История платежей

✅ **Публичный каталог**
- Поиск помещений по параметрам
- Карточки помещений с фото
- Форма заявки для потенциальных клиентов

✅ **Система обработки заявок (Лиды)**
- Прием заявок с сайта
- Воронка продаж
- История коммуникаций с клиентами

✅ **Система ролей**
- Супер-администратор
- Администратор объекта
- Модератор
- Менеджер по продажам
- Арендатор

✅ **Уведомления**
- Email-уведомления
- Напоминания о платежах
- Уведомления о новых заявках

## 📋 Требования

- Python 3.11+
- PostgreSQL 14+
- Redis (опционально, для кеширования)

## 🛠 Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd Arenda
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

Создайте базу данных PostgreSQL:

```bash
createdb arenda
```

### 5. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните настройки:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
# Application
SECRET_KEY=your-super-secret-key-change-this
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/arenda
DATABASE_URL_SYNC=postgresql://user:password@localhost:5432/arenda

# Email
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@arenda.kz
MAIL_SERVER=smtp.gmail.com
```

### 6. Применение миграций

```bash
alembic upgrade head
```

### 7. Создание первого суперадминистратора

Запустите Python интерактивную оболочку:

```bash
python
```

Выполните:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.company import Company

async def create_superadmin():
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Создать компанию
        company = Company(
            name="Моя компания",
            legal_name="ТОО Моя компания",
            bin_iin="123456789012",
            address="Алматы, ул. Примерная, 1",
            phone="+7 777 123 45 67",
            email="info@company.kz"
        )
        session.add(company)
        await session.flush()

        # Создать суперадминистратора
        admin = User(
            email="admin@arenda.kz",
            hashed_password=get_password_hash("admin123"),
            full_name="Администратор",
            role=UserRole.SUPER_ADMIN,
            company_id=company.id,
            is_active=True,
            is_verified=True
        )
        session.add(admin)
        await session.commit()
        print("✅ Суперадминистратор создан!")
        print("Email: admin@arenda.kz")
        print("Пароль: admin123")

asyncio.run(create_superadmin())
```

## 🚀 Запуск приложения

### Режим разработки

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Продакшн

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Приложение будет доступно по адресу: `http://localhost:8000`

## 📚 Документация API

После запуска приложения документация API доступна по адресам:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## 🔑 API Endpoints

### Аутентификация

```
POST   /api/v1/auth/register    - Регистрация пользователя
POST   /api/v1/auth/login       - Вход (получение JWT токена)
GET    /api/v1/auth/me          - Информация о текущем пользователе
```

### Объекты недвижимости

```
POST   /api/v1/properties                    - Создать объект
GET    /api/v1/properties                    - Список объектов
GET    /api/v1/properties/{id}               - Получить объект
PUT    /api/v1/properties/{id}               - Обновить объект
DELETE /api/v1/properties/{id}               - Удалить объект
POST   /api/v1/properties/{id}/buildings     - Создать здание
GET    /api/v1/properties/{id}/buildings     - Список зданий
```

### Помещения

```
POST   /api/v1/premises           - Создать помещение
GET    /api/v1/premises           - Список помещений
GET    /api/v1/premises/{id}      - Получить помещение
PUT    /api/v1/premises/{id}      - Обновить помещение
DELETE /api/v1/premises/{id}      - Удалить помещение
PATCH  /api/v1/premises/{id}/publish - Опубликовать/снять с публикации
```

### Публичный каталог

```
GET    /api/v1/catalog/premises       - Список опубликованных помещений
GET    /api/v1/catalog/premises/{id}  - Карточка помещения
GET    /api/v1/catalog/search         - Поиск помещений
```

### Заявки (Лиды)

```
POST   /api/v1/leads                         - Создать заявку (публичный)
GET    /api/v1/leads                         - Список заявок
GET    /api/v1/leads/{id}                    - Получить заявку
PATCH  /api/v1/leads/{id}                    - Обновить заявку
POST   /api/v1/leads/{id}/communications     - Добавить коммуникацию
GET    /api/v1/leads/{id}/communications     - История коммуникаций
```

### Арендаторы

```
GET    /api/v1/tenants        - Список арендаторов
GET    /api/v1/tenants/{id}   - Получить арендатора
```

### Договоры

```
GET    /api/v1/contracts      - Список договоров
```

### Платежи

```
GET    /api/v1/payments       - Список платежей
```

## 🗄 Структура базы данных

```
companies                  # Компании
├── users                  # Пользователи системы
├── properties            # Объекты недвижимости
│   ├── buildings        # Здания/корпуса
│   │   └── premises     # Помещения
├── tenants              # Арендаторы
│   ├── tenant_contacts  # Контактные лица
│   └── contracts        # Договоры аренды
│       ├── payment_schedules  # График платежей
│       └── payments          # Платежи
│           └── payment_documents  # Документы к платежам
└── leads                # Заявки от клиентов
    └── lead_communications    # История коммуникаций
```

## 🔐 Роли пользователей

1. **SUPER_ADMIN** - Супер-администратор
   - Полный доступ ко всем функциям
   - Управление всеми объектами и компаниями

2. **PROPERTY_ADMIN** - Администратор объекта
   - Управление своим объектом
   - Назначение модераторов

3. **MODERATOR** - Модератор
   - Работа с помещениями, арендаторами, договорами
   - Обработка платежей

4. **SALES_MANAGER** - Менеджер по продажам
   - Работа с заявками
   - Организация просмотров

5. **TENANT** - Арендатор
   - Просмотр своих помещений и договоров
   - Загрузка платежных документов

## 📁 Структура проекта

```
Arenda/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── deps.py         # Зависимости (авторизация)
│   │   └── v1/
│   │       ├── api.py      # Главный роутер
│   │       └── endpoints/  # Endpoints по модулям
│   ├── core/               # Ядро приложения
│   │   ├── config.py       # Конфигурация
│   │   └── security.py     # Безопасность (JWT, хеширование)
│   ├── db/                 # База данных
│   │   └── session.py      # Сессии SQLAlchemy
│   ├── models/             # SQLAlchemy модели
│   ├── schemas/            # Pydantic схемы
│   ├── services/           # Бизнес-логика
│   ├── utils/              # Утилиты
│   └── main.py             # Главный файл приложения
├── alembic/                # Миграции базы данных
│   ├── versions/           # Файлы миграций
│   └── env.py              # Конфигурация Alembic
├── uploads/                # Загруженные файлы
├── requirements.txt        # Зависимости Python
├── .env.example            # Пример переменных окружения
├── .gitignore
├── alembic.ini             # Конфигурация Alembic
└── README.md
```

## 🔄 Миграции базы данных

### Создание новой миграции

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграции

```bash
alembic downgrade -1
```

## 🧪 Тестирование

Примеры использования API:

### 1. Регистрация и вход

```bash
# Вход
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@arenda.kz&password=admin123"
```

### 2. Создание объекта недвижимости

```bash
curl -X POST "http://localhost:8000/api/v1/properties" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "ТРЦ Dostyk Plaza",
    "property_type": "shopping_center",
    "address": "Алматы, ул. Достык, 111",
    "total_area": 50000
  }'
```

### 3. Отправка заявки (публичный endpoint)

```bash
curl -X POST "http://localhost:8000/api/v1/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Иван Иванов",
    "phone": "+7 777 123 45 67",
    "email": "ivan@example.com",
    "desired_area": 100,
    "budget": 500000,
    "message": "Интересует офис в центре города",
    "consent_given": true
  }'
```

## 📊 Следующие шаги (Этап 2)

- [ ] Мобильное приложение (iOS/Android)
- [ ] Продвинутая аналитика и отчеты
- [ ] CRM для лидов с воронкой продаж
- [ ] Чат в реальном времени
- [ ] 3D-туры помещений
- [ ] Push-уведомления
- [ ] SMS-уведомления
- [ ] Система задач
- [ ] База знаний

## 🤝 Поддержка

При возникновении вопросов или проблем:
- Создайте issue в репозитории
- Напишите на email: support@arenda.kz

## 📄 Лицензия

Copyright © 2024 Arenda. Все права защищены.

---

**Разработано с ❤️ для управления коммерческой недвижимостью**
