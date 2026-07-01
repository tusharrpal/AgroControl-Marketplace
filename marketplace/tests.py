from django.test import TestCase
from django.urls import reverse

from users.models import User

from .models import Category, Product


class MarketplaceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        farmer = User.objects.create_user(
            username="farmer",
            password="test-password",
            phone_number="9999999999",
            role=User.Role.FARMER,
        )
        vegetable = Category.objects.create(name="Vegetables")
        fruit = Category.objects.create(name="Fruits")
        cls.tomato = Product.objects.create(
            farmer=farmer,
            category=vegetable,
            name="Fresh Tomato",
            description="Farm fresh tomatoes",
            price="40.00",
            quantity=25,
            location="Nashik",
        )
        Product.objects.create(
            farmer=farmer,
            category=fruit,
            name="Mango",
            description="Seasonal mangoes",
            price="100.00",
            quantity=0,
            location="Ratnagiri",
        )

    def test_marketplace_shows_available_products_with_stock(self):
        response = self.client.get(reverse("product_list"))

        self.assertContains(response, "Fresh Tomato")
        self.assertNotContains(response, "Mango")

    def test_marketplace_searches_by_crop_name(self):
        response = self.client.get(reverse("product_list"), {"q": "tomato"})

        self.assertContains(response, "Fresh Tomato")

    def test_marketplace_filters_by_category(self):
        fruits = Category.objects.get(name="Fruits")
        response = self.client.get(reverse("product_list"), {"category": fruits.pk})

        self.assertNotContains(response, "Fresh Tomato")

    def test_product_detail_displays_farmer_and_quantity(self):
        response = self.client.get(reverse("product_detail", args=[self.tomato.pk]))

        self.assertContains(response, "farmer")
        self.assertContains(response, "25 Kilogram")
