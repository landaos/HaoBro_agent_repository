# ============================================
# users.py - 用户管理 API 路由
# ============================================
#
# ═══════════════════════════════════════════
# 需要在此文件中编写的路由：
# ═══════════════════════════════════════════
#
# 所有路由挂载在 /api/v1/users 下
# 所有路由都需要 admin 角色权限（user:manage）
#
# 1. GET /users
#    - 分页查询用户列表
#    - 查询参数：page, page_size, search（用户名搜索）, role_id, is_active
#    - 响应：PaginatedResponse[UserResponse]
#    - 权限：require_permission("user:read")
#
# 2. GET /users/{user_id}
#    - 查询单个用户详情
#    - 响应：UserResponse（含角色信息、权限列表）
#    - 权限：require_permission("user:read")
#
# 3. POST /users
#    - 创建新用户
#    - 请求体：CreateUserRequest
#    - 响应：UserResponse
#    - 权限：require_permission("user:create")
#
# 4. PUT /users/{user_id}
#    - 更新用户信息
#    - 请求体：UpdateUserRequest
#    - 响应：UserResponse
#    - 权限：require_permission("user:update")
#
# 5. PUT /users/{user_id}/role
#    - 变更用户角色
#    - 请求体：ChangeRoleRequest { role_id: int }
#    - 响应：UserResponse
#    - 权限：require_permission("user:update")
#
# 6. PUT /users/{user_id}/active
#    - 启用/禁用用户
#    - 请求体：SetActiveRequest { is_active: bool }
#    - 响应：UserResponse
#    - 权限：require_permission("user:update")
#
# 7. DELETE /users/{user_id}
#    - 删除用户（软删除）
#    - 响应：{status: "deleted"}
#    - 权限：require_permission("user:delete")
#
# 8. GET /users/me
#    - 获取当前用户信息（任何人都可以查自己）
#    - 不需要特殊权限
#
# 9. PUT /users/me/password
#    - 修改自己密码
#    - 请求体：ChangePasswordRequest { old_password, new_password }
#    - 不需要特殊权限
#
# ═══════════════════════════════════════════
# 依赖注入：
#   db: AsyncSession = Depends(get_db)
#   current_user: User = Depends(get_current_user)
#   service = UserService()
# ═══════════════════════════════════════════
from sqlalchemy import select, or_
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, HTTPException

from src.db.session import async_session_factory
from src.db.redis import connect_redis
from src.auth.security import get_current_user_id, get_user_info_from_redis, security, blacklist_token, generate_token, encode_password, verify_password
from src.schemas.user import UserResponse, LoginRequest, UserUpdateRequest, RegisterRequest, ResetPasswordRequest
from src.models.user import User, UserStatusChoice
from src.services.rate_limiter import rate_limit

user_router = APIRouter(tags=["user"],prefix="/user")

def dict_user_response(user: User) -> UserResponse:
    return UserResponse(
        user_id=user.user_id,
        username=user.user_name,
        email=user.email,
        phone=user.phone,
        gender=user.gender,
        status=user.status,
    )
    

@user_router.post("/login")
async def login(
    req: LoginRequest,
    _rate_limit: None = Depends(rate_limit(limit=5, windows=60)),
):
    async with async_session_factory() as db:
        if not req.username and not req.email:
            raise HTTPException(status_code=400, detail="用户名或邮箱不能为空")
        result = await db.execute(select(User).where(or_(User.user_name == req.username, User.email == req.email)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户或邮箱不存在")
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=400, detail="密码错误")
        if user.status != UserStatusChoice.ACTIVE:
            raise HTTPException(status_code=400, detail="用户已被禁用或者未激活")

        
    token,expire_time = generate_token(user.user_id,user.email,user.user_name)
    return {
        "message": f"{user.user_name}登录成功",
        "user": dict_user_response(user).model_dump(),    
        "token": token,
    }

      

@user_router.post("/register")
async def register(
    req: RegisterRequest,
    _rate_limit: None = Depends(rate_limit(limit=3, windows=60)),
):
    if req.password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(or_(User.user_name == req.username, User.email == req.email)))
        user = result.scalar_one_or_none()
        if user:
            raise HTTPException(status_code=400, detail="用户名或者邮箱已存在")
        if req.phone:
            result = await db.execute(select(User).where(User.phone == req.phone))
            user = result.scalar_one_or_none()
            if user:
                raise HTTPException(status_code=400, detail="手机号已存在")
        user = User(
            user_name=req.username,
            email=req.email,
            phone=req.phone,
            gender=req.gender,
            password_hash=encode_password(req.password),
            status=UserStatusChoice.ACTIVE,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        token,expire_time = generate_token(user.user_id,user.email,user.user_name)
        return {"status": 201,"message": f"{user.user_name}注册成功","user": dict_user_response(user).model_dump(),"token": token}
        
    

@user_router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest,user_id: str = Depends(get_current_user_id),credentials: HTTPAuthorizationCredentials = Depends(security)):
    if req.new_password != req.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")
    if req.new_password == req.old_password:
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if not verify_password(req.old_password, user.password_hash):
            raise HTTPException(status_code=400, detail="旧密码错误")

        await blacklist_token(credentials.credentials)
        user.password_hash = encode_password(req.new_password)
        await db.commit()
        
    redis_client = await connect_redis()
    await redis_client.delete(f"user:{user_id}")

    new_token,expire_time = generate_token(user.user_id,user.email,user.user_name)
    return {"message": "密码重置成功","token": new_token}

@user_router.get("/detail/")
async def get_user_info(
    user_id: str = Depends(get_current_user_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    user_info = await get_user_info_from_redis(user_id)
    return {
        "success": True,
        "message": "获取用户详情成功",
        "data": user_info,
    }
    
@user_router.put("/update/")
async def update_user(
    req: UserUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=400, detail="用户不存在")

        if req.phone:
            existing = await session.execute(
                select(User).where(User.phone == req.phone, User.user_id != user_id)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(status_code=400, detail={"phone": "该电话号码已被注册"})

        update_data = req.model_dump(exclude_unset=True)
        # 映射前端字段名到模型字段名
        if 'username' in update_data:
            update_data['user_name'] = update_data.pop('username')
        for field, value in update_data.items():
            setattr(user, field, value)
        await session.commit()

    await blacklist_token(credentials.credentials)
    redis = await connect_redis()
    await redis.delete(f"user:{user_id}")

    new_token, expire_time = generate_token(user.user_id, user.email, user.user_name)
    return {
        "message": "用户信息更新成功",
        "user": dict_user_response(user).model_dump(),
        "token": new_token,
    }


@user_router.post("/logout/")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    await blacklist_token(credentials.credentials)
    return {"message": "用户注销成功"}