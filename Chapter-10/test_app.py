import os
from my_app import create_app, db, babel
import unittest
from unittest import mock
import tempfile
import geoip2.records
import coverage

cov = coverage.coverage(
    omit = [
        '/Users/shalabh.aggarwal/workspace/cookbook10/lib/python3.6/site-packages/*',
        'app_tests.py'
    ]
)
cov.start()


class CatalogTestCase(unittest.TestCase):

    def setUp(self):
        test_config = {}
        self.test_db_file = tempfile.mkstemp()[1]

        test_config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + self.test_db_file
        test_config['TESTING'] = True
        test_config['WTF_CSRF_ENABLED'] = False

        self.app = create_app(test_config)
        db.init_app(self.app)
        babel.init_app(self.app)

        self.geoip_city_patcher = mock.patch('geoip2.models.City',
            location=geoip2.records.Location(time_zone = 'America/Los_Angeles')
        )
        PatchedGeoipCity = self.geoip_city_patcher.start()
        self.geoip_reader_patcher = mock.patch('geoip2.database.Reader')
        PatchedGeoipReader = self.geoip_reader_patcher.start()
        PatchedGeoipReader().city.return_value = PatchedGeoipCity

        with self.app.app_context():
            db.create_all()

        from my_app.catalog.views import catalog
        self.app.register_blueprint(catalog)

        self.client = self.app.test_client()

    def tearDown(self):
        self.geoip_city_patcher.stop()
        self.geoip_reader_patcher.stop()
        os.remove(self.test_db_file)

    def test_home(self):
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)

    def test_products(self):
        "Test Products list page"
        rv = self.client.get('/en/products')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('No Previous Page' in rv.data.decode("utf-8"))
        self.assertTrue('No Next Page' in rv.data.decode("utf-8"))

    def test_create_category(self):
        "Test creation of new category"
        rv = self.client.get('/en/category-create')
        self.assertEqual(rv.status_code, 200)

        rv = self.client.post('/en/category-create')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('This field is required.' in rv.data.decode("utf-8"))

        rv = self.client.get('/en/categories')
        self.assertEqual(rv.status_code, 200)
        self.assertFalse('Phones' in rv.data.decode("utf-8"))

        rv = self.client.post('/en/category-create', data={
            'name': 'Phones',
        })
        self.assertEqual(rv.status_code, 302)

        rv = self.client.get('/en/categories')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('Phones' in rv.data.decode("utf-8"))

        rv = self.client.get('/en/category/1')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('Phones' in rv.data.decode("utf-8"))

    def test_create_product(self):
        "Test creation of new product"
        rv = self.client.get('/en/product-create')
        self.assertEqual(rv.status_code, 200)

        # Raise a ValueError for a valid category not found
        self.assertRaises(ValueError, self.client.post, '/en/product-create')

        # Create a category to be used in product creation
        rv = self.client.post('/en/category-create', data={
            'name': 'Phones',
        })
        self.assertEqual(rv.status_code, 302)

        rv = self.client.post('/en/product-create', data={
            'name': 'iPhone 5',
            'price': 549.49,
            'company': 'Apple',
            'category': 1,
            'image': tempfile.NamedTemporaryFile()
        })
        self.assertEqual(rv.status_code, 302)

        rv = self.client.get('/en/product/1')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('iPhone 5' in rv.data.decode("utf-8"))
        self.assertTrue('America/Los_Angeles' in rv.data.decode("utf-8"))

    def test_search_product(self):
        "Test searching product"
        # Create a category to be used in product creation
        rv = self.client.post('/en/category-create', data={
            'name': 'Phones',
        })
        self.assertEqual(rv.status_code, 302)

        # Create a product
        rv = self.client.post('/en/product-create', data={
            'name': 'iPhone 5',
            'price': 549.49,
            'company': 'Apple',
            'category': 1,
            'image': tempfile.NamedTemporaryFile()
        })
        self.assertEqual(rv.status_code, 302)

        # Create another product
        rv = self.client.post('/en/product-create', data={
            'name': 'Galaxy S5',
            'price': 549.49,
            'company': 'Samsung',
            'category': 1,
            'image': tempfile.NamedTemporaryFile()
        })
        self.assertEqual(rv.status_code, 302)

        self.client.get('/')

        rv = self.client.get('/en/product-search?name=iPhone')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('iPhone 5' in rv.data.decode("utf-8"))
        self.assertFalse('Galaxy S5' in rv.data.decode("utf-8"))

        rv = self.client.get('/en/product-search?name=iPhone 6')
        self.assertEqual(rv.status_code, 200)
        self.assertFalse('iPhone 6' in rv.data.decode("utf-8"))


if __name__ == '__main__':
    try:
        unittest.main()
    finally:
        cov.stop()
        cov.save()
        cov.report()
        cov.html_report(directory = 'coverage')
        cov.erase()
