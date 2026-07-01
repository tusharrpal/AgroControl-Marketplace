from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from marketplace.models import Category, Product


User = get_user_model()


class RegistrationTests(TestCase):
    def registration_data(self, **overrides):
        data = {
            "first_name": "Asha",
            "last_name": "Patil",
            "username": "asha",
            "email": "asha@example.com",
            "phone_number": "9876543210",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        data.update(overrides)
        return data

    def test_buyer_registration_sets_role_and_logs_user_in(self):
        response = self.client.post(reverse("buyer_register"), self.registration_data())

        user = User.objects.get(username="asha")
        self.assertEqual(user.role, User.Role.BUYER)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
        self.assertRedirects(response, reverse("product_list"))

    def test_farmer_registration_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("farmer_register"),
            self.registration_data(username="farmer", email="farmer@example.com"),
        )

        user = User.objects.get(username="farmer")
        self.assertEqual(user.role, User.Role.FARMER)
        self.assertRedirects(response, reverse("farmer_dashboard"))

    def test_password_confirmation_is_validated(self):
        response = self.client.post(
            reverse("buyer_register"),
            self.registration_data(password2="DifferentPass123!"),
        )

        self.assertContains(response, "The two password fields didn’t match.")
        self.assertFalse(User.objects.filter(username="asha").exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        User.objects.create_user(
            username="existing",
            email="asha@example.com",
            phone_number="9876543210",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("buyer_register"),
            self.registration_data(email="ASHA@example.com"),
        )

        self.assertContains(response, "An account with this email already exists.")


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.buyer = User.objects.create_user(
            username="buyer",
            password="StrongPass123!",
            phone_number="9876543210",
            role=User.Role.BUYER,
        )
        cls.farmer = User.objects.create_user(
            username="farmer",
            password="StrongPass123!",
            phone_number="9876543211",
            role=User.Role.FARMER,
        )
        cls.admin_user = User.objects.create_user(
            username="manager",
            password="StrongPass123!",
            phone_number="9876543212",
            role=User.Role.ADMIN,
            is_staff=True,
        )

    def test_buyer_login_redirects_to_marketplace(self):
        response = self.client.post(reverse("login"), {
            "username": "buyer",
            "password": "StrongPass123!",
        })

        self.assertRedirects(response, reverse("product_list"))

    def test_farmer_login_redirects_to_dashboard(self):
        response = self.client.post(reverse("login"), {
            "username": "farmer",
            "password": "StrongPass123!",
        })

        self.assertRedirects(response, reverse("farmer_dashboard"))

    def test_admin_login_redirects_to_django_admin(self):
        response = self.client.post(reverse("login"), {
            "username": "manager",
            "password": "StrongPass123!",
        })

        self.assertRedirects(response, reverse("admin:index"))

    def test_external_next_url_is_not_followed(self):
        response = self.client.post(reverse("login"), {
            "username": "buyer",
            "password": "StrongPass123!",
            "next": "https://malicious.example/",
        })

        self.assertRedirects(response, reverse("product_list"))

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.buyer)
        get_response = self.client.get(reverse("logout"))
        self.assertEqual(get_response.status_code, 405)

        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_buyer_cannot_access_farmer_dashboard(self):
        self.client.force_login(self.buyer)

        response = self.client.get(reverse("farmer_dashboard"))

        self.assertRedirects(response, reverse("product_list"))


class FarmerDashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.farmer = User.objects.create_user(
            username="farmer-one",
            password="StrongPass123!",
            phone_number="9876543211",
            role=User.Role.FARMER,
        )
        cls.other_farmer = User.objects.create_user(
            username="farmer-two",
            password="StrongPass123!",
            phone_number="9876543212",
            role=User.Role.FARMER,
        )
        cls.buyer = User.objects.create_user(
            username="buyer",
            password="StrongPass123!",
            phone_number="9876543213",
            role=User.Role.BUYER,
        )
        cls.category = Category.objects.create(name="Vegetables")
        cls.crop = Product.objects.create(
            farmer=cls.farmer,
            category=cls.category,
            name="Tomato",
            description="Fresh tomatoes",
            price="40.00",
            quantity=25,
            location="Nashik",
        )
        cls.out_of_stock_crop = Product.objects.create(
            farmer=cls.farmer,
            category=cls.category,
            name="Potato",
            description="Farm potatoes",
            price="25.00",
            quantity=0,
            location="Pune",
        )
        cls.other_crop = Product.objects.create(
            farmer=cls.other_farmer,
            category=cls.category,
            name="Onion",
            description="Red onions",
            price="30.00",
            quantity=10,
            location="Satara",
        )

    def crop_data(self, **overrides):
        data = {
            "name": "Spinach",
            "category": self.category.pk,
            "description": "Fresh leafy spinach",
            "price": "20.00",
            "quantity": 15,
            "unit": Product.Unit.KG,
            "location": "Kolhapur",
            "harvest_date": "2026-06-30",
            "is_available": "on",
        }
        data.update(overrides)
        return data

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("farmer_dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('farmer_dashboard')}",
        )

    def test_dashboard_shows_only_farmer_totals_and_recent_products(self):
        self.client.force_login(self.farmer)

        response = self.client.get(reverse("farmer_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_crops"], 2)
        self.assertEqual(response.context["available_crops"], 1)
        self.assertEqual(response.context["out_of_stock_crops"], 1)
        self.assertContains(response, "Tomato")
        self.assertNotContains(response, "Onion")

    def test_buyer_is_denied_all_farmer_crop_pages(self):
        self.client.force_login(self.buyer)
        urls = [
            reverse("farmer_dashboard"),
            reverse("my_crops"),
            reverse("add_crop"),
            reverse("edit_crop", args=[self.crop.pk]),
            reverse("delete_crop", args=[self.crop.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, reverse("product_list"))

    def test_my_crops_displays_only_logged_in_farmers_products(self):
        self.client.force_login(self.farmer)

        response = self.client.get(reverse("my_crops"))

        self.assertContains(response, "Tomato")
        self.assertContains(response, "Potato")
        self.assertNotContains(response, "Onion")

    def test_farmer_can_add_crop_and_is_assigned_as_owner(self):
        self.client.force_login(self.farmer)

        response = self.client.post(reverse("add_crop"), self.crop_data())

        crop = Product.objects.get(name="Spinach")
        self.assertEqual(crop.farmer, self.farmer)
        self.assertRedirects(response, reverse("my_crops"))

    def test_add_crop_rejects_non_positive_price(self):
        self.client.force_login(self.farmer)

        response = self.client.post(
            reverse("add_crop"),
            self.crop_data(price="0.00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Price must be greater than zero.")
        self.assertFalse(Product.objects.filter(name="Spinach").exists())

    def test_farmer_can_edit_own_crop(self):
        self.client.force_login(self.farmer)

        response = self.client.post(
            reverse("edit_crop", args=[self.crop.pk]),
            self.crop_data(name="Cherry Tomato"),
        )

        self.crop.refresh_from_db()
        self.assertEqual(self.crop.name, "Cherry Tomato")
        self.assertEqual(self.crop.farmer, self.farmer)
        self.assertRedirects(response, reverse("my_crops"))

    def test_farmer_cannot_edit_another_farmers_crop(self):
        self.client.force_login(self.farmer)

        response = self.client.post(
            reverse("edit_crop", args=[self.other_crop.pk]),
            self.crop_data(name="Stolen Crop"),
        )

        self.assertEqual(response.status_code, 404)
        self.other_crop.refresh_from_db()
        self.assertEqual(self.other_crop.name, "Onion")

    def test_delete_has_confirmation_and_farmer_can_delete_own_crop(self):
        self.client.force_login(self.farmer)
        url = reverse("delete_crop", args=[self.crop.pk])

        confirmation = self.client.get(url)
        self.assertContains(confirmation, "Delete Tomato?")
        self.assertTrue(Product.objects.filter(pk=self.crop.pk).exists())

        response = self.client.post(url)
        self.assertRedirects(response, reverse("my_crops"))
        self.assertFalse(Product.objects.filter(pk=self.crop.pk).exists())

    def test_farmer_cannot_delete_another_farmers_crop(self):
        self.client.force_login(self.farmer)

        response = self.client.post(
            reverse("delete_crop", args=[self.other_crop.pk]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Product.objects.filter(pk=self.other_crop.pk).exists())
