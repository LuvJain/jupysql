"""
User management module for JupySQL.

This module provides functionality for creating and managing users with
persistence to SQLite databases.

Examples:
    >>> from sql.user import create_user
    >>> create_user(username="johndoe", email="john@example.com")

Notes:
    User data is persisted in the SQLite database connected via the
    ConnectionManager.
"""

import datetime
import pandas as pd
from typing import Dict, Any, Optional, List, Union

from sqlalchemy import text, exc

from sql import exceptions
from sql.connection.connection import ConnectionManager


class UserManager:
    """
    Manages user-related operations such as creation and persistence.

    This class provides methods to create and manage users, ensuring they are
    properly persisted in the connected SQLite database.
    """

    USERS_TABLE_NAME = "jupysql_users"

    @classmethod
    def ensure_users_table(cls) -> None:
        """
        Ensures the users table exists in the database.

        Creates the jupysql_users table if it doesn't already exist in the
        connected database.

        Raises:
            exceptions.UsageError: If no database connection is available.
        """
        conn = ConnectionManager.current

        if conn is None:
            raise exceptions.UsageError(
                "No database connection available. "
                "Please connect to a database first with %sql."
            )

        try:
            # Check if we're connected to SQLite
            dialect = conn.dialect.lower()
            if dialect != "sqlite":
                raise exceptions.UsageError(
                    f"User persistence currently only supports SQLite. "
                    f"Connected database is {dialect}."
                )

            # Create the users table if it doesn't exist
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {cls.USERS_TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                full_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
            """

            conn.execute(create_table_sql)

        except exc.SQLAlchemyError as e:
            raise exceptions.UsageError(
                f"Failed to create users table: {str(e)}"
            )

    @classmethod
    def create_user(cls, username: str, email: Optional[str] = None,
                   full_name: Optional[str] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates a new user and persists it to the database.

        Args:
            username: Unique username for the user
            email: Optional email address
            full_name: Optional full name
            metadata: Optional JSON-serializable metadata

        Returns:
            Dict containing the created user information

        Raises:
            exceptions.UsageError: If user creation fails
        """
        import json

        # Ensure the users table exists
        cls.ensure_users_table()

        conn = ConnectionManager.current

        # Convert metadata to JSON string if provided
        metadata_json = None
        if metadata is not None:
            try:
                metadata_json = json.dumps(metadata)
            except (TypeError, ValueError) as e:
                raise exceptions.UsageError(
                    f"Invalid metadata: {str(e)}. Must be JSON serializable."
                )

        # Current timestamp for created_at and updated_at
        now = datetime.datetime.now().isoformat()

        try:
            # Insert the user into the database
            insert_sql = f"""
            INSERT INTO {cls.USERS_TABLE_NAME}
            (username, email, full_name, created_at, updated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            """

            result = conn.execute(
                insert_sql,
                (username, email, full_name, now, now, metadata_json)
            )

            # Get the inserted user's ID
            if hasattr(result, 'lastrowid'):
                user_id = result.lastrowid
            else:
                # Get the last inserted ID if result doesn't have lastrowid
                last_id_result = conn.execute("SELECT last_insert_rowid()")
                user_id = last_id_result.fetchone()[0]

            # Return the created user
            user_data = {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'created_at': now,
                'updated_at': now,
                'metadata': metadata
            }

            return user_data

        except exc.IntegrityError:
            raise exceptions.UsageError(
                f"User with username '{username}' or email '{email}' already exists."
            )
        except exc.SQLAlchemyError as e:
            raise exceptions.UsageError(
                f"Failed to create user: {str(e)}"
            )

    @classmethod
    def get_user(cls, username: Optional[str] = None,
                user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves a user by username or ID.

        Args:
            username: Username to look up
            user_id: User ID to look up

        Returns:
            Dict containing the user information or None if not found

        Raises:
            exceptions.UsageError: If no lookup criteria is provided or if an error occurs
        """
        import json

        if username is None and user_id is None:
            raise exceptions.UsageError(
                "Either username or user_id must be provided."
            )

        # Ensure the users table exists
        cls.ensure_users_table()

        conn = ConnectionManager.current

        try:
            if username is not None:
                query = f"SELECT * FROM {cls.USERS_TABLE_NAME} WHERE username = ?"
                result = conn.execute(query, (username,))
            else:
                query = f"SELECT * FROM {cls.USERS_TABLE_NAME} WHERE id = ?"
                result = conn.execute(query, (user_id,))

            row = result.fetchone()

            if row is None:
                return None

            # Convert row to dict based on column names
            user_dict = {}
            for idx, column in enumerate(result.keys()):
                if column == 'metadata' and row[idx] is not None:
                    # Parse JSON metadata
                    try:
                        user_dict[column] = json.loads(row[idx])
                    except json.JSONDecodeError:
                        user_dict[column] = row[idx]
                else:
                    user_dict[column] = row[idx]

            return user_dict

        except exc.SQLAlchemyError as e:
            raise exceptions.UsageError(
                f"Failed to retrieve user: {str(e)}"
            )

    @classmethod
    def get_all_users(cls) -> List[Dict[str, Any]]:
        """
        Retrieves all users from the database.

        Returns:
            List of dicts containing user information

        Raises:
            exceptions.UsageError: If an error occurs
        """
        import json

        # Ensure the users table exists
        cls.ensure_users_table()

        conn = ConnectionManager.current

        try:
            query = f"SELECT * FROM {cls.USERS_TABLE_NAME} ORDER BY id"
            result = conn.execute(query)

            users = []
            for row in result:
                # Convert row to dict based on column names
                user_dict = {}
                for idx, column in enumerate(result.keys()):
                    if column == 'metadata' and row[idx] is not None:
                        # Parse JSON metadata
                        try:
                            user_dict[column] = json.loads(row[idx])
                        except json.JSONDecodeError:
                            user_dict[column] = row[idx]
                    else:
                        user_dict[column] = row[idx]

                users.append(user_dict)

            return users

        except exc.SQLAlchemyError as e:
            raise exceptions.UsageError(
                f"Failed to retrieve users: {str(e)}"
            )

    @classmethod
    def user_exists(cls, username: str) -> bool:
        """
        Checks if a user with the given username exists.

        Args:
            username: The username to check

        Returns:
            True if the user exists, False otherwise
        """
        return cls.get_user(username=username) is not None

    @classmethod
    def to_dataframe(cls) -> pd.DataFrame:
        """
        Converts the users table to a pandas DataFrame.

        Returns:
            pandas.DataFrame containing all users

        Raises:
            exceptions.UsageError: If pandas is not installed or an error occurs
        """
        if not pd:
            raise exceptions.MissingPackageError(
                "pandas is required to convert users to DataFrame. "
                "Install with: pip install pandas"
            )

        # Get all users
        users = cls.get_all_users()

        # Convert to DataFrame
        return pd.DataFrame(users)


# Module-level functions for direct use

def create_user(username: str, email: Optional[str] = None,
               full_name: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Creates a new user in the database.

    Args:
        username: Unique username for the user
        email: Optional email address
        full_name: Optional full name
        metadata: Optional JSON-serializable metadata

    Returns:
        Dict containing the created user information

    Examples:
        >>> from sql.user import create_user
        >>> create_user('johndoe', email='john@example.com')
        {'id': 1, 'username': 'johndoe', 'email': 'john@example.com', ...}
    """
    return UserManager.create_user(
        username=username,
        email=email,
        full_name=full_name,
        metadata=metadata
    )


def get_user(username: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves a user by username or ID.

    Args:
        username: Username to look up
        user_id: User ID to look up

    Returns:
        Dict containing the user information or None if not found

    Examples:
        >>> from sql.user import get_user
        >>> get_user(username='johndoe')
        {'id': 1, 'username': 'johndoe', 'email': 'john@example.com', ...}
    """
    return UserManager.get_user(username=username, user_id=user_id)


def get_all_users() -> List[Dict[str, Any]]:
    """
    Retrieves all users from the database.

    Returns:
        List of dicts containing user information

    Examples:
        >>> from sql.user import get_all_users
        >>> get_all_users()
        [{'id': 1, 'username': 'johndoe', ...}, {'id': 2, 'username': 'janedoe', ...}]
    """
    return UserManager.get_all_users()


def user_exists(username: str) -> bool:
    """
    Checks if a user with the given username exists.

    Args:
        username: The username to check

    Returns:
        True if the user exists, False otherwise

    Examples:
        >>> from sql.user import user_exists
        >>> user_exists('johndoe')
        True
    """
    return UserManager.user_exists(username=username)


def users_to_dataframe() -> pd.DataFrame:
    """
    Converts the users table to a pandas DataFrame.

    Returns:
        pandas.DataFrame containing all users

    Examples:
        >>> from sql.user import users_to_dataframe
        >>> df = users_to_dataframe()
        >>> df.head()
          id  username          email full_name            created_at            updated_at metadata
        0  1   johndoe  john@example.com      John  2023-01-01T12:00:00  2023-01-01T12:00:00     None
    """
    return UserManager.to_dataframe()