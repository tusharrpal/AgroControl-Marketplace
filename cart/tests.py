from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from marketplace.models import Category, Product

from .models import Cart, CartItem


User = get_user_model()


class CartViewTests(TestCase):
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
            quantity=2,
            location="Nashik",
        )

    def messages_for(self, response):
        return [str(message) for message in get_messages(response.wsgi_request)]

    def add_product(self):
        return self.client.post(reverse("add_to_cart", args=[self.product.pk]))

    def test_cart_requires_login(self):
        response = self.client.get(reverse("cart_detail"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('cart_detail')}",
        )

    def test_buyer_can_add_product(self):
        self.client.force_login(self.buyer)

        response = self.add_product()

        item = CartItem.objects.get(cart__buyer=self.buyer, product=self.product)
        self.assertEqual(item.quantity, 1)
        self.assertRedirects(response, reverse("cart_detail"))
        self.assertIn("Added to cart.", self.messages_for(response))

    def test_adding_existing_product_increases_quantity(self):
        self.client.force_login(self.buyer)
        self.add_product()

        self.add_product()

        item = CartItem.objects.get(cart__buyer=self.buyer, product=self.product)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_buyer_cannot_exceed_available_stock(self):
        self.client.force_login(self.buyer)
        self.add_product()
        self.add_product()

        response = self.add_product()

        item = CartItem.objects.get(cart__buyer=self.buyer, product=self.product)
        self.assertEqual(item.quantity, 2)
        self.assertIn(
            "Requested quantity exceeds available stock.",
            self.messages_for(response),
        )

    def test_farmer_cannot_access_or_add_to_cart(self):
        self.client.force_login(self.farmer)

        cart_response = self.client.get(reverse("cart_detail"))
        add_response = self.add_product()

        self.assertRedirects(cart_response, reverse("product_list"))
        self.assertRedirects(add_response, reverse("product_list"))
        self.assertFalse(Cart.objects.filter(buyer=self.farmer).exists())

    def test_buyer_cannot_add_own_product(self):
        own_product = Product.objects.create(
            farmer=self.buyer,
            category=self.category,
            name="Own Crop",
            description="A product assigned to this buyer",
            price="10.00",
            quantity=4,
            location="Pune",
        )
        self.client.force_login(self.buyer)

        response = self.client.post(reverse("add_to_cart", args=[own_product.pk]))

        self.assertFalse(CartItem.objects.filter(product=own_product).exists())
        self.assertIn(
            "You cannot add your own product to the cart.",
            self.messages_for(response),
        )

    def test_buyer_can_remove_item(self):
        self.client.force_login(self.buyer)
        self.add_product()
        item = CartItem.objects.get(cart__buyer=self.buyer)

        response = self.client.post(reverse("remove_cart_item", args=[item.pk]))

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())
        self.assertIn("Removed from cart.", self.messages_for(response))

    def test_buyer_can_increase_and_decrease_quantity(self):
        self.client.force_login(self.buyer)
        self.add_product()
        item = CartItem.objects.get(cart__buyer=self.buyer)

        increase_response = self.client.post(
            reverse("increase_cart_item", args=[item.pk]),
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.assertIn("Quantity updated.", self.messages_for(increase_response))

        decrease_response = self.client.post(
            reverse("decrease_cart_item", args=[item.pk]),
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertIn("Quantity updated.", self.messages_for(decrease_response))

    def test_decreasing_quantity_one_removes_item(self):
        self.client.force_login(self.buyer)
        self.add_product()
        item = CartItem.objects.get(cart__buyer=self.buyer)

        self.client.post(reverse("decrease_cart_item", args=[item.pk]))

        self.assertFalse(CartItem.objects.filter(pk=item.pk).exists())

    def test_buyer_cannot_modify_another_buyers_item(self):
        cart = Cart.objects.create(buyer=self.other_buyer)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_login(self.buyer)

        for url_name in (
            "remove_cart_item",
            "increase_cart_item",
            "decrease_cart_item",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.post(reverse(url_name, args=[item.pk]))
                self.assertEqual(response.status_code, 404)

        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)

    def test_clear_cart_removes_all_items(self):
        self.client.force_login(self.buyer)
        self.add_product()

        response = self.client.post(reverse("clear_cart"))

        self.assertFalse(CartItem.objects.filter(cart__buyer=self.buyer).exists())
        self.assertIn("Cart cleared.", self.messages_for(response))

    def test_cart_displays_subtotal_grand_total_and_navbar_count(self):
        cart = Cart.objects.create(buyer=self.buyer)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("cart_detail"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cart_item_count"], 2)
        self.assertEqual(response.context["cart"].grand_total, Decimal("80.00"))
        self.assertContains(response, "₹80.00")

    def test_mutating_views_require_post(self):
        cart = Cart.objects.create(buyer=self.buyer)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        self.client.force_login(self.buyer)
        urls = [
            reverse("add_to_cart", args=[self.product.pk]),
            reverse("remove_cart_item", args=[item.pk]),
            reverse("increase_cart_item", args=[item.pk]),
            reverse("decrease_cart_item", args=[item.pk]),
            reverse("clear_cart"),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)
