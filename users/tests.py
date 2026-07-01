from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


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
