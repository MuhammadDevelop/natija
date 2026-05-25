# Barcha modellar shu yerda import qilinadi,
# Alembic migratsiyalari ularni ko'rishi uchun
from app.db.database import Base  # noqa: F401

# Modellarni import qilish
from app.models.user import User  # noqa: F401
from app.models.course import Course, Group, GroupStudent  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.finance import Payment, Salary  # noqa: F401
from app.models.lesson import Lesson  # noqa: F401
from app.models.task import Task, StudentTask  # noqa: F401
from app.models.bonus import StudentBonus  # noqa: F401
from app.models.material import CourseMaterial  # noqa: F401

