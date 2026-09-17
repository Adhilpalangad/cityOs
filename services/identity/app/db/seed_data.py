"""Canonical RBAC seed data.

This module is the single source of truth for the platform's starting
departments, permissions, and roles. It is imported by migration `0002`
(so the rows land in the database) and by the application layer (so
`GET /api/v1/permissions` and role-update validation never drift from what
was actually seeded). Changing RBAC defaults means editing this file and
writing a new migration to reconcile existing databases -- never editing
`0002` after it has shipped.

Section references are to `CityOS_Master_Specification.md`.
"""

DEPARTMENTS: list[tuple[str, str]] = [
    ("PLATFORM", "Platform Administration"),
    ("TRAFFIC", "Traffic Department"),
    ("EMERGENCY", "Emergency Department"),
    ("HEALTHCARE", "Healthcare"),
    ("TRANSPORT", "Transport"),
    ("UTILITIES", "Utilities"),
    ("INFRASTRUCTURE", "Infrastructure"),
    ("FINANCE", "Finance"),
    ("CITIZEN_SERVICES", "Citizen Services"),
]

# (code, description) -- resource.action naming, per spec section 9.
PERMISSIONS: list[tuple[str, str]] = [
    ("user.read", "View user accounts"),
    ("user.create", "Create user accounts"),
    ("user.update", "Update user accounts"),
    ("user.delete", "Deactivate user accounts"),
    ("role.read", "View roles and their permissions"),
    ("role.create", "Create roles"),
    ("role.update", "Update roles and their permissions"),
    ("role.delete", "Delete roles"),
    ("department.read", "View departments"),
    ("department.create", "Create departments"),
    ("department.update", "Update departments"),
    ("department.delete", "Delete departments"),
    ("permission.read", "View the platform permission catalog"),
    ("road.read", "View roads"),
    ("road.create", "Create roads"),
    ("road.update", "Update roads"),
    ("road.delete", "Delete roads"),
    ("traffic.read", "View live traffic conditions"),
    ("traffic.create", "Create traffic records"),
    ("traffic.update", "Update traffic conditions"),
    ("traffic.delete", "Delete traffic records"),
    ("vehicle.read", "View vehicles"),
    ("vehicle.create", "Create vehicles"),
    ("vehicle.update", "Update vehicles"),
    ("vehicle.delete", "Delete vehicles"),
    ("incident.read", "View incidents"),
    ("incident.create", "Report incidents"),
    ("incident.update", "Update incidents"),
    ("incident.assign", "Assign incident resources"),
    ("incident.resolve", "Resolve incidents"),
    ("hospital.read", "View hospitals"),
    ("hospital.create", "Create hospital records"),
    ("hospital.update", "Update hospital capacity and status"),
    ("hospital.delete", "Delete hospital records"),
    ("ambulance.read", "View ambulances"),
    ("ambulance.update", "Update ambulance status/assignment"),
    ("complaint.read", "View citizen complaints"),
    ("complaint.create", "Create citizen complaints"),
    ("complaint.update", "Update citizen complaints"),
    ("complaint.resolve", "Resolve citizen complaints"),
    ("infrastructure.read", "View infrastructure assets"),
    ("infrastructure.create", "Create infrastructure assets"),
    ("infrastructure.update", "Update infrastructure assets"),
    ("infrastructure.delete", "Delete infrastructure assets"),
    ("utility.read", "View utility network status"),
    ("utility.update", "Update utility network status"),
    ("finance.read", "View budgets and projects"),
    ("finance.create", "Create budgets and projects"),
    ("finance.update", "Update budgets and projects"),
    ("simulation.create", "Create simulation scenarios"),
    ("simulation.run", "Run simulations"),
    ("simulation.read", "View simulation results"),
    ("data_source.read", "View data source configuration"),
    ("data_source.create", "Create data sources"),
    ("data_source.update", "Update or disable data sources"),
    ("data_source.delete", "Delete data sources"),
    ("notification.read", "View notifications"),
    ("notification.create", "Send notifications"),
    ("audit.read", "View audit logs"),
]

PERMISSION_CODES = [code for code, _ in PERMISSIONS]

# Wildcard understood by the permission checker to mean "every permission".
WILDCARD_PERMISSION = "*"

_READ_ALL = [code for code in PERMISSION_CODES if code.endswith(".read")]

# (role_code, name, department_code | None, is_platform_role, permission codes | ["*"])
ROLES: list[tuple[str, str, str | None, bool, list[str]]] = [
    ("SUPER_ADMIN", "Super Administrator", "PLATFORM", True, [WILDCARD_PERMISSION]),
    (
        "CITY_ADMIN",
        "City Administrator",
        "PLATFORM",
        True,
        [
            *_READ_ALL,
            "incident.create",
            "incident.update",
            "incident.assign",
            "incident.resolve",
            "simulation.create",
            "simulation.run",
            "notification.create",
        ],
    ),
    (
        "MAYOR_EXECUTIVE",
        "Mayor / Executive",
        "PLATFORM",
        True,
        [
            "road.read",
            "traffic.read",
            "incident.read",
            "hospital.read",
            "vehicle.read",
            "simulation.read",
            "finance.read",
            "audit.read",
        ],
    ),
    (
        "TRAFFIC_ADMIN",
        "Traffic Administrator",
        "TRAFFIC",
        False,
        [
            "traffic.read",
            "traffic.create",
            "traffic.update",
            "traffic.delete",
            "road.read",
            "road.create",
            "road.update",
            "road.delete",
            "incident.read",
            "incident.create",
            "incident.update",
            "vehicle.read",
        ],
    ),
    (
        "TRAFFIC_OFFICER",
        "Traffic Officer",
        "TRAFFIC",
        False,
        # Matches the worked example in spec section 9 exactly.
        ["traffic.read", "traffic.update", "incident.create", "incident.read", "vehicle.read"],
    ),
    (
        "TRAFFIC_ANALYST",
        "Traffic Analyst",
        "TRAFFIC",
        False,
        ["traffic.read", "road.read", "incident.read"],
    ),
    (
        "EMERGENCY_ADMIN",
        "Emergency Administrator",
        "EMERGENCY",
        False,
        [
            "incident.read",
            "incident.create",
            "incident.update",
            "incident.assign",
            "incident.resolve",
            "ambulance.read",
            "ambulance.update",
            "hospital.read",
        ],
    ),
    (
        "DISPATCHER",
        "Dispatcher",
        "EMERGENCY",
        False,
        ["incident.read", "incident.assign", "ambulance.read", "ambulance.update"],
    ),
    (
        "EMERGENCY_OFFICER",
        "Emergency Officer",
        "EMERGENCY",
        False,
        ["incident.read", "incident.update", "incident.resolve"],
    ),
    (
        "HEALTHCARE_ADMIN",
        "Healthcare Administrator",
        "HEALTHCARE",
        False,
        [
            "hospital.read",
            "hospital.create",
            "hospital.update",
            "hospital.delete",
            "ambulance.read",
        ],
    ),
    (
        "HOSPITAL_ADMIN",
        "Hospital Administrator",
        "HEALTHCARE",
        False,
        ["hospital.read", "hospital.update"],
    ),
    ("HEALTHCARE_ANALYST", "Healthcare Analyst", "HEALTHCARE", False, ["hospital.read"]),
    (
        "TRANSPORT_ADMIN",
        "Transport Administrator",
        "TRANSPORT",
        False,
        ["vehicle.read", "vehicle.create", "vehicle.update", "vehicle.delete", "road.read"],
    ),
    ("FLEET_MANAGER", "Fleet Manager", "TRANSPORT", False, ["vehicle.read", "vehicle.update"]),
    ("TRANSPORT_OFFICER", "Transport Officer", "TRANSPORT", False, ["vehicle.read"]),
    (
        "WATER_ADMIN",
        "Water Administrator",
        "UTILITIES",
        False,
        ["utility.read", "utility.update"],
    ),
    (
        "ENERGY_ADMIN",
        "Energy Administrator",
        "UTILITIES",
        False,
        ["utility.read", "utility.update"],
    ),
    ("UTILITY_OFFICER", "Utility Officer", "UTILITIES", False, ["utility.read"]),
    (
        "INFRASTRUCTURE_ADMIN",
        "Infrastructure Administrator",
        "INFRASTRUCTURE",
        False,
        [
            "infrastructure.read",
            "infrastructure.create",
            "infrastructure.update",
            "infrastructure.delete",
        ],
    ),
    (
        "INFRASTRUCTURE_OFFICER",
        "Infrastructure Officer",
        "INFRASTRUCTURE",
        False,
        ["infrastructure.read", "infrastructure.update"],
    ),
    (
        "MAINTENANCE_MANAGER",
        "Maintenance Manager",
        "INFRASTRUCTURE",
        False,
        ["infrastructure.read", "infrastructure.update"],
    ),
    (
        "FINANCE_ADMIN",
        "Finance Administrator",
        "FINANCE",
        False,
        ["finance.read", "finance.create", "finance.update"],
    ),
    ("FINANCE_OFFICER", "Finance Officer", "FINANCE", False, ["finance.read", "finance.update"]),
    ("AUDITOR", "Auditor", "FINANCE", False, ["finance.read", "audit.read"]),
    (
        "CITIZEN",
        "Citizen",
        "CITIZEN_SERVICES",
        False,
        ["complaint.create", "complaint.read"],
    ),
]

DEFAULT_SELF_REGISTRATION_ROLE = "CITIZEN"

# Fail fast and loudly at import time rather than as an opaque UNIQUE
# constraint violation from the seed migration's bulk insert.
for _code, _name, _department_code, _is_platform_role, _permission_codes in ROLES:
    _duplicates = {c for c in _permission_codes if _permission_codes.count(c) > 1}
    assert not _duplicates, f"role {_code} lists duplicate permission codes: {_duplicates}"
