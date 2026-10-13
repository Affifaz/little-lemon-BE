from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from restaurant.models import Booking, Menu
from restaurant.serializers import MenuSerializer

PASSWORD = 'lemon@789!'


class IndexViewTest(APITestCase):
    def test_home_page(self):
        for url in ('/', '/restaurant/'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'index.html')
            self.assertContains(response, 'restaurant/styles.css')


class AuthTest(APITestCase):
    def test_register_and_get_tokens(self):
        response = self.client.post(
            '/auth/users/', {'username': 'adrian', 'password': PASSWORD})
        self.assertEqual(response.status_code, 201)

        credentials = {'username': 'adrian', 'password': PASSWORD}
        response = self.client.post('/restaurant/api-token-auth/', credentials)
        self.assertEqual(response.status_code, 200)
        token = response.data['token']
        # Djoser hands out the same token
        response = self.client.post('/auth/token/login/', credentials)
        self.assertEqual(response.data['auth_token'], token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        self.assertEqual(self.client.get('/auth/users/me/').data['username'], 'adrian')

    def test_wrong_password(self):
        User.objects.create_user('adrian', password=PASSWORD)
        response = self.client.post(
            '/restaurant/api-token-auth/', {'username': 'adrian', 'password': 'wrong'})
        self.assertEqual(response.status_code, 400)


class MenuViewTest(APITestCase):
    def setUp(self):
        self.staff = User.objects.create_user('staff', password=PASSWORD, is_staff=True)
        self.customer = User.objects.create_user('customer', password=PASSWORD)
        self.pasta = Menu.objects.create(title='Beef Pasta', price='12.00', inventory=20)
        Menu.objects.create(title='Greek Salad', price='8.50', inventory=15)
        Menu.objects.create(title='Baklava', price='4.50', inventory=30)

    def test_getall(self):
        response = self.client.get('/restaurant/menu/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, MenuSerializer(Menu.objects.all(), many=True).data)
        self.assertEqual(len(response.data), 3)

    def test_get_one(self):
        response = self.client.get(f'/restaurant/menu/{self.pasta.pk}/')
        self.assertEqual(
            response.data,
            {'id': self.pasta.pk, 'title': 'Beef Pasta', 'price': '12.00', 'inventory': 20})

    def test_staff_can_change_the_menu(self):
        self.client.force_authenticate(self.staff)
        response = self.client.post(
            '/restaurant/menu/', {'title': 'Lemonade', 'price': '3.00', 'inventory': 50})
        self.assertEqual(response.status_code, 201)
        url = f"/restaurant/menu/{response.data['id']}/"
        self.assertEqual(self.client.patch(url, {'inventory': 49}).status_code, 200)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertEqual(Menu.objects.count(), 3)

    def test_others_cannot_change_the_menu(self):
        item = {'title': 'Lemonade', 'price': '3.00', 'inventory': 50}
        url = f'/restaurant/menu/{self.pasta.pk}/'
        self.assertEqual(self.client.post('/restaurant/menu/', item).status_code, 401)
        self.client.force_authenticate(self.customer)
        self.assertEqual(self.client.post('/restaurant/menu/', item).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)


class BookingViewTest(APITestCase):
    booking = {'name': 'Adrian', 'no_of_guests': 4, 'booking_date': '2026-12-24T19:00:00Z'}

    def setUp(self):
        self.customer = User.objects.create_user('customer', password=PASSWORD)

    def test_login_required(self):
        self.assertEqual(self.client.get('/restaurant/booking/tables/').status_code, 401)
        response = self.client.post('/restaurant/booking/tables/', self.booking)
        self.assertEqual(response.status_code, 401)

    def test_book_a_table(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post('/restaurant/booking/tables/', self.booking)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {'id': response.data['id'], **self.booking})
        url = f"/restaurant/booking/tables/{response.data['id']}/"

        self.assertEqual(len(self.client.get('/restaurant/booking/tables/').data), 1)
        self.assertEqual(self.client.patch(url, {'no_of_guests': 6}).status_code, 200)
        self.assertEqual(self.client.get(url).data['no_of_guests'], 6)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Booking.objects.exists())

    def test_invalid_booking(self):
        self.client.force_authenticate(self.customer)
        response = self.client.post(
            '/restaurant/booking/tables/', {**self.booking, 'no_of_guests': 0})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/restaurant/booking/tables/', {'name': 'Adrian'})
        self.assertEqual(response.status_code, 400)
