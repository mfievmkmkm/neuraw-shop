import hashlib
import hmac
import json
import tempfile
import time
import unittest
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


if __name__ == '__main__':
    unittest.main()
