from django.contrib.auth.models import Group, User
from django.core.cache import cache
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Booking, Cart, Category, MenuItem, Order
from .permissions import DELIVERY_CREW_GROUP, MANAGER_GROUP

PASSWORD = 'lemon@789!'


class LittleLemonAPITests(APITestCase):
    def setUp(self):
        cache.clear()  # reset throttle counters
        self.admin = User.objects.create_superuser('admin', password=PASSWORD)
        self.manager = User.objects.create_user('manager', password=PASSWORD)
        self.manager.groups.add(Group.objects.get(name=MANAGER_GROUP))
        self.crew = User.objects.create_user('crew', password=PASSWORD)
        self.crew.groups.add(Group.objects.get(name=DELIVERY_CREW_GROUP))
        self.customer = User.objects.create_user('customer', password=PASSWORD)
        self.other = User.objects.create_user('other', password=PASSWORD)

        self.main = Category.objects.create(slug='main', title='Main')
        self.dessert = Category.objects.create(slug='dessert', title='Dessert')
        self.pasta = MenuItem.objects.create(
            title='Beef Pasta', price='12.00', category=self.main, featured=True)
        self.salad = MenuItem.objects.create(
            title='Greek Salad', price='8.50', category=self.main)
        self.baklava = MenuItem.objects.create(
            title='Baklava', price='4.50', category=self.dessert)

    def login(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def place_order(self, user):
        self.login(user)
        self.client.post('/api/cart/menu-items', {'menuitem': self.pasta.pk, 'quantity': 2})
        return self.client.post('/api/orders').data['id']

    # Users and groups

    def test_customer_can_register_and_get_token(self):
        response = self.client.post(
            '/api/users/', {'username': 'adrian', 'password': PASSWORD})
        self.assertEqual(response.status_code, 201)
        response = self.client.post(
            '/token/login/', {'username': 'adrian', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['auth_token']}")
        self.assertEqual(self.client.get('/api/users/me/').data['username'], 'adrian')

    def test_manager_can_log_in(self):
        response = self.client.post(
            '/token/login/', {'username': 'manager', 'password': PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.data)

    def test_admin_can_manage_manager_group(self):
        self.login(self.admin)
        response = self.client.post('/api/groups/manager/users', {'username': 'other'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data, {'message': 'user added to the manager group'})
        usernames = [u['username'] for u in self.client.get('/api/groups/manager/users').data]
        self.assertEqual(usernames, ['manager', 'other'])
        response = self.client.delete(f'/api/groups/manager/users/{self.other.pk}')
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.other.groups.exists())
        self.assertEqual(
            self.client.post('/api/groups/manager/users', {'username': 'nobody'}).status_code,
            404)

    def test_manager_can_assign_delivery_crew(self):
        self.login(self.manager)
        response = self.client.post('/api/groups/delivery-crew/users', {'username': 'other'})
        self.assertEqual(response.status_code, 201)
        self.assertTrue(self.other.groups.filter(name=DELIVERY_CREW_GROUP).exists())

    def test_groups_are_forbidden_to_non_managers(self):
        self.assertEqual(self.client.get('/api/groups/manager/users').status_code, 401)
        for user in (self.customer, self.crew):
            self.login(user)
            self.assertEqual(self.client.get('/api/groups/manager/users').status_code, 403)
            response = self.client.post('/api/groups/manager/users', {'username': user.username})
            self.assertEqual(response.status_code, 403)

    # Categories and menu items

    def test_admin_can_add_categories_and_menu_items(self):
        self.login(self.admin)
        response = self.client.post('/api/categories', {'slug': 'drinks', 'title': 'Drinks'})
        self.assertEqual(response.status_code, 201)
        response = self.client.post('/api/menu-items', {
            'title': 'Lemonade', 'price': '3.00', 'category': response.data['id']})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['featured'], False)

    def test_customers_cannot_change_the_menu(self):
        self.login(self.customer)
        item = {'title': 'Lemonade', 'price': '3.00', 'category': self.main.pk}
        self.assertEqual(self.client.post('/api/menu-items', item).status_code, 403)
        self.assertEqual(
            self.client.post('/api/categories', {'slug': 'x', 'title': 'X'}).status_code, 403)
        url = f'/api/menu-items/{self.pasta.pk}'
        self.assertEqual(self.client.patch(url, {'featured': False}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_manager_can_update_item_of_the_day(self):
        self.login(self.manager)
        response = self.client.patch(f'/api/menu-items/{self.salad.pk}', {'featured': True})
        self.assertEqual(response.status_code, 200)
        self.salad.refresh_from_db()
        self.assertTrue(self.salad.featured)

    def test_customer_can_browse_categories_and_menu_items(self):
        self.login(self.customer)
        response = self.client.get('/api/categories')
        self.assertEqual([c['title'] for c in response.data], ['Main', 'Dessert'])

        response = self.client.get('/api/menu-items')
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 2)
        self.assertIn('page=2', response.data['next'])
        self.assertEqual(
            response.data['results'][0],
            {'id': self.pasta.pk, 'title': 'Beef Pasta', 'price': '12.00',
             'category': self.main.pk, 'featured': True})

        response = self.client.get('/api/menu-items?page=2')
        self.assertEqual([i['title'] for i in response.data['results']], ['Baklava'])
        response = self.client.get('/api/menu-items?perpage=10')
        self.assertEqual(len(response.data['results']), 3)
        response = self.client.get(f'/api/menu-items/{self.baklava.pk}')
        self.assertEqual(response.data['title'], 'Baklava')

    def test_menu_items_filter_and_sort(self):
        def titles(query):
            response = self.client.get(f'/api/menu-items?perpage=10&{query}')
            return [i['title'] for i in response.data['results']]

        self.assertEqual(titles(f'category={self.dessert.pk}'), ['Baklava'])
        self.assertEqual(titles('category__title=Main'), ['Beef Pasta', 'Greek Salad'])
        self.assertEqual(titles('ordering=price'), ['Baklava', 'Greek Salad', 'Beef Pasta'])
        self.assertEqual(titles('ordering=-price'), ['Beef Pasta', 'Greek Salad', 'Baklava'])
        self.assertEqual(titles('search=salad'), ['Greek Salad'])
        self.assertEqual(titles('featured=true'), ['Beef Pasta'])

    # Cart

    def test_cart(self):
        self.assertEqual(self.client.get('/api/cart/menu-items').status_code, 401)
        self.login(self.customer)
        response = self.client.post(
            '/api/cart/menu-items', {'menuitem': self.pasta.pk, 'quantity': 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['unit_price'], '12.00')
        self.assertEqual(response.data['price'], '24.00')
        # Adding the same item again increases the quantity
        response = self.client.post(
            '/api/cart/menu-items', {'menuitem': self.pasta.pk, 'quantity': 1})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['price'], '36.00')
        self.client.post('/api/cart/menu-items', {'menuitem': self.baklava.pk, 'quantity': 1})
        response = self.client.post(
            '/api/cart/menu-items', {'menuitem': self.baklava.pk, 'quantity': 0})
        self.assertEqual(response.status_code, 400)

        response = self.client.get('/api/cart/menu-items')
        self.assertEqual([i['quantity'] for i in response.data], [3, 1])

        # Carts are private
        self.login(self.other)
        self.assertEqual(self.client.get('/api/cart/menu-items').data, [])
        self.assertEqual(self.client.delete('/api/cart/menu-items').status_code, 200)
        self.assertEqual(Cart.objects.filter(user=self.customer).count(), 2)

        self.login(self.customer)
        self.assertEqual(self.client.delete('/api/cart/menu-items').status_code, 200)
        self.assertEqual(self.client.get('/api/cart/menu-items').data, [])

    # Orders

    def test_customer_can_place_and_browse_orders(self):
        self.login(self.customer)
        self.assertEqual(self.client.post('/api/orders').status_code, 400)  # empty cart

        self.client.post('/api/cart/menu-items', {'menuitem': self.pasta.pk, 'quantity': 2})
        self.client.post('/api/cart/menu-items', {'menuitem': self.baklava.pk, 'quantity': 1})
        response = self.client.post('/api/orders')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['total'], '28.50')
        self.assertEqual(response.data['user'], self.customer.pk)
        self.assertEqual(response.data['status'], False)
        self.assertEqual(len(response.data['order_items']), 2)
        self.assertFalse(Cart.objects.filter(user=self.customer).exists())
        order_id = response.data['id']

        other_order_id = self.place_order(self.other)

        self.login(self.customer)
        response = self.client.get('/api/orders')
        self.assertEqual([o['id'] for o in response.data['results']], [order_id])
        self.assertEqual(self.client.get(f'/api/orders/{order_id}').status_code, 200)
        self.assertEqual(self.client.get(f'/api/orders/{other_order_id}').status_code, 404)
        # Customers cannot update or delete orders
        url = f'/api/orders/{order_id}'
        self.assertEqual(self.client.patch(url, {'status': True}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)

    def test_manager_assigns_order_and_crew_delivers_it(self):
        order_id = self.place_order(self.customer)
        unassigned_id = self.place_order(self.other)
        url = f'/api/orders/{order_id}'

        self.login(self.manager)
        self.assertEqual(self.client.get('/api/orders').data['count'], 2)
        # Only members of the delivery crew can be assigned
        response = self.client.patch(url, {'delivery_crew': self.customer.pk})
        self.assertEqual(response.status_code, 400)
        response = self.client.patch(url, {'delivery_crew': self.crew.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['delivery_crew'], self.crew.pk)

        self.login(self.crew)
        response = self.client.get('/api/orders')
        self.assertEqual([o['id'] for o in response.data['results']], [order_id])
        self.assertEqual(self.client.get(f'/api/orders/{unassigned_id}').status_code, 404)
        # Delivery crew can only change the status
        self.assertEqual(self.client.patch(url, {'delivery_crew': ''}).status_code, 403)
        self.assertEqual(self.client.put(url, {'status': True}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        response = self.client.patch(url, {'status': True})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Order.objects.get(pk=order_id).status)

        self.login(self.manager)
        self.assertEqual(self.client.get('/api/orders?status=true').data['count'], 1)
        self.assertEqual(self.client.delete(url).status_code, 204)

    # Table bookings

    def test_customer_can_book_a_table(self):
        booking = {'name': 'Adrian', 'no_of_guests': 4, 'booking_date': '2026-12-24T19:00:00Z'}
        self.assertEqual(self.client.post('/api/bookings', booking).status_code, 401)

        self.login(self.customer)
        response = self.client.post('/api/bookings', booking)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user'], self.customer.pk)
        self.assertEqual(response.data['no_of_guests'], 4)
        self.assertEqual(str(Booking.objects.get()), 'Adrian - 4 guests on 2026-12-24 19:00')
        url = f"/api/bookings/{response.data['id']}"

        response = self.client.post('/api/bookings', {**booking, 'no_of_guests': 0})
        self.assertEqual(response.status_code, 400)
        response = self.client.post('/api/bookings', {'name': 'Adrian'})
        self.assertEqual(response.status_code, 400)

        self.assertEqual(self.client.get('/api/bookings').data['count'], 1)
        self.assertEqual(self.client.patch(url, {'no_of_guests': 6}).status_code, 200)
        self.assertEqual(self.client.get(url).data['no_of_guests'], 6)

        # Bookings are private to the customer who made them
        self.login(self.other)
        self.assertEqual(self.client.get('/api/bookings').data['count'], 0)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.delete(url).status_code, 404)

        # Managers see every booking
        self.login(self.manager)
        self.assertEqual(self.client.get('/api/bookings').data['count'], 1)

        self.login(self.customer)
        self.assertEqual(self.client.delete(url).status_code, 204)
        self.assertFalse(Booking.objects.exists())

    # Static content

    def test_home_page_is_served(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'LittleLemonAPI/styles.css')


class ModelTests(APITestCase):
    def test_str(self):
        category = Category.objects.create(slug='main', title='Main')
        item = MenuItem.objects.create(title='Beef Pasta', price='12.00', category=category)
        self.assertEqual(str(category), 'Main')
        self.assertEqual(str(item), 'Beef Pasta')
