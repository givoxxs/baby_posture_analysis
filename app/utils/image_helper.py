import numpy as np
import cv2
from PIL import Image
from typing import Tuple

class Image_Helper:
    def __init__(self):
        pass
    
    def square_image(self, image: np.ndarray):
        if isinstance(image, np.ndarray):
            img_pil = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            img_pil = image
            
        original = img_pil.size
        
        max_size = max(original)
        new_size = (max_size, max_size)
        
        new_img = Image.new("RGB", new_size, ( 0, 0, 0))
        
        new_img.paste(img_pil, ((max_size - original[0]) // 2, (max_size - original[1]) // 2))
        
        new_img_np = np.array(new_img)
        
        # new_img_cv2 = cv2.cvtColor(np.ndarray(new_img), cv2.COLOR_RGB2BGR)
        new_img_cv2 = cv2.cvtColor(new_img_np, cv2.COLOR_RGB2BGR)
        
        return new_img_cv2, new_size
    
    def process_image(self, image: np.ndarray):
        image, new_size = self.square_image(image)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), new_size 
    
class Image_Rotation_Helper:
    def __init__(self):
        pass
    
    def rotate_image_baby(self, keypoints, origin_size=(612, 408)) -> np.ndarray:
        """
        Xoay ảnh của em bé về phía trước, dựa vào vị trí của vai và hông.
        Đầu vào là keypoints của em bé, đầu ra là keypoints đã được xoay.
        
        """
        left_shoulder = keypoints.landmark[11]
        right_shoulder = keypoints.landmark[12]
        left_hip = keypoints.landmark[23]
        right_hip = keypoints.landmark[24]
        
        c_shoulder = (left_shoulder.x + right_shoulder.x) / 2, (left_shoulder.y + right_shoulder.y) / 2
        c_hip = (left_hip.x + right_hip.x) / 2, (left_hip.y + right_hip.y) / 2
        
        center = (c_shoulder[0] + c_hip[0]) / 2, (c_shoulder[1] + c_hip[1]) / 2
        
        vector_center_to_c_shoulder = (c_shoulder[0] - center[0], c_shoulder[1] - center[1])
        O_y = (0, -1)  # Updated O_y to a fixed vector
        
        angle = self.calc_angle_rotate(vector_center_to_c_shoulder, O_y)
        
        for point in keypoints.landmark:
            new_point = self.rotate_point(point, center, angle)
            point.x = new_point[0]
            point.y = new_point[1]
        
        return keypoints
    
    def calc_angle_rotate(self, OA: Tuple, OB: Tuple):
        dot_product = OA[0] * OB[0] + OA[1] * OB[1]
        normOA = np.sqrt(OA[0]**2 + OA[1]**2)
        normOB = np.sqrt(OB[0]**2 + OB[1]**2)
        
        cos_angle = dot_product / (normOA * normOB) # cosin của góc giữa 2 vector OA và OB
        
        cos_angle = np.clip(cos_angle, -1.0, 1.0) # hàm clip để giới hạn giá trị trong khoảng [-1, 1]
        angle = np.arccos(cos_angle)
        
        cross_product = OA[0] * OB[1] - OA[1] * OB[0] # tích có hướng của 2 vector OA và OB -> để xác định chiều quay
        if cross_product < 0:
            angle = 2*np.pi - angle
        
        return np.degrees(angle) # trả về góc quay theo độ

    def rotate_point(self, point: Tuple, center: Tuple, angle: float, origin_size=(612, 408)) -> tuple:
        x, y = point.x, point.y
        center_x, center_y = center
        
        x_new = (
            (x - center_x) * np.cos(np.radians(angle)) * origin_size[0] - (y - center_y) * np.sin(np.radians(angle)) * origin_size[1] + center_x * origin_size[0]
        )
        y_new = (
            (x - center_x) * np.sin(np.radians(angle)) * origin_size[0] + (y - center_y) * np.cos(np.radians(angle)) * origin_size[1] + center_y * origin_size[1]
        )
        
        return x_new / origin_size[0], y_new / origin_size[1]