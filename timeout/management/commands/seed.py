"""
Custom management command to seed the database with test data.

Usage:
    python manage.py seed
"""

import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from faker import Faker

User = get_user_model()
fake = Faker()

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


class Command(BaseCommand):
    help = 'Seed the database with a superuser and 25 random student users.'

    def handle(self, *args, **options):
        self.stdout.write('=' * 50)
        self.stdout.write('SEEDING DATABASE')
        self.stdout.write('=' * 50)

        self.stdout.write('\n[1/3] Creating superuser...')
        self._create_superuser()

        self.stdout.write(f'\n[2/3] Creating {NUM_USERS} users...')
        users = self._create_users(NUM_USERS)

        self.stdout.write(f'\n[3/3] Creating follow relationships...')
        self._create_follow_relationships(users)

        total = User.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Total users in database: {total}'
        ))

    def _create_superuser(self):
        """Create the @johndoe superuser if they don't already exist."""
        if User.objects.filter(username=SUPERUSER_USERNAME).exists():
            self.stdout.write(self.style.WARNING(
                f'  Superuser @{SUPERUSER_USERNAME} already exists, skipping.'
            ))
            return

        try:
            User.objects.create_superuser(
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
            self.stdout.write(self.style.SUCCESS(
                f'  Superuser @{SUPERUSER_USERNAME} created.'
            ))
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(
                f'  Failed to create superuser: {e}'
            ))

    def _create_users(self, count):
        """Create regular user accounts with randomized Faker data."""
        users = []
        existing = set(User.objects.values_list('username', flat=True))

        for i in range(count):
            username = fake.user_name()
            while username in existing:
                username = fake.user_name() + str(random.randint(10, 99))
            existing.add(username)

            try:
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
                    academic_interests=', '.join(
                        random.sample(INTERESTS, k=random.randint(1, 4))
                    ),
                    privacy_private=random.choice([True, False]),
                    management_style=random.choice(MANAGEMENT_STYLES),
                )
                users.append(user)
                self.stdout.write(f'  [{i + 1}/{count}] Created @{username}')
            except IntegrityError as e:
                self.stdout.write(self.style.ERROR(
                    f'  [{i + 1}/{count}] Failed @{username}: {e}'
                ))

        return users

    def _create_follow_relationships(self, users):
        """Establish random follow relationships between all users."""
        all_users = list(User.objects.all())
        follow_count = 0

        for user in all_users:
            others = [u for u in all_users if u != user]
            to_follow = random.sample(
                others, k=min(random.randint(2, 8), len(others))
            )
            user.following.add(*to_follow)
            follow_count += len(to_follow)

        self.stdout.write(self.style.SUCCESS(
            f'  Created {follow_count} follow relationships.'
        ))
