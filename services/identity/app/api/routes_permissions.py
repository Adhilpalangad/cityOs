from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_permission
from app.db.models import Permission
from app.schemas.rbac import PermissionRead

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])


@router.get(
    "",
    response_model=list[PermissionRead],
    dependencies=[Depends(require_permission("permission.read"))],
)
async def list_permissions(db: AsyncSession = Depends(get_db)) -> list[PermissionRead]:
    permissions = (await db.scalars(select(Permission).order_by(Permission.code))).all()
    return [PermissionRead(code=p.code, description=p.description) for p in permissions]
