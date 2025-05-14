import sqlite3
import os
from pathlib import Path

# Define the default path for the database file relative to this script's project structure
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "user_preferences.db"

class StructuredMemory:
    """
    Manages structured data storage for user preferences and other explicit facts
    using an SQLite database.
    """

    def __init__(self, db_path: str | Path | None = None):
        """
        Initializes the StructuredMemory and connects to the SQLite database.
        Creates necessary tables if they don't exist.

        Args:
            db_path: Path to the SQLite database file. Uses a default if None.
        """
        if db_path is None:
            self.db_path = DEFAULT_DB_PATH
        else:
            self.db_path = Path(db_path)

        # Ensure the data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Access columns by name
            self._create_tables()
        except sqlite3.Error as e:
            print(f"Error connecting to or initializing database at {self.db_path}: {e}")
            # Potentially raise a custom exception or handle more gracefully

    def _create_tables(self):
        """Creates the necessary tables if they don't already exist."""
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            # Table for user preferences
            # A user_id is included to support multi-user scenarios in the future,
            # defaulting to a generic 'default_user' for now.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    key TEXT NOT NULL,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, key)
                )
            """)
            # Trigger to update 'updated_at' timestamp
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS update_user_preferences_updated_at
                AFTER UPDATE ON user_preferences
                FOR EACH ROW
                BEGIN
                    UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
                END;
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")

    def store_preference(self, key: str, value: str, user_id: str = "default_user") -> bool:
        """
        Stores or updates a user preference.

        Args:
            user_id: The ID of the user.
            key: The preference key.
            value: The preference value.

        Returns:
            True if successful, False otherwise.
        """
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO user_preferences (user_id, key, value)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
            """, (user_id, key, value))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error storing preference for user '{user_id}', key '{key}': {e}")
            return False

    def get_preference(self, key: str, user_id: str = "default_user") -> str | None:
        """
        Retrieves a user preference.

        Args:
            user_id: The ID of the user.
            key: The preference key.

        Returns:
            The preference value, or None if not found or error.
        """
        if not self.conn:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM user_preferences WHERE user_id = ? AND key = ?", (user_id, key))
            row = cursor.fetchone()
            return row["value"] if row else None
        except sqlite3.Error as e:
            print(f"Error retrieving preference for user '{user_id}', key '{key}': {e}")
            return None

    def delete_preference(self, key: str, user_id: str = "default_user") -> bool:
        """
        Deletes a user preference.

        Args:
            user_id: The ID of the user.
            key: The preference key.

        Returns:
            True if successful, False otherwise.
        """
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM user_preferences WHERE user_id = ? AND key = ?", (user_id, key))
            self.conn.commit()
            return cursor.rowcount > 0 # Check if a row was actually deleted
        except sqlite3.Error as e:
            print(f"Error deleting preference for user '{user_id}', key '{key}': {e}")
            return False

    def get_all_preferences(self, user_id: str = "default_user") -> dict[str, str] | None:
        """
        Retrieves all preferences for a given user.

        Args:
            user_id: The ID of the user.

        Returns:
            A dictionary of all preferences (key-value pairs), or None if error.
        """
        if not self.conn:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT key, value FROM user_preferences WHERE user_id = ?", (user_id,))
            rows = cursor.fetchall()
            return {row["key"]: row["value"] for row in rows} if rows else {}
        except sqlite3.Error as e:
            print(f"Error retrieving all preferences for user '{user_id}': {e}")
            return None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """Ensures the connection is closed when the object is deleted."""
        self.close()

if __name__ == '__main__':
    # Example Usage and Testing
    print("Testing StructuredMemory...")
    # Uses a temporary in-memory database for testing or a specific test file
    # For production, db_path should be managed by the application.
    # Ensure the 'data' directory exists if not using an in-memory db for this test.
    
    # Create a data directory for the test if it doesn't exist
    test_data_dir = Path(__file__).resolve().parent.parent / "data"
    test_data_dir.mkdir(parents=True, exist_ok=True)
    test_db_path = test_data_dir / "test_user_preferences.db"

    # Clean up old test database if it exists
    if test_db_path.exists():
        os.remove(test_db_path)

    memory = StructuredMemory(db_path=test_db_path)

    # Test storing preferences
    print("\n--- Storing Preferences ---")
    print(f"Store 'name'='Jarvis': {memory.store_preference('name', 'Jarvis')}")
    print(f"Store 'version'='1.0': {memory.store_preference('version', '1.0')}")
    print(f"Store 'theme'='dark' for user 'henry': {memory.store_preference('theme', 'dark', user_id='henry')}")

    # Test retrieving preferences
    print("\n--- Retrieving Preferences ---")
    print(f"Get 'name': {memory.get_preference('name')}") # Expected: Jarvis
    print(f"Get 'version': {memory.get_preference('version')}") # Expected: 1.0
    print(f"Get 'theme' for user 'henry': {memory.get_preference('theme', user_id='henry')}") # Expected: dark
    print(f"Get 'non_existent_key': {memory.get_preference('non_existent_key')}") # Expected: None

    # Test updating a preference
    print("\n--- Updating Preferences ---")
    print(f"Update 'version' to '1.1': {memory.store_preference('version', '1.1')}")
    print(f"Get 'version' after update: {memory.get_preference('version')}") # Expected: 1.1

    # Test retrieving all preferences
    print("\n--- Retrieving All Preferences ---")
    print(f"All preferences for 'default_user': {memory.get_all_preferences()}")
    # Expected: {'name': 'Jarvis', 'version': '1.1'}
    print(f"All preferences for 'henry': {memory.get_all_preferences(user_id='henry')}")
    # Expected: {'theme': 'dark'}
    print(f"All preferences for 'other_user': {memory.get_all_preferences(user_id='other_user')}")
    # Expected: {}

    # Test deleting a preference
    print("\n--- Deleting Preferences ---")
    print(f"Delete 'name': {memory.delete_preference('name')}")
    print(f"Get 'name' after delete: {memory.get_preference('name')}") # Expected: None
    print(f"Delete 'theme' for user 'henry': {memory.delete_preference('theme', user_id='henry')}")
    print(f"Get 'theme' for 'henry' after delete: {memory.get_preference('theme', user_id='henry')}") # Expected: None
    print(f"Delete non_existent_key: {memory.delete_preference('non_existent_key')}") # Should be False or handle gracefully

    # Test with a different user to ensure data separation (basic test)
    print("\n--- Multi-user Basic Test ---")
    print(f"Store 'color'='blue' for 'user_A': {memory.store_preference('color', 'blue', user_id='user_A')}")
    print(f"Get 'color' for 'user_A': {memory.get_preference('color', user_id='user_A')}") # Expected: blue
    print(f"Get 'color' for 'default_user': {memory.get_preference('color')}") # Expected: None

    print("\n--- Final State ---")
    print(f"All preferences for 'default_user': {memory.get_all_preferences()}")
    print(f"All preferences for 'henry': {memory.get_all_preferences(user_id='henry')}")
    print(f"All preferences for 'user_A': {memory.get_all_preferences(user_id='user_A')}")


    # Clean up: close connection and remove test database
    memory.close()
    if test_db_path.exists():
        print(f"\nRemoving test database: {test_db_path}")
        os.remove(test_db_path)
    
    print("\nStructuredMemory test complete.") 