from db.session import engine
from app.db.base_class import Base


from models.user import User
from models.role import Role
from models.vessel import Vessel
from models.vendor import Vendor
from models.equipment import Equipment
from models.defect import Defect
from models.vendor_assignment import VendorAssignment


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")


if __name__ == "__main__":
    init_db()
