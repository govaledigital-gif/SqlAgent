import unittest
from app.infrastructure.inventory_repository import InventoryRepository
from app.config.settings import settings
from sqlalchemy import text


class ExecuteSafeSelectTests(unittest.TestCase):
    def setUp(self):
        # Use in-memory SQLite for tests
        self._orig_db = settings.DATABASE_URL
        settings.DATABASE_URL = "sqlite:///:memory:"
        # Recreate repository which will create tables
        self.repo = InventoryRepository()
        # create a simple table for testing
        with self.repo.session_scope() as session:
            session.execute(text("CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, name TEXT, company_id TEXT)"))
            session.execute(text("INSERT INTO products (id, sku, name, company_id) VALUES ('p1','S1','Widget','comp1')"))

    def tearDown(self):
        settings.DATABASE_URL = self._orig_db

    def test_simple_select_returns_rows(self):
        rows = self.repo.execute_safe_select('comp1', "SELECT id, name FROM products")
        self.assertTrue(isinstance(rows, list))
        self.assertGreater(len(rows), 0)

    def test_rejects_union_and_comments(self):
        with self.assertRaises(ValueError):
            self.repo.execute_safe_select('comp1', "SELECT id FROM products UNION SELECT id FROM products")

        with self.assertRaises(ValueError):
            self.repo.execute_safe_select('comp1', "SELECT id FROM products -- comment")

    def test_parameterization_of_literals(self):
        # Query with literal should be parameterized and return the row
        rows = self.repo.execute_safe_select('comp1', "SELECT id, name FROM products WHERE name = 'Widget'")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['name'], 'Widget')


if __name__ == '__main__':
    unittest.main()
