"""课程 CRUD + 状态流转测试。"""
from app.models.user import UserRole
from tests.conftest import auth_headers, create_user


class TestCourseCRUD:
    def test_create(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=1)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "Python 入门"}, headers=h)
        assert r.status_code == 200
        d = r.json()["data"]
        assert d["teacher_id"] == t.id
        assert d["status"] == "draft"

    def test_pagination(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=2)
        h = auth_headers(t)
        for i in range(5):
            client.post("/api/v1/courses", json={"title": f"C{i}"}, headers=h)
        r = client.get("/api/v1/courses?page=1&page_size=3")
        d = r.json()["data"]
        assert len(d["items"]) == 3
        assert d["total"] == 5

    def test_keyword_search(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=3)
        h = auth_headers(t)
        client.post("/api/v1/courses", json={"title": "Java"}, headers=h)
        client.post("/api/v1/courses", json={"title": "Python"}, headers=h)
        r = client.get("/api/v1/courses?keyword=Python")
        items = r.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["title"] == "Python"


class TestCourseOwnership:
    def test_teacher_blocked(self, client, db):
        ta = create_user(db, UserRole.teacher, _seq=10, username="a")
        tb = create_user(db, UserRole.teacher, _seq=11, username="b")
        r = client.post("/api/v1/courses", json={"title": "A"}, headers=auth_headers(ta))
        cid = r.json()["data"]["id"]
        resp = client.put(f"/api/v1/courses/{cid}", json={"title": "B"}, headers=auth_headers(tb))
        assert resp.status_code == 403

    def test_admin_allowed(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=12)
        a = create_user(db, UserRole.admin, _seq=13)
        r = client.post("/api/v1/courses", json={"title": "T"}, headers=auth_headers(t))
        cid = r.json()["data"]["id"]
        resp = client.put(f"/api/v1/courses/{cid}", json={"title": "Admin"}, headers=auth_headers(a))
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Admin"


class TestStatusTransition:
    def test_valid(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=20)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "S"}, headers=h)
        cid = r.json()["data"]["id"]

        r = client.put(f"/api/v1/courses/{cid}/status", json={"status": "published"}, headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "published"

        r = client.put(f"/api/v1/courses/{cid}/status", json={"status": "offline"}, headers=h)
        assert r.status_code == 200

    def test_invalid(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=21)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "S2"}, headers=h)
        cid = r.json()["data"]["id"]

        r = client.put(f"/api/v1/courses/{cid}/status", json={"status": "offline"}, headers=h)
        assert r.status_code == 400
        assert "不允许" in r.json()["message"]
