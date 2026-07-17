"""选课模块测试：选课/退课/幂等复用/我的课程列表。"""

from app.models.user import UserRole
from tests.conftest import auth_headers, create_user


def _make_published_course(client, db, seq: int) -> tuple[int, dict]:
    """创建教师并发布一门课，返回 (course_id, 教师headers)。"""
    teacher = create_user(db, UserRole.teacher, _seq=seq)
    th = auth_headers(teacher)
    r = client.post("/api/v1/courses", json={"title": f"课程{seq}"}, headers=th)
    cid = r.json()["data"]["id"]
    client.put(
        f"/api/v1/courses/{cid}/status", json={"status": "published"}, headers=th
    )
    return cid, th


class TestEnroll:
    def test_enroll_success(self, client, db):
        cid, _ = _make_published_course(client, db, 100)
        s = create_user(db, UserRole.student, _seq=101)
        r = client.post(f"/api/v1/courses/{cid}/enroll", headers=auth_headers(s))
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["course_id"] == cid
        assert d["status"] == "active"
        assert d["enrolled_at"] is not None

    def test_enroll_increments_student_count(self, client, db):
        cid, _ = _make_published_course(client, db, 102)
        s = create_user(db, UserRole.student, _seq=103)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=auth_headers(s))
        r = client.get(f"/api/v1/courses/{cid}")
        assert r.json()["data"]["student_count"] == 1

    def test_enroll_duplicate_rejected(self, client, db):
        cid, _ = _make_published_course(client, db, 104)
        s = create_user(db, UserRole.student, _seq=105)
        h = auth_headers(s)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        r = client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        assert r.status_code == 400
        assert "重复" in r.json()["message"]

    def test_enroll_unpublished_rejected(self, client, db):
        teacher = create_user(db, UserRole.teacher, _seq=106)
        th = auth_headers(teacher)
        r = client.post("/api/v1/courses", json={"title": "草稿课"}, headers=th)
        cid = r.json()["data"]["id"]
        s = create_user(db, UserRole.student, _seq=107)
        r = client.post(f"/api/v1/courses/{cid}/enroll", headers=auth_headers(s))
        assert r.status_code == 400

    def test_enroll_missing_course_rejected(self, client, db):
        s = create_user(db, UserRole.student, _seq=108)
        r = client.post("/api/v1/courses/99999/enroll", headers=auth_headers(s))
        assert r.status_code == 400


class TestDrop:
    def test_drop_success_and_count_decrement(self, client, db):
        cid, _ = _make_published_course(client, db, 110)
        s = create_user(db, UserRole.student, _seq=111)
        h = auth_headers(s)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        r = client.delete(f"/api/v1/courses/{cid}/enroll", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "dropped"
        r = client.get(f"/api/v1/courses/{cid}")
        assert r.json()["data"]["student_count"] == 0

    def test_drop_without_enroll_rejected(self, client, db):
        cid, _ = _make_published_course(client, db, 112)
        s = create_user(db, UserRole.student, _seq=113)
        r = client.delete(f"/api/v1/courses/{cid}/enroll", headers=auth_headers(s))
        assert r.status_code == 400

    def test_re_enroll_after_drop_reuses_record(self, client, db):
        """dropped 记录复用：再选课成功且 student_count 恢复为 1（不重复累计）。"""
        cid, _ = _make_published_course(client, db, 114)
        s = create_user(db, UserRole.student, _seq=115)
        h = auth_headers(s)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        client.delete(f"/api/v1/courses/{cid}/enroll", headers=h)
        r = client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "active"
        r = client.get(f"/api/v1/courses/{cid}")
        assert r.json()["data"]["student_count"] == 1


class TestMyCourses:
    def test_list_with_progress(self, client, db):
        cid, _ = _make_published_course(client, db, 120)
        s = create_user(db, UserRole.student, _seq=121)
        h = auth_headers(s)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        r = client.get("/api/v1/my/courses", headers=h)
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["total"] == 1
        item = d["items"][0]
        assert item["course_id"] == cid
        assert item["status"] == "active"
        assert item["progress_percent"] == 0.0

    def test_dropped_excluded(self, client, db):
        cid, _ = _make_published_course(client, db, 122)
        s = create_user(db, UserRole.student, _seq=123)
        h = auth_headers(s)
        client.post(f"/api/v1/courses/{cid}/enroll", headers=h)
        client.delete(f"/api/v1/courses/{cid}/enroll", headers=h)
        r = client.get("/api/v1/my/courses", headers=h)
        assert r.json()["data"]["total"] == 0
