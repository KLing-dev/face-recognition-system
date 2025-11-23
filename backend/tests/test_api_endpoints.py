import unittest
import json
from app.api import create_app


class APITestCase(unittest.TestCase):
    def setUp(self):
        # 使用现有的应用创建函数
        self.app = create_app()
        self.app.config['TESTING'] = True
        
        # 创建测试客户端
        self.client = self.app.test_client()
    
    def tearDown(self):
        # 清理资源
        pass
    
    def test_register_camera_api_exists(self):
        """测试摄像头注册API是否存在"""
        # 测试注册API是否存在（预期400错误，因为缺少必要参数）
        response = self.client.post('/api/register/camera')
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_register_upload_api_exists(self):
        """测试上传注册API是否存在"""
        # 测试上传注册API是否存在
        # 构造最小化的请求
        response = self.client.post('/api/register/upload', data={
            'name': '测试用户'
        })
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_recognize_camera_api_exists(self):
        """测试摄像头识别API是否存在"""
        # 测试摄像头识别API是否存在
        response = self.client.post('/api/recognize/camera')
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_recognize_upload_api_exists(self):
        """测试上传识别API是否存在"""
        # 测试上传识别API是否存在
        response = self.client.post('/api/recognize/upload')
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_delete_single_api_exists(self):
        """测试单用户删除API是否存在"""
        # 测试单用户删除API是否存在
        response = self.client.delete('/api/delete/single?user_id=test123')
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_delete_batch_api_exists(self):
        """测试批量删除API是否存在"""
        # 测试批量删除API是否存在
        response = self.client.delete('/api/delete/batch?user_ids=test123,test456')
        # 只要不是404，就说明路由存在
        self.assertNotEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('code', data)
    
    def test_statistic_api_exists(self):
        """测试统计API是否存在"""
        # 测试统计API是否存在
        response = self.client.get('/api/statistic')
        # 统计API应该返回200，即使没有数据
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('code', data)


if __name__ == '__main__':
    unittest.main()
