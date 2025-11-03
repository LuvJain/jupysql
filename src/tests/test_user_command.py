import pytest
import json
from sql.connection import ConnectionManager
from sql.cmd.users import users
import pandas as pd


@pytest.fixture
def sqlite_connection(ip_empty):
    """Setup a SQLite connection for testing user operations"""
    ip_empty.run_cell("%sql sqlite://")
    return ConnectionManager.current


class TestUsersCommand:
    """Test the %sqlcmd users command functionality"""

    def test_users_command_create(self, sqlite_connection):
        """Test creating a user with the users command"""
        # Create a user using the command
        result = users(["create", "--username", "cmduser", "--email", "cmd@example.com",
                        "--full-name", "Command User"])

        # Verify the result contains confirmation of user creation
        assert isinstance(result, str)
        assert "User created" in result
        assert "cmduser" in result
        assert "cmd@example.com" in result
        assert "Command User" in result

    def test_users_command_create_with_metadata(self, sqlite_connection):
        """Test creating a user with metadata using the users command"""
        # Create a user with metadata
        metadata = '{"role": "admin", "department": "IT"}'
        result = users(["create", "--username", "metauser", "--metadata", metadata])

        # Verify the result contains confirmation of user creation with metadata
        assert isinstance(result, str)
        assert "User created" in result
        assert "metauser" in result
        assert "admin" in result  # The result string should include the metadata

    def test_users_command_get(self, sqlite_connection):
        """Test getting a user with the users command"""
        # First create a user
        users(["create", "--username", "getuser", "--email", "get@example.com"])

        # Get the user
        result = users(["get", "--username", "getuser"])

        # Verify the result contains the user information
        assert isinstance(result, str)
        assert "User found" in result
        assert "getuser" in result
        assert "get@example.com" in result

    def test_users_command_get_nonexistent(self, sqlite_connection):
        """Test getting a nonexistent user with the users command"""
        # Try to get a nonexistent user
        result = users(["get", "--username", "nonexistentuser"])

        # Verify the result indicates the user was not found
        assert isinstance(result, str)
        assert "User not found" in result
        assert "nonexistentuser" in result

    def test_users_command_list(self, sqlite_connection):
        """Test listing all users with the users command"""
        # First create a couple of users
        users(["create", "--username", "user1", "--email", "user1@example.com"])
        users(["create", "--username", "user2", "--email", "user2@example.com"])

        # List all users
        result = users(["list"])

        # Verify the result is a DataFrame or contains user information
        assert result is not None
        # Could be a DataFrame (if pandas is installed) or a string (if pandas is not installed)
        if isinstance(result, pd.DataFrame):
            assert len(result) >= 2
            usernames = result["username"].tolist()
            assert "user1" in usernames
            assert "user2" in usernames
        else:
            assert isinstance(result, str)
            assert "Users:" in result
            assert "user1" in result
            assert "user2" in result

    def test_users_command_no_subcommand(self, sqlite_connection):
        """Test that calling the users command without a subcommand raises an error"""
        # Call the users command without a subcommand
        with pytest.raises(Exception) as excinfo:
            users([])

        # Verify the error message indicates a subcommand is required
        assert "Please specify a subcommand" in str(excinfo.value)

    def test_users_command_invalid_args(self, sqlite_connection):
        """Test that calling the users command with invalid arguments raises an error"""
        # Call the create command without required arguments
        with pytest.raises(Exception) as excinfo:
            users(["create"])

        # Verify the error message indicates invalid arguments
        assert "Invalid arguments" in str(excinfo.value)