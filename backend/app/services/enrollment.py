"""选课模块服务层。"""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course, CourseStatus
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.user import User


class EnrollmentService:
    """选课服务。"""

    @staticmethod
    def enroll(db: Session, user_id: int, course_id: int) -> Enrollment:
        """选课（幂等复用逻辑）。

        规则：已 active 拒绝重复选课；completed 为终态不可重选；
        dropped 记录复用（重置进度与选课时间）。同步维护 courses.student_count。
        """
        course = db.execute(
            select(Course).where(
                Course.id == course_id,
                Course.status == CourseStatus.published,
            )
        ).scalar_one_or_none()
        if not course:
            raise ValueError("课程不存在或未上架")

        existing = db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
            )
        ).scalar_one_or_none()

        if existing:
            if existing.status == EnrollmentStatus.active:
                raise ValueError("已选课，无需重复操作")
            if existing.status == EnrollmentStatus.completed:
                raise ValueError("该课程已结课，无法重新选课")
            # dropped：复用旧记录，重置状态和进度
            existing.status = EnrollmentStatus.active
            existing.progress_percent = 0.00
            existing.enrolled_at = datetime.now(timezone.utc)
            enrollment = existing
        else:
            enrollment = Enrollment(
                user_id=user_id,
                course_id=course_id,
                status=EnrollmentStatus.active,
                progress_percent=0.00,
                enrolled_at=datetime.now(timezone.utc),
            )
            db.add(enrollment)

        # 退课时已 -1，复用与新建同样需要 +1
        course.student_count = (course.student_count or 0) + 1
        db.flush()
        return enrollment

    @staticmethod
    def drop(db: Session, user_id: int, course_id: int) -> Enrollment:
        """退课：将 active 记录置为 dropped，courses.student_count 同步 -1。

        completed 为终态不允许退课（避免与 enroll 侧“已结课不可重选”矛盾）。
        """
        enrollment = db.execute(
            select(Enrollment).where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.status == EnrollmentStatus.active,
            )
        ).scalar_one_or_none()

        if not enrollment:
            raise ValueError("未找到进行中的选课记录，无法退课")

        enrollment.status = EnrollmentStatus.dropped

        course = db.execute(select(Course).where(Course.id == course_id)).scalar_one()
        course.student_count = max((course.student_count or 1) - 1, 0)
        db.flush()
        return enrollment

    @staticmethod
    def get_my_courses(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        """我的课程列表（active/completed，含整体进度），返回 (items, total)。"""
        status_filter = Enrollment.status.in_(
            [EnrollmentStatus.active, EnrollmentStatus.completed]
        )

        total = db.execute(
            select(func.count())
            .select_from(Enrollment)
            .where(Enrollment.user_id == user_id, status_filter)
        ).scalar_one()

        stmt = (
            select(
                Enrollment,
                Course.title.label("course_title"),
                Course.cover_url,
                User.nickname.label("teacher_name"),
            )
            .join(Course, Enrollment.course_id == Course.id)
            .join(User, Course.teacher_id == User.id)
            .where(Enrollment.user_id == user_id, status_filter)
            .order_by(Enrollment.enrolled_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = db.execute(stmt).all()

        items = [
            {
                "course_id": row[0].course_id,
                "course_title": row.course_title,
                "cover_url": row.cover_url,
                "teacher_name": row.teacher_name,
                "status": row[0].status.value,
                "progress_percent": float(row[0].progress_percent or 0.00),
                "enrolled_at": row[0].enrolled_at,
            }
            for row in rows
        ]
        return items, total
