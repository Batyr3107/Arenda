# Arenda - Полноценная система управления арендой недвижимости

## 🎉 ПОЛНАЯ ВЕРСИЯ - Все функции реализованы!

Это комплексная CRM-система для управления коммерческой недвижимостью с полным функционалом:
- ✅ Управление объектами и помещениями
- ✅ Управление арендаторами с контактами
- ✅ Договоры с автоматическим графиком платежей
- ✅ Двухэтапное подтверждение платежей
- ✅ Загрузка файлов (фото, документы)
- ✅ Генерация PDF (договоры, счета, акты)
- ✅ Email-уведомления
- ✅ Публичный каталог помещений
- ✅ CRM для лидов (заявок)
- ✅ Отчеты и аналитика
- ✅ Дашборд с метриками

## 📋 Полный список API Endpoints

### 🔐 Аутентификация
```
POST   /api/v1/auth/register         - Регистрация
POST   /api/v1/auth/login            - Вход (JWT токен)
GET    /api/v1/auth/me               - Текущий пользователь
```

### 🏢 Объекты недвижимости
```
POST   /api/v1/properties                    - Создать объект
GET    /api/v1/properties                    - Список объектов
GET    /api/v1/properties/{id}               - Получить объект
PUT    /api/v1/properties/{id}               - Обновить объект
DELETE /api/v1/properties/{id}               - Удалить объект
POST   /api/v1/properties/{id}/buildings     - Создать здание
GET    /api/v1/properties/{id}/buildings     - Список зданий
```

### 🏠 Помещения
```
POST   /api/v1/premises                - Создать помещение
GET    /api/v1/premises                - Список помещений (с фильтрами)
GET    /api/v1/premises/{id}           - Получить помещение
PUT    /api/v1/premises/{id}           - Обновить помещение
DELETE /api/v1/premises/{id}           - Удалить помещение
PATCH  /api/v1/premises/{id}/publish   - Опубликовать/снять с публикации
```

### 👥 Арендаторы
```
POST   /api/v1/tenants                        - Создать арендатора
GET    /api/v1/tenants                        - Список арендаторов (поиск, фильтры)
GET    /api/v1/tenants/{id}                   - Получить арендатора с контактами
PUT    /api/v1/tenants/{id}                   - Обновить арендатора
DELETE /api/v1/tenants/{id}                   - Удалить арендатора
POST   /api/v1/tenants/{id}/contacts          - Добавить контактное лицо
GET    /api/v1/tenants/{id}/contacts          - Список контактов
PUT    /api/v1/tenants/contacts/{id}          - Обновить контакт
DELETE /api/v1/tenants/contacts/{id}          - Удалить контакт
```

### 📝 Договоры
```
POST   /api/v1/contracts                         - Создать договор (автогенерация графика)
GET    /api/v1/contracts                         - Список договоров (фильтры)
GET    /api/v1/contracts/{id}                    - Получить договор с графиком
PUT    /api/v1/contracts/{id}                    - Обновить договор
PATCH  /api/v1/contracts/{id}/activate          - Активировать договор
PATCH  /api/v1/contracts/{id}/terminate         - Расторгнуть договор
GET    /api/v1/contracts/{id}/pdf               - Скачать договор в PDF
GET    /api/v1/contracts/{id}/payment-schedules - График платежей
```

### 💰 Платежи
```
POST   /api/v1/payments                              - Создать платеж
GET    /api/v1/payments                              - Список платежей (фильтры)
GET    /api/v1/payments/{id}                         - Получить платеж с документами
POST   /api/v1/payments/{id}/upload-document         - Загрузить документ (арендатор)
POST   /api/v1/payments/{id}/approve-first           - 1-е подтверждение (модератор)
POST   /api/v1/payments/{id}/approve-second          - 2-е подтверждение (админ)
GET    /api/v1/payments/{id}/invoice-pdf             - Скачать счет в PDF
GET    /api/v1/payments/overdue/list                 - Список просроченных
```

### 🎯 Лиды и CRM
```
POST   /api/v1/leads                            - Создать заявку (публичный)
GET    /api/v1/leads                            - Список заявок (фильтры)
GET    /api/v1/leads/{id}                       - Получить заявку
PATCH  /api/v1/leads/{id}                       - Обновить статус
POST   /api/v1/leads/{id}/communications        - Добавить запись о коммуникации
GET    /api/v1/leads/{id}/communications        - История коммуникаций
```

### 🌐 Публичный каталог
```
GET    /api/v1/catalog/premises         - Список помещений (фильтры, поиск)
GET    /api/v1/catalog/premises/{id}    - Карточка помещения (+просмотры)
GET    /api/v1/catalog/search           - Поиск по тексту
```

### 📁 Загрузка файлов
```
POST   /api/v1/files/premises/photos     - Загрузить фото помещений
POST   /api/v1/files/properties/photos   - Загрузить фото объектов
POST   /api/v1/files/contracts/documents - Загрузить документы договоров
DELETE /api/v1/files/delete              - Удалить файл
```

### 📊 Отчеты и аналитика
```
GET    /api/v1/reports/dashboard              - Дашборд с метриками
GET    /api/v1/reports/occupancy/{property}   - Отчет по заполненности
GET    /api/v1/reports/financial              - Финансовый отчет (период)
GET    /api/v1/reports/leads/conversion       - Конверсия лидов
```

### 🔔 Уведомления
```
GET    /api/v1/notifications                  - Мои уведомления
GET    /api/v1/notifications/unread/count     - Количество непрочитанных
PATCH  /api/v1/notifications/{id}/read        - Отметить прочитанным
POST   /api/v1/notifications/mark-all-read    - Отметить все прочитанными
```

## 🚀 Быстрый старт

### 1. Запуск с Docker (рекомендуется)

```bash
# Настроить окружение
cp .env.example .env

# Запустить все сервисы
docker-compose up -d

# Применить миграции
docker-compose exec api alembic upgrade head

# Создать суперадминистратора
docker-compose exec api python scripts/create_superuser.py
```

### 2. Открыть документацию API
```
http://localhost:8000/api/docs
```

## 💡 Ключевые возможности

### 1. Двухэтапное подтверждение платежей

**Workflow:**
1. Арендатор загружает документ об оплате
2. Платеж переходит в статус "pending_approval"
3. Модератор проверяет и делает 1-е подтверждение
4. Администратор делает 2-е подтверждение
5. Платеж получает статус "approved"

### 2. Автоматическая генерация графика платежей

При создании договора автоматически генерируется график платежей в зависимости от частоты оплаты (ежемесячно/ежеквартально/ежегодно).

### 3. Расчет пени за просрочку

Система автоматически:
- Отслеживает просроченные платежи
- Рассчитывает пеню (0.1% за день просрочки по умолчанию)
- Обновляет статусы платежей

### 4. Email-уведомления

Автоматические уведомления о:
- Приближающихся платежах (за 3 дня)
- Просрочке платежей
- Истечении договоров
- Новых заявках

### 5. Генерация PDF документов

- **Договоры** - полный договор аренды
- **Счета** - счета на оплату
- **Акты** - акты об оказании услуг

### 6. Отчеты и метрики

**Дашборд показывает:**
- Количество объектов, помещений, договоров
- Процент заполненности
- Ежемесячный доход
- Количество просроченных платежей
- Новые заявки

**Отчеты:**
- Заполненность по объектам
- Финансовый отчет за период
- Конверсия лидов
- Платежная дисциплина арендаторов

## 🏗️ Технический стек

- **Backend**: FastAPI 0.109.0 (Python 3.11+)
- **Database**: PostgreSQL 15+ с asyncpg
- **ORM**: SQLAlchemy 2.0 (async)
- **Migrations**: Alembic 1.13.1
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt (passlib)
- **PDF Generation**: ReportLab
- **Email**: FastAPI-Mail
- **File Upload**: aiofiles + PIL
- **Validation**: Pydantic 2.5.3
- **Deployment**: Docker + Docker Compose

## 📂 Структура проекта

```
Arenda/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (auth, roles)
│   │   └── v1/
│   │       ├── api.py           # Main router
│   │       └── endpoints/       # All endpoints (11 modules)
│   ├── core/
│   │   ├── config.py            # Settings
│   │   └── security.py          # JWT, hashing
│   ├── db/
│   │   └── session.py           # Database session
│   ├── models/                  # SQLAlchemy models (9 models)
│   ├── schemas/                 # Pydantic schemas (50+ schemas)
│   ├── services/                # Business logic
│   │   ├── payment_service.py
│   │   ├── contract_service.py
│   │   └── report_service.py
│   ├── utils/                   # Utilities
│   │   ├── email.py             # Email templates
│   │   ├── file_upload.py       # File handling
│   │   └── pdf_generator.py     # PDF generation
│   └── main.py                  # FastAPI app
├── alembic/                     # Migrations
├── uploads/                     # Uploaded files
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── README.md
└── QUICKSTART.md
```

## 🔒 Система ролей

| Роль | Права |
|------|-------|
| **Super Admin** | Полный доступ ко всему |
| **Property Admin** | Управление своим объектом |
| **Moderator** | Помещения, договоры, 1-е подтверждение платежей |
| **Sales Manager** | Работа с лидами |
| **Tenant** | Просмотр своих договоров, загрузка платежей |

## 📈 Примеры использования

### Создание договора с автоматическим графиком

```bash
curl -X POST "http://localhost:8000/api/v1/contracts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": 1,
    "premise_id": 1,
    "contract_number": "ARD-2024-001",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "monthly_rent": 500000,
    "payment_frequency": "monthly",
    "payment_day": 1,
    "status": "active"
  }'
```

### Двухэтапное подтверждение платежа

```bash
# 1. Арендатор загружает документ
curl -X POST "http://localhost:8000/api/v1/payments/1/upload-document" \
  -H "Authorization: Bearer $TENANT_TOKEN" \
  -F "file=@payment_receipt.jpg"

# 2. Модератор подтверждает (1-й этап)
curl -X POST "http://localhost:8000/api/v1/payments/1/approve-first" \
  -H "Authorization: Bearer $MODERATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# 3. Админ подтверждает (2-й этап)
curl -X POST "http://localhost:8000/api/v1/payments/1/approve-second" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'
```

### Получение отчета по финансам

```bash
curl "http://localhost:8000/api/v1/reports/financial?period_start=2024-01-01&period_end=2024-12-31" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔮 Будущие улучшения (Фаза 2)

- [ ] Планировщик задач (APScheduler) для автоматических уведомлений
- [ ] Мобильное приложение (iOS/Android)
- [ ] WebSocket для уведомлений в реальном времени
- [ ] SMS-уведомления
- [ ] Интеграция с платежными шлюзами
- [ ] Экспорт в 1С
- [ ] 3D-туры помещений
- [ ] Система задач и напоминаний

## 📄 Лицензия

Copyright © 2024 Arenda. All rights reserved.

---

**Создано с ❤️ для управления коммерческой недвижимостью**
