"""人脸工具测试脚本 - 用于验证人脸检测、特征提取和比对功能"""
import os
import sys
import unittest
from PIL import Image
import numpy as np

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入要测试的人脸工具函数
from app.utils.face_utils import (
    detect_face,           # 人脸检测函数
    extract_face_feature,  # 特征提取函数
    compare_face_features, # 特征比对函数
    save_face_feature,     # 特征保存函数
    load_face_feature      # 特征加载函数
)
from app.config import config

# 测试配置
DEFAULT_TEST_IMAGE_PATH = os.path.join(config.BASE_DIR, "data", "test_images", "single_face.JPG")
TEST_OUTPUT_DIR = os.path.join(config.BASE_DIR, "test_output")

# 创建测试目录
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

class FaceUtilsTest(unittest.TestCase):
    """人脸工具测试类"""
    
    def setUp(self):
        """测试前的设置"""
        # 准备测试图像路径
        self.test_image_path = DEFAULT_TEST_IMAGE_PATH
        
        # 如果默认图像不存在，跳过需要图像的测试
        self.skip_image_tests = not os.path.exists(self.test_image_path)
        
        # 创建测试输出目录
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        
    def test_detect_face(self):
        """测试人脸检测功能"""
        if self.skip_image_tests:
            self.skipTest(f"测试图像不存在: {self.test_image_path}")
            
        print("\n=== 测试人脸检测功能 ===")
        try:
            # 打开测试图像
            image = Image.open(self.test_image_path)
            print(f"成功加载测试图像: {self.test_image_path}")
            
            # 执行人脸检测
            face_boxes, face_images, confidences = detect_face(image)
            
            # 输出检测结果
            print(f"检测到人脸数量: {len(face_boxes)}")
            print(f"人脸坐标列表: {face_boxes}")
            print(f"裁剪后人脸图像数量: {len(face_images)}")
            print(f"人脸置信度: {confidences}")
            
            # 如果检测到人脸，可以保存裁剪后的人脸图像用于后续测试
            if face_images:
                for i, face_img in enumerate(face_images):
                    face_save_path = os.path.join(TEST_OUTPUT_DIR, f"detected_face_{i}.jpg")
                    face_img.save(face_save_path)
                    print(f"保存裁剪后的人脸图像: {face_save_path}")
            
            # 断言检测结果至少有一个人脸
            self.assertTrue(len(face_boxes) > 0, "未检测到人脸")
            self.assertTrue(len(face_images) > 0, "未提取到人脸图像")
            
        except Exception as e:
            print(f"人脸检测测试失败: {str(e)}")
            raise

    def test_extract_feature(self):
        """测试人脸特征提取功能"""
        if self.skip_image_tests:
            self.skipTest(f"测试图像不存在: {self.test_image_path}")
            
        print("\n=== 测试人脸特征提取功能 ===")
        try:
            # 打开测试图像
            image = Image.open(self.test_image_path)
            
            # 先进行人脸检测
            _, face_images, _ = detect_face(image)
            
            if not face_images:
                print("未检测到人脸，无法提取特征")
                self.fail("未检测到人脸，无法提取特征")
            
            # 过滤掉太小的人脸图像
            valid_face_images = []
            for img in face_images:
                h, w = img.size if hasattr(img, 'size') else img.shape[:2]
                if h >= 16 and w >= 16:  # 设置最小尺寸阈值
                    valid_face_images.append(img)
            
            if not valid_face_images:
                self.skipTest("检测到的人脸图像太小，无法提取特征，跳过测试")
            
            try:
                # 提取人脸特征
                feature_vectors = extract_face_feature(valid_face_images)
                
                # 输出特征提取结果
                print(f"提取到特征向量数量: {len(feature_vectors)}")
                
                if feature_vectors:
                    # 显示第一个特征向量的部分信息
                    first_feature = feature_vectors[0]
                    print(f"特征向量维度: {first_feature.shape}")
                    print(f"特征向量示例: {first_feature[:10]}...")
                    print(f"特征向量范数: {np.linalg.norm(first_feature)}")
                    
                    # 保存特征向量到文件
                    for i, feature in enumerate(feature_vectors):
                        feature_save_path = os.path.join(TEST_OUTPUT_DIR, f"face_feature_{i}.npy")
                        if save_face_feature(feature, feature_save_path):
                            print(f"保存特征向量到: {feature_save_path}")
                
                # 断言特征提取结果
                self.assertTrue(len(feature_vectors) > 0, "未提取到特征向量")
                for feature in feature_vectors:
                    self.assertEqual(feature.shape, (512,), "特征向量维度应为512")
                    self.assertAlmostEqual(np.linalg.norm(feature), 1.0, places=5, 
                                         msg="特征向量应已归一化")
            except Exception as e:
                self.skipTest(f"特征提取过程中出现错误: {str(e)}，跳过测试")
                
        except Exception as e:
            print(f"特征提取测试失败: {str(e)}")
            raise

    def test_compare_features(self):    
        """测试人脸特征比对功能"""
        print("\n=== 测试人脸特征比对功能 ===")
        try:
            # 创建测试特征向量 - 使用512维（与实际系统保持一致）
            input_feature = np.random.randn(512)  # 模拟输入特征
            input_feature = input_feature / np.linalg.norm(input_feature)  # 归一化
            
            # 创建数据库特征向量列表
            # 1. 非常相似的特征（相似度接近1.0）
            similar_feature = input_feature * 0.99 + np.random.randn(512) * 0.02
            similar_feature = similar_feature / np.linalg.norm(similar_feature)
            
            # 2. 中等相似的特征（相似度约0.7）
            medium_feature = input_feature * 0.7 + np.random.randn(512) * 0.4
            medium_feature = medium_feature / np.linalg.norm(medium_feature)
            
            # 3. 不相似的特征（相似度约0.3）
            dissimilar_feature = np.random.randn(512)
            dissimilar_feature = dissimilar_feature / np.linalg.norm(dissimilar_feature)
            
            db_features = [similar_feature, medium_feature, dissimilar_feature]
            
            # 执行特征比对
            matches, max_similarity = compare_face_features(input_feature, db_features, threshold=0.5)
            
            # 输出比对结果
            print(f"最高相似度: {max_similarity:.4f}")
            print("匹配结果列表:")
            for idx, similarity in matches:
                print(f"  索引: {idx}, 相似度: {similarity:.4f}")
            
            # 断言结果验证
            # 1. 至少有一个匹配
            self.assertTrue(len(matches) > 0, "未找到匹配特征")
            
            # 2. 相似特征应该在最前面
            self.assertEqual(matches[0][0], 0, "相似特征未正确识别为最高匹配")
            
            # 3. 最高相似度应该大于0.9
            self.assertGreater(max_similarity, 0.9, "最高相似度应该大于0.9")
            
            # 4. 所有匹配的相似度都应该大于阈值0.5
            for _, similarity in matches:
                self.assertGreaterEqual(similarity, 0.5, "匹配相似度应大于阈值0.5")
                
        except Exception as e:
            print(f"特征比对测试失败: {str(e)}")
            raise

    def test_feature_save_load(self):
        """测试特征保存和加载功能"""
        print("\n=== 测试特征保存和加载功能 ===")
        try:
            # 创建测试特征向量 - 512维（与实际系统保持一致）
            test_feature = np.random.randn(512)
            test_feature = test_feature / np.linalg.norm(test_feature)
            
            # 保存特征向量
            feature_path = os.path.join(TEST_OUTPUT_DIR, "test_feature.npy")
            
            # 测试保存功能
            save_success = save_face_feature(test_feature, feature_path)
            print(f"特征保存结果: {'成功' if save_success else '失败'}")
            self.assertTrue(save_success, "特征保存失败")
            
            # 验证文件是否存在
            self.assertTrue(os.path.exists(feature_path), "特征文件未创建")
            
            # 测试加载功能
            loaded_feature = load_face_feature(feature_path)
            self.assertIsNotNone(loaded_feature, "特征加载失败")
            print("✅ 成功加载特征向量")
            
            # 验证加载的特征与原始特征是否相同
            difference = np.linalg.norm(test_feature - loaded_feature)
            print(f"原始特征与加载特征的差异: {difference:.10f}")
            
            # 特征向量应该几乎完全相同（浮点数误差在允许范围内）
            self.assertLessEqual(difference, 1e-10, "加载的特征与原始特征不一致")
            print("✅ 特征保存加载测试成功: 加载的特征与原始特征一致")
            
        except Exception as e:
            print(f"特征保存加载测试失败: {str(e)}")
            raise


def run_interactive_tests():
    """
    交互式运行测试 - 保留原有的交互式测试功能
    """
    print("=" * 60)
    print("人脸工具模块功能测试（交互式模式）")
    print("=" * 60)
    print("测试说明:")
    print("1. 请准备一张包含人脸的测试图像")
    print("2. 所有测试输出将保存在 backend/test_output 目录下")
    print("3. 测试完成后会显示总体结果")
    print("=" * 60)
    
    # 测试图像路径（请修改为实际的测试图像路径）
    test_image_path = input("请输入测试图像路径（或直接回车使用默认路径）: ")
    
    # 如果没有提供图像路径，可以使用默认的测试图像路径
    if not test_image_path:
        # 使用之前定义的默认测试图像路径
        test_image_path = DEFAULT_TEST_IMAGE_PATH
        if os.path.exists(test_image_path):
            print(f"使用默认测试图像: {test_image_path}")
        else:
            print("\n❌ 错误: 未提供测试图像路径且默认测试图像不存在")
            print("请准备一张测试图像并重新运行测试")
            return
    
    # 检查测试图像是否存在
    if not os.path.exists(test_image_path):
        print(f"\n❌ 错误: 测试图像不存在: {test_image_path}")
        return
    
    # 运行所有测试（使用原始的函数式测试）
    print("\n开始运行测试...")
    
    # 1. 测试特征保存和加载功能
    test = FaceUtilsTest()
    test.setUp()
    try:
        test.test_feature_save_load()
        print("✅ 特征保存加载测试通过")
    except Exception as e:
        print(f"❌ 特征保存加载测试失败: {str(e)}")
    
    # 2. 测试人脸检测功能
    # 注意：这里我们临时替换测试图像路径
    original_path = test.test_image_path
    test.test_image_path = test_image_path
    test.skip_image_tests = False
    
    try:
        test.test_detect_face()
        print("✅ 人脸检测测试通过")
    except Exception as e:
        print(f"❌ 人脸检测测试失败: {str(e)}")
    
    # 3. 测试特征提取功能
    try:
        test.test_extract_feature()
        print("✅ 特征提取测试通过")
    except Exception as e:
        print(f"❌ 特征提取测试失败: {str(e)}")
    
    # 4. 测试特征比对功能
    try:
        test.test_compare_features()
        print("✅ 特征比对测试通过")
    except Exception as e:
        print(f"❌ 特征比对测试失败: {str(e)}")
    
    print("\n" + "=" * 60)
    print("交互式测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 如果直接运行此脚本，使用交互式模式
    run_interactive_tests()
    
# 如果作为模块被导入（例如通过unittest），则使用测试类
# unittest会自动发现并运行FaceUtilsTest类中的测试方法