# Деплой Master CRM на VPS

## Требования к серверу

- Ubuntu 22.04+ / Debian 12+
- 2 GB RAM, 1 ядро, 50 GB диск
- Домен, направленный на IP сервера (A-запись)
- SSH доступ (root или sudo)

## Шаг 1. Подготовка сервера

```bash
# Подключаемся по SSH
ssh root@YOUR_SERVER_IP

# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем Docker + Docker Compose
curl -fsSL https://get.docker.com | sh

# Проверяем
docker --version
    

# Устанавливаем git
apt install -y git

# Создаём пользователя (не работаем от root)
adduser deploy
usermod -aG docker deploy
su - deploy
```

## Шаг 2. Клонируем проект

```bash
# От пользователя deploy
cd ~
git clone YOUR_REPO_URL master_crm
cd master_crm
```

**Если репозиторий приватный:**
```bash
# Вариант A: SSH ключ
ssh-keygen -t ed25519 -C "deploy@mastercrm"
cat ~/.ssh/id_ed25519.pub
# Добавить в GitHub/GitLab → Settings → Deploy Keys

# Вариант B: HTTPS с токеном
git clone https://YOUR_TOKEN@github.com/YOUR_USER/master_crm.git
```

## Шаг 3. Настраиваем DNS

В панели управления доменом создай A-запись:

```
moiokoshki.ru  →  YOUR_SERVER_IP
```

Подожди 5-15 минут пока DNS обновится. Проверь:
```bash
ping moiokoshki.ru
```

## Шаг 4. Создаём .env файл

```bash
cd ~/master_crm

# Генерируем секреты
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from base64 import urlsafe_b64encode; from os import urandom; print(urlsafe_b64encode(urandom(32)).decode())" 2>/dev/null || openssl rand -base64 32)
DB_PASS=$(openssl rand -hex 16)
APP_USER_PASS=$(openssl rand -hex 16)

echo "Сохрани эти пароли в надёжное место:"
echo "DB_PASSWORD=$DB_PASS"
echo "APP_USER_PASSWORD=$APP_USER_PASS"
echo "JWT_SECRET_KEY=$JWT_SECRET"
echo "ENCRYPTION_KEY=$ENCRYPTION_KEY"
```

Создаём `.env`:
```bash
cat > .env << 'ENVEOF'
# === Core ===
DEBUG=false
DOMAIN=moiokoshki.ru

# === Database ===
DATABASE_URL=postgresql+asyncpg://mastercrm_owner:REPLACE_DB_PASS@db:5432/mastercrm
DATABASE_APP_URL=postgresql+asyncpg://app_user:REPLACE_APP_USER_PASS@db:5432/mastercrm
DB_ECHO=false
DB_PASSWORD=REPLACE_DB_PASS
APP_USER_PASSWORD=REPLACE_APP_USER_PASS

# === Auth ===
JWT_SECRET_KEY=REPLACE_JWT_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENCRYPTION_KEY=REPLACE_ENCRYPTION_KEY

# === CORS ===
ALLOWED_ORIGINS=["https://moiokoshki.ru"]

# === Telegram Bot ===
TG_BOT_TOKEN=
BASE_WEBHOOK_URL=https://moiokoshki.ru
MINI_APP_URL=https://moiokoshki.ru/app
WEB_ADMIN_URL=https://moiokoshki.ru/admin

# === MAX Messenger (заполнить позже) ===
MAX_BOT_TOKEN=
MAX_BOT_ACCESS_TOKEN=

# === VK (заполнить позже) ===
VK_APP_ID=
VK_APP_SECRET=
VK_BOT_TOKEN=
VK_CONFIRMATION_TOKEN=

# === Robokassa (заполнить позже) ===
ROBOKASSA_RESULT_URL=https://moiokoshki.ru/webhook/robokassa/result
ENVEOF
```

**ВАЖНО:** Замени все `REPLACE_*` на сгенерированные значения:
```bash
sed -i "s/REPLACE_DB_PASS/$DB_PASS/g" .env
sed -i "s/REPLACE_APP_USER_PASS/$APP_USER_PASS/g" .env
sed -i "s/REPLACE_JWT_SECRET/$JWT_SECRET/g" .env
sed -i "s/REPLACE_ENCRYPTION_KEY/$ENCRYPTION_KEY/g" .env
sed -i "s/moiokoshki.ru/ТВОЙ_ДОМЕН/g" .env
```

## Шаг 5. Правим init-db.sql под продакшн пароль

```bash
# Пароль app_user должен совпадать с APP_USER_PASSWORD из .env
sed -i "s/appuserpassword/$APP_USER_PASS/g" backend/scripts/init-db.sql
```

## Шаг 6. Оптимизация под 2GB RAM

На 2GB сервере с 1 ядром нужно снизить потребление:

```bash
# Меняем workers с 4 на 2 (1 ядро = 2 workers максимум)
sed -i 's/--workers 4/--workers 2/g' docker-compose.yml

# Убираем проброс портов для внутренних сервисов (только Caddy слушает 80/443)
# Это также безопаснее — PostgreSQL не торчит наружу
```

Или вручную отредактируй `docker-compose.yml` — убери `ports:` у api, frontend, web, db (оставь только у caddy):

```yaml
services:
  api:
    # убери строки:
    # ports:
    #   - "8000:8000"

  frontend:
    # убери строки:
    # ports:
    #   - "3000:3000"

  db:
    # убери строки:
    # ports:
    #   - "5432:5432"

  web:
    # убери строки:
    # ports:
    #   - "3001:3001"

  caddy:
    ports:
      - "80:80"     # ← только Caddy слушает снаружи
      - "443:443"
```

## Шаг 7. Добавляем swap (обязательно для 2GB)

```bash
# Возвращаемся в root
exit  # или sudo

# Создаём 2GB swap
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Делаем постоянным
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Проверяем
free -h
# Должно показать 2GB RAM + 2GB swap
```

## Шаг 8. Запускаем

```bash
su - deploy
cd ~/master_crm

# Собираем образы (первый раз долго, ~5-10 минут)
docker compose build

# Запускаем
docker compose up -d

# Смотрим логи
docker compose logs -f

# Ждём пока всё поднимется (30-60 секунд)
# Caddy автоматически получит TLS сертификат от Let's Encrypt
```

## Шаг 9. Проверяем

```bash
# Проверяем все контейнеры запущены
docker compose ps

# Ожидаемый результат:
# api        running (healthy)
# frontend   running (healthy)
# web        running (healthy)
# db         running (healthy)
# caddy      running

# Проверяем API
curl https://moiokoshki.ru/api/v1/health
# Ответ: {"status":"ok","version":"0.1.0"}

# Проверяем мини-апп
curl -I https://moiokoshki.ru/app/
# Ответ: 200 OK

# Проверяем админку
curl -I https://moiokoshki.ru/admin/
# Ответ: 200 OK
```

## Шаг 10. Создаём мастера через API

```bash
# Регистрация первого мастера
curl -X POST https://moiokoshki.ru/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "master@example.com",
    "password": "YourSecurePassword123",
    "name": "Имя Мастера",
    "phone": "+79161234567",
    "business_name": "Студия красоты",
    "timezone": "Europe/Moscow"
  }'

# Ответ содержит access_token — можно войти в админку
```

## Шаг 11. Настраиваем Telegram бота

### 11.1 Создай бота в @BotFather

```
/newbot
→ Название: Master CRM
→ Username: mastercrm_bot (или свой)
```

Скопируй токен.

### 11.2 Создай Mini App

```
/newapp (в @BotFather)
→ Выбери бота: @mastercrm_bot
→ URL: https://moiokoshki.ru/app
→ Short name: booking
```

### 11.3 Обнови .env

```bash
cd ~/master_crm
nano .env

# Заполни:
TG_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
```

### 11.4 Перезапусти

```bash
docker compose restart api
```

### 11.5 Проверь webhook

```bash
# Webhook регистрируется автоматически при старте
docker compose logs api | grep -i webhook
# Должно быть: "Telegram webhook set successfully"
```

## Шаг 12. Тестируем полный flow

1. Открой бота в Telegram → `/start`
2. Бот пришлёт приветствие и кнопку "Открыть"
3. Нажми "Открыть" → откроется мини-апп
4. Войди в админку: `https://moiokoshki.ru/admin/`
5. Создай услугу → создай расписание
6. Открой мини-апп как клиент → запишись

---

## Полезные команды

```bash
# Логи конкретного сервиса
docker compose logs -f api
docker compose logs -f caddy

# Перезапуск после изменения .env
docker compose restart

# Пересборка после изменения кода
git pull
docker compose build
docker compose up -d

# Бэкап базы данных
docker compose exec db pg_dump -U mastercrm_owner mastercrm > backup_$(date +%Y%m%d).sql

# Восстановление из бэкапа
cat backup_20260319.sql | docker compose exec -T db psql -U mastercrm_owner mastercrm

# Статус и потребление ресурсов
docker stats --no-stream

# Миграции (запускаются автоматически, но можно вручную)
docker compose exec api uv run alembic upgrade head
```

## Troubleshooting

### Caddy не получает сертификат
```bash
# Проверь DNS
dig moiokoshki.ru
# Должен показать IP твоего сервера

# Проверь что порты 80 и 443 открыты
# В панели хостера → Firewall → разрешить 80, 443

# Логи Caddy
docker compose logs caddy
```

### API не стартует
```bash
docker compose logs api
# Частые причины:
# - Неверный DATABASE_URL в .env (проверь пароли)
# - PostgreSQL ещё не готов (подожди 30с, перезапусти)
# - Ошибка миграции (проверь alembic логи)
```

### Мало памяти
```bash
free -h
docker stats --no-stream

# Если OOM killer убивает контейнеры:
# 1. Убедись что swap создан (Шаг 7)
# 2. Уменьши workers до 1: sed -i 's/--workers 2/--workers 1/g' docker-compose.yml
# 3. docker compose up -d
```

### PostgreSQL — "role app_user already exists"
```bash
# Это нормально — init-db.sql проверяет IF NOT EXISTS
# Ошибка в логах db — можно игнорировать
```

---

## Обновление

```bash
cd ~/master_crm
git pull origin main
docker compose build
docker compose up -d
# Миграции применятся автоматически при старте api
```
