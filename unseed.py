"""
Database unseeder for the Timeout application.

Removes all users from the database except the superuser.
Run with --all flag to remove superusers too.

Usage:
    python unseed.py           # Keep superusers
    python unseed.py --all     # Remove everyone
"""

import os
import sys
import django

# Django setup for standalone execution
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeout_pwa.settings')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()


def unseed(remove_all=False):
    """Remove users from the database."""
    print('=' * 50)
    print('UNSEEDING DATABASE')
    print('=' * 50)

    total_before = User.objects.count()

    if remove_all:
        print('\nMode: Remove ALL users (including superusers)')
        count, _ = User.objects.all().delete()
    else:
        print('\nMode: Remove regular users only (keeping superusers)')
        superuser_count = User.objects.filter(is_superuser=True).count()
        count, _ = User.objects.filter(is_superuser=False).delete()
        print(f'  Preserved {superuser_count} superuser(s).')

    total_after = User.objects.count()
    print(f'  Removed {total_before - total_after} user(s).')
    print(f'  Remaining users: {total_after}')
    print('=' * 50)


if __name__ == '__main__':
    flag = '--all' in sys.argv
    unseed(remove_all=flag)
