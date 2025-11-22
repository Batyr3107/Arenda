# 🚀 Быстрый старт с Docker

## Запуск всех сервисов с помощью Docker Compose

### 1. Настройка переменных окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` и убедитесь, что указаны правильные настройки для Docker:

```env
DATABASE_URL=postgresql+asyncpg://arenda_user:arenda_password@postgres:5432/arenda
DATABASE_URL_SYNC=postgresql://arenda_user:arenda_password@postgres:5432/arenda
REDIS_URL=redis://redis:6379/0
```

### 2. Запуск сервисов

```bash
docker-compose up -d
```

Это запустит:
- PostgreSQL (порт 5432)
- Redis (порт 6379)
- FastAPI приложение (порт 8000)

### 3. Применение миграций

```bash
docker-compose exec api alembic upgrade head
```

### 4. Создание суперадминистратора

```bash
docker-compose exec api python -c "
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
        company = Company(
            name='Demo Company',
            legal_name='ТОО Demo Company',
            bin_iin='123456789012',
            address='Алматы, ул. Примерная, 1',
            phone='+7 777 123 45 67',
            email='info@demo.kz'
        )
        session.add(company)
        await session.flush()

        admin = User(
            email='admin@arenda.kz',
            hashed_password=get_password_hash('admin123'),
            full_name='Администратор',
            role=UserRole.SUPER_ADMIN,
            company_id=company.id,
            is_active=True,
            is_verified=True
        )
        session.add(admin)
        await session.commit()
        print('✅ Суперадминистратор создан!')
        print('Email: admin@arenda.kz')
        print('Пароль: admin123')

asyncio.run(create_superadmin())
"
```

### 5. Проверка работы

Откройте в браузере:
- API Docs: http://localhost:8000/api/docs
- Health check: http://localhost:8000/health

### 6. Остановка сервисов

```bash
docker-compose down
```

Для удаления всех данных (включая базу данных):

```bash
docker-compose down -v
```

---

## 📝 Примеры API запросов

### 1. Получение токена

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@arenda.kz&password=admin123"
```

Ответ:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Сохраните токен в переменную:
```bash
export TOKEN="ваш_токен_здесь"
```

### 2. Создание объекта недвижимости

```bash
curl -X POST "http://localhost:8000/api/v1/properties" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_id": 1,
    "name": "Бизнес-центр Алатау",
    "property_type": "business_center",
    "address": "г. Алматы, пр. Аль-Фараби, 15",
    "latitude": 43.2220,
    "longitude": 76.8512,
    "description": "Современный бизнес-центр класса А",
    "total_area": 15000,
    "year_built": 2020,
    "parking_spaces": 200,
    "has_security": true,
    "has_cctv": true,
    "working_hours": "24/7"
  }'
```

### 3. Создание здания

```bash
curl -X POST "http://localhost:8000/api/v1/properties/1/buildings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": 1,
    "name": "Корпус A",
    "floors_count": 10,
    "total_area": 8000,
    "has_elevator": true,
    "has_ventilation": true
  }'
```

### 4. Создание помещения

```bash
curl -X POST "http://localhost:8000/api/v1/premises" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "building_id": 1,
    "number": "301",
    "floor": 3,
    "area": 120.5,
    "premise_type": "office",
    "price_per_month": 450000,
    "price_per_sqm": 3500,
    "description": "Угловой офис с панорамными окнами",
    "has_furniture": true,
    "has_internet": true,
    "has_conditioning": true,
    "ceiling_height": 3.2,
    "rooms_count": 4,
    "status": "available"
  }'
```

### 5. Публикация помещения в каталог

```bash
curl -X PATCH "http://localhost:8000/api/v1/premises/1/publish?is_published=true" \
  -H "Authorization: Bearer $TOKEN"
```

### 6. Получение списка помещений (публичный каталог)

```bash
# Без авторизации
curl "http://localhost:8000/api/v1/catalog/premises?min_area=100&max_area=200&premise_type=office"
```

### 7. Создание заявки от клиента

```bash
# Публичный endpoint, не требует авторизации
curl -X POST "http://localhost:8000/api/v1/leads" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Алексей Петров",
    "company_name": "ТОО Рога и Копыта",
    "phone": "+7 701 234 56 78",
    "email": "alexey@example.kz",
    "premise_id": 1,
    "desired_area": 120,
    "budget": 500000,
    "lease_term": "12 месяцев",
    "message": "Интересует офис на 3 этаже",
    "consent_given": true
  }'
```

### 8. Получение списка заявок (для менеджеров)

```bash
curl "http://localhost:8000/api/v1/leads?status=new" \
  -H "Authorization: Bearer $TOKEN"
```

### 9. Обновление статуса заявки

```bash
curl -X PATCH "http://localhost:8000/api/v1/leads/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "contacted",
    "assigned_to_id": 1,
    "priority": 1
  }'
```

### 10. Добавление записи о коммуникации с клиентом

```bash
curl -X POST "http://localhost:8000/api/v1/leads/1/communications" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "communication_type": "phone",
    "notes": "Созвонились с клиентом, договорились о просмотре на завтра в 14:00",
    "next_action": "Показ помещения",
    "next_action_date": "2024-12-01T14:00:00"
  }'
```

---

## 🔍 Полезные команды Docker

### Просмотр логов

```bash
# Все сервисы
docker-compose logs -f

# Только API
docker-compose logs -f api

# Только PostgreSQL
docker-compose logs -f postgres
```

### Вход в контейнер

```bash
# API
docker-compose exec api bash

# PostgreSQL
docker-compose exec postgres psql -U arenda_user -d arenda
```

### Перезапуск сервисов

```bash
docker-compose restart
```

### Пересборка образов

```bash
docker-compose up -d --build
```

---

## 🎯 Типичные сценарии использования

### Сценарий 1: Публикация нового помещения

1. Создать объект недвижимости (если еще нет)
2. Создать здание (если еще нет)
3. Создать помещение
4. Загрузить фотографии (TODO: endpoint для загрузки файлов)
5. Опубликовать помещение: `PATCH /api/v1/premises/{id}/publish`

### Сценарий 2: Обработка входящей заявки

1. Клиент оставляет заявку через публичный каталог: `POST /api/v1/leads`
2. Менеджер видит новую заявку: `GET /api/v1/leads?status=new`
3. Менеджер назначает себя ответственным: `PATCH /api/v1/leads/{id}`
4. Менеджер связывается с клиентом и записывает результат: `POST /api/v1/leads/{id}/communications`
5. Планирует просмотр: обновляет `viewing_date`
6. После просмотра обновляет статус заявки

### Сценарий 3: Создание договора и прием платежей

1. Создать арендатора (TODO: endpoint)
2. Создать договор (TODO: endpoint)
3. Система автоматически генерирует график платежей
4. Арендатор загружает платежный документ (TODO: endpoint)
5. Модератор подтверждает платеж (первое подтверждение)
6. Администратор подтверждает платеж (второе подтверждение)

---

**Приятной работы с Arenda! 🚀**
