from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand

from LittleLemonAPI.models import Category, MenuItem
from LittleLemonAPI.permissions import DELIVERY_CREW_GROUP, MANAGER_GROUP

PASSWORD = 'lemon@789!'

# username, group, is_superuser
USERS = [
    ('admin', None, True),
    ('manager', MANAGER_GROUP, False),
    ('delivery', DELIVERY_CREW_GROUP, False),
    ('customer', None, False),
]

# category slug, category title, [(item title, price, featured)]
MENU = [
    ('main', 'Main', [
        ('Beef Pasta', '12.00', True),
        ('Tomato Pasta', '5.00', False),
        ('Greek Salad', '8.50', False),
    ]),
    ('dessert', 'Dessert', [
        ('Lemon Dessert', '6.00', False),
        ('Baklava', '4.50', False),
    ]),
]


class Command(BaseCommand):
    help = 'Create sample users, categories and menu items for local testing.'

    def handle(self, *args, **options):
        for username, group, is_superuser in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@littlelemon.com',
                    'is_superuser': is_superuser,
                    'is_staff': is_superuser,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            if group:
                user.groups.add(Group.objects.get_or_create(name=group)[0])

        for slug, title, items in MENU:
            category, _ = Category.objects.get_or_create(slug=slug, defaults={'title': title})
            for item_title, price, featured in items:
                MenuItem.objects.get_or_create(
                    title=item_title,
                    defaults={'price': price, 'featured': featured, 'category': category},
                )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(USERS)} users (password: {PASSWORD}) and the sample menu.'
        ))
