"""人脸工具测试脚本 - 用于验证人脸检测、特征提取和比对功能"""
import os
import sys
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

def test_detect_face(image_path):
    """
    测试人脸检测功能
    
    Args:
        image_path (str): 测试图像路径
        
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试人脸检测功能 ===")
    try:
        # 打开测试图像
        image = Image.open(image_path)
        print(f"成功加载测试图像: {image_path}")
        
        # 执行人脸检测
        face_boxes, face_images = detect_face(image)
        
        # 输出检测结果
        print(f"检测到人脸数量: {len(face_boxes)}")
        print(f"人脸坐标列表: {face_boxes}")
        print(f"裁剪后人脸图像数量: {len(face_images)}")
        
        # 如果检测到人脸，可以保存裁剪后的人脸图像用于后续测试
        if face_images:
            test_output_dir = os.path.join(config.BASE_DIR, "test_output")
            os.makedirs(test_output_dir, exist_ok=True)
            
            for i, face_img in enumerate(face_images):
                face_save_path = os.path.join(test_output_dir, f"detected_face_{i}.jpg")
                face_img.save(face_save_path)
                print(f"保存裁剪后的人脸图像: {face_save_path}")
        
        return True
        
    except Exception as e:
        print(f"人脸检测测试失败: {str(e)}")
        return False

def test_extract_feature(image_path):
    """
    测试人脸特征提取功能
    
    Args:
        image_path (str): 测试图像路径
        
    Returns:
        list: 提取的特征向量列表，如果失败返回空列表
    """
    print("\n=== 测试人脸特征提取功能 ===")
    try:
        # 打开测试图像
        image = Image.open(image_path)
        
        # 先进行人脸检测
        _, face_images = detect_face(image)
        
        if not face_images:
            print("未检测到人脸，无法提取特征")
            return []
        
        # 提取人脸特征
        feature_vectors = extract_face_feature(face_images)
        
        # 输出特征提取结果
        print(f"提取到特征向量数量: {len(feature_vectors)}")
        
        if feature_vectors:
            # 显示第一个特征向量的部分信息
            first_feature = feature_vectors[0]
            print(f"特征向量维度: {first_feature.shape}")
            print(f"特征向量示例: {first_feature[:10]}...")
            print(f"特征向量范数: {np.linalg.norm(first_feature)}")
            
            # 保存特征向量到文件
            test_output_dir = os.path.join(config.BASE_DIR, "test_output")
            os.makedirs(test_output_dir, exist_ok=True)
            
            for i, feature in enumerate(feature_vectors):
                feature_save_path = os.path.join(test_output_dir, f"face_feature_{i}.npy")
                if save_face_feature(feature, feature_save_path):
                    print(f"保存特征向量到: {feature_save_path}")
        
        return feature_vectors
        
    except Exception as e:
        print(f"特征提取测试失败: {str(e)}")
        return []

def test_compare_features():    
    """
    测试人脸特征比对功能
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试人脸特征比对功能 ===")
    try:
        # 创建测试特征向量
        # 创建一个标准特征向量和一些相似/不相似的特征向量
        input_feature = np.random.randn(128)  # 模拟输入特征
        input_feature = input_feature / np.linalg.norm(input_feature)  # 归一化
        
        # 创建数据库特征向量列表
        # 1. 非常相似的特征（相似度接近1.0）
        similar_feature = input_feature * 0.99 + np.random.randn(128) * 0.02
        similar_feature = similar_feature / np.linalg.norm(similar_feature)
        
        # 2. 中等相似的特征（相似度约0.7）
        medium_feature = input_feature * 0.7 + np.random.randn(128) * 0.4
        medium_feature = medium_feature / np.linalg.norm(medium_feature)
        
        # 3. 不相似的特征（相似度约0.3）
        dissimilar_feature = np.random.randn(128)
        dissimilar_feature = dissimilar_feature / np.linalg.norm(dissimilar_feature)
        
        db_features = [similar_feature, medium_feature, dissimilar_feature]
        
        # 执行特征比对
        matches, max_similarity = compare_face_features(input_feature, db_features, threshold=0.5)
        
        # 输出比对结果
        print(f"最高相似度: {max_similarity:.4f}")
        print("匹配结果列表 (索引, 相似度值):")
        for idx, similarity in matches:
            print(f"  索引: {idx}, 相似度: {similarity:.4f}")
        
        # 验证结果（相似特征应该在最前面）
        if matches and matches[0][0] == 0:  # 第一个特征应该是最相似的
            print("✅ 特征比对测试成功: 相似特征正确排在第一位")
        else:
            print("❌ 特征比对测试失败: 相似特征未正确识别")
        
        return True
        
    except Exception as e:
        print(f"特征比对测试失败: {str(e)}")
        return False

def test_feature_save_load():
    """
    测试特征保存和加载功能
    
    Returns:
        bool: 测试是否成功
    """
    print("\n=== 测试特征保存和加载功能 ===")
    try:
        # 创建测试特征向量
        test_feature = np.random.randn(128)
        test_feature = test_feature / np.linalg.norm(test_feature)
        
        # 创建测试输出目录
        test_output_dir = os.path.join(config.BASE_DIR, "test_output")
        os.makedirs(test_output_dir, exist_ok=True)
        
        # 保存特征向量
        feature_path = os.path.join(test_output_dir, "test_feature.npy")
        if save_face_feature(test_feature, feature_path):
            print(f"✅ 成功保存特征向量到: {feature_path}")
        else:
            print("❌ 特征保存失败")
            return False
        
        # 加载特征向量
        loaded_feature = load_face_feature(feature_path)
        if loaded_feature is not None:
            print("✅ 成功加载特征向量")
            
            # 验证加载的特征与原始特征是否相同
            difference = np.linalg.norm(test_feature - loaded_feature)
            print(f"原始特征与加载特征的差异: {difference:.10f}")
            
            if difference < 1e-10:
                print("✅ 特征保存加载测试成功: 加载的特征与原始特征一致")
                return True
            else:
                print("❌ 特征保存加载测试失败: 加载的特征与原始特征不一致")
                return False
        else:
            print("❌ 特征加载失败")
            return False
            
    except Exception as e:
        print(f"特征保存加载测试失败: {str(e)}")
        return False

def main():
    """
    主测试函数 - 运行所有测试
    """
    print("=" * 60)
    print("人脸工具模块功能测试")
    print("=" * 60)
    print("测试说明:")
    print("1. 请准备一张包含人脸的测试图像")
    print("2. 所有测试输出将保存在 backend/test_output 目录下")
    print("3. 测试完成后会显示总体结果")
    print("=" * 60)
    
    # 测试图像路径（请修改为实际的测试图像路径）
    test_image_path = input("请输入测试图像路径（或直接回车使用默认路径）: ")
    
    # 如果没有提供图像路径，可以使用默认的测试图像路径（如果存在）
    if not test_image_path:
        # 尝试使用一个常见的测试图像路径
        default_test_image = os.path.join(config.BASE_DIR, "data", "test_face.jpg")
        if os.path.exists(default_test_image):
            test_image_path = default_test_image
            print(f"使用默认测试图像: {test_image_path}")
        else:
            print("\n❌ 错误: 未提供测试图像路径且默认测试图像不存在")
            print("请准备一张测试图像并重新运行测试")
            return
    
    # 检查测试图像是否存在
    if not os.path.exists(test_image_path):
        print(f"\n❌ 错误: 测试图像不存在: {test_image_path}")
        return
    
    # 运行所有测试
    test_results = []
    
    # 1. 测试特征保存和加载功能（无需图像）
    test_results.append(('特征保存加载', test_feature_save_load()))
    
    # 2. 测试人脸检测功能
    test_results.append(('人脸检测', test_detect_face(test_image_path)))
    
    # 3. 测试特征提取功能
    feature_vectors = test_extract_feature(test_image_path)
    test_results.append(('特征提取', len(feature_vectors) > 0))
    
    # 4. 测试特征比对功能
    test_results.append(('特征比对', test_compare_features()))
    
    # 显示测试总结
    print("\n" + "=" * 60)
    print("测试结果总结")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("🎉 所有测试通过！人脸工具模块功能正常。")
    else:
        print("⚠️  部分测试失败，请检查错误信息并修复问题。")
    print("=" * 60)


if __name__ == "__main__":
    main()