from db.session import SessionLocal

from models.role import Role
from models.user import User
from core.security import hashing


def init_roles(db):
    roles = ["Admin", "GuaranteeDept", "OverseeingTeam", "Vendor"]

    for it in roles:
        existing = db.query(Role).filter(Role.role_name == it).first()

        if not existing:
            db.add(Role(role_name=it))

    db.commit()
    print("Roles added")


def init_admin(db):
    admin_role = db.query(Role).filter(Role.role_name == "Admin").first()

    if not admin_role:
        print("Admin role not found")
        return

    existing_admin = db.query(User).filter(
        User.email == "admin@example.com").first()

    if not existing_admin:
        admin = User(
            name="Admin",
            email="admin@example.com",
            password_hash=hashing("admin123"),
            role_id=admin_role.role_id,
            organisation="SYSTEM"
        )
        db.add(admin)
        db.commit()
        print("Admin user created")
    else:
        print("Admin already exists")
