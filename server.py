"""NEURAW shop: Telegram Mini App, order API and small admin bot (stdlib only)."""
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import sqlite3
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
TOKEN = os.environ.get('SHOP_BOT_TOKEN', '')
ADMIN_ID = int(os.environ.get('SHOP_ADMIN_ID', '0'))
WEBAPP_URL = os.environ.get('SHOP_WEBAPP_URL', '')
DB_PATH = Path(os.environ.get('SHOP_DB_PATH', 'shop.sqlite3'))
SERVICES = {'cover': 'Кликабельная обложка', 'song': 'Песня-поздравление',
            'photo': 'AI-фотосессия', 'motion': 'Оживление фото',
            'video': 'Рекламный ролик', 'custom': 'Индивидуальный проект'}
STATUSES = {'new': 'Новая', 'progress': 'В работе', 'ready': 'Готово', 'cancelled': 'Отменена'}


def validate_init_data(raw, token, now=None):
    if not raw or len(raw) > 8192:
        raise ValueError('Откройте магазин через Telegram.')
    pairs = parse_qsl(raw, keep_blank_values=True, strict_parsing=True)
    data = dict(pairs)
    if len(pairs) != len(data) or 'hash' not in data:
        raise ValueError('Некорректная авторизация.')
    provided = data.pop('hash')
    secret = hmac.new(b'WebAppData', token.encode(), hashlib.sha256).digest()
    check = '\n'.join(f'{k}={v}' for k, v in sorted(data.items()))
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided, expected):
        raise ValueError('Не удалось подтвердить вход в Telegram.')
    age = int(now or time.time()) - int(data.get('auth_date', '0'))
    if age < -60 or age > 86400:
        raise ValueError('Сессия устарела. Откройте магазин заново.')
    user = json.loads(data.get('user', '{}'))
    if not isinstance(user.get('id'), int) or user['id'] <= 0:
        raise ValueError('Не найден Telegram ID.')
    return user


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS orders (
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          username TEXT NOT NULL, service TEXT NOT NULL, brief TEXT NOT NULL,
          deadline TEXT NOT NULL, request_id TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new',
          created_at INTEGER NOT NULL, UNIQUE(user_id, request_id))''')


def create_order(user, data):
    service = data.get('service')
    brief = str(data.get('brief', '')).strip()
    deadline = str(data.get('deadline', '')).strip()
    request_id = str(data.get('request_id', ''))
    if service not in SERVICES or not 10 <= len(brief) <= 3000 or len(deadline) > 120:
        raise ValueError('Проверьте услугу, описание и срок (от 10 до 3000 символов).')
    if not 8 <= len(request_id) <= 80 or not all(c.isalnum() or c in '-_' for c in request_id):
        raise ValueError('Некорректный ID заявки.')
    with connect() as db:
        cursor = db.execute('''INSERT OR IGNORE INTO orders
          (user_id, username, service, brief, deadline, request_id, created_at)
          VALUES (?, ?, ?, ?, ?, ?, ?)''', (user['id'], user.get('username', ''),
                                      service, brief, deadline, request_id, int(time.time())))
        row = db.execute('SELECT * FROM orders WHERE user_id=? AND request_id=?',
                         (user['id'], request_id)).fetchone()
        return dict(row), cursor.rowcount == 1


def telegram(method, payload):
    req = Request(f'https://api.telegram.org/bot{TOKEN}/{method}',
                  data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=20) as response:
        result = json.load(response)
    if not result.get('ok'):
        raise RuntimeError(f'Telegram {method} failed')
    return result['result']


def notify_admin(row):
    message = (f"NEURAW · заявка #{row['id']}\n{SERVICES[row['service']]}\n"
               f"Клиент: {row['user_id']} @{row['username']}\n"
               f"Срок: {row['deadline'] or 'не указан'}\n\n{row['brief']}")
    telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': message[:4000],
             'reply_markup': {'inline_keyboard': [[
                 {'text': 'В работу', 'callback_data': f"status:{row['id']}:progress"},
                 {'text': 'Готово', 'callback_data': f"status:{row['id']}:ready"}],
                 [{'text': 'Отменить', 'callback_data': f"status:{row['id']}:cancelled"}]]}})


def process_update(update):
    msg = update.get('message', {})
    if msg.get('text', '').startswith('/start'):
        payload = {'chat_id': msg['chat']['id'], 'text': 'NEURAW · цифровая студия\nВыбери услугу и оставь бриф.'}
        if WEBAPP_URL.startswith('https://'):
            payload['reply_markup'] = {'inline_keyboard': [[{'text': 'Открыть магазин ↗',
                                                             'web_app': {'url': WEBAPP_URL}}]]}
        telegram('sendMessage', payload)
    elif msg.get('text', '').startswith('/my'):
        with connect() as db:
            rows = db.execute('SELECT * FROM orders WHERE user_id=? ORDER BY id DESC LIMIT 10',
                              (msg['from']['id'],)).fetchall()
        text = '\n'.join(f"#{r['id']} · {SERVICES[r['service']]} · {STATUSES[r['status']]}" for r in rows)
        telegram('sendMessage', {'chat_id': msg['chat']['id'], 'text': text or 'Заявок пока нет.'})
    elif msg and msg.get('from', {}).get('id') == ADMIN_ID and msg.get('text', '').startswith('/orders'):
        with connect() as db:
            rows = db.execute('SELECT * FROM orders ORDER BY id DESC LIMIT 15').fetchall()
        text = '\n'.join(f"#{r['id']} · {SERVICES[r['service']]} · {STATUSES[r['status']]} · {r['user_id']}" for r in rows)
        telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': text or 'Заказов пока нет.'})
    elif msg and msg.get('from', {}).get('id') == ADMIN_ID and msg.get('text', '').startswith(('/quote ', '/reply ')):
        parts = msg['text'].split(maxsplit=2)
        if len(parts) != 3 or not parts[1].isdigit() or not 1 <= len(parts[2]) <= 2500:
            telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': 'Формат: /quote 12 цена, срок и условия или /reply 12 сообщение'})
        else:
            with connect() as db:
                row = db.execute('SELECT * FROM orders WHERE id=?', (int(parts[1]),)).fetchone()
            if not row:
                telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': 'Заявка не найдена.'})
            else:
                title = 'Предложение по заказу' if parts[0] == '/quote' else 'Сообщение по заказу'
                telegram('sendMessage', {'chat_id': row['user_id'],
                    'text': f"NEURAW · {title} #{row['id']}\n\n{parts[2]}\n\nОтветьте в этом чате. Для отправки файла добавьте подпись #{row['id']}."})
                telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': f"Сообщение по заявке #{row['id']} отправлено."})
    elif msg and (msg.get('photo') or msg.get('document') or msg.get('video') or msg.get('audio')):
        import re
        caption = msg.get('caption', '')
        delivery = re.fullmatch(r'/deliver\s+(\d{1,10})', caption.strip()) if msg['from']['id'] == ADMIN_ID else None
        if delivery:
            with connect() as db:
                row = db.execute('SELECT * FROM orders WHERE id=?', (int(delivery.group(1)),)).fetchone()
            if row:
                telegram('copyMessage', {'chat_id': row['user_id'], 'from_chat_id': msg['chat']['id'],
                                         'message_id': msg['message_id'],
                                         'caption': f"NEURAW · результат по заявке #{row['id']}"})
                telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': f"Файл доставлен по заявке #{row['id']}."})
            else:
                telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': 'Заявка не найдена.'})
            return
        match = re.search(r'(?<!\w)#(\d{1,10})\b', caption)
        if not match:
            telegram('sendMessage', {'chat_id': msg['chat']['id'],
                                    'text': 'Чтобы прикрепить файл к заказу, добавьте в подпись его номер, например #12.'})
        else:
            with connect() as db:
                row = db.execute('SELECT * FROM orders WHERE id=? AND user_id=?',
                                 (int(match.group(1)), msg['from']['id'])).fetchone()
            if row:
                telegram('sendMessage', {'chat_id': ADMIN_ID, 'text': f"Материалы к заявке #{row['id']} от {row['user_id']}:"})
                telegram('forwardMessage', {'chat_id': ADMIN_ID, 'from_chat_id': msg['chat']['id'],
                                            'message_id': msg['message_id']})
                telegram('sendMessage', {'chat_id': msg['chat']['id'], 'text': f"Файл для заявки #{row['id']} получен."})
            else:
                telegram('sendMessage', {'chat_id': msg['chat']['id'], 'text': 'Заявка с таким номером не найдена.'})
    elif msg and msg.get('text', '').strip().startswith('#') and msg.get('from', {}).get('id') != ADMIN_ID:
        import re
        match = re.match(r'#(\d{1,10})\s+(.+)', msg['text'], re.S)
        if match:
            with connect() as db:
                row = db.execute('SELECT * FROM orders WHERE id=? AND user_id=?',
                                 (int(match.group(1)), msg['from']['id'])).fetchone()
            if row:
                telegram('sendMessage', {'chat_id': ADMIN_ID,
                                         'text': f"Ответ клиента по заявке #{row['id']}:\n{match.group(2)[:3000]}"})
                telegram('sendMessage', {'chat_id': msg['chat']['id'], 'text': 'Ответ передан студии.'})
    callback = update.get('callback_query')
    if callback and callback.get('data', '').startswith('status:'):
        try:
            _, oid, status = callback['data'].split(':')
            if callback['from']['id'] != ADMIN_ID or status not in STATUSES or status == 'new':
                raise ValueError('Нет доступа')
            with connect() as db:
                db.execute('UPDATE orders SET status=? WHERE id=?', (status, int(oid)))
                row = db.execute('SELECT * FROM orders WHERE id=?', (int(oid),)).fetchone()
            if not row:
                raise ValueError('Заявка не найдена')
            telegram('answerCallbackQuery', {'callback_query_id': callback['id'], 'text': STATUSES[status]})
            telegram('sendMessage', {'chat_id': row['user_id'],
                                     'text': f"NEURAW · заявка #{oid}: {STATUSES[status].lower()}."})
        except (ValueError, KeyError) as exc:
            telegram('answerCallbackQuery', {'callback_query_id': callback['id'], 'text': str(exc)[:180],
                                             'show_alert': True})


def poll_bot():
    offset = None
    while True:
        try:
            result = telegram('getUpdates', {'timeout': 25, 'offset': offset,
                                             'allowed_updates': ['message', 'callback_query']})
            for update in result:
                offset = update['update_id'] + 1
                try:
                    process_update(update)
                except Exception:
                    logging.exception('Update failed')
        except Exception:
            logging.exception('Polling failed; retrying')
            time.sleep(5)


class Handler(BaseHTTPRequestHandler):
    def respond(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self):
        if self.path != '/api/orders':
            return self.respond(404, {'error': 'Не найдено'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 12000:
                return self.respond(413, {'error': 'Слишком большой запрос'})
            data = json.loads(self.rfile.read(size))
            user = validate_init_data(data.get('init_data'), TOKEN)
            row, created = create_order(user, data)
            if created:
                try:
                    notify_admin(row)
                except Exception:
                    logging.exception('Admin notification failed for order %s', row['id'])
            self.respond(201 if created else 200, {'id': row['id'], 'status': row['status']})
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            self.respond(400, {'error': str(exc)})
        except Exception:
            logging.exception('Order failed')
            self.respond(500, {'error': 'Не удалось сохранить заявку. Попробуйте снова.'})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health':
            return self.respond(200, {'ok': True})
        if path == '/api/orders':
            try:
                from urllib.parse import parse_qs
                raw = parse_qs(urlparse(self.path).query).get('init_data', [''])[0]
                user = validate_init_data(raw, TOKEN)
                with connect() as db:
                    rows = db.execute('SELECT id, service, status, created_at FROM orders WHERE user_id=? '
                                      'ORDER BY id DESC LIMIT 20', (user['id'],)).fetchall()
                return self.respond(200, {'orders': [dict(row) for row in rows]})
            except (ValueError, TypeError, KeyError) as exc:
                return self.respond(400, {'error': str(exc)})
        rel = 'index.html' if path == '/' else path.lstrip('/')
        target = (ROOT / rel).resolve()
        if not target.is_relative_to(ROOT) or not target.is_file() or not (rel == 'index.html' or rel.startswith('assets/')):
            return self.send_error(404)
        import mimetypes
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(target.name)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(target.stat().st_size))
        self.end_headers()
        with target.open('rb') as file:
            while chunk := file.read(65536):
                self.wfile.write(chunk)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    if not TOKEN or not ADMIN_ID or not WEBAPP_URL.startswith('https://'):
        raise SystemExit('Set SHOP_BOT_TOKEN, SHOP_ADMIN_ID, and HTTPS SHOP_WEBAPP_URL')
    init_db()
    threading.Thread(target=poll_bot, daemon=True).start()
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('PORT', '8080'))), Handler).serve_forever()
