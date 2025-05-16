import os


class FileHandler:
    """
    Utility class for file handling operations
    """
    @staticmethod
    def cleanup_temp_files(directory: str, max_age_hours: int = 24) -> None:
        """
        Clean up temporary files older than specified hours
        
        :param directory: Directory to clean
        :param max_age_hours: Maximum age of files to keep
        """
        import time
        
        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                # Skip if not a file
                if not os.path.isfile(file_path):
                    continue
                
                # Check file age
                file_age = time.time() - os.path.getctime(file_path)
                if file_age > (max_age_hours * 3600):
                    try:
                        os.unlink(file_path)
                    except Exception as e:
                        print(f"Error deleting {filename}: {e}")
        except Exception as e:
            print(f"Error in cleanup_temp_files: {e}")