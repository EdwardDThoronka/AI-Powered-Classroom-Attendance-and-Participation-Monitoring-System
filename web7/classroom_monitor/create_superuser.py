import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'classroom_monitor.settings')
django.setup()

from core.models import Teacher

# Check if superuser exists
if not Teacher.objects.filter(username='admin').exists():
    Teacher.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpassword',
        first_name='Admin',
        last_name='User'
    )
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")
