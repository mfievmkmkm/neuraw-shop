import hashlib
import hmac
import json
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.parse import urlencode

import server


def signed(user_id=42, timestamp=None):
    fields = {'auth_date': str(timestamp or int(time.time())),
              'user': json.dumps({'id': user_id, 'username': 'buyer'}, separators=(',', ':'))}
    secret = hmac.new(b'WebAppData', b'test-token', hashlib.sha256).digest()
    check = '\n'.join(f'{k}={v}' for k, v in sorted(fields.items()))
    fields['hash'] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


class ShopTests(unittest.TestCase):
    def test_telegram_signature_and_expiry(self):
        self.assertEqual(server.validate_init_data(signed(), 'test-token')['id'], 42)
        with self.assertRaises(ValueError):
            server.validate_init_data(signed().replace('buyer', 'attacker'), 'test-token')
        with self.assertRaises(ValueError):
            server.validate_init_data(signed(timestamp=int(time.time()) - 90000), 'test-token')

    def test_order_persistence_and_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            original = server.DB_PATH
            server.DB_PATH = Path(folder) / 'shop.sqlite3'
            try:
                server.init_db()
                user = server.validate_init_data(signed(), 'test-token')
                data = {'service': 'cover', 'brief': 'Нужна обложка в ярких цветах',
                        'deadline': 'на неделе', 'request_id': 'retry-12345'}
                first, created = server.create_order(user, data)
                second, created_again = server.create_order(user, data)
                self.assertTrue(created)
                self.assertFalse(created_again)
                self.assertEqual(first['id'], second['id'])
                self.assertEqual(first['status'], 'new')
            finally:
                server.DB_PATH = original

    def test_admin_delivery_requires_existing_order(self):
        with tempfile.TemporaryDirectory() as folder:
            original_db, original_admin = server.DB_PATH, server.ADMIN_ID
            server.DB_PATH, server.ADMIN_ID = Path(folder) / 'shop.sqlite3', 99
            try:
                server.init_db()
                row, _ = server.create_order({'id': 42, 'username': 'buyer'},
                    {'service': 'cover', 'brief': 'Обложка с цветком и заголовком',
                     'deadline': '', 'request_id': 'delivery-123'})
                update = {'message': {'from': {'id': 99}, 'chat': {'id': 99},
                                      'message_id': 7, 'document': {'file_id': 'abc'},
                                      'caption': f"/deliver {row['id']}"}}
                with patch.object(server, 'telegram') as send:
                    server.process_update(update)
                self.assertEqual(send.call_args_list[0].args[0], 'copyMessage')
                self.assertEqual(send.call_args_list[0].args[1]['chat_id'], 42)
            finally:
                server.DB_PATH, server.ADMIN_ID = original_db, original_admin


if __name__ == '__main__':
    unittest.main()
