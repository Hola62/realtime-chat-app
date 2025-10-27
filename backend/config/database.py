import os
from typing import Optional

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """Read env var with optional fallback key name.
    Supports both MYSQL_* and DATABASE_* naming to reduce config friction.
    """
    value = os.getenv(name)
    if value is not None:
        return value
    # Map MYSQL_* -> DATABASE_* and vice versa
    mapping = {
        "MYSQL_HOST": "DATABASE_HOST",
        "MYSQL_PORT": "DATABASE_PORT",
        "MYSQL_USER": "DATABASE_USER",
        "MYSQL_PASSWORD": "DATABASE_PASSWORD",
        "MYSQL_DB": "DATABASE_NAME",
        "DATABASE_HOST": "MYSQL_HOST",
        "DATABASE_PORT": "MYSQL_PORT",
        "DATABASE_USER": "MYSQL_USER",
        "DATABASE_PASSWORD": "MYSQL_PASSWORD",
        "DATABASE_NAME": "MYSQL_DB",
    }
    alt = mapping.get(name)
    if alt:
        return os.getenv(alt, fallback)
    return fallback


def get_connection():
    """Create a new MySQL connection using environment variables.

    Env keys supported (preferred): MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB
    Also supported (fallback): DATABASE_HOST, DATABASE_PORT, DATABASE_USER, DATABASE_PASSWORD, DATABASE_NAME
    """
    host = _get_env("MYSQL_HOST", "127.0.0.1")
    port = int(_get_env("MYSQL_PORT", "3306") or 3306)
    user = _get_env("MYSQL_USER", "root")
    password = _get_env("MYSQL_PASSWORD", "")
    database = _get_env("MYSQL_DB")

    try:
        connection = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            auth_plugin=os.getenv("MYSQL_AUTH_PLUGIN"),  # optional
        )
        return connection
    except Error as e:
        print("Error connecting to MySQL:", e)
        return None
