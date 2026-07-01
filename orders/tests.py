from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from cart.models import Cart, CartItem
from marketplace.models import Category, Product

from .models import Order, OrderItem


User = get_user_model()


class OrderManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username="farmer",
            password="StrongPass123!",
            phone_number="9876543210",
            role=User.Role.FARMER,
        )
        cls.other_farmer = User.objects.create_user(
            username="other-farmer",
            password="StrongPass123!",
            phone_number="9876543211",
            role=User.Role.FARMER,
        )
        cls.buyer = User.objects.create_user(
            username="buyer",
            password="StrongPass123!",
            phone_number="9876543212",
            role=User.Role.BUYER,
        )
        cls.other_buyer = User.objects.create_user(
            username="other-buyer",
            password="StrongPass123!",
            phone_number="9876543213",
            role=User.Role.BUYER,
        )
        cls.category = Category.objects.create(name="Vegetables")
        cls.product = Product.objects.create(
            farmer=cls.farmer,
            category=cls.category,
            name="Tomato",
            description="Fresh tomatoes",
            price="40.00",
            quantity=3,
            location="Nashik",
        )
        cls.other_product = Product.objects.create(
            farmer=cls.other_farmer,
            category=cls.category,
            name="Potato",
            description="Farm potatoes",
            price="25.00",
            quantity=5,
            location="Pune",
        )

    def setUp(self):
        self.cart = Cart.objects.create(buyer=self.buyer)

    def add_cart_item(self, product=None, quantity=1):
        return CartItem.objects.create(
            cart=self.cart,
            product=product or self.product,
            quantity=quantity,
        )

    def checkout(self):
        self.client.force_login(self.buyer)
        return self.client.post(reverse("checkout"))

    def response_messages(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def create_order(self, buyer=None, product=None, farmer=None):
        product = product or self.product
        order = Order.objects.create(
            buyer=buyer or self.buyer,
            total_amount=product.price,
        )
        OrderItem.objects.create(
            order=order,
            product=product,
            farmer=farmer or product.farmer,
            quantity=1,
            price_at_purchase=product.price,
        )
        return order

    def test_checkout_creates_order_and_purchase_snapshot(self):
        self.add_cart_item(quantity=2)

        response = self.checkout()

        order = Order.objects.get(buyer=self.buyer)
        item = order.items.get()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.total_amount, Decimal("80.00"))
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.farmer, self.farmer)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price_at_purchase, Decimal("40.00"))
        self.assertRedirects(response, reverse("order_detail", args=[order.pk]))
        self.assertIn("Order placed successfully.", self.response_messages(response))

    def test_checkout_deducts_stock_and_marks_zero_stock_unavailable(self):
        self.add_cart_item(quantity=3)

        self.checkout()

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 0)
        self.assertFalse(self.product.is_available)

    def test_checkout_clears_cart(self):
        self.add_cart_item()

        self.checkout()

        self.assertFalse(CartItem.objects.filter(cart=self.cart).exists())
        self.assertTrue(Cart.objects.filter(pk=self.cart.pk).exists())

    def test_out_of_stock_prevents_entire_checkout(self):
        self.add_cart_item(quantity=2)
        self.product.quantity = 1
        self.product.save(update_fields=["quantity"])
        original_quantity = self.product.quantity

        response = self.checkout()

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, original_quantity)
        self.assertFalse(Order.objects.filter(buyer=self.buyer).exists())
        self.assertTrue(CartItem.objects.filter(cart=self.cart).exists())
        self.assertTrue(
            any("out of stock" in message for message in self.response_messages(response))
        )

    def test_checkout_is_atomic_when_order_item_creation_fails(self):
        self.add_cart_item(quantity=2)

        with patch(
            "orders.views.OrderItem.objects.bulk_create",
            side_effect=RuntimeError("simulated database failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.checkout()

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 3)
        self.assertFalse(Order.objects.filter(buyer=self.buyer).exists())
        self.assertTrue(CartItem.objects.filter(cart=self.cart).exists())

    def test_empty_cart_does_not_create_order(self):
        response = self.checkout()

        self.assertRedirects(response, reverse("cart_detail"))
        self.assertFalse(Order.objects.exists())
        self.assertIn("Your cart is empty.", self.response_messages(response))

    def test_farmer_cannot_checkout(self):
        self.client.force_login(self.farmer)

        response = self.client.post(reverse("checkout"))

        self.assertRedirects(response, reverse("product_list"))
        self.assertFalse(Order.objects.exists())

    def test_buyer_order_history_contains_only_own_orders(self):
        own_order = self.create_order()
        other_order = self.create_order(buyer=self.other_buyer)
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("my_orders"))

        self.assertContains(response, f"Order #{own_order.pk}")
        self.assertNotContains(response, f"Order #{other_order.pk}")

    def test_buyer_cannot_view_another_buyers_order(self):
        order = self.create_order(buyer=self.other_buyer)
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("order_detail", args=[order.pk]))

        self.assertEqual(response.status_code, 404)

    def test_farmer_sees_only_their_received_items(self):
        order = Order.objects.create(buyer=self.buyer, total_amount="65.00")
        OrderItem.objects.create(
            order=order,
            product=self.product,
            farmer=self.farmer,
            quantity=1,
            price_at_purchase="40.00",
        )
        OrderItem.objects.create(
            order=order,
            product=self.other_product,
            farmer=self.other_farmer,
            quantity=1,
            price_at_purchase="25.00",
        )
        self.client.force_login(self.farmer)

        response = self.client.get(reverse("orders_received"))

        self.assertContains(response, "Tomato")
        self.assertNotContains(response, "Potato")

    def test_deleting_purchased_product_preserves_order_history(self):
        order = self.create_order()

        self.product.delete()

        item = order.items.get()
        self.assertIsNone(item.product)
        self.client.force_login(self.buyer)
        response = self.client.get(reverse("order_detail", args=[order.pk]))
        self.assertContains(response, "Product no longer available")

    def test_buyer_cannot_access_farmer_received_orders(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("orders_received"))

        self.assertRedirects(response, reverse("product_list"))

    def test_farmer_cannot_access_buyer_order_history(self):
        self.client.force_login(self.farmer)

        response = self.client.get(reverse("my_orders"))

        self.assertRedirects(response, reverse("product_list"))

    def test_pending_order_can_be_cancelled_and_stock_is_restored(self):
        self.add_cart_item(quantity=2)
        self.checkout()
        order = Order.objects.get(buyer=self.buyer)
        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity, 1)

        response = self.client.post(reverse("cancel_order", args=[order.pk]))

        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.quantity, 3)
        self.assertTrue(self.product.is_available)
        self.assertIn("Order cancelled.", self.response_messages(response))

    def test_non_pending_order_cannot_be_cancelled(self):
        order = self.create_order()
        order.status = Order.Status.SHIPPED
        order.save(update_fields=["status"])
        self.client.force_login(self.buyer)

        response = self.client.post(reverse("cancel_order", args=[order.pk]))

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.SHIPPED)
        self.assertIn(
            "Only pending orders can be cancelled.",
            self.response_messages(response),
        )

    def test_checkout_and_cancel_require_post(self):
        order = self.create_order()
        self.client.force_login(self.buyer)

        self.assertEqual(self.client.get(reverse("checkout")).status_code, 405)
        self.assertEqual(
            self.client.get(reverse("cancel_order", args=[order.pk])).status_code,
            405,
        )
