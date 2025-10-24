# utils/file_utils.py
import os
import shutil
from datetime import datetime

def get_file_size_human(file_path):
    """Get human-readable file size"""
    try:
        size_bytes = os.path.getsize(file_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} GB"
    except:
        return "Unknown size"

def export_user_photos(store, mobile, export_dir=None):
    """Export all photos for a user"""
    if export_dir is None:
        export_dir = os.path.join(os.path.expanduser("~"), "PhotoExports", f"user_{mobile}")
    
    os.makedirs(export_dir, exist_ok=True)
    exported_files = []
    
    uploads = store.list_uploads_for_user(mobile)
    for upload in uploads:
        filename = os.path.basename(upload.path)
        dest_path = os.path.join(export_dir, filename)
        shutil.copy2(upload.path, dest_path)
        exported_files.append(dest_path)
    
    return exported_files, export_dir

def calculate_storage_usage(store):
    """Calculate total storage usage across all users"""
    total_size = 0
    user_stats = {}
    
    for user in store.list_users():
        user_size = 0
        uploads = store.list_uploads_for_user(user)
        for upload in uploads:
            try:
                size = os.path.getsize(upload.path)
                user_size += size
                total_size += size
            except:
                pass
        user_stats[user] = user_size
    
    return total_size, user_stats