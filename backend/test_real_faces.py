#!/usr/bin/env python3
"""
真实人脸测试脚本 - 用于测试人脸识别系统的完整功能

本模块提供了一个结构化的测试框架，用于验证人脸识别系统的核心功能，包括：
1. 单人注册测试
2. 单人识别测试
3. 多人合影识别测试
4. 错误处理测试

使用说明：
- 确保测试图片存放在正确的目录下
- 支持结果可视化，会在test_output目录生成带标注的图片
- 提供详细的测试统计和结果分析
"""
import os
import sys
from PIL import Image
from datetime import datetime
from PIL import ImageDraw, ImageFont

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.utils.data_process import register_face, recognize_face
from app.models.models import init_db, SessionLocal, User
from app.utils.face_utils import detect_face, compare_face_features, extract_face_feature


def print_test_header(title):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")


def print_result(result, success=True):
    """打印测试结果"""
    if success:
        print(f"✅ 成功: {result}")
    else:
        print(f"❌ 失败: {result}")


def get_test_images_dir():
    """获取测试图片目录
    
    自动检测当前工作目录结构，找到正确的测试图片路径
    
    Returns:
        str: 测试图片目录的绝对路径
    """
    # 可能的测试图片路径
    possible_paths = [
        "data/test_images",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data/test_images")
    ]
    
    for path in possible_paths:
        if os.path.isdir(path):
            return os.path.abspath(path)
    
    # 默认返回相对路径
    return "data/test_images"

def test_single_person_registration():
    """测试单人注册"""
    print_test_header("测试1: 单人注册测试")
    
    test_images_dir = get_test_images_dir()
    
    # 测试图片路径
    test_images = [
        os.path.join(test_images_dir, "single_face.JPG"),
        os.path.join(test_images_dir, "side_face.JPG")
    ]
    
    registered_users = []
    
    for i, image_path in enumerate(test_images):
        try:
            if not os.path.exists(image_path):
                print(f"⚠️ 图片不存在: {image_path}")
                continue
                
            print(f"\n📸 处理图片: {image_path}")
            
            # 打开图片
            image = Image.open(image_path)
            username = f"test_user_{i+1}"
            
            # 尝试检测人脸（添加预处理验证）
            try:
                face_boxes, face_images, confidences = detect_face(image)
                print(f"   🧪 预处理验证: 检测到 {len(face_boxes)} 个人脸")
                
                # 过滤掉太小的人脸图像
                valid_faces = []
                for img, box, conf in zip(face_images, face_boxes, confidences):
                    h, w = img.size[1], img.size[0] if isinstance(img, Image.Image) else img.shape[:2]
                    if h >= 16 and w >= 16:
                        valid_faces.append((img, box, conf))
                        
                if not valid_faces:
                    print(f"⚠️ 未检测到有效人脸，跳过注册")
                    continue
            except Exception as e:
                print(f"⚠️ 人脸检测预处理失败: {str(e)}")
                # 继续尝试注册，让register_face函数内部处理
            
            # 尝试注册
            result = register_face(username, image)
            print_result(f"用户 '{username}' 注册成功！用户ID: {result['user_id']}")
            registered_users.append(username)
            
        except ValueError as e:
            print_result(f"注册失败 - {e}", success=False)
        except Exception as e:
            print_result(f"意外错误 - {e}", success=False)
    
    return registered_users


def visualize_test_result(test_name, image_path, recognition_result):
    """可视化测试结果"""
    try:
        # 打开原图
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体，如果失败使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # 绘制每个人脸的框和标签
            for detail in recognition_result['match_details']:
                try:
                    face_box = detail['face_box']
                    x1, y1, x2, y2 = face_box
                except (KeyError, ValueError) as e:
                    print(f"⚠️  无效的人脸框数据: {e}")
                    continue
            
            # 根据是否匹配选择颜色
            if detail.get('matched_user'):
                # 匹配成功 - 蓝色框
                box_color = (0, 0, 255)  # 蓝色 (BGR格式)
                text = f"{detail['matched_user']} ({detail['similarity']:.2f})"
                text_color = (255, 255, 255)  # 白色文字
                bg_color = (0, 0, 255)  # 蓝色背景
            else:
                # 未匹配 - 红色框
                box_color = (255, 0, 0)  # 红色 (BGR格式)
                text = "非库内人员"
                text_color = (255, 255, 255)  # 白色文字
                bg_color = (255, 0, 0)  # 红色背景
            
            # 绘制矩形框（稍微粗一点）
            draw.rectangle([x1, y1, x2, y2], outline=box_color, width=3)
            
            # 绘制文字背景
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # 文字背景框
            bg_y1 = y1 - text_height - 8
            bg_y2 = y1
            draw.rectangle([x1, bg_y1, x1 + text_width + 8, bg_y2], fill=bg_color)
            
            # 绘制文字
            draw.text((x1 + 4, bg_y1 + 2), text, fill=text_color, font=font)
        
        # 保存结果图片
        output_dir = "test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{test_name}_result_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        image.save(output_path)
        print(f"🖼️  可视化结果已保存: {output_path}")
        
        # 显示统计信息
        print(f"📊 识别统计:")
        print(f"   总人脸数: {recognition_result['total_count']}")
        print(f"   匹配成功: {recognition_result['matched_count']} (蓝色框)")
        print(f"   未匹配: {recognition_result['total_count'] - recognition_result['matched_count']} (红色框)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 可视化失败: {e}")
        return None

def test_single_person_recognition(registered_users):
    """测试单人识别"""
    print_test_header("测试2: 单人识别测试")
    
    if not registered_users:
        print("⚠️ 没有已注册的用户，跳过单人识别测试")
        return
    
    test_images_dir = get_test_images_dir()
    
    # 使用相同的图片进行识别测试
    test_images = [
        os.path.join(test_images_dir, "single_face.JPG"),
        os.path.join(test_images_dir, "side_face.JPG")
    ]
    
    for image_path in test_images:
        try:
            if not os.path.exists(image_path):
                continue
                
            print(f"\n🔍 识别图片: {image_path}")
            image = Image.open(image_path)
            
            # 执行识别
            result = recognize_face(image)
            
            print(f"📊 识别结果:")
            print(f"   检测到人脸总数: {result['total_count']}")
            print(f"   匹配成功人数: {result['matched_count']}")
            print(f"   数据库中未出现人数: {result['unmatched_count_db']}")
            
            if result['matched_names']:
                print(f"   ✅ 匹配到的用户: {', '.join(result['matched_names'])}")
            
            if result['match_details']:
                for detail in result['match_details']:
                    if detail['matched_user']:
                        print(f"   👤 人脸{detail['face_index']+1}: 匹配到 '{detail['matched_user']}' (相似度: {detail['similarity']:.3f})")
                    else:
                        print(f"   ❌ 人脸{detail['face_index']+1}: 未找到匹配 (最高相似度: {detail['similarity']:.3f})")
            
            # 生成可视化结果
            print(f"\n🎨 生成可视化结果...")
            visualize_test_result("single_person", image_path, result)
            
        except ValueError as e:
            print_result(f"识别失败 - {e}", success=False)
        except Exception as e:
            print_result(f"意外错误 - {e}", success=False)


def test_group_photo_recognition():
    """测试多人合影识别"""
    print_test_header("测试3: 多人合影识别测试")
    
    test_images_dir = get_test_images_dir()
    group_photo_path = os.path.join(test_images_dir, "group_photo.JPG")
    
    if not os.path.exists(group_photo_path):
        print(f"⚠️ 合影图片不存在: {group_photo_path}")
        return
    
    try:
        print(f"\n👥 识别合影: {group_photo_path}")
        image = Image.open(group_photo_path)
        
        # 执行识别
        result = recognize_face(image)
        
        print(f"📊 合影识别结果:")
        print(f"   检测到人脸总数: {result['total_count']}")
        print(f"   匹配成功人数: {result['matched_count']}")
        print(f"   数据库中未出现人数: {result['unmatched_count_db']}")
        
        # 生成可视化结果
        print(f"\n🎨 生成可视化结果...")
        visualize_test_result("group_photo", group_photo_path, result)
        
        if result['matched_names']:
            print(f"   ✅ 匹配到的用户: {', '.join(result['matched_names'])}")
        
        if result['unmatched_names_db']:
            print(f"   📋 数据库中未出现的用户: {', '.join(result['unmatched_names_db'])}")
        
        if result['match_details']:
            for detail in result['match_details']:
                face_info = f"人脸{detail['face_index']+1} 坐标: {detail['face_box']}"
                if detail['matched_user']:
                    print(f"   👤 {face_info}: 匹配到 '{detail['matched_user']}' (相似度: {detail['similarity']:.3f})")
                else:
                    print(f"   ❌ {face_info}: 未找到匹配 (最高相似度: {detail['similarity']:.3f})")
        
    except ValueError as e:
        print_result(f"合影识别失败 - {e}", success=False)
    except Exception as e:
        print_result(f"意外错误 - {e}", success=False)


def test_error_handling():
    """测试错误处理"""
    print_test_header("测试4: 错误处理测试")
    
    # 测试1: 无人脸图片
    print(f"\n🖼️ 测试无人脸图片...")
    try:
        # 创建一张空白图片
        blank_image = Image.new('RGB', (200, 200), color='white')
        result = recognize_face(blank_image)
        # 即使没有检测到人脸，recognize_face函数也应该返回一个有效的结果对象
        # 检查结果是否包含预期的键
        if isinstance(result, dict) and 'match_details' in result:
            print_result("空白图片处理成功（应该检测不到人脸）", success=True)
        else:
            print_result("返回结果格式不正确", success=False)
    except ValueError as e:
        print_result(f"正确捕获错误: {e}", success=True)
    except Exception as e:
        print_result(f"意外错误: {e}", success=False)
    
    # 测试2: 重复注册
    print(f"\n🔄 测试重复注册...")
    try:
        test_images_dir = get_test_images_dir()
        single_face_path = os.path.join(test_images_dir, "single_face.JPG")
        
        if os.path.exists(single_face_path):
            image = Image.open(single_face_path)
            result = register_face("test_user_1", image)  # 重复注册
            print_result("重复注册不应该成功", success=False)
        else:
            print_result("测试图片不存在，跳过重复注册测试", success=True)
    except ValueError as e:
        if "已存在" in str(e):
            print_result(f"正确捕获重复注册错误: {e}", success=True)
        else:
            print_result(f"其他错误: {e}", success=False)
    except Exception as e:
        print_result(f"意外错误: {e}", success=False)
    
    # 测试3: 模拟低质量图片
    print(f"\n📸 测试低质量图片处理...")
    try:
        # 创建一个模糊的小图片
        small_image = Image.new('RGB', (10, 10), color='black')
        result = recognize_face(small_image)
        print_result("小图片处理成功", success=True)
    except Exception as e:
        print_result(f"异常处理: {e}", success=True)


def show_database_status():
    """显示数据库状态"""
    print_test_header("数据库状态")
    
    try:
        db = SessionLocal()
        users = db.query(User).all()
        
        print(f"📊 数据库统计:")
        print(f"   总用户数: {len(users)}")
        
        if users:
            print(f"   👥 用户列表:")
            for user in users:
                print(f"      - ID: {user.id}, 姓名: {user.name}, 创建时间: {user.created_at}")
        
        db.close()
        
    except Exception as e:
        print_result(f"数据库查询失败: {e}", success=False)


def main():
    """主测试函数"""
    print(f"🚀 开始真实人脸测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 初始化数据库
        print("\n📋 初始化数据库...")
        init_db()
        
        # 显示初始状态
        show_database_status()
        
        # 执行测试
        registered_users = test_single_person_registration()
        test_single_person_recognition(registered_users)
        test_group_photo_recognition()
        test_error_handling()
        
        # 显示最终状态
        show_database_status()
        
        print(f"\n🎉 测试完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 测试结果汇总
        print(f"\n📊 测试总结:")
        print(f"   ✅ 已执行单人注册测试")
        print(f"   ✅ 已执行单人识别测试")
        print(f"   ✅ 已执行多人合影识别测试")
        print(f"   ✅ 已执行错误处理测试")
        
        print(f"\n📖 使用说明:")
        print(f"1. 准备更多真实人脸图片，放在 {get_test_images_dir()} 目录下")
        print("2. 确保图片清晰，人脸清晰可见")
        print("3. 可以修改本脚本添加更多测试用例")
        print("4. 观察相似度分数，调整系统中的识别阈值参数")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        print("请检查系统依赖和数据库连接是否正常")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n📋 测试程序结束")


if __name__ == "__main__":
    main()