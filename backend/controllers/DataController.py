import json
import os
import portalocker
from typing import Any, Dict

class DataController:
    """
    DataController handles atomic reads and writes to local JSON files.
    It uses portalocker to prevent data corruption during concurrent access
    by the FastAPI server, Telegram polling, and Gmail ingestion loops.
    """
    
    def __init__(self, data_dir: str = "data"):
        # Anchor the data directory relative to the project root
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.data_dir = os.path.join(root_dir, data_dir)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

    def _get_file_path(self, filename: str) -> str:
        # Ensure the filename ends with .json
        if not filename.endswith('.json'):
            filename += '.json'
        return os.path.join(self.data_dir, filename)

    def read_json(self, filename: str, default_val: Any = None) -> Any:
        """
        Reads a JSON file with a shared lock.
        Returns `default_val` (defaults to empty dict if None) if the file doesn't exist.
        """
        if default_val is None:
            default_val = {}
            
        filepath = self._get_file_path(filename)
        
        if not os.path.exists(filepath):
            return default_val

        try:
            with portalocker.Lock(filepath, mode='r', timeout=5) as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default_val
        except portalocker.exceptions.LockException:
            # In case the file is heavily locked, we might want to retry or raise
            # For now, return default_val or raise a custom error. Let's raise.
            raise RuntimeError(f"Could not acquire read lock on {filepath}")

    def write_json(self, filename: str, data: Any) -> None:
        """
        Writes data to a JSON file with an exclusive lock.
        """
        filepath = self._get_file_path(filename)
        
        try:
            # mode 'w' truncates the file. portalocker.Lock will acquire an exclusive lock
            # preventing other processes/threads from reading or writing while this is open.
            with portalocker.Lock(filepath, mode='w', timeout=5) as f:
                json.dump(data, f, indent=4)
        except portalocker.exceptions.LockException:
            raise RuntimeError(f"Could not acquire write lock on {filepath}")

    def update_json(self, filename: str, update_dict: Dict[str, Any]) -> None:
        """
        Convenience method to read, update with a dictionary, and write back.
        Uses an exclusive lock 'r+' to read and write without releasing the lock.
        """
        filepath = self._get_file_path(filename)
        
        if not os.path.exists(filepath):
            # If it doesn't exist, just write the new dict
            self.write_json(filename, update_dict)
            return

        try:
            with portalocker.Lock(filepath, mode='r+', timeout=5) as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        data = {}
                except json.JSONDecodeError:
                    data = {}
                
                # Update the data
                data.update(update_dict)
                
                # Seek to beginning, rewrite, and truncate
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except portalocker.exceptions.LockException:
            raise RuntimeError(f"Could not acquire update lock on {filepath}")
