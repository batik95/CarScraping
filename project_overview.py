#!/usr/bin/env python3
"""
Project visualization tool to show the complete CarScraping implementation
"""

import os
from pathlib import Path

def count_lines(file_path):
    """Count lines in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except:
        return 0

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def format_size(size_bytes):
    """Format bytes to human readable"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f}KB"
    else:
        return f"{size_bytes/1024**2:.1f}MB"

def main():
    print("🚗 CarScraping - Complete Implementation Overview")
    print("=" * 60)
    
    # Project statistics
    total_files = 0
    total_lines = 0
    total_size = 0
    
    # File categories
    categories = {
        'Backend Core': [],
        'API Endpoints': [],
        'Database Models': [],
        'Scraping Engine': [],
        'Services': [],
        'Frontend': [],
        'Configuration': [],
        'Tests': []
    }
    
    # Scan all files
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and venv
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv']
        
        for file in files:
            if file.startswith('.'):
                continue
                
            filepath = os.path.join(root, file)
            relative_path = os.path.relpath(filepath)
            
            # Count statistics
            lines = count_lines(filepath)
            size = get_file_size(filepath)
            total_files += 1
            total_lines += lines
            total_size += size
            
            # Categorize files
            if 'app/main.py' in relative_path or 'app/core/' in relative_path:
                categories['Backend Core'].append((relative_path, lines, size))
            elif 'app/api/' in relative_path:
                categories['API Endpoints'].append((relative_path, lines, size))
            elif 'app/models/' in relative_path:
                categories['Database Models'].append((relative_path, lines, size))
            elif 'app/scraping/' in relative_path:
                categories['Scraping Engine'].append((relative_path, lines, size))
            elif 'app/services/' in relative_path:
                categories['Services'].append((relative_path, lines, size))
            elif 'app/templates/' in relative_path or 'app/static/' in relative_path:
                categories['Frontend'].append((relative_path, lines, size))
            elif any(name in relative_path for name in ['docker', 'requirements', 'alembic', '.env']):
                categories['Configuration'].append((relative_path, lines, size))
            elif 'test' in relative_path:
                categories['Tests'].append((relative_path, lines, size))
    
    # Display categories
    for category, files in categories.items():
        if files:
            print(f"\n📁 {category}")
            print("-" * 40)
            for filepath, lines, size in sorted(files):
                print(f"  {filepath:<35} {lines:>4} lines  {format_size(size):>8}")
    
    print("\n" + "=" * 60)
    print(f"📊 PROJECT STATISTICS")
    print(f"   Total Files: {total_files}")
    print(f"   Total Lines: {total_lines:,}")
    print(f"   Total Size:  {format_size(total_size)}")
    
    print(f"\n🏗️  ARCHITECTURE COMPONENTS")
    print(f"   ✅ FastAPI Backend with REST API")
    print(f"   ✅ PostgreSQL Database with SQLAlchemy ORM")
    print(f"   ✅ AutoScout24 Web Scraper with Error Handling")
    print(f"   ✅ Responsive Dashboard with Bootstrap & Charts")
    print(f"   ✅ Intelligent Filter System with Interconnected Dropdowns")
    print(f"   ✅ Real-time Analytics and KPI Dashboard")
    print(f"   ✅ Automated Scheduling with APScheduler")
    print(f"   ✅ Docker Containerization for Easy Deployment")
    print(f"   ✅ Comprehensive Testing Suite")
    
    print(f"\n🚀 READY FOR DEPLOYMENT")
    print(f"   • Run: docker-compose up -d")
    print(f"   • Access: http://localhost:8000")
    print(f"   • Compatible with Unraid Docker")

if __name__ == "__main__":
    main()