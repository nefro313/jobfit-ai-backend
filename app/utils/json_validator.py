import json
import os
import re


class JSONValidator:
    def __init__(self, file_path):
        """
        Initialize the JSON validator with a file path.
        
        Args:
            file_path (str): Path to the JSON file to validate
        """
        self.file_path = file_path
        
    def read_file(self):
        """
        Read the content of the JSON file.
        
        Returns:
            str: Content of the file, or None if file doesn't exist
        """
        if not os.path.exists(self.file_path):
            print(f"File {self.file_path} doesn't exist!")
            return None
            
        try:
            with open(self.file_path, encoding="utf-8") as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def clean_json_string(self, json_str):
        """
        Clean the JSON string by removing markdown code block syntax.
        
        Args:
            json_str (str): Raw JSON string that might contain markdown syntax
            
        Returns:
            str: Cleaned JSON string
        """
        if json_str is None:
            return None
            
        # Remove markdown code block syntax if present
        # Pattern matches ```json at the start and ``` at the end
        pattern = r"^```json(.*?)```$"
        match = re.search(pattern, json_str, re.DOTALL)
        
        if match:
            # Extract just the JSON data
            return match.group(1).strip()
        
        return json_str
    
    def validate_json(self):
        """
        Validate and clean the JSON file.
        
        Returns:
            dict: Parsed JSON data if valid
            None: If JSON is invalid or file doesn't exist
        """
        # Read the file
        content = self.read_file()
        if content is None:
            return None
        
        # Clean the JSON string
        cleaned_content = self.clean_json_string(content)
        
        # Try to parse the JSON
        try:
            json_data = json.loads(cleaned_content)
            return json_data
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return None
    
    def save_cleaned_json(self):
        """
        Clean the JSON file and save it back if needed.
        
        Returns:
            dict: The validated JSON data
            None: If validation failed
        """
        # Read the file
        content = self.read_file()
        if content is None:
            return None
        
        # Check if cleaning is needed
        cleaned_content = self.clean_json_string(content)
        
        # If content was modified, save it back
        if cleaned_content != content:
            try:
                # Try to parse to ensure it's valid JSON
                json_data = json.loads(cleaned_content)
                
                # Write back to file with proper formatting
                with open(self.file_path, "w", encoding="utf-8") as file:
                    json.dump(json_data, file, indent=2)
                
                print(f"Cleaned and saved JSON to {self.file_path}")
                return json_data
            except json.JSONDecodeError as e:
                print(f"Failed to clean JSON: {e}")
                return None
        else:
            # No cleaning needed, just validate
            try:
                json_data = json.loads(content)
                print("JSON is already properly formatted.")
                return json_data
            except json.JSONDecodeError as e:
                print(f"Invalid JSON and cleaning didn't help: {e}")
                return None


# Example usage
def validate_tailor_resume_json(file_path):
    """
    Validate the tailor_resume.json file.
    
    Returns:
        dict: The JSON data if valid
        None: If validation failed
    """
    validator = JSONValidator(file_path)
    return validator.save_cleaned_json()


