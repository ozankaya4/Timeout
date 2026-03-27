from django.contrib.auth import get_user_model

User = get_user_model()


def make_user(username='testuser', password='TestPass1!', **kwargs):
    """Create a user with default credentials. Shared across test modules."""
    return User.objects.create_user(username=username, password=password, **kwargs)
