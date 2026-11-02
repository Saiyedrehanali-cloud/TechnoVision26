"""
Packaging script for TechnoVision 2026-27 project submission.
Uses Python standard library (zipfile) to build a clean deliverable package:
TechnoVision_ASR_Simulator.zip
"""

import os
import zipfile

ZIP_NAME = "TechnoVision_ASR_Simulator.zip"

EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache'}
EXCLUDE_FILES = {'.gitignore', ZIP_NAME}

def package_submission():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(root_dir, ZIP_NAME)
    
    print(f"Creating submission package: {ZIP_NAME}...")
    
    file_count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file in EXCLUDE_FILES or file.endswith('.pyc'):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                zipf.write(full_path, rel_path)
                file_count += 1
                
    zip_size_kb = os.path.getsize(zip_path) / 1024.0
    print(f"[OK] Successfully packaged {file_count} files into {ZIP_NAME} ({zip_size_kb:.1f} KB).")
    print(f"Deliverable archive ready at: {zip_path}")

if __name__ == '__main__':
    package_submission()

