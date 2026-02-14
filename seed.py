"""
Database seeder for the Timeout application.

Creates 1 superuser and 25 regular users with randomized student data.
Establishes random "following" relationships between users.

Usage:
    python manage.py shell < seed.py
    OR
    python seed.py
"""

import os
import sys
import random
import django

# Django setup for standalone execution
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timeout_pwa.settings')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from faker import Faker

User = get_user_model()
fake = Faker()

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------
NUM_USERS = 25
SUPERUSER_USERNAME = 'johndoe'
SUPERUSER_PASSWORD = 'Password123'
SUPERUSER_EMAIL = 'john.doe@email.com'
DEFAULT_PASSWORD = 'Student@123'

UNIVERSITIES = [
    'Galatasaray University',
    'Bogazici University',
    'Istanbul Technical University',
    'METU',
    'Koc University',
    'Sabanci University',
    'Bilkent University',
    'Ankara University',
    'Hacettepe University',
    'Ege University',
]

INTERESTS = [
    'Computer Science',
    'Mathematics',
    'Physics',
    'Engineering',
    'Literature',
    'Philosophy',
    'Economics',
    'Biology',
    'Chemistry',
    'History',
    'Psychology',
    'Art',
    'Music',
    'Political Science',
    'Data Science',
]

MANAGEMENT_STYLES = ['early_bird', 'night_owl']


def create_superuser():
    """Create the main superuser account."""
    if User.objects.filter(username=SUPERUSER_USERNAME).exists():
        print(f'  Superuser @{SUPERUSER_USERNAME} already exists, skipping.')
        return User.objects.get(username=SUPERUSER_USERNAME)

    superuser = User.objects.create_superuser(
        username=SUPERUSER_USERNAME,
        email=SUPERUSER_EMAIL,
        password=SUPERUSER_PASSWORD,
        first_name='John',
        last_name='Doe',
        university='Galatasaray University',
        year_of_study=3,
        bio='Admin account for the Timeout platform.',
        academic_interests='Computer Science, Data Science',
        management_style='early_bird',
    )
    print(f'  Superuser @{SUPERUSER_USERNAME} created.')
    return superuser


def create_users(count):
    """Create regular user accounts with randomized Faker data."""
    users = []
    existing = set(User.objects.values_list('username', flat=True))

    for i in range(count):
        # Generate a unique username
        username = fake.user_name()
        while username in existing:
            username = fake.user_name() + str(random.randint(10, 99))
        existing.add(username)

        user = User.objects.create_user(
            username=username,
            email=fake.unique.email(),
            password=DEFAULT_PASSWORD,
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            middle_name=fake.first_name() if random.random() < 0.3 else '',
            university=random.choice(UNIVERSITIES),
            year_of_study=random.randint(1, 5),
            bio=fake.sentence(nb_words=12),
            academic_interests=', '.join(random.sample(INTERESTS, k=random.randint(1, 4))),
            privacy_private=random.choice([True, False]),
            management_style=random.choice(MANAGEMENT_STYLES),
        )
        users.append(user)
        print(f'  [{i + 1}/{count}] Created @{username}')

    return users


def create_follow_relationships(users):
    """Establish random follow relationships between users."""
    all_users = list(User.objects.all())
    follow_count = 0

    for user in all_users:
        # Each user follows 2-8 random other users
        others = [u for u in all_users if u != user]
        to_follow = random.sample(others, k=min(random.randint(2, 8), len(others)))
        user.following.add(*to_follow)
        follow_count += len(to_follow)

    print(f'  Created {follow_count} follow relationships.')


def seed():
    """Main seeding function."""
    print('=' * 50)
    print('SEEDING DATABASE')
    print('=' * 50)

    print('\n[1/3] Creating superuser...')
    create_superuser()

    print(f'\n[2/3] Creating {NUM_USERS} users...')
    users = create_users(NUM_USERS)

    print('\n[3/3] Creating follow relationships...')
    create_follow_relationships(users)

    total = User.objects.count()
    print(f'\nDone! Total users in database: {total}')
    print('=' * 50)


if __name__ == '__main__':
    seed()
