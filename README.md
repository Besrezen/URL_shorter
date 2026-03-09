# API-сервис сокращения ссылок на FastAPI

Проект реализует сервис сокращения ссылок с регистрацией пользователей, статистикой, кастомными alias, сроком жизни ссылки, Redis-кэшированием и Docker Compose.

## Выбранные внешние порты
Чтобы не конфликтовать с вашими существующими контейнерами, в проекте выставлены другие host-порты:

- **FastAPI**: `8088:8000`
- **PostgreSQL**: `5541:5432`
- **Redis**: `6385:6379`

Внутри docker-сети сервисы по-прежнему общаются на стандартных портах контейнеров.

## Запуск

```bash
cp .env.example .env
docker-compose up --build
```

Документация Swagger:

```text
http://localhost:8088/docs
```

## Основной функционал

### Обязательные функции
- `POST /links/shorten` — создать короткую ссылку
- `GET /{short_code}` — редирект на оригинальный URL
- `DELETE /links/{short_code}` — удалить ссылку
- `PUT /links/{short_code}` — изменить URL или alias
- `GET /links/{short_code}/stats` — статистика по ссылке
- `GET /links/search?original_url=...` — поиск по оригинальному URL
- `POST /links/shorten` с `custom_alias` — кастомная ссылка
- `POST /links/shorten` с `expires_at` — ссылка со сроком жизни

### Регистрация
- `POST /auth/register`
- `POST /auth/login`

Изменение и удаление доступны только владельцу ссылки.

### Дополнительные функции
- `GET /expired-links` — история истекших ссылок
- `DELETE /admin/cleanup-unused` — очистка старых неиспользуемых ссылок
- `POST /projects` и `GET /projects` — группировка по проектам

## Механизм сокращения ссылки

Используется генерация случайного короткого кода из букв и цифр. Если передан `custom_alias`, используется он после проверки уникальности.

Алгоритм:
1. Генерируется `short_code` длиной 7 символов.
2. Проверяется уникальность в PostgreSQL.
3. При коллизии код генерируется заново.
4. Сохраняется связь `short_code -> original_url`.

## Кэширование Redis

Кэшируются:
- переходы по короткому коду: `link:{short_code}`
- статистика: `stats:{short_code}`
- поиск по оригинальному URL: `search:{original_url}`

При обновлении или удалении ссылки связанный кэш очищается.

## Примеры запросов

### Регистрация
```bash
curl -X POST http://localhost:8088/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345678"}'
```

### Логин
```bash
curl -X POST http://localhost:8088/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"12345678"}'
```

### Создание ссылки
```bash
curl -X POST http://localhost:8088/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example.com/very/long/path"}'
```

### Создание кастомной ссылки
```bash
curl -X POST http://localhost:8088/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example.com","custom_alias":"my-link"}'
```

### Создание ссылки с истечением срока
```bash
curl -X POST http://localhost:8088/links/shorten \
  -H "Content-Type: application/json" \
  -d '{"original_url":"https://example.com","expires_at":"2026-01-10T15:30:00"}'
```

### Получение статистики
```bash
curl http://localhost:8088/links/my-link/stats
```

## Структура БД

### Таблица `users`
- `id`
- `email`
- `hashed_password`
- `created_at`

### Таблица `projects`
- `id`
- `name`
- `owner_id`
- `created_at`

### Таблица `links`
- `id`
- `short_code`
- `original_url`
- `click_count`
- `created_at`
- `last_accessed_at`
- `expires_at`
- `owner_id`
- `project_id`

### Таблица `expired_links`
- `id`
- `short_code`
- `original_url`
- `created_at`
- `expired_at`
- `last_accessed_at`
- `click_count`
