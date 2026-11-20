import os
import unittest
import json
import tempfile

# Configure a temporary database for test isolation
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.environ["ECOMMERCE_DB"] = temp_db_path

import app


class EcommerceCartApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.app.config['TESTING'] = True
        cls.client = app.app.test_client()

    def setUp(self):
        # Reset database state before each test
        app.initialize_database()
        self.client.post('/reset')

    @classmethod
    def tearDownClass(cls):
        os.close(temp_db_fd)
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

    # -------------------------------------------------------------
    # 1. Health & Product Catalog Tests
    # -------------------------------------------------------------
    def test_health_check(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "API is running successfully")

    def test_get_all_products(self):
        response = self.client.get('/products')
        self.assertEqual(response.status_code, 200)
        products = response.get_json()
        self.assertEqual(len(products), 5)
        self.assertEqual(products[0]["name"], "Laptop")

    def test_get_single_product_valid(self):
        response = self.client.get('/products/1')
        self.assertEqual(response.status_code, 200)
        product = response.get_json()
        self.assertEqual(product["id"], 1)
        self.assertEqual(product["name"], "Laptop")
        self.assertEqual(product["price"], 55000.0)
        self.assertEqual(product["stock"], 10)

    def test_get_single_product_not_found(self):
        response = self.client.get('/products/999')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["error"], "Product not found")

    # -------------------------------------------------------------
    # 2. Cart Operations Tests
    # -------------------------------------------------------------
    def test_add_to_cart_success(self):
        payload = {"product_id": 1, "quantity": 2}
        response = self.client.post('/cart', json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["product_id"], 1)
        self.assertEqual(data["quantity"], 2)

    def test_add_to_cart_accumulates(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 2})
        response = self.client.post('/cart', json={"product_id": 1, "quantity": 3})
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["quantity"], 5)

    def test_add_to_cart_insufficient_stock(self):
        payload = {"product_id": 1, "quantity": 100}
        response = self.client.post('/cart', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Insufficient stock")

    def test_add_to_cart_invalid_input(self):
        # Empty body
        response = self.client.post('/cart', json={})
        self.assertEqual(response.status_code, 400)

        # Negative quantity
        response = self.client.post('/cart', json={"product_id": 1, "quantity": -2})
        self.assertEqual(response.status_code, 400)

        # Non-existent product
        response = self.client.post('/cart', json={"product_id": 888, "quantity": 1})
        self.assertEqual(response.status_code, 404)

    def test_view_cart_calculations(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})  # 55000
        self.client.post('/cart', json={"product_id": 3, "quantity": 2})  # 1500 * 2 = 3000
        response = self.client.get('/cart')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["item_count"], 2)
        self.assertEqual(data["subtotal"], 58000.0)
        self.assertEqual(data["total"], 58000.0)

    def test_update_cart_quantity(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 2})
        response = self.client.put('/cart/1', json={"quantity": 4})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["quantity"], 4)

        cart = self.client.get('/cart').get_json()
        self.assertEqual(cart["items"][0]["quantity"], 4)
        self.assertEqual(cart["total"], 220000.0)

    def test_remove_single_item(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        response = self.client.delete('/cart/1')
        self.assertEqual(response.status_code, 200)

        cart = self.client.get('/cart').get_json()
        self.assertEqual(cart["item_count"], 0)

    def test_clear_entire_cart(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        self.client.post('/cart', json={"product_id": 2, "quantity": 1})
        response = self.client.delete('/cart')
        self.assertEqual(response.status_code, 200)

        cart = self.client.get('/cart').get_json()
        self.assertEqual(cart["item_count"], 0)
        self.assertEqual(cart["total"], 0.0)

    # -------------------------------------------------------------
    # 3. Discount Coupon Tests
    # -------------------------------------------------------------
    def test_get_coupons(self):
        response = self.client.get('/coupons')
        self.assertEqual(response.status_code, 200)
        coupons = response.get_json()
        self.assertGreaterEqual(len(coupons), 4)

    def test_apply_percentage_coupon_success(self):
        # Add 1 Laptop = 55000.0
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        response = self.client.post('/cart/apply-coupon', json={"code": "SAVE10"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["coupon_code"], "SAVE10")
        self.assertEqual(data["discount_amount"], 5500.0)  # 10% of 55000
        self.assertEqual(data["final_total"], 49500.0)     # 55000 - 5500

        # Verify GET /cart reflects discount
        cart = self.client.get('/cart').get_json()
        self.assertEqual(cart["applied_coupon"], "SAVE10")
        self.assertEqual(cart["discount_amount"], 5500.0)
        self.assertEqual(cart["total"], 49500.0)

    def test_apply_flat_coupon_success(self):
        # Add 1 Smartphone = 20000.0
        self.client.post('/cart', json={"product_id": 2, "quantity": 1})
        response = self.client.post('/cart/apply-coupon', json={"code": "FLAT500"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["coupon_code"], "FLAT500")
        self.assertEqual(data["discount_amount"], 500.0)
        self.assertEqual(data["final_total"], 19500.0)

    def test_apply_invalid_coupon(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        response = self.client.post('/cart/apply-coupon', json={"code": "NONEXISTENT"})
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertEqual(data["error"], "Coupon code not found")

    def test_apply_expired_coupon(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        response = self.client.post('/cart/apply-coupon', json={"code": "EXPIRED50"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Coupon code is expired or inactive")

    def test_apply_coupon_empty_cart(self):
        response = self.client.post('/cart/apply-coupon', json={"code": "SAVE10"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Cannot apply coupon to an empty cart")

    def test_apply_coupon_below_min_order_value(self):
        # Add 1 Mouse = 500.0 (below SAVE10 min_order_value of 1000)
        self.client.post('/cart', json={"product_id": 5, "quantity": 1})
        response = self.client.post('/cart/apply-coupon', json={"code": "SAVE10"})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("Minimum order value", data["error"])

    def test_remove_coupon(self):
        self.client.post('/cart', json={"product_id": 1, "quantity": 1})
        self.client.post('/cart/apply-coupon', json={"code": "SAVE10"})
        response = self.client.delete('/cart/coupon')
        self.assertEqual(response.status_code, 200)

        cart = self.client.get('/cart').get_json()
        self.assertIsNone(cart["applied_coupon"])
        self.assertEqual(cart["discount_amount"], 0.0)
        self.assertEqual(cart["total"], 55000.0)

    # -------------------------------------------------------------
    # 4. Checkout & Order Lifecycle Tests
    # -------------------------------------------------------------
    def test_checkout_empty_cart_fails(self):
        response = self.client.post('/cart/checkout')
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data["error"], "Cannot checkout an empty cart")

    def test_checkout_success_with_coupon(self):
        # Add 2 Smartphones (20000 * 2 = 40000)
        self.client.post('/cart', json={"product_id": 2, "quantity": 2})
        # Apply SAVE10 (10% off of 40000 = 4000 discount) -> total = 36000
        self.client.post('/cart/apply-coupon', json={"code": "SAVE10"})

        response = self.client.post('/cart/checkout')
        self.assertEqual(response.status_code, 201)

        order = response.get_json()
        self.assertEqual(order["status"], "CONFIRMED")
        self.assertEqual(order["subtotal"], 40000.0)
        self.assertEqual(order["applied_coupon"], "SAVE10")
        self.assertEqual(order["discount_amount"], 4000.0)
        self.assertEqual(order["total_amount"], 36000.0)

        # Cart should now be empty and coupon cleared
        cart = self.client.get('/cart').get_json()
        self.assertEqual(cart["item_count"], 0)
        self.assertIsNone(cart["applied_coupon"])

        # Smartphone stock should be 15 - 2 = 13
        product = self.client.get('/products/2').get_json()
        self.assertEqual(product["stock"], 13)


if __name__ == '__main__':
    unittest.main()
