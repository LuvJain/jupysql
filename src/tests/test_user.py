import pytest
import json
from sql.user import UserManager, create_user, get_user, get_all_users, user_exists
from sql.connection import ConnectionManager
import pandas as pd


@pytest.fixture
def sqlite_connection(ip_empty):
    """Setup a SQLite connection for testing user operations"""
    ip_empty.run_cell("%sql sqlite://")
    return ConnectionManager.current


class TestUserManager:
    """Test the UserManager class and module-level functions for user management"""

    def test_ensure_users_table_creates_table(self, sqlite_connection):
        """Test that ensure_users_table creates the jupysql_users table"""
        # Ensure the table is created
        UserManager.ensure_users_table()

        # Check if the table exists
        result = ConnectionManager.current.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (UserManager.USERS_TABLE_NAME,)
        )
        table_exists = bool(result.fetchone())
        assert table_exists is True

    def test_create_user_basic(self, sqlite_connection):
        """Test creating a user with basic information"""
        username = "testuser"
        email = "test@example.com"
        full_name = "Test User"

        # Create a user
        user = create_user(username=username, email=email, full_name=full_name)

        # Verify the user was created with correct data
        assert user["username"] == username
        assert user["email"] == email
        assert user["full_name"] == full_name
        assert user["id"] is not None
        assert user["created_at"] is not None
        assert user["updated_at"] is not None

    def test_create_user_with_metadata(self, sqlite_connection):
        """Test creating a user with metadata"""
        username = "metauser"
        metadata = {"role": "admin", "department": "engineering"}

        # Create a user with metadata
        user = create_user(username=username, metadata=metadata)

        # Verify the user was created with correct metadata
        assert user["username"] == username
        assert user["metadata"] == metadata

    def test_create_user_duplicate_username(self, sqlite_connection):
        """Test that creating a user with duplicate username raises an error"""
        username = "duplicate_user"

        # Create a user
        create_user(username=username)

        # Try to create another user with the same username
        with pytest.raises(Exception) as excinfo:
            create_user(username=username)

        # Verify the error message mentions duplicate username
        assert "already exists" in str(excinfo.value)

    def test_get_user_by_username(self, sqlite_connection):
        """Test retrieving a user by username"""
        username = "retrieval_user"

        # Create a user
        created_user = create_user(username=username)

        # Retrieve the user by username
        retrieved_user = get_user(username=username)

        # Verify the retrieved user matches the created user
        assert retrieved_user["id"] == created_user["id"]
        assert retrieved_user["username"] == username

    def test_get_user_by_id(self, sqlite_connection):
        """Test retrieving a user by ID"""
        username = "id_retrieval_user"

        # Create a user
        created_user = create_user(username=username)
        user_id = created_user["id"]

        # Retrieve the user by ID
        retrieved_user = get_user(user_id=user_id)

        # Verify the retrieved user matches the created user
        assert retrieved_user["id"] == user_id
        assert retrieved_user["username"] == username

    def test_get_user_nonexistent(self, sqlite_connection):
        """Test retrieving a nonexistent user"""
        # Try to retrieve a nonexistent user
        retrieved_user = get_user(username="nonexistent_user")

        # Verify that None is returned
        assert retrieved_user is None

    def test_get_all_users(self, sqlite_connection):
        """Test retrieving all users"""
        # Clear any existing users by recreating the table
        ConnectionManager.current.execute(f"DROP TABLE IF EXISTS {UserManager.USERS_TABLE_NAME}")
        UserManager.ensure_users_table()

        # Create multiple users
        users = [
            create_user(username=f"user_{i}") for i in range(3)
        ]

        # Retrieve all users
        all_users = get_all_users()

        # Verify all created users are retrieved
        assert len(all_users) == 3
        usernames = [user["username"] for user in all_users]
        assert all(f"user_{i}" in usernames for i in range(3))

    def test_user_exists(self, sqlite_connection):
        """Test checking if a user exists"""
        username = "existing_user"

        # Create a user
        create_user(username=username)

        # Check if the user exists
        assert user_exists(username) is True
        assert user_exists("nonexistent_user") is False

    def test_to_dataframe(self, sqlite_connection):
        """Test converting users to a DataFrame"""
        # Clear any existing users by recreating the table
        ConnectionManager.current.execute(f"DROP TABLE IF EXISTS {UserManager.USERS_TABLE_NAME}")
        UserManager.ensure_users_table()

        # Create a user
        create_user(username="dataframe_user")

        # Convert users to DataFrame
        df = UserManager.to_dataframe()

        # Verify the DataFrame contains the user
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 1
        assert "dataframe_user" in df["username"].values