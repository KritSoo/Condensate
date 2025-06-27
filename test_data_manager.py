"""
Test script for data_manager module
"""

import os
import logging
from datetime import datetime
from data_manager import (
    get_project_dir, get_data_file_path, save_data, 
    init_data_files, generate_mock_data, verify_data_file
)

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_data_manager():
    """Test the main functionality of data_manager"""
    print("===== TESTING DATA MANAGER =====")
    
    # 1. Check project directory
    proj_dir = get_project_dir()
    print(f"Project directory: {proj_dir}")
    print(f"Directory exists: {os.path.exists(proj_dir)}")
    
    # 2. Initialize data files
    print("\nInitializing data files...")
    init_data_files()
    
    # 3. Get file paths
    mock_path = get_data_file_path(mock_mode=True)
    real_path = get_data_file_path(mock_mode=False)
    print(f"Mock data file: {mock_path}")
    print(f"Real data file: {real_path}")
    
    # 4. Save test data
    now = datetime.now()
    print("\nSaving test data point...")
    result = save_data(now, 123.45, "µS/cm", 25.5)
    print(f"Save result: {'Success' if result else 'Failed'}")
    
    # 5. Generate mock data
    print("\nGenerating mock data...")
    mock_result = generate_mock_data(num_days=1)  # Just 1 day of data for the test
    print(f"Mock data generation: {'Success' if mock_result else 'Failed'}")
    
    # 6. Verify files
    print("\nVerifying data files...")
    mock_valid = verify_data_file(mock_path)
    real_valid = verify_data_file(real_path)
    print(f"Mock file valid: {mock_valid}")
    print(f"Real file valid: {real_valid}")
    
    # 7. Display file sizes
    try:
        mock_size = os.path.getsize(mock_path) if os.path.exists(mock_path) else 0
        real_size = os.path.getsize(real_path) if os.path.exists(real_path) else 0
        print(f"\nMock file size: {mock_size} bytes")
        print(f"Real file size: {real_size} bytes")
    except Exception as e:
        print(f"Error checking file sizes: {e}")
    
    print("\n===== TEST COMPLETE =====")

if __name__ == "__main__":
    test_data_manager()
