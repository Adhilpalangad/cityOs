// Mirrors services/identity/app/schemas/*.py field-for-field. Keep these in
// sync by hand -- there is no shared codegen yet, so a field renamed on one
// side and not the other is a real, silent bug.

export type UserStatus = "PENDING_VERIFICATION" | "ACTIVE" | "SUSPENDED" | "DEACTIVATED";

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface RegisterResponse {
  id: string;
  email: string;
  status: UserStatus;
}

export interface MeResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  department: string | null;
  permissions: string[];
  email_verified: boolean;
  status: UserStatus;
}

export interface UserRead {
  id: string;
  email: string;
  full_name: string;
  role_code: string;
  department_code: string | null;
  status: UserStatus;
  email_verified: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface PageMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface UserListResponse {
  items: UserRead[];
  meta: PageMeta;
}

export interface PermissionRead {
  code: string;
  description: string;
}

export interface RoleRead {
  code: string;
  name: string;
  department_code: string | null;
  is_platform_role: boolean;
  permissions: string[];
}

export interface DepartmentRead {
  code: string;
  name: string;
}

export interface MessageResponse {
  message: string;
}

/** The `{"error": {...}}` envelope every CityOS service error response uses. */
export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}
