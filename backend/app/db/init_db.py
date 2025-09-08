import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, '/app')

from app.core.database import AsyncSessionLocal
from app.crud.user import get_user_by_username, create_user
from app.schemas.user import UserCreate
from app.core.config import settings


async def init_db() -> None:
    """初始化数据库，创建超级管理员用户"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在admin用户
        user = await get_user_by_username(session, username="admin")
        if not user:
            # 创建超级管理员用户
            user_in = UserCreate(
                email="admin@example.com",
                username="admin",
                password="admin123",  # 请在生产环境中修改
                full_name="System Administrator",
                is_active=True
            )
            user = await create_user(session, user=user_in)
            # 设置为超级用户
            user.is_superuser = True
            await session.commit()
            print("Super user created successfully")
        else:
            print("Super user already exists")


if __name__ == "__main__":
    asyncio.run(init_db())