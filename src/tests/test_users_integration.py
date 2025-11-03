import pytest
from sql.connection import ConnectionManager


@pytest.fixture
def sqlite_connection(ip_empty):
    """Setup a SQLite connection for testing user operations"""
    ip_empty.run_cell("%sql sqlite://")
    return ConnectionManager.current


class TestUsersIntegration:
    """Test the integration of users command with magic_cmd"""

    def test_users_command_in_available_commands(self, ip_empty):
        """Test that 'users' is in the available commands list"""
        # Run the help command to get available commands
        output = ip_empty.run_line_magic("sqlcmd", "")

        # Check that the error message mentions 'users' as an available command
        assert "users" in output.output_type.error

    def test_users_command_execution(self, sqlite_connection, ip_empty):
        """Test executing the users command through magic_cmd"""
        # Create a user using the %sqlcmd magic
        result = ip_empty.run_line_magic(
            "sqlcmd", "users create --username magiccmduser --email magic@example.com"
        )

        # Verify the result is a success message
        assert "User created" in str(result)
        assert "magiccmduser" in str(result)

        # Get the user using the %sqlcmd magic
        result = ip_empty.run_line_magic(
            "sqlcmd", "users get --username magiccmduser"
        )

        # Verify the result contains the user information
        assert "User found" in str(result)
        assert "magiccmduser" in str(result)
        assert "magic@example.com" in str(result)

        # List users using the %sqlcmd magic
        result = ip_empty.run_line_magic(
            "sqlcmd", "users list"
        )

        # Verify the result contains user information
        assert result is not None
        result_str = str(result)
        assert "magiccmduser" in result_str

    def test_users_command_connection_required(self, ip_empty):
        """Test that users command requires a connection"""
        # Close any existing connections
        ConnectionManager.close_all()
        ConnectionManager.current = None

        # Try to execute the users command without a connection
        with pytest.raises(Exception) as excinfo:
            ip_empty.run_line_magic("sqlcmd", "users list")

        # Verify the error message indicates a connection is required
        assert "no active connection" in str(excinfo.value).lower()

    def test_users_command_requires_sqlite(self, ip_empty):
        """Test that users command only works with SQLite"""
        # This test would require mocking a non-SQLite connection
        # For simplicity, we'll just verify the error message exists in the users.py module
        from sql.cmd.users import users

        # Check if the error message mentions SQLite requirement
        with pytest.raises(Exception) as excinfo:
            # Simulate a non-SQLite connection by patching the dialect check
            ConnectionManager.current.dialect = "mysql"
            users(["list"])

        # Verify the error message mentions SQLite requirement
        assert "only supports SQLite" in str(excinfo.value)