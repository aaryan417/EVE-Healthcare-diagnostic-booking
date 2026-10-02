import pytest
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:

    def test_create_user_successful(self):
        """Test creating a normal user with valid email and password."""
        user = User.objects.create_user(
            email="aaryan@example.com",
            password="StrongPassword123",
            name="Aaryan Verma"
        )
        assert user.email == "aaryan@example.com"
        assert user.name == "Aaryan Verma"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password("StrongPassword123") is True
        assert user.password != "StrongPassword123"

    def test_create_user_without_email_raises_error(self):
        """Test that creating a user without an email raises ValueError."""
        with pytest.raises(ValueError, match="The Email field must be set"):
            User.objects.create_user(email="", password="Password123")

    def test_create_superuser_successful(self):
        """Test creating a superuser with staff and superuser permissions."""
        admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="AdminPassword123",
            name="Admin User"
        )
        assert admin_user.email == "admin@example.com"
        assert admin_user.is_staff is True
        assert admin_user.is_superuser is True
        assert admin_user.is_active is True
        assert admin_user.check_password("AdminPassword123") is True

    def test_create_superuser_invalid_staff_flag(self):
        """Test that superuser creation fails if is_staff is set to False."""
        with pytest.raises(ValueError, match="Superuser must have is_staff=True."):
            User.objects.create_superuser(
                email="admin@example.com",
                password="AdminPassword123",
                is_staff=False
            )

    def test_create_superuser_invalid_superuser_flag(self):
        """Test that superuser creation fails if is_superuser is set to False."""
        with pytest.raises(ValueError, match="Superuser must have is_superuser=True."):
            User.objects.create_superuser(
                email="admin@example.com",
                password="AdminPassword123",
                is_superuser=False
            )

    def test_duplicate_email_raises_error(self):
        """Test that email uniqueness is enforced at the model level."""
        User.objects.create_user(
            email="duplicate@example.com",
            password="Password123",
            name="User One"
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="duplicate@example.com",
                password="Password456",
                name="User Two"
            )

    def test_user_string_representation(self):
        """Test that __str__ returns the user's email address."""
        user = User.objects.create_user(
            email="str_test@example.com",
            password="Password123",
            name="Str Test"
        )
        assert str(user) == "str_test@example.com"
