from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from pos_app.models import Store, Category, Product, Inventory

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up initial data for the POS system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create default stores
        store1, created = Store.objects.get_or_create(
            name='Main Store',
            defaults={
                'address': '123 Main Street, City, Country',
                'phone': '+1234567890',
                'email': 'main@store.com'
            }
        )
        if created:
            self.stdout.write(f'Created store: {store1.name}')
        else:
            self.stdout.write(f'Store {store1.name} already exists')

        store2, created = Store.objects.get_or_create(
            name='Branch Store',
            defaults={
                'address': '456 Branch Avenue, City, Country',
                'phone': '+1987654321',
                'email': 'branch@store.com'
            }
        )
        if created:
            self.stdout.write(f'Created store: {store2.name}')
        else:
            self.stdout.write(f'Store {store2.name} already exists')

        # Create default categories
        cat1, created = Category.objects.get_or_create(name='Electronics')
        if created:
            self.stdout.write(f'Created category: {cat1.name}')
        else:
            self.stdout.write(f'Category {cat1.name} already exists')

        cat2, created = Category.objects.get_or_create(name='Clothing')
        if created:
            self.stdout.write(f'Created category: {cat2.name}')
        else:
            self.stdout.write(f'Category {cat2.name} already exists')

        cat3, created = Category.objects.get_or_create(name='Food')
        if created:
            self.stdout.write(f'Created category: {cat3.name}')
        else:
            self.stdout.write(f'Category {cat3.name} already exists')

        # Create default products
        prod1, created = Product.objects.get_or_create(
            name='Smartphone',
            defaults={
                'description': 'Latest model smartphone',
                'category': cat1,
                'price': 699.99
            }
        )
        if created:
            self.stdout.write(f'Created product: {prod1.name}')
        else:
            self.stdout.write(f'Product {prod1.name} already exists')

        prod2, created = Product.objects.get_or_create(
            name='T-Shirt',
            defaults={
                'description': 'Cotton T-Shirt',
                'category': cat2,
                'price': 19.99
            }
        )
        if created:
            self.stdout.write(f'Created product: {prod2.name}')
        else:
            self.stdout.write(f'Product {prod2.name} already exists')

        prod3, created = Product.objects.get_or_create(
            name='Bread',
            defaults={
                'description': 'Fresh white bread loaf',
                'category': cat3,
                'price': 2.99
            }
        )
        if created:
            self.stdout.write(f'Created product: {prod3.name}')
        else:
            self.stdout.write(f'Product {prod3.name} already exists')

        # Create default users if they don't exist
        director_user, created = User.objects.get_or_create(
            username='director',
            defaults={
                'email': 'director@pos.com',
                'first_name': 'System',
                'last_name': 'Director',
                'role': 'director',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            director_user.set_password('director123')
            director_user.save()
            self.stdout.write(f'Created director user: {director_user.username}')
        else:
            self.stdout.write(f'Director user {director_user.username} already exists')

        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@pos.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(f'Created admin user: {admin_user.username}')
        else:
            self.stdout.write(f'Admin user {admin_user.username} already exists')

        manager1, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager1@store1.com',
                'first_name': 'Store',
                'last_name': 'Manager 1',
                'role': 'manager',
                'store': store1,
                'is_staff': True
            }
        )
        if created:
            manager1.set_password('manager123')
            manager1.save()
            self.stdout.write(f'Created manager user: {manager1.username}')
        else:
            self.stdout.write(f'Manager user {manager1.username} already exists')

        staff1, created = User.objects.get_or_create(
            username='staff1',
            defaults={
                'email': 'staff1@store1.com',
                'first_name': 'Store',
                'last_name': 'Staff 1',
                'role': 'staff',
                'store': store1,
                'is_staff': False
            }
        )
        if created:
            staff1.set_password('staff123')
            staff1.save()
            self.stdout.write(f'Created staff user: {staff1.username}')
        else:
            self.stdout.write(f'Staff user {staff1.username} already exists')

        # Create initial inventory
        inventory1, created = Inventory.objects.get_or_create(
            product=prod1,
            store=store1,
            defaults={'quantity': 50, 'reorder_level': 10}
        )
        if created:
            self.stdout.write(f'Created inventory for {prod1.name} at {store1.name}')
        else:
            self.stdout.write(f'Inventory for {prod1.name} at {store1.name} already exists')

        inventory2, created = Inventory.objects.get_or_create(
            product=prod2,
            store=store1,
            defaults={'quantity': 100, 'reorder_level': 20}
        )
        if created:
            self.stdout.write(f'Created inventory for {prod2.name} at {store1.name}')
        else:
            self.stdout.write(f'Inventory for {prod2.name} at {store1.name} already exists')

        inventory3, created = Inventory.objects.get_or_create(
            product=prod1,
            store=store2,
            defaults={'quantity': 30, 'reorder_level': 10}
        )
        if created:
            self.stdout.write(f'Created inventory for {prod1.name} at {store2.name}')
        else:
            self.stdout.write(f'Inventory for {prod1.name} at {store2.name} already exists')

        self.stdout.write(
            self.style.SUCCESS('Successfully set up initial data for POS system')
        )