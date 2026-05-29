from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.group_application import GroupApplication, ApplicationStatus
from app.models.course import Group, GroupStudent
from app.models.user import Subject
from app.schemas.group_application import GroupApplicationCreate, GroupCreateFromApplications
from app.services.course_service import group_service
from app.core.exceptions import NotFoundException, ConflictException


class GroupApplicationService:
    def create_application(
        self, db: Session, student_id: int, app_in: GroupApplicationCreate
    ) -> GroupApplication:
        # Tekshiramiz: O'quvchi xuddi shu fan va daraja uchun faol (pending) ariza bergandirmi?
        existing = db.query(GroupApplication).filter(
            GroupApplication.student_id == student_id,
            GroupApplication.subject == app_in.subject,
            GroupApplication.level == app_in.level,
            GroupApplication.status == ApplicationStatus.PENDING,
        ).first()

        if existing:
            raise ConflictException("Siz ushbu fan va daraja uchun ariza topshirgansiz va u hozir ko'rib chiqilmoqda")

        application = GroupApplication(
            student_id=student_id,
            subject=app_in.subject,
            level=app_in.level,
            notes=app_in.notes,
            status=ApplicationStatus.PENDING,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    def get_application_by_id(self, db: Session, app_id: int) -> GroupApplication:
        app = db.query(GroupApplication).filter(GroupApplication.id == app_id).first()
        if not app:
            raise NotFoundException(f"Ariza (id={app_id}) topilmadi")
        return app

    def get_applications(
        self,
        db: Session,
        student_id: Optional[int] = None,
        subject: Optional[Subject] = None,
        level: Optional[str] = None,
        status: Optional[ApplicationStatus] = None,
    ) -> List[GroupApplication]:
        query = db.query(GroupApplication)
        if student_id:
            query = query.filter(GroupApplication.student_id == student_id)
        if subject:
            query = query.filter(GroupApplication.subject == subject)
        if level:
            query = query.filter(GroupApplication.level == level)
        if status:
            query = query.filter(GroupApplication.status == status)
        return query.all()

    def create_group_from_applications(
        self, db: Session, group_in: GroupCreateFromApplications
    ) -> Group:
        # 1. Guruh yaratish
        group = Group(
            name=group_in.name,
            schedule=group_in.schedule,
            max_students=group_in.max_students,
            course_id=group_in.course_id,
            is_active=True,
        )
        db.add(group)
        db.commit()
        db.refresh(group)

        # 2. Arizadagi o'quvchilarni guruhga qo'shish va arizalarni 'grouped' qilish
        for app_id in group_in.application_ids:
            app = self.get_application_by_id(db, app_id)
            if app.status != ApplicationStatus.PENDING:
                continue  # Faqat ko'rilmagan arizalarni guruhlaymiz

            # Guruhga qo'shish
            group_service.add_student(db, group_id=group.id, student_id=app.student_id)
            
            # Statusni yangilash
            app.status = ApplicationStatus.GROUPED

        db.commit()
        db.refresh(group)
        return group


group_application_service = GroupApplicationService()
