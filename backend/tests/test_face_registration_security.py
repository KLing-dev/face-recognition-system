import unittest
import os
import sys
from PIL import Image
import io
import numpy as np

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.data_process import register_face
from app.database.models import User
from app.database.database import SessionLocal

class TestFaceRegistrationSecurity(unittest.TestCase):
    
    def setUp(self):
        # 创建一个空图像用于测试
        self.empty_image = Image.new('RGB', (100, 100), color='white')
        
        # 创建一个测试数据库会话
        self.db = SessionLocal()
        
        # 清理测试数据
        self.cleanup_test_data()
    
    def tearDown(self):
        # 清理测试数据
        self.cleanup_test_data()
        self.db.close()
    
    def cleanup_test_data(self):
        # 删除测试用户
        self.db.query(User).filter(User.name.like('test_%')).delete()
        self.db.commit()
    
    def create_test_face_image(self):
        # 创建一个简单的人脸图像（这里只是一个示例，实际上不是真实人脸）
        # 在真实测试中，应该使用包含真实人脸的测试图像
        img = Image.new('RGB', (200, 200), color='white')
        return img
    
    def test_empty_username(self):
        """测试空用户名注册"""
        with self.assertRaises(ValueError) as context:
            register_face("", self.empty_image)
        self.assertIn("[注册阻断]", str(context.exception))
        self.assertIn("用户名不能为空", str(context.exception))
    
    def test_invalid_image_format(self):
        """测试无效的图像格式"""
        with self.assertRaises(ValueError) as context:
            register_face("test_user", "not_an_image")
        self.assertIn("[注册阻断]", str(context.exception))
        self.assertIn("图片格式无效", str(context.exception))
    
    def test_no_face_detected(self):
        """测试未检测到人脸的情况"""
        # 使用纯色图像，不包含人脸
        solid_image = Image.new('RGB', (200, 200), color='blue')
        
        with self.assertRaises(ValueError) as context:
            register_face("test_user", solid_image)
        self.assertIn("[注册阻断]", str(context.exception))
        self.assertIn("未检测到人脸", str(context.exception))
    
    def test_duplicate_face_registration(self):
        """测试重复人脸注册"""
        # 注意：这个测试需要使用真实的人脸图像才能通过
        # 在这里只是模拟测试框架，实际使用时需要替换为真实的人脸图像
        print("注意：重复人脸注册测试需要真实人脸图像")
        print("请手动测试以下场景：")
        print("1. 使用同一人脸图像注册用户A")
        print("2. 尝试使用相同的人脸图像注册用户B")
        print("预期结果：第二次注册应被阻断，并显示[注册阻断]和'该人脸已注册'错误消息")
    
    def test_duplicate_identity_id(self):
        """测试重复的身份ID"""
        # 注意：这个测试需要使用真实的人脸图像才能通过
        # 在这里只是模拟测试框架，实际使用时需要替换为真实的人脸图像
        print("注意：重复身份ID测试需要真实人脸图像")
        print("请手动测试以下场景：")
        print("1. 注册一个用户，获取其身份ID")
        print("2. 尝试使用不同的人脸图像但相同的身份ID注册另一个用户")
        print("预期结果：第二次注册应被阻断，并显示[注册阻断]和'身份ID已存在'错误消息")
    
    def test_face_quality_validation(self):
        """测试人脸质量验证"""
        # 注意：这个测试需要使用真实的人脸图像才能通过
        # 在这里只是模拟测试框架，实际使用时需要替换为真实的人脸图像
        print("注意：人脸质量验证测试需要不同质量的真实人脸图像")
        print("请手动测试以下场景：")
        print("1. 使用模糊/低质量的人脸图像尝试注册")
        print("2. 使用过小的人脸图像尝试注册")
        print("预期结果：注册应被阻断，并显示[注册阻断]和相应的质量问题错误消息")

if __name__ == '__main__':
    unittest.main()
