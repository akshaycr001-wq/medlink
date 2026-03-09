import os
import zipfile
from datetime import datetime

def create_backup():
    # Define source directory and exclusion list
    source_dir = r"c:\Users\eldho\Downloads\Templatefolder"
    
    # Target Google Drive location provided by user
    target_dir = r"C:\Users\eldho\Google Drive"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)
        print(f"Created directory: {target_dir}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"MedLink_Project_Backup_{timestamp}.zip"
    zip_path = os.path.join(target_dir, zip_filename)
    
    exclude_dirs = {'.git', 'venv', '__pycache__', 'instance', '.gemini'}
    exclude_files = {'.env', 'database.db', 'reg_test.log'}

    print(f"Starting backup of {source_dir} to {zip_path}...")
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                # Modify dirs in-place to skip excluded directories
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    if file in exclude_files:
                        continue
                    
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Success! Backup saved to: {zip_path}")
    except Exception as e:
        print(f"Error creating backup: {e}")

if __name__ == "__main__":
    create_backup()
