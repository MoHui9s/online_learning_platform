"""选课模块服务层。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session

from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.course import Course  # 假设已存在
from app.models.user import User
from app.models.course import CourseStatus

class EnrollmentService:
    """选课服务。"""

    @staticmethod
    def enroll(db: Session, user_id: int, course_id: int) -> Enrollment:
        """
        选课（幂等复用逻辑）。
        规则：若存在 dropped 记录则复用（重置进度/状态）；若不存在则新建。
        同时同步维护 courses.student_count。
        """
        # 1. 校验课程是否存在且可报名（status = published）
        course = db.execute(
            select(Course).where(
                Course.id == course_id,
                Course.status == CourseStatus.published  # 使用枚举，而不是 "published"
            )
        ).scalar_one_or_none()
        if not course:
            raise ValueError("课程不存在或未上架")

        # 2. 查询已有选课记录（含 dropped 状态）
        existing = db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id
            )
        ).scalar_one_or_none()

        if existing:
            if existing.status == EnrollmentStatus.active:
                raise ValueError("已选课，无需重复操作")
            elif existing.status == EnrollmentStatus.completed:
                raise ValueError("该课程已结课，无法重新选课")
            elif existing.status == EnrollmentStatus.dropped:
                # 复用旧记录：重置状态和进度
                existing.status = EnrollmentStatus.active
                existing.progress_percent = 0.00
                existing.enrolled_at = datetime.now()
                db.flush()
                # student_count 已经包含该用户，无需再 +1
                return existing
        else:
            # 3. 新建选课记录
            new_enrollment = Enrollment(
                user_id=user_id,
                course_id=course_id,
                status=EnrollmentStatus.active,
                progress_percent=0.00,
                enrolled_at=datetime.now(),
            )
            db.add(new_enrollment)
            db.flush()
            # 4. 冗余字段 +1
            course.student_count = (course.student_count or 0) + 1
            db.flush()
            return new_enrollment

        raise RuntimeError("选课流程异常")  # 理论上不会走到

    @staticmethod
    def drop(db: Session, user_id: int, course_id: int) -> Enrollment:
        """
        退课：将 status 置为 dropped。
        同时同步维护 courses.student_count -1。
        """
        enrollment = db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.status.in_([EnrollmentStatus.active, EnrollmentStatus.completed])
            )
        ).scalar_one_or_none()

        if not enrollment:
            raise ValueError("未找到有效选课记录，无法退课")

        # 已完成的课程是否允许退课？按设计允许，但业务上可能需限制。
        # 这里统一允许，仅做状态变更。
        enrollment.status = EnrollmentStatus.dropped
        db.flush()

        # 冗余字段 -1（防止负数）
        course = db.execute(select(Course).where(Course.id == course_id)).scalar_one()
        course.student_count = max((course.student_count or 1) - 1, 0)
        db.flush()

        return enrollment

    @staticmethod
    def get_my_courses(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[dict], int]:
        """
        获取我的课程列表（含整体进度 progress_percent）。
        返回 (items, total)
        """
        # 1. 查询选课记录总数
        total = db.execute(
            select(func.count()).select_from(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.status.in_([EnrollmentStatus.active, EnrollmentStatus.completed])
            )
        ).scalar_one()

        # 2. 分页查询选课记录，关联课程和教师
        offset = (page - 1) * page_size
        stmt = (
            select(
                Enrollment,
                Course.title.label("course_title"),
                Course.cover_url,
                User.nickname.label("teacher_name"),
            )
            .join(Course, Enrollment.course_id == Course.id)
            .join(User, Course.teacher_id == User.id)
            .where(
                Enrollment.user_id == user_id,
                Enrollment.status.in_([EnrollmentStatus.active, EnrollmentStatus.completed])
            )
            .order_by(Enrollment.enrolled_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        rows = db.execute(stmt).all()

        items = []
        for row in rows:
            enrollment = row[0]  # Enrollment 对象
            items.append({
                "course_id": enrollment.course_id,
                "course_title": row.course_title,
                "cover_url": row.cover_url,
                "teacher_name": row.teacher_name,
                "status": enrollment.status.value,
                "progress_percent": float(enrollment.progress_percent or 0.00),
                "enrolled_at": enrollment.enrolled_at,
            })

        return items, total