import unittest
from decimal import Decimal
from unittest.mock import Mock, patch
from django.test import RequestFactory
from .cart import Cart
from store.models import Product

class CartTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_cart_initialization(self):
        request = self.factory.get('/')
        cart = Cart(request)

        self.assertEqual(len(cart), 0)
        self.assertEqual(cart.get_subtotal_price(), Decimal('0'))

    def test_add_product(self):
        request = self.factory.get('/')
        cart = Cart(request)

        product = Mock(spec=Product)
        product.price = Decimal('9.99')

        cart.add(product)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_subtotal_price(), Decimal('9.99'))

        cart.add(product, quantity=2)
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart.get_subtotal_price(), Decimal('29.97'))

    def test_save_cart(self):
        request = self.factory.get('/')
        cart = Cart(request)
        cart.save()

        self.assertTrue(cart.session.modified)

    def test_remove_product(self):
        request = self.factory.get('/')
        cart = Cart(request)

        product = Mock(spec=Product)
        cart.add(product)

        self.assertEqual(len(cart), 1)
        cart.remove(product)
        self.assertEqual(len(cart), 0)

    def test_get_cart_products(self):
        request = self.factory.get('/')
        cart = Cart(request)

        product1 = Mock(spec=Product)
        product2 = Mock(spec=Product)

        cart.add(product1)
        cart.add(product2)

        cart_products = cart.get_cart_products()

        self.assertEqual(len(cart_products), 2)
        self.assertIn(product1, cart_products)
        self.assertIn(product2, cart_products)

    def test_get_subtotal_price(self):
        request = self.factory.get('/')
        cart = Cart(request)

        product1 = Mock(spec=Product)
        product1.price = Decimal('9.99')

        product2 = Mock(spec=Product)
        product2.price = Decimal('19.99')

        cart.add(product1)
        cart.add(product2, quantity=2)

        subtotal_price = cart.get_subtotal_price()

        self.assertEqual(subtotal_price, Decimal('49.97'))

    def test_get_shipping_cost(self):
        request = self.factory.get('/')
        cart = Cart(request)

        # Mocking the get_shipping_cost method
        expected_shipping_cost = Decimal('10.00')
        with patch.object(cart, 'get_shipping_cost', return_value=expected_shipping_cost):
            shipping_cost = cart.get_shipping_cost()

        self.assertEqual(shipping_cost, expected_shipping_cost)

    def test_cart_iteration(self):
        request = self.factory.get('/')
        cart = Cart(request)

        product1 = Mock(spec=Product)
        product1.title = 'Product 1'
        product1.price = Decimal('9.99')

        product2 = Mock(spec=Product)
        product2.title = 'Product 2'
        product2.price = Decimal('19.99')

        cart.add(product1)
        cart.add(product2, quantity=2)

        cart_items = list(cart)

        self.assertEqual(len(cart_items), 2)
        self.assertEqual(cart_items[0]['product'], product1)
        self.assertEqual(cart_items[0]['quantity'], 1)
        self.assertEqual(cart_items[0]['price'], Decimal('9.99'))
        self.assertEqual(cart_items[0]['total_price'], Decimal('9.99'))

        self.assertEqual(cart_items[1]['product'], product2)
        self.assertEqual(cart_items[1]['quantity'], 2)
        self.assertEqual(cart_items[1]['price'], Decimal('19.99'))
        self.assertEqual(cart_items[1]['total_price'], Decimal('39.98'))

if __name__ == '__main__':
    unittest.main()
