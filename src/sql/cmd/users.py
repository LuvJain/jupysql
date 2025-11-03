"""
Users command for JupySQL.

This module provides a command to create and manage users in the connected
SQLite database.

Examples:
    %sqlcmd users create --username johndoe --email john@example.com
    %sqlcmd users list
    %sqlcmd users get --username johndoe
"""

import argparse
from sql import exceptions
from sql.user import create_user, get_user, get_all_users, users_to_dataframe
from sql.connection import ConnectionManager


def users(others):
    """Handle user-related operations.

    Args:
        others: The arguments passed to the users command.

    Returns:
        The result of the user operation.

    Examples:
        %sqlcmd users create --username johndoe --email john@example.com
        %sqlcmd users list
        %sqlcmd users get --username johndoe
    """
    parser = argparse.ArgumentParser(
        prog="%sqlcmd users",
        description="Create and manage users in the connected database"
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new user")
    create_parser.add_argument(
        "--username", required=True, help="Username for the new user"
    )
    create_parser.add_argument(
        "--email", help="Email address for the user"
    )
    create_parser.add_argument(
        "--full-name", help="Full name of the user"
    )
    create_parser.add_argument(
        "--metadata", help="JSON metadata for the user (e.g., '{\"role\": \"admin\"}')"
    )

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a user by username")
    get_parser.add_argument(
        "--username", required=True, help="Username of the user to retrieve"
    )

    # List command
    subparsers.add_parser("list", help="List all users")

    # Parse arguments
    try:
        args = parser.parse_args(others)
    except SystemExit:
        raise exceptions.UsageError("Invalid arguments for %sqlcmd users")

    # Check if we have a subcommand
    if not args.subcommand:
        raise exceptions.UsageError(
            "Please specify a subcommand: create, get, or list"
        )

    # Check if we're connected to a database
    if not ConnectionManager.current:
        raise exceptions.UsageError(
            "No database connection available. "
            "Please connect to a database first with %sql."
        )

    # Check if we're connected to SQLite
    dialect = ConnectionManager.current.dialect.lower()
    if dialect != "sqlite":
        raise exceptions.UsageError(
            f"User management currently only supports SQLite. "
            f"Connected database is {dialect}."
        )

    # Execute the appropriate subcommand
    if args.subcommand == "create":
        metadata = None
        if args.metadata:
            import json
            try:
                metadata = json.loads(args.metadata)
            except json.JSONDecodeError:
                raise exceptions.UsageError(
                    f"Invalid JSON metadata: {args.metadata}"
                )

        user = create_user(
            username=args.username,
            email=args.email,
            full_name=args.full_name,
            metadata=metadata
        )

        return f"User created: {user}"

    elif args.subcommand == "get":
        user = get_user(username=args.username)
        if user:
            return f"User found: {user}"
        else:
            return f"User not found: {args.username}"

    elif args.subcommand == "list":
        try:
            # Try to return a DataFrame for better display
            return users_to_dataframe()
        except exceptions.MissingPackageError:
            # Fall back to regular list if pandas isn't installed
            users_list = get_all_users()
            if users_list:
                return f"Users: {users_list}"
            else:
                return "No users found"

    return None