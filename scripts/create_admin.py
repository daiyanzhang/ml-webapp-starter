#!/usr/bin/env python3
"""
创建管理员用户脚本
Usage: 
  cd backend && python ../scripts/create_admin.py
  或在 Docker 中: docker-compose exec backend python ../scripts/create_admin.py
"""
import asyncio
import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, '/app')

from app.core.database import AsyncSessionLocal
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate


async def create_admin_user():
    """创建管理员用户"""
    print("🚀 正在创建管理员用户...")
    
    async with AsyncSessionLocal() as session:
        # 检查是否已存在admin用户
        existing_user = await get_user_by_username(session, username="admin")
        if existing_user:
            print("✅ 管理员用户已存在")
            print(f"   用户名: {existing_user.username}")
            print(f"   邮箱: {existing_user.email}")
            print(f"   超级用户: {existing_user.is_superuser}")
            return existing_user
        
        # 创建管理员用户
        try:
            admin_user = UserCreate(
                email="admin@example.com",
                username="admin",
                password="admin123",
                full_name="System Administrator",
                is_active=True
            )
            
            user = await create_user(session, user=admin_user)
            
            # 设置为超级用户
            user.is_superuser = True
            await session.commit()
            await session.refresh(user)
            
            print("✅ 管理员用户创建成功!")
            print(f"   用户名: {user.username}")
            print(f"   邮箱: {user.email}")
            print(f"   密码: admin123")
            print(f"   超级用户: {user.is_superuser}")
            print("\n⚠️  请在生产环境中修改默认密码!")
            
            return user
            
        except Exception as e:
            print(f"❌ 创建管理员用户失败: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(create_admin_user())