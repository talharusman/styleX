"""
Database Repositories

Provides data access layer for MongoDB collections.
"""

from .user_repo import (
    UserRepository,
    user_repository,
    get_user_repository,
    hash_password,
    verify_password,
)
from .clothing_repo import (
    ClothingRepository,
    clothing_repository,
    get_clothing_repository,
)
from .chat_repo import (
    ChatRepository,
    chat_repository,
    get_chat_repository,
)

__all__ = [
    # User Repository
    "UserRepository",
    "user_repository",
    "get_user_repository",
    "hash_password",
    "verify_password",
    # Clothing Repository
    "ClothingRepository",
    "clothing_repository",
    "get_clothing_repository",
    # Chat Repository
    "ChatRepository",
    "chat_repository",
    "get_chat_repository",
]
