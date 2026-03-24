import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User  # noqa: E402

from app.models import UserProfile  # noqa: E402


def ensure_superuser():
    email = 'admin@bookstore.com'
    password = 'admin123'
    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            'email': email,
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'System Admin',
        },
    )
    if created:
        user.set_password(password)
        user.save()
    else:
        changed = False
        if not user.is_staff:
            user.is_staff = True
            changed = True
        if not user.is_superuser:
            user.is_superuser = True
            changed = True
        if changed:
            user.save(update_fields=['is_staff', 'is_superuser'])
    print(f'[seed_auth] superuser ready: {email}')


def ensure_staff_user():
    email = 'staff@bookstore.com'
    password = 'staff123'
    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            'email': email,
            'is_staff': True,
            'first_name': 'Demo Staff',
        },
    )
    if created:
        user.set_password(password)
        user.save()
    elif not user.is_staff:
        user.is_staff = True
        user.save(update_fields=['is_staff'])

    profile, p_created = UserProfile.objects.get_or_create(
        user=user,
        defaults={'role': 'staff', 'staff_id': 1},
    )
    if not p_created:
        update_fields = []
        if profile.role != 'staff':
            profile.role = 'staff'
            update_fields.append('role')
        if profile.staff_id != 1:
            profile.staff_id = 1
            update_fields.append('staff_id')
        if update_fields:
            profile.save(update_fields=update_fields)
    print(f'[seed_auth] staff user ready: {email}')


def main():
    ensure_superuser()
    ensure_staff_user()


if __name__ == '__main__':
    main()
