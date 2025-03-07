import sys
import os

# Thêm thư mục gốc vào sys.path để import các module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from location.main import LocationService

def test_search_by_coordinates():
    """Kiểm tra chức năng tìm kiếm quán ăn theo tọa độ"""
    # Tọa độ trung tâm Hà Nội
    latitude = 21.0278
    longitude = 105.8342
    
    print(f"Tìm kiếm quán ăn gần vị trí: {latitude}, {longitude}")
    restaurants = LocationService.search_restaurants_by_coordinates(latitude, longitude, radius=1000)
    
    print(f"Tìm thấy {len(restaurants)} quán ăn")
    
    # Hiển thị top 3 quán ăn
    top_restaurants = LocationService.get_top_restaurants(restaurants, limit=3)
    for i, restaurant in enumerate(top_restaurants, 1):
        print(f"\n--- Quán ăn #{i} ---")
        print(LocationService.format_restaurant_info(restaurant))

def test_search_by_address():
    """Kiểm tra chức năng tìm kiếm quán ăn theo địa chỉ"""
    address = "Hồ Hoàn Kiếm, Hà Nội"
    
    print(f"Tìm kiếm quán ăn gần địa chỉ: {address}")
    restaurants = LocationService.search_restaurants_by_address(address, radius=1000)
    
    print(f"Tìm thấy {len(restaurants)} quán ăn")
    
    # Hiển thị top 3 quán ăn
    top_restaurants = LocationService.get_top_restaurants(restaurants, limit=3)
    for i, restaurant in enumerate(top_restaurants, 1):
        print(f"\n--- Quán ăn #{i} ---")
        print(LocationService.format_restaurant_info(restaurant))

if __name__ == "__main__":
    print("=== Kiểm tra tìm kiếm theo tọa độ ===")
    test_search_by_coordinates()
    
    print("\n=== Kiểm tra tìm kiếm theo địa chỉ ===")
    test_search_by_address() 