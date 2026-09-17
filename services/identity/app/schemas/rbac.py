from pydantic import BaseModel


class PermissionRead(BaseModel):
    code: str
    description: str


class RoleRead(BaseModel):
    code: str
    name: str
    department_code: str | None
    is_platform_role: bool
    permissions: list[str]


class RoleCreate(BaseModel):
    code: str
    name: str
    department_code: str | None = None
    permissions: list[str] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    department_code: str | None = None
    permissions: list[str] | None = None


class DepartmentRead(BaseModel):
    code: str
    name: str


class DepartmentCreate(BaseModel):
    code: str
    name: str


class DepartmentUpdate(BaseModel):
    name: str
