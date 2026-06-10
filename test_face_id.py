from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.models.attendance import Attendance
from app.models.course import Course, Group, GroupStudent

client = TestClient(app)

def test_face_id_endpoints():
    db = SessionLocal()
    
    # 1. Superadmin yoki Teacher yaratamiz (auth uchun)
    teacher = db.query(User).filter(User.phone == "+998901112233").first()
    if not teacher:
        teacher = User(
            full_name="Test Teacher",
            phone="+998901112233",
            hashed_password="hashed_pass",
            role=UserRole.TEACHER,
            is_active=True
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)

    # 2. Student yaratamiz (Face ID uchun)
    student = db.query(User).filter(User.phone == "+998909998877").first()
    if not student:
        student = User(
            full_name="Test Student",
            phone="+998909998877",
            hashed_password="hashed_pass",
            role=UserRole.STUDENT,
            is_active=True
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    # 2.5 Guruh va Kurs yaratamiz
    course = Course(name="Face ID Test Course", price=1000)
    db.add(course)
    db.commit()
    db.refresh(course)

    group = Group(name="Face ID Test Group", course_id=course.id)
    db.add(group)
    db.commit()
    db.refresh(group)

    gs = GroupStudent(group_id=group.id, student_id=student.id)
    db.add(gs)
    db.commit()

    # 3. Tokenni simulyatsiya qilish uchun TestClient dagi get_current_active_user ni override qilamiz
    from app.api import deps
    app.dependency_overrides[deps.get_current_active_user] = lambda: teacher

    print("--- FACE ID TEST START ---")

    # 4. Yuzni ro'yxatdan o'tkazish testi
    mock_encoding = [0.1, 0.2, 0.3, 0.4] * 32 # 128-d mock array
    
    reg_response = client.post(
        f"/api/v1/face-id/register/{student.id}",
        json={"encoding": mock_encoding, "image_base64": "dummy_base64_string"}
    )
    
    print(f"REGISTER RESPONSE: {reg_response.status_code}")
    print(reg_response.json())
    assert reg_response.status_code == 200

    # 5. Yuz bilan davomat qilish testi
    # O'xshash encoding yuboramiz
    verify_response = client.post(
        "/api/v1/face-id/verify",
        json={"group_id": group.id, "encoding": mock_encoding}
    )
    
    print(f"VERIFY RESPONSE: {verify_response.status_code}")
    print(verify_response.json())
    assert verify_response.status_code == 200
    assert verify_response.json()["matched"] == True
    
    # Notanish yuz yuboramiz
    wrong_encoding = [-0.9, -0.8, -0.7, -0.6] * 32
    verify_fail = client.post(
        "/api/v1/face-id/verify",
        json={"group_id": group.id, "encoding": wrong_encoding}
    )
    
    print(f"VERIFY FAIL RESPONSE: {verify_fail.status_code}")
    print(verify_fail.json())
    assert verify_fail.status_code == 200
    assert verify_fail.json()["matched"] == False

    print("--- BARCHA TESTLAR MUVAFFAQIYATLI O'TDI! ---")
    
    # O'chirib tashlaymiz
    db.query(Attendance).filter(Attendance.student_id == student.id).delete()
    db.delete(gs)
    db.delete(group)
    db.delete(course)
    db.delete(student)
    db.delete(teacher)
    db.commit()

if __name__ == "__main__":
    test_face_id_endpoints()
