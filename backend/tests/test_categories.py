"""分类 CRUD 测试。"""
from app.models.course import Course
from app.models.user import UserRole
from tests.conftest import auth_headers, create_user


class TestCategoryTree:
    def test_list_empty(self, client):
        r = client.get("/api/v1/categories")
        assert r.status_code == 200
        assert r.json()["data"] == []

    def test_tree_two_level(self, client, db):
        admin = create_user(db, UserRole.admin, _seq=1)
        h = auth_headers(admin)

        r1 = client.post("/api/v1/categories", json={"name": "后端", "parent_id": None, "sort_order": 0}, headers=h)
        assert r1.status_code == 200
        pid = r1.json()["data"]["id"]

        client.post("/api/v1/categories", json={"name": "Python", "parent_id": pid, "sort_order": 0}, headers=h)

        tree = client.get("/api/v1/categories").json()["data"]
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1


class TestCategoryDelete:
    def test_blocked_by_courses(self, client, db):
        admin = create_user(db, UserRole.admin, _seq=2)
        h = auth_headers(admin)

        r = client.post("/api/v1/categories", json={"name": "前端", "parent_id": None, "sort_order": 0}, headers=h)
        cid = r.json()["data"]["id"]

        db.add(Course(title="Vue", teacher_id=admin.id, category_id=cid, status="draft"))
        db.commit()

        resp = client.delete(f"/api/v1/categories/{cid}", headers=h)
        assert resp.status_code == 400
        assert "课程" in resp.json()["message"]

    def test_blocked_by_children(self, client, db):
        admin = create_user(db, UserRole.admin, _seq=3)
        h = auth_headers(admin)

        r = client.post("/api/v1/categories", json={"name": "父", "parent_id": None, "sort_order": 0}, headers=h)
        pid = r.json()["data"]["id"]
        client.post("/api/v1/categories", json={"name": "子", "parent_id": pid, "sort_order": 0}, headers=h)

        resp = client.delete(f"/api/v1/categories/{pid}", headers=h)
        assert resp.status_code == 400
        assert "子分类" in resp.json()["message"]

    def test_delete_leaf_ok(self, client, db):
        admin = create_user(db, UserRole.admin, _seq=4)
        h = auth_headers(admin)

        r = client.post("/api/v1/categories", json={"name": "待删", "parent_id": None, "sort_order": 0}, headers=h)
        resp = client.delete(f"/api/v1/categories/{r.json()['data']['id']}", headers=h)
        assert resp.status_code == 200


class TestCategoryDepth:
    def test_third_level_blocked(self, client, db):
        admin = create_user(db, UserRole.admin, _seq=5)
        h = auth_headers(admin)

        r1 = client.post("/api/v1/categories", json={"name": "L1", "parent_id": None, "sort_order": 0}, headers=h)
        r2 = client.post("/api/v1/categories", json={"name": "L2", "parent_id": r1.json()["data"]["id"], "sort_order": 0}, headers=h)
        r3 = client.post("/api/v1/categories", json={"name": "L3", "parent_id": r2.json()["data"]["id"], "sort_order": 0}, headers=h)
        assert r3.status_code == 400
        assert "二级" in r3.json()["message"]
