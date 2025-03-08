import requests
import logging
from typing import List, Dict, Any, Tuple, Optional
from geopy.distance import geodesic

# Cấu hình logging
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình API
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"

class LocationService:
    """Dịch vụ xử lý vị trí và tìm kiếm quán ăn"""
    
    @staticmethod
    def search_restaurants_by_coordinates(latitude: float, longitude: float, criteria: List[str] = None, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Tìm kiếm quán ăn gần vị trí được chỉ định
        
        Args:
            latitude: Vĩ độ
            longitude: Kinh độ
            criteria: Danh sách tiêu chí để lọc kết quả
            radius: Bán kính tìm kiếm (mét)
            
        Returns:
            Danh sách các quán ăn tìm thấy
        """
        try:
            # Xây dựng truy vấn Overpass QL
            # Mở rộng truy vấn để tìm kiếm nhiều loại địa điểm ăn uống
            overpass_query = f"""
            [out:json];
            (
              node["amenity"="restaurant"](around:{radius},{latitude},{longitude});
              node["amenity"="cafe"](around:{radius},{latitude},{longitude});
              node["amenity"="fast_food"](around:{radius},{latitude},{longitude});
              node["amenity"="food_court"](around:{radius},{latitude},{longitude});
              node["shop"="convenience"](around:{radius},{latitude},{longitude});
              node["cuisine"](around:{radius},{latitude},{longitude});
              way["amenity"="restaurant"](around:{radius},{latitude},{longitude});
              way["amenity"="cafe"](around:{radius},{latitude},{longitude});
              way["amenity"="fast_food"](around:{radius},{latitude},{longitude});
              way["amenity"="food_court"](around:{radius},{latitude},{longitude});
              way["cuisine"](around:{radius},{latitude},{longitude});
            );
            out body;
            >;
            out skel qt;
            """
            
            # Gửi yêu cầu đến Overpass API
            response = requests.post(OVERPASS_API_URL, data={"data": overpass_query})
            response.raise_for_status()
            data = response.json()
            
            # Xử lý kết quả
            restaurants = []
            for element in data.get("elements", []):
                if element.get("type") in ["node", "way"]:
                    tags = element.get("tags", {})
                    
                    # Chỉ lấy các địa điểm có tên
                    if "name" in tags:
                        # Tính khoảng cách từ vị trí người dùng
                        if "lat" in element and "lon" in element:
                            distance = geodesic(
                                (latitude, longitude),
                                (element["lat"], element["lon"])
                            ).meters
                        else:
                            # Đối với way, sử dụng tọa độ trung tâm nếu có
                            center = element.get("center", {})
                            if "lat" in center and "lon" in center:
                                distance = geodesic(
                                    (latitude, longitude),
                                    (center["lat"], center["lon"])
                                ).meters
                            else:
                                distance = None
                        
                        # Lấy thông tin về ẩm thực và loại hình
                        cuisine = tags.get("cuisine", "").lower()
                        amenity = tags.get("amenity", "").lower()
                        food_type = tags.get("food", "").lower()
                        description = tags.get("description", "").lower()
                        
                        # Kiểm tra xem địa điểm có phù hợp với tiêu chí không
                        is_relevant = True
                        if criteria:
                            # Nếu là quán cà phê và không có tiêu chí liên quan đến cà phê, bỏ qua
                            if amenity == "cafe" and not any(c.lower() in ["cafe", "cà phê", "coffee"] for c in criteria):
                                is_relevant = False
                            
                            # Kiểm tra xem có tiêu chí nào phù hợp không
                            criteria_matched = False
                            for criterion in criteria:
                                criterion_lower = criterion.lower()
                                # Kiểm tra trong các trường thông tin
                                if (criterion_lower in cuisine or 
                                    criterion_lower in amenity or 
                                    criterion_lower in food_type or 
                                    criterion_lower in description or
                                    criterion_lower in tags.get("name", "").lower()):
                                    criteria_matched = True
                                    break
                            
                            # Nếu không có tiêu chí nào phù hợp, đánh dấu là không liên quan
                            if not criteria_matched:
                                is_relevant = False
                        
                        # Chỉ thêm địa điểm liên quan
                        if is_relevant:
                            restaurant = {
                                "id": element["id"],
                                "name": tags.get("name", "Không có tên"),
                                "type": tags.get("amenity", tags.get("shop", "restaurant")),
                                "cuisine": tags.get("cuisine", "Không xác định"),
                                "address": tags.get("addr:full", tags.get("addr:street", "Không có địa chỉ")),
                                "distance": round(distance) if distance else None,
                                "latitude": element.get("lat", center.get("lat") if "center" in element else None),
                                "longitude": element.get("lon", center.get("lon") if "center" in element else None),
                                "phone": tags.get("phone", None),
                                "website": tags.get("website", None),
                                "opening_hours": tags.get("opening_hours", None),
                                "description": tags.get("description", None)
                            }
                            
                            restaurants.append(restaurant)
            
            # Sắp xếp theo khoảng cách
            restaurants = [r for r in restaurants if r["distance"] is not None]
            restaurants.sort(key=lambda x: x["distance"])
            
            # Nếu không tìm thấy kết quả phù hợp, mở rộng bán kính tìm kiếm
            if not restaurants and criteria and radius < 5000:
                logger.info(f"Không tìm thấy kết quả với bán kính {radius}m, mở rộng tìm kiếm đến 5000m")
                return LocationService.search_restaurants_by_coordinates(latitude, longitude, criteria, 5000)
            
            return restaurants
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi gọi Overpass API: {e}")
            return []
        except Exception as e:
            logger.error(f"Lỗi không xác định: {e}")
            return []
    
    @staticmethod
    def search_restaurants_by_address(address: str, criteria: List[str] = None, radius: int = 1000) -> List[Dict[str, Any]]:
        """
        Tìm kiếm quán ăn gần địa chỉ được chỉ định
        
        Args:
            address: Địa chỉ cần tìm
            criteria: Danh sách tiêu chí để lọc kết quả
            radius: Bán kính tìm kiếm (mét)
            
        Returns:
            Danh sách các quán ăn tìm thấy
        """
        try:
            # Chuyển đổi địa chỉ thành tọa độ sử dụng Nominatim API
            params = {
                "q": address,
                "format": "json",
                "limit": 1
            }
            
            response = requests.get(NOMINATIM_API_URL, params=params, headers={"User-Agent": "FoodChatbot/1.0"})
            response.raise_for_status()
            data = response.json()
            
            if not data:
                logger.warning(f"Không tìm thấy địa chỉ: {address}")
                return []
            
            # Lấy tọa độ từ kết quả đầu tiên
            location = data[0]
            latitude = float(location["lat"])
            longitude = float(location["lon"])
            
            # Tìm kiếm quán ăn gần tọa độ này
            return LocationService.search_restaurants_by_coordinates(latitude, longitude, criteria, radius)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi khi gọi Nominatim API: {e}")
            return []
        except Exception as e:
            logger.error(f"Lỗi không xác định: {e}")
            return []
    
    @staticmethod
    def format_restaurant_info(restaurant: Dict[str, Any]) -> str:
        """
        Định dạng thông tin quán ăn thành chuỗi văn bản
        
        Args:
            restaurant: Thông tin quán ăn
            
        Returns:
            Chuỗi văn bản đã định dạng
        """
        name = restaurant["name"]
        cuisine = f"Loại: {restaurant['cuisine']}" if restaurant["cuisine"] != "Không xác định" else ""
        address = f"Địa chỉ: {restaurant['address']}" if restaurant["address"] != "Không có địa chỉ" else ""
        distance = f"Khoảng cách: {restaurant['distance']}m" if restaurant["distance"] is not None else ""
        phone = f"Điện thoại: {restaurant['phone']}" if restaurant["phone"] else ""
        website = f"Website: {restaurant['website']}" if restaurant["website"] else ""
        opening_hours = f"Giờ mở cửa: {restaurant['opening_hours']}" if restaurant["opening_hours"] else ""
        description = f"Mô tả: {restaurant['description']}" if restaurant["description"] else ""
        
        # Kết hợp các thông tin có sẵn
        info_parts = [part for part in [name, cuisine, address, distance, phone, website, opening_hours, description] if part]
        return "\n".join(info_parts)
    
    @staticmethod
    def get_top_restaurants(restaurants: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
        """
        Lấy danh sách top quán ăn
        
        Args:
            restaurants: Danh sách quán ăn
            limit: Số lượng quán ăn tối đa
            
        Returns:
            Danh sách top quán ăn
        """
        return restaurants[:limit] if restaurants else []
    
    @staticmethod
    def format_restaurant_results(restaurants: List[Dict[str, Any]], criteria: List[str]) -> str:
        """
        Định dạng kết quả gợi ý quán ăn
        
        Args:
            restaurants: Danh sách quán ăn
            criteria: Danh sách tiêu chí
            
        Returns:
            Chuỗi văn bản đã định dạng
        """
        if not restaurants:
            return "Không tìm thấy quán ăn nào phù hợp với tiêu chí của bạn."
            
        result = f"Dựa trên tiêu chí của bạn ({', '.join(criteria)}), đây là top {len(restaurants)} quán ăn gần bạn:\n\n"
        
        for i, restaurant in enumerate(restaurants, 1):
            result += f"#{i}: {LocationService.format_restaurant_info(restaurant)}\n\n"
        
        result += "Bạn có thể hỏi tôi về việc gợi ý món ăn bất cứ lúc nào."
        
        return result 