import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from app.config import settings

class DatabaseManager:
    @staticmethod
    @contextmanager
    def get_connection():
        connection = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            cursorclass=DictCursor,
            autocommit=False
        )
        try:
            yield connection
        finally:
            connection.close()