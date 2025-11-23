#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库修复脚本 - 添加缺失的identity_id列

用于修复数据库表结构与模型定义不同步的问题，
确保users表包含identity_id列。
"""

import os
import sys
from datetime import datetime

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入数据库相关模块
from app.models.models import Base, User, engine, SessionLocal
from sqlalchemy import text

def check_and_fix_database():
    """
    检查并修复数据库表结构
    - 检查表中是否存在identity_id列
    - 如果不存在，添加该列并设置默认值
    - 更新现有记录的identity_id值
    """
    print("🔍 开始检查数据库结构...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 使用原始SQL检查列是否存在
        with engine.connect() as conn:
            # 查询表结构
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            print(f"📋 当前users表列: {columns}")
            
            # 检查是否缺少identity_id列
            if 'identity_id' not in columns:
                print("⚠️ 发现问题: users表中缺少identity_id列")
                print("🛠️  正在添加identity_id列...")
                
                try:
                    # 添加新列
                    conn.execute(text("ALTER TABLE users ADD COLUMN identity_id VARCHAR(50)"))
                    conn.commit()
                    print("✅ identity_id列添加成功")
                    
                    # 更新现有记录的identity_id值
                    print("📝 更新现有记录的identity_id值...")
                    users = db.query(User).all()
                    
                    for index, user in enumerate(users, 1):
                        # 使用序号作为identity_id
                        user.identity_id = str(index)
                        db.add(user)
                        
                        # 每10条记录提交一次
                        if index % 10 == 0:
                            db.commit()
                            print(f"  - 已更新 {index} 条记录")
                    
                    # 最后一次提交
                    db.commit()
                    print(f"✅ 已更新所有 {len(users)} 条记录的identity_id值")
                    
                    # 添加唯一索引
                    try:
                        conn.execute(text("CREATE INDEX idx_users_identity_id ON users(identity_id)"))
                        conn.execute(text("CREATE UNIQUE INDEX idx_users_identity_id_unique ON users(identity_id)"))
                        conn.commit()
                        print("✅ 已为identity_id列添加唯一索引")
                    except Exception as e:
                        print(f"⚠️ 添加索引时出错: {e}")
                        print("   继续执行其他操作...")
                        
                except Exception as e:
                    print(f"❌ 添加列时出错: {e}")
                    print("   请检查数据库权限或手动执行SQL语句")
            else:
                print("✅ 数据库结构正常，users表已包含identity_id列")
                
                # 检查是否有null值记录
                null_count = db.query(User).filter(User.identity_id.is_(None)).count()
                if null_count > 0:
                    print(f"⚠️ 发现 {null_count} 条记录的identity_id为NULL")
                    print("🛠️  正在填充NULL值...")
                    
                    users = db.query(User).filter(User.identity_id.is_(None)).all()
                    for index, user in enumerate(users, 1):
                        user.identity_id = str(datetime.now().strftime("%Y%m%d%H%M%S")) + f"_{index}"
                        db.add(user)
                    
                    db.commit()
                    print(f"✅ 已填充所有 {len(users)} 条NULL值记录")
                
                # 检查唯一约束
                try:
                    conn.execute(text("SELECT COUNT(*), identity_id FROM users GROUP BY identity_id HAVING COUNT(*) > 1"))
                    duplicate_count = len(result.fetchall())
                    if duplicate_count > 0:
                        print(f"⚠️ 发现 {duplicate_count} 个重复的identity_id值")
                        print("⚠️ 警告: 这可能导致后续操作失败，请检查数据一致性")
                except Exception as e:
                    print(f"⚠️ 检查重复值时出错: {e}")
        
        # 重新创建数据库（如果以上方法失败）
        print("\n⚠️ 注意: 如果基本修复失败，可能需要重新初始化数据库")
        print("   要重新初始化，请运行脚本时传入参数 --recreate")
        
        # 检查命令行参数
        if len(sys.argv) > 1 and '--recreate' in sys.argv:
            print("⚠️ 警告: 这将删除所有数据！确认继续？")
            confirm = input("请输入 'DELETE' 确认删除所有数据: ")
            
            if confirm == 'DELETE':
                print("🗑️  删除所有表...")
                Base.metadata.drop_all(bind=engine)
                print("🏗️  重新创建表结构...")
                Base.metadata.create_all(bind=engine)
                print("✅ 数据库已重新初始化")
            else:
                print("❌ 取消重新初始化")
        
    except Exception as e:
        print(f"❌ 修复过程中出错: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """
    主函数
    """
    print("🎯 数据库修复工具 - 修复identity_id列")
    print("=" * 50)
    
    try:
        check_and_fix_database()
        print("\n🎉 数据库检查和修复完成")
        print("📋 后续建议:")
        print("  1. 运行应用程序测试功能是否恢复正常")
        print("  2. 监控日志，确保不再出现相关错误")
        print("  3. 考虑定期备份数据库以防止数据丢失")
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        print(f"   详细错误信息: {str(e)}")

if __name__ == "__main__":
    main()