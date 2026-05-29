from typing import Optional, List
from datetime import datetime
from decimal import Decimal
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session
# pyrefly: ignore [missing-import]
from sqlalchemy import func

from app.models.course import Course, Group, GroupStudent
from app.models.finance import Payment, Salary, PaymentStatus
from app.schemas.course import CourseCreate, CourseUpdate, GroupCreate, GroupUpdate
from app.schemas.finance import PaymentCreate, PaymentUpdate, SalaryCreate, SalaryUpdate
from app.core.exceptions import NotFoundException


class CourseService:
    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Course]:
        return db.query(Course).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, course_id: int) -> Course:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise NotFoundException(f"Kurs (id={course_id}) topilmadi")
        return course

    def create(self, db: Session, course_in: CourseCreate) -> Course:
        course = Course(**course_in.model_dump())
        db.add(course)
        db.commit()
        db.refresh(course)
        return course

    def update(self, db: Session, course_id: int, course_in: CourseUpdate) -> Course:
        course = self.get_by_id(db, course_id)
        for key, value in course_in.model_dump(exclude_unset=True).items():
            setattr(course, key, value)
        db.commit()
        db.refresh(course)
        return course

    def delete(self, db: Session, course_id: int) -> bool:
        course = self.get_by_id(db, course_id)
        db.delete(course)
        db.commit()
        return True


class GroupService:
    def get_all(self, db: Session, course_id: Optional[int] = None) -> List[Group]:
        query = db.query(Group)
        if course_id:
            query = query.filter(Group.course_id == course_id)
        return query.all()

    def get_by_id(self, db: Session, group_id: int) -> Group:
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            raise NotFoundException(f"Guruh (id={group_id}) topilmadi")
        return group

    def create(self, db: Session, group_in: GroupCreate) -> Group:
        group = Group(**group_in.model_dump())
        db.add(group)
        db.commit()
        db.refresh(group)
        return group

    def update(self, db: Session, group_id: int, group_in: GroupUpdate) -> Group:
        group = self.get_by_id(db, group_id)
        for key, value in group_in.model_dump(exclude_unset=True).items():
            setattr(group, key, value)
        db.commit()
        db.refresh(group)
        return group

    def add_student(self, db: Session, group_id: int, student_id: int) -> GroupStudent:
        # Guruhda allaqachon borligini tekshiramiz
        existing = db.query(GroupStudent).filter(
            GroupStudent.group_id == group_id,
            GroupStudent.student_id == student_id,
            GroupStudent.is_active == True,
        ).first()
        if existing:
            return existing

        gs = GroupStudent(group_id=group_id, student_id=student_id)
        db.add(gs)
        db.commit()
        db.refresh(gs)
        return gs

    def get_student_count(self, db: Session, group_id: int) -> int:
        return db.query(func.count(GroupStudent.id)).filter(
            GroupStudent.group_id == group_id,
            GroupStudent.is_active == True
        ).scalar()


class FinanceService:
    def get_payments(
        self,
        db: Session,
        student_id: Optional[int] = None,
        month: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
    ) -> List[Payment]:
        query = db.query(Payment)
        if student_id:
            query = query.filter(Payment.student_id == student_id)
        if month:
            query = query.filter(Payment.month == month)
        if status:
            query = query.filter(Payment.status == status)
        return query.all()

    def create_payment(self, db: Session, payment_in: PaymentCreate, received_by: int) -> Payment:
        payment = Payment(**payment_in.model_dump(), received_by=received_by)
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def update_payment(self, db: Session, payment_id: int, payment_in: PaymentUpdate) -> Payment:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise NotFoundException("To'lov topilmadi")
        update_data = payment_in.model_dump(exclude_unset=True)
        if payment_in.status == PaymentStatus.PAID and not payment.paid_at:
            update_data["paid_at"] = datetime.utcnow()
        for key, value in update_data.items():
            setattr(payment, key, value)
        db.commit()
        db.refresh(payment)
        return payment

    def get_monthly_summary(self, db: Session, month: str) -> dict:
        total_income = db.query(func.sum(Payment.amount)).filter(
            Payment.month == month,
            Payment.status == PaymentStatus.PAID,
        ).scalar() or Decimal("0")

        total_salary = db.query(func.sum(Salary.amount + Salary.bonus - Salary.fine)).filter(
            Salary.month == month,
            Salary.status == PaymentStatus.PAID,
        ).scalar() or Decimal("0")

        pending = db.query(func.count(Payment.id)).filter(
            Payment.month == month,
            Payment.status == PaymentStatus.PENDING,
        ).scalar()

        overdue = db.query(func.count(Payment.id)).filter(
            Payment.month == month,
            Payment.status == PaymentStatus.OVERDUE,
        ).scalar()

        return {
            "total_income": total_income,
            "total_expenses": total_salary,
            "net_profit": total_income - total_salary,
            "pending_payments": pending,
            "overdue_payments": overdue,
        }

    def create_salary(self, db: Session, salary_in: SalaryCreate) -> Salary:
        salary = Salary(**salary_in.model_dump())
        db.add(salary)
        db.commit()
        db.refresh(salary)
        return salary

    def update_salary(self, db: Session, salary_id: int, salary_in: SalaryUpdate) -> Salary:
        salary = db.query(Salary).filter(Salary.id == salary_id).first()
        if not salary:
            raise NotFoundException("Oylik topilmadi")
        update_data = salary_in.model_dump(exclude_unset=True)
        if salary_in.status == PaymentStatus.PAID and not salary.paid_at:
            update_data["paid_at"] = datetime.utcnow()
        for key, value in update_data.items():
            setattr(salary, key, value)
        db.commit()
        db.refresh(salary)
        return salary

    def get_salaries(self, db: Session, teacher_id: Optional[int] = None, month: Optional[str] = None) -> List[Salary]:
        query = db.query(Salary)
        if teacher_id:
            query = query.filter(Salary.teacher_id == teacher_id)
        if month:
            query = query.filter(Salary.month == month)
        return query.all()

    def renew_monthly_payments(self, db: Session, month: str) -> dict:
        """
        Faol guruhlardagi barcha faol o'quvchilar uchun berilgan oyga (YYYY-MM formatda)
        to'lov yozuvlarini avtomat yaratadi (agar allaqachon mavjud bo'lmasa).
        """
        active_memberships = db.query(GroupStudent).join(Group).filter(
            GroupStudent.is_active == True,
            Group.is_active == True
        ).all()

        created_count = 0
        skipped_count = 0

        for gs in active_memberships:
            course = gs.group.course
            if not course or not course.is_active:
                continue

            # Ushbu talaba va kurs uchun bu oyda to'lov bormi?
            existing_payment = db.query(Payment).filter(
                Payment.student_id == gs.student_id,
                Payment.course_id == course.id,
                Payment.month == month
            ).first()

            if not existing_payment:
                # Yangi to'lov yozuvi (PENDING holatda)
                payment = Payment(
                    amount=course.price,
                    month=month,
                    status=PaymentStatus.PENDING,
                    student_id=gs.student_id,
                    course_id=course.id,
                    notes=f"{gs.group.name} guruhi uchun oylik to'lov ({month})"
                )
                db.add(payment)
                created_count += 1
            else:
                skipped_count += 1

        if created_count > 0:
            db.commit()

        return {
            "created": created_count,
            "skipped": skipped_count,
            "month": month
        }



course_service = CourseService()
group_service = GroupService()
finance_service = FinanceService()
