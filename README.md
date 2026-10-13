# Little Lemon capstone

Back-end for the Little Lemon restaurant: a Django project called `littlelemon` with an app called `restaurant`, using Django REST framework, Djoser and MySQL.

## Setup

Create the MySQL database and user first (`mysql -u root -p`):

```sql
CREATE DATABASE littlelemon_capstone CHARACTER SET utf8mb4;
CREATE USER 'littlelemon'@'localhost' IDENTIFIED BY 'lemon@789!';
GRANT ALL PRIVILEGES ON littlelemon_capstone.* TO 'littlelemon'@'localhost';
GRANT ALL PRIVILEGES ON test_littlelemon_capstone.* TO 'littlelemon'@'localhost';
```

The connection details are in the `DATABASES` section of `littlelemon/settings.py`.

Then install and run the project:

```bash
pipenv install
pipenv shell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Tests

```bash
python manage.py test
```

The unit tests are in `tests/test_models.py` and `tests/test_views.py`.

## Paths to test

| Path                                | Method                  | Who                | Purpose                                     |
|-------------------------------------|-------------------------|--------------------|---------------------------------------------|
| `/` and `/restaurant/`              | GET                     | Everyone           | Static home page                            |
| `/admin/`                           | GET                     | Staff              | Django admin                                |
| `/auth/users/`                      | POST                    | Everyone           | Register with `username`, `password`, `email` |
| `/auth/users/me/`                   | GET                     | Any logged-in user | Show the current user                       |
| `/auth/token/login/`                | POST                    | Everyone           | Get a token (Djoser)                        |
| `/auth/token/logout/`               | POST                    | Any logged-in user | Delete the current token                    |
| `/restaurant/api-token-auth/`       | POST                    | Everyone           | Get a token (DRF `obtain_auth_token`)       |
| `/restaurant/menu/`                 | GET                     | Everyone           | List the menu                               |
| `/restaurant/menu/`                 | POST                    | Staff              | Add a menu item: `title`, `price`, `inventory` |
| `/restaurant/menu/{id}/`            | GET                     | Everyone           | Show one menu item                          |
| `/restaurant/menu/{id}/`            | PUT, PATCH, DELETE      | Staff              | Change a menu item                          |
| `/restaurant/booking/tables/`       | GET                     | Any logged-in user | List table bookings                         |
| `/restaurant/booking/tables/`       | POST                    | Any logged-in user | Book a table: `name`, `no_of_guests`, `booking_date` |
| `/restaurant/booking/tables/{id}/`  | GET, PUT, PATCH, DELETE | Any logged-in user | Show, change or cancel a booking            |

`booking_date` is a date and time, for example `2026-12-24T19:00:00Z`.

## Testing with Insomnia

1. `POST http://127.0.0.1:8000/restaurant/api-token-auth/` with a form body of `username` and `password`. Copy the `token` from the response.
2. On every other request, open the Bearer tab, paste the token and set the prefix to `Token`.
3. `POST http://127.0.0.1:8000/restaurant/booking/tables/` with a form body of `name`, `no_of_guests` and `booking_date`.

## Testing in the browser

Log in at http://127.0.0.1:8000/api-auth/login/ and then open any of the `/restaurant/` paths above to use the browsable API.
