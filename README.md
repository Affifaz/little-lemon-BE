# Little Lemon API

REST API for the Little Lemon restaurant, built with Django, Django REST framework and Djoser on MySQL.

## Setup

Create the MySQL database and user first (`mysql -u root -p`):

```sql
CREATE DATABASE LittleLemon CHARACTER SET utf8mb4;
CREATE USER 'littlelemon'@'localhost' IDENTIFIED BY 'lemon@789!';
GRANT ALL PRIVILEGES ON LittleLemon.* TO 'littlelemon'@'localhost';
GRANT ALL PRIVILEGES ON test_LittleLemon.* TO 'littlelemon'@'localhost';
```

To use a different database or account, set `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST` and `MYSQL_PORT`.

Then install and run the project:

```bash
pipenv install
pipenv shell
python manage.py migrate
python manage.py seed        # optional: sample users and menu
python manage.py runserver
```

Run the tests with `python manage.py test`. The home page is at http://127.0.0.1:8000/.

## Test users

`python manage.py seed` creates these users, all with the password `lemon@789!`:

| Username   | Role                |
|------------|---------------------|
| `admin`    | Admin (superuser)   |
| `manager`  | Manager group       |
| `delivery` | Delivery crew group |
| `customer` | Customer (no group) |

The `Manager` and `Delivery crew` groups are created by a migration. The Django admin is at `/admin/`.

## Authentication

Get a token from `/token/login/` and send it on every request as `Authorization: Token <token>`.
In Insomnia, choose Bearer auth and set the prefix to `Token`.

| Endpoint          | Method | Purpose                                             |
|-------------------|--------|-----------------------------------------------------|
| `/api/users/`     | POST   | Register with `username`, `password` and `email`    |
| `/api/users/me/`  | GET    | Show the current user                               |
| `/token/login/`   | POST   | Exchange `username` and `password` for a token      |
| `/token/logout/`  | POST   | Delete the current token                            |

These four Djoser endpoints need the trailing slash. On every endpoint below it is optional.

## Endpoints

An admin can do everything a manager can.

### Menu

| Endpoint               | Method             | Who             | Purpose                 |
|------------------------|--------------------|-----------------|-------------------------|
| `/api/categories`      | GET                | Everyone        | List all categories     |
| `/api/categories`      | POST               | Admin, manager  | Add a category          |
| `/api/categories/{id}` | PUT, PATCH, DELETE | Admin, manager  | Change a category       |
| `/api/menu-items`      | GET                | Everyone        | List menu items         |
| `/api/menu-items`      | POST               | Admin, manager  | Add a menu item         |
| `/api/menu-items/{id}` | GET                | Everyone        | Show one menu item      |
| `/api/menu-items/{id}` | PUT, PATCH, DELETE | Admin, manager  | Change a menu item      |

To set the item of the day, `PATCH /api/menu-items/{id}` with `featured=true`.

Query parameters for `/api/menu-items`:

| Parameter                       | Example                      |
|---------------------------------|------------------------------|
| `category` (category id)        | `?category=1`                |
| `category__title`               | `?category__title=Dessert`   |
| `category__slug`                | `?category__slug=dessert`    |
| `featured`                      | `?featured=true`             |
| `search` (title, category)      | `?search=pasta`              |
| `ordering` (`price`, `title`)   | `?ordering=price`, `?ordering=-price` |
| `page`                          | `?page=2`                    |
| `perpage` (default 2, max 100)  | `?perpage=10`                |

### Groups

| Endpoint                                | Method | Who            | Purpose                                 |
|-----------------------------------------|--------|----------------|-----------------------------------------|
| `/api/groups/manager/users`             | GET    | Admin, manager | List managers                           |
| `/api/groups/manager/users`             | POST   | Admin, manager | Add the user in `username` to managers  |
| `/api/groups/manager/users/{userId}`    | DELETE | Admin, manager | Remove a user from managers             |
| `/api/groups/delivery-crew/users`       | GET    | Admin, manager | List the delivery crew                  |
| `/api/groups/delivery-crew/users`       | POST   | Admin, manager | Add the user in `username` to the crew  |
| `/api/groups/delivery-crew/users/{userId}` | DELETE | Admin, manager | Remove a user from the crew          |

### Cart

| Endpoint               | Method | Who                | Purpose                                         |
|------------------------|--------|--------------------|-------------------------------------------------|
| `/api/cart/menu-items` | GET    | Any logged-in user | Show the items in your cart                     |
| `/api/cart/menu-items` | POST   | Any logged-in user | Add an item with `menuitem` (id) and `quantity` |
| `/api/cart/menu-items` | DELETE | Any logged-in user | Empty your cart                                 |

### Orders

| Endpoint           | Method     | Who                | Purpose                                              |
|--------------------|------------|--------------------|------------------------------------------------------|
| `/api/orders`      | GET        | Customer           | List your own orders                                 |
| `/api/orders`      | GET        | Delivery crew      | List the orders assigned to you                      |
| `/api/orders`      | GET        | Admin, manager     | List all orders                                      |
| `/api/orders`      | POST       | Any logged-in user | Place an order from your cart, then empty the cart   |
| `/api/orders/{id}` | GET        | Same as the list   | Show one order with its items                        |
| `/api/orders/{id}` | PUT, PATCH | Admin, manager     | Set `delivery_crew` (user id) and `status`           |
| `/api/orders/{id}` | PATCH      | Delivery crew      | Set `status` only (`true` = delivered)               |
| `/api/orders/{id}` | DELETE     | Admin, manager     | Delete an order                                      |

`/api/orders` can be filtered with `status`, `delivery_crew` and `date`, sorted with `ordering=date` or `ordering=total`, and paginated like the menu items.

### Table bookings

| Endpoint             | Method             | Who                | Purpose                                                    |
|----------------------|--------------------|--------------------|------------------------------------------------------------|
| `/api/bookings`      | GET                | Customer           | List your own bookings                                     |
| `/api/bookings`      | GET                | Admin, manager     | List all bookings                                          |
| `/api/bookings`      | POST               | Any logged-in user | Book a table with `name`, `no_of_guests` and `booking_date` |
| `/api/bookings/{id}` | GET                | Same as the list   | Show one booking                                           |
| `/api/bookings/{id}` | PUT, PATCH, DELETE | Same as the list   | Change or cancel a booking                                 |

`booking_date` is a date and time, for example `2026-12-24T19:00:00Z`.

## Throttling

Anonymous clients are limited to 30 requests a minute and logged-in users to 120.
