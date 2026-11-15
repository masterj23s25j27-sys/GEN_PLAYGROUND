import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'employee_mgmt.settings')
django.setup()

from django.contrib.auth.models import User
from attendance.models import EmployeeProfile

def seed():
    # 1. Create superuser/management
    admin_username = 'vismaya'
    if not User.objects.filter(username=admin_username).exists():
        admin_user = User.objects.create_superuser(admin_username, 'admin@example.com', 'vichu@123')
        EmployeeProfile.objects.create(user=admin_user, employee_id='MGT001', role='management')
        print(f"Created management user: {admin_username}")
    else:
        # Update just in case
        u = User.objects.get(username=admin_username)
        u.set_password('vichu@123')
        u.is_superuser = True
        u.is_staff = True
        u.save()
        prof, created = EmployeeProfile.objects.get_or_create(user=u, defaults={'employee_id': 'MGT001'})
        prof.role = 'management'
        prof.save()
        print(f"Updated management user: {admin_username}")

    # 2. Create dev001 to dev100
    for i in range(1, 101):
        username = f'dev{i:03d}'
        if not User.objects.filter(username=username).exists():
            u = User.objects.create_user(username, f'{username}@example.com', 'pass123')
            EmployeeProfile.objects.create(user=u, employee_id=username.upper(), role='developer')
            if i % 10 == 0:
                print(f"Created {username}")

if __name__ == '__main__':
    seed()
    print("Database seeding completed.")
