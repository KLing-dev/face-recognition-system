#!/usr/bin/env python3
"""修复用户名name字段的唯一约束问题

该脚本通过重建表的方式移除name字段的唯一约束，
以允许注册姓名相同但身份ID不同的用户。
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import config
from app.models.models import User, Base, SessionLocal


def fix_name_constraint():
    """修复name字段的唯一约束"""
    print("🔍 开始修复name字段约束...")
    
    # 创建数据库引擎
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    
    try:
        with engine.begin() as conn:
            # 检查是否存在name字段的唯一索引
            print("📋 查询表索引信息...")
            result = conn.execute(text("PRAGMA index_list(users)"))
            indexes = result.fetchall()
            
            # 查找包含name的唯一索引
            name_unique_index = None
            for idx in indexes:
                idx_name, idx_unique = idx[1], idx[2]
                if idx_unique:  # 如果是唯一索引
                    # 检查索引包含的列
                    idx_info = conn.execute(text(f"PRAGMA index_info('{idx_name}')")).fetchall()
                    columns = [info[2] for info in idx_info]
                    if 'name' in columns:
                        name_unique_index = idx_name
                        break
            
            if name_unique_index:
                print(f"⚠️  发现name字段的唯一索引: {name_unique_index}")
                print(f"🛠️  正在删除索引: {name_unique_index}")
                conn.execute(text(f"DROP INDEX IF EXISTS {name_unique_index}"))
                print(f"✅ 索引 {name_unique_index} 已删除")
            else:
                print("✅ 未发现name字段的唯一索引")
            
            # 确保name字段有普通索引
            print("📝 创建name字段的普通索引...")
            try:
                # 尝试创建普通索引
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_name ON users(name)"))
                print("✅ name字段普通索引创建成功")
            except Exception as e:
                print(f"⚠️ 创建索引时的警告: {e}")
            
            print("🎉 修复完成！现在可以注册姓名相同的用户了。")
            print("💡 提示: 身份ID仍然保持唯一性约束，确保系统安全。")
            
    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        sys.exit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    fix_name_constraint()
