#!/usr/bin/env python3
"""
交互式人脸测试脚本 - 用于测试人脸识别系统的核心功能

此脚本提供了一个简单的命令行界面，用于测试人脸注册、识别和数据库管理功能。
支持：
- 图片上传方式的人脸注册
- 图片识别和结果可视化
- 数据库状态查看
- 用户数据管理
"""
import os
import sys
import cv2
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# 添加backend目录到Python路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.utils.data_process import register_face, recognize_face
from app.models.models import init_db, SessionLocal, User

def print_menu():
    """打印菜单"""
    print(f"\n{'='*50}")
    print("🎯 人脸识别系统 - 交互式测试")
    print(f"{'='*50}")
    print("1. 📸 注册新用户（人脸注册）")
    print("2. 🔍 人脸识别")
    print("3. 📊 查看数据库状态")
    print("4. 🗑️ 清空所有用户数据")
    print("5. 📋 删除单个/多个用户")
    print("6. ❌ 退出")
    print(f"{'='*50}")

def capture_face_from_camera():
    """使用摄像头捕获人脸"""
    print("\n📹 正在打开摄像头...")
    
    # 初始化摄像头
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return None
    
    print("\n💡 使用提示:")
    print("   - 按空格键拍摄照片")
    print("   - 按ESC键取消拍摄")
    print("   - 请将脸对准画面中央")
    
    # 创建保存目录
    captures_dir = os.path.join(backend_dir, "data", "captures")
    os.makedirs(captures_dir, exist_ok=True)
    
    # 获取当前时间作为文件名的一部分
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(captures_dir, f"capture_{timestamp}.jpg")
    
    while True:
        # 读取一帧
        ret, frame = cap.read()
        
        if not ret:
            print("❌ 无法读取摄像头画面")
            break
        
        # 显示画面
        cv2.imshow("人脸拍摄 - 按空格拍摄，ESC取消", frame)
        
        # 检查按键
        key = cv2.waitKey(1) & 0xFF
        
        # 按ESC键退出
        if key == 27:
            print("❌ 已取消拍摄")
            image_path = None
            break
        
        # 按空格键拍摄
        if key == 32:
            # 保存图片
            cv2.imwrite(image_path, frame)
            print(f"📸 照片已保存: {os.path.basename(image_path)}")
            break
    
    # 释放摄像头并关闭窗口
    cap.release()
    cv2.destroyAllWindows()
    
    return image_path

def register_new_user():
    """注册新用户 - 支持本地图片上传和摄像头拍摄，自动生成唯一身份ID"""
    print(f"\n{'='*40}")
    print("📸 人脸注册")
    print(f"{'='*40}")
    
    # 输入用户名
    name = input("请输入用户名: ").strip()
    if not name:
        print("❌ 用户名不能为空！")
        return
    
    # 身份ID将在后端自动生成，无需用户输入
    identity_id = None
    
    # 选择注册方式
    print("\n📋 请选择注册方式:")
    print("   1. 📂 上传本地图片")
    print("   2. 📹 使用摄像头拍摄")
    
    method_choice = input("请输入选择 (1/2): ").strip()
    image_path = None
    
    if method_choice == '1':
        # 定义测试图片目录
        test_image_dir = os.path.join(backend_dir, "data", "test_images")
        default_images = []
        
        # 自动检测并列出可用的测试图片
        if os.path.exists(test_image_dir):
            default_images = [f for f in os.listdir(test_image_dir) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        # 输入图片路径
        if default_images:
            print(f"\n💡 可用的测试图片:")
            for i, img in enumerate(default_images, 1):
                print(f"   {i}. {img}")
            
            choice = input("请输入图片序号或直接输入自定义图片路径: ").strip()
            
            try:
                # 如果用户输入的是序号
                index = int(choice) - 1
                if 0 <= index < len(default_images):
                    image_path = os.path.join(test_image_dir, default_images[index])
                else:
                    print("❌ 无效的图片序号")
                    return
            except ValueError:
                # 如果用户输入的是路径
                image_path = choice
        else:
            image_path = input("请输入图片路径: ").strip()
            
    elif method_choice == '2':
        # 使用摄像头拍摄
        image_path = capture_face_from_camera()
        if not image_path:
            return
    else:
        print("❌ 无效的选择")
        return
    
    # 检查图片是否存在
    if not os.path.exists(image_path):
        print(f"❌ 图片不存在: {image_path}")
        return
    
    try:
        print(f"🔄 正在处理图片: {image_path}")
        image = Image.open(image_path)
        
        # 添加二次确认
        print(f"\n📋 注册信息确认:")
        print(f"   用户名: {name}")
        print(f"   图片路径: {os.path.basename(image_path)}")
        print(f"   提示: 身份ID将在后端自动生成并确保唯一性")
        
        confirm = input("\n✅ 确认注册以上信息吗？(y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 已取消注册")
            return
        
        # 注册人脸（不传递identity_id，让后端自动生成）
        result = register_face(name, image)
        
        print(f"✅ 注册成功！")
        print(f"   用户ID: {result['user_id']}")
        print(f"   用户名: {name}")
        print(f"   生成的身份ID: {result['identity_id']}")
        print(f"   消息: {result['message']}")
        
    except ValueError as e:
        error_msg = str(e)
        print(f"❌ 注册失败: {error_msg}")
        if "未检测到人脸" in error_msg:
            print("💡 建议: 确保图片中有清晰的人脸，光线充足")
        elif "已存在" in error_msg and "身份ID" in error_msg:
            # 虽然现在不会因为身份ID重复报错（自动生成），但保留兼容性
            print("💡 建议: 系统将自动生成唯一ID，请重新尝试")
        elif "多人脸" in error_msg:
            print("💡 建议: 注册时请使用仅包含单人的图片")
    except Exception as e:
        print(f"❌ 意外错误: {str(e)}")
        print("💡 请检查图片格式是否支持 (JPG, PNG, BMP等)")

def visualize_recognition(image_path, recognition_result):
    """可视化识别结果 - 在人脸上绘制框和标签"""
    try:
        # 打开原图
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)
        
        # 尝试加载字体，如果失败使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 20)
            font_small = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # 绘制每个人脸的框和标签
        for detail in recognition_result['match_details']:
            face_box = detail['face_box']
            x1, y1, x2, y2 = face_box
            
            # 根据是否匹配选择颜色
            if detail['matched_user']:
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
        
        # 保存结果图片到指定的输出目录
        output_dir = "f:\\data\\Projects\\Homework\\face_recongnition_system\\backend\\test_output"
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"recognition_result_{timestamp}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        image.save(output_path)
        print(f"🖼️  可视化结果已保存: {output_path}")
        
        # 显示统计信息
        print(f"\n📊 识别统计:")
        print(f"   总人脸数: {recognition_result['total_count']}")
        print(f"   匹配成功: {recognition_result['matched_count']} (蓝色框)")
        print(f"   未匹配: {recognition_result['total_count'] - recognition_result['matched_count']} (红色框)")
        
        return output_path
        
    except Exception as e:
        print(f"❌ 可视化失败: {e}")
        return None

def recognize_faces():
    """人脸识别"""
    print(f"\n{'='*40}")
    print("🔍 人脸识别")
    print(f"{'='*40}")
    
    # 定义测试图片目录
    test_image_dir = os.path.join(backend_dir, "data", "test_images")
    default_images = []
    
    # 自动检测并列出可用的测试图片
    if os.path.exists(test_image_dir):
        default_images = [f for f in os.listdir(test_image_dir) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    
    # 输入图片路径
    if default_images:
        print(f"\n💡 可用的测试图片:")
        for i, img in enumerate(default_images, 1):
            print(f"   {i}. {img}")
        
        choice = input("请输入图片序号或直接输入自定义图片路径: ").strip()
        
        try:
            # 如果用户输入的是序号
            index = int(choice) - 1
            if 0 <= index < len(default_images):
                image_path = os.path.join(test_image_dir, default_images[index])
            else:
                print("❌ 无效的图片序号")
                return
        except ValueError:
            # 如果用户输入的是路径
            image_path = choice
    else:
        image_path = input("请输入要识别的图片路径: ").strip()
    
    if not os.path.exists(image_path):
        print(f"❌ 图片不存在: {image_path}")
        return
    
    try:
        print(f"🔄 正在识别图片: {image_path}")
        image = Image.open(image_path)
        
        # 执行识别
        result = recognize_face(image)
        
        print(f"\n📊 识别结果:")
        print(f"   检测到人脸总数: {result['total_count']}")
        print(f"   匹配成功人数: {result['matched_count']}")
        print(f"   未匹配人数: {result['total_count'] - result['matched_count']}")
        
        if result['matched_names']:
            print(f"   ✅ 匹配到的用户: {', '.join(result['matched_names'])}")
        
        print(f"\n🔍 详细匹配信息:")
        for detail in result['match_details']:
            face_info = f"人脸{detail['face_index']+1}"
            if 'error' in detail and detail['error']:
                print(f"   ❌ {face_info}: {detail['error']}")
            elif detail['matched_user']:
                print(f"   👤 {face_info}: 匹配到 '{detail['matched_user']}' (相似度: {detail['similarity']:.3f})")
            else:
                print(f"   ❓ {face_info}: 未找到匹配 (最高相似度: {detail['similarity']:.3f})")
        
        # 生成可视化结果
        print(f"\n🎨 生成可视化结果...")
        output_path = visualize_recognition(image_path, result)
        
        # 分析结果
        if result['total_count'] == 0:
            print(f"\n💡 提示: 未检测到人脸")
            print("   - 确保图片中有清晰的人脸，光线充足")
        elif result['matched_count'] == 0:
            print(f"\n💡 提示: 没有匹配到任何注册用户")
            print("   - 确保先注册一些用户")
            print("   - 检查图片质量是否足够清晰")
        elif result['matched_count'] == result['total_count']:
            print(f"\n🎉 完美！所有检测到的人脸都已成功识别")
        else:
            print(f"\n📈 部分识别成功，识别率: {result['matched_count']}/{result['total_count']} ({result['matched_count']/result['total_count']*100:.1f}%)")
        
    except ValueError as e:
        error_msg = str(e)
        print(f"❌ 识别失败: {error_msg}")
        if "未检测到人脸" in error_msg:
            print("💡 建议: 确保图片中有清晰的人脸")
    except Exception as e:
        print(f"❌ 意外错误: {str(e)}")

def show_database_status():
    """显示数据库状态"""
    print(f"\n{'='*40}")
    print("📊 数据库状态")
    print(f"{'='*40}")
    
    try:
        db = SessionLocal()
        users = db.query(User).all()
        
        print(f"总用户数: {len(users)}")
        
        if users:
            print(f"\n👥 用户详细信息:")
            for i, user in enumerate(users, 1):
                print(f"   {i}. ID: {user.id}")
                print(f"      姓名: {user.name}")
                print(f"      创建时间: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 检查文件是否存在
                img_exists = os.path.exists(user.image_path)
                feat_exists = os.path.exists(user.feature_path)
                
                print(f"      图片路径: {os.path.basename(user.image_path)} {'✅' if img_exists else '❌ 不存在'}")
                print(f"      特征路径: {os.path.basename(user.feature_path)} {'✅' if feat_exists else '❌ 不存在'}")
                print()
        else:
            print("💡 数据库为空，请先注册一些用户")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {str(e)}")
        print("💡 请检查数据库连接和权限")

def clear_all_users():
    """清空所有用户数据"""
    print(f"\n{'='*40}")
    print("🗑️ 清空用户数据")
    print(f"{'='*40}")
    
    confirm = input("⚠️ 确定要清空所有用户数据吗？(输入 'yes' 确认): ").strip().lower()
    
    if confirm == 'yes':
        try:
            db = SessionLocal()
            
            # 获取所有用户
            users = db.query(User).all()
            deleted_count = len(users)
            
            if deleted_count == 0:
                print("数据库已经是空的")
                return
            
            # 删除每个用户的文件
            for user in users:
                try:
                    # 删除图片文件
                    if os.path.exists(user.image_path):
                        os.remove(user.image_path)
                        print(f"   删除图片: {os.path.basename(user.image_path)}")
                    
                    # 删除特征文件
                    if os.path.exists(user.feature_path):
                        os.remove(user.feature_path)
                        print(f"   删除特征: {os.path.basename(user.feature_path)}")
                except Exception as e:
                    print(f"   警告: 删除文件失败 - {e}")
            
            # 删除数据库记录
            db.query(User).delete()
            db.commit()
            
            print(f"✅ 成功清空 {deleted_count} 个用户的数据")
            
        except Exception as e:
            print(f"❌ 清空数据失败: {e}")
    else:
        print("已取消清空操作")

def delete_users():
    """删除单个或多个用户"""
    print(f"\n{'='*40}")
    print("🗑️ 删除用户")
    print(f"{'='*40}")
    
    try:
        db = SessionLocal()
        users = db.query(User).all()
        
        if not users:
            print("💡 数据库为空，没有可删除的用户")
            db.close()
            return
        
        # 显示所有用户供选择
        print(f"\n👥 可用删除的用户 ({len(users)}):")
        for i, user in enumerate(users, 1):
            print(f"   {i}. ID: {user.id}, 姓名: {user.name}")
        
        # 获取用户选择
        print("\n💡 请输入要删除的用户序号（多个序号用逗号分隔，例如：1,3,5）:")
        selection = input("请输入: ").strip()
        
        if not selection:
            print("❌ 未选择任何用户，取消操作")
            db.close()
            return
        
        # 解析用户选择
        selected_indices = []
        try:
            # 处理逗号分隔的序号
            parts = selection.split(',')
            for part in parts:
                # 处理范围输入，例如 "1-3"
                if '-' in part:
                    start, end = part.strip().split('-')
                    start_idx = int(start.strip()) - 1
                    end_idx = int(end.strip()) - 1
                    if start_idx < 0 or end_idx >= len(users) or start_idx > end_idx:
                        print(f"❌ 无效的范围: {part}")
                        db.close()
                        return
                    selected_indices.extend(range(start_idx, end_idx + 1))
                else:
                    idx = int(part.strip()) - 1
                    if idx < 0 or idx >= len(users):
                        print(f"❌ 无效的序号: {part}")
                        db.close()
                        return
                    if idx not in selected_indices:
                        selected_indices.append(idx)
        except ValueError:
            print("❌ 输入格式错误，请使用数字序号")
            db.close()
            return
        
        # 去重并排序
        selected_indices = sorted(list(set(selected_indices)))
        
        # 确认删除
        print(f"\n⚠️ 即将删除以下 {len(selected_indices)} 个用户:")
        for idx in selected_indices:
            user = users[idx]
            print(f"   {user.id} - {user.name}")
        
        confirm = input("\n请确认删除 (输入 'yes' 确认): ").strip().lower()
        
        if confirm != 'yes':
            print("✅ 已取消删除操作")
            db.close()
            return
        
        # 执行删除
        deleted_count = 0
        error_count = 0
        
        for idx in selected_indices:
            user = users[idx]
            try:
                # 删除相关文件
                # 删除图片文件
                if os.path.exists(user.image_path):
                    os.remove(user.image_path)
                    print(f"   📷 删除图片: {os.path.basename(user.image_path)}")
                
                # 删除特征文件
                if os.path.exists(user.feature_path):
                    os.remove(user.feature_path)
                    print(f"   🔬 删除特征: {os.path.basename(user.feature_path)}")
                
                # 删除数据库记录
                db.delete(user)
                db.commit()
                deleted_count += 1
                print(f"   ✅ 成功删除用户: {user.name} (ID: {user.id})")
                
            except Exception as e:
                error_count += 1
                print(f"   ❌ 删除用户 {user.name} 失败: {str(e)}")
                # 回滚当前用户的删除操作
                db.rollback()
        
        print(f"\n📊 删除结果:")
        print(f"   ✅ 成功删除: {deleted_count} 个用户")
        if error_count > 0:
            print(f"   ❌ 删除失败: {error_count} 个用户")
        
        db.close()
        
    except Exception as e:
        print(f"❌ 删除过程中发生错误: {str(e)}")
        try:
            db.close()
        except:
            pass

def main():
    """主函数"""
    try:
        print("🚀 初始化数据库...")
        init_db()
        print("✅ 数据库初始化完成")
        
        while True:
            print_menu()
            
            try:
                choice = input("\n请选择操作 (1-6): ").strip()
                
                if choice == '1':
                    register_new_user()
                elif choice == '2':
                    recognize_faces()
                elif choice == '3':
                    show_database_status()
                elif choice == '4':
                    clear_all_users()
                elif choice == '5':
                    delete_users()
                elif choice == '6':
                    print("👋 感谢使用，再见！")
                    break
                else:
                    print("❌ 无效选择，请输入 1-6")
                    
            except KeyboardInterrupt:
                print("\n\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"❌ 操作过程中发生错误: {str(e)}")
                print("💡 建议: 尝试重新选择操作或检查输入")
    except Exception as e:
        print(f"❌ 程序启动失败: {str(e)}")
        print("💡 请检查环境配置和依赖安装")

if __name__ == "__main__":
    main()