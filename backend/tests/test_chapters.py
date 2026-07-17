"""章节 CRUD + 排序测试。"""
from app.models.user import UserRole
from tests.conftest import auth_headers, create_user


class TestChapterTree:
    def test_tree(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=1)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "C"}, headers=h)
        cid = r.json()["data"]["id"]

        r1 = client.post(f"/api/v1/courses/{cid}/chapters", json={"title": "Ch1", "sort_order": 1}, headers=h)
        assert r1.status_code == 200
        ch1 = r1.json()["data"]["id"]
        client.post(f"/api/v1/courses/{cid}/chapters", json={"title": "1.1", "parent_id": ch1, "sort_order": 0}, headers=h)

        tree = client.get(f"/api/v1/courses/{cid}/chapters").json()["data"]
        assert len(tree) == 1
        assert len(tree[0]["children"]) == 1

    def test_self_parent_blocked(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=2)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "C"}, headers=h)
        cid = r.json()["data"]["id"]
        r = client.post(f"/api/v1/courses/{cid}/chapters", json={"title": "X"}, headers=h)
        ch = r.json()["data"]["id"]
        resp = client.put(f"/api/v1/courses/{cid}/chapters/{ch}", json={"parent_id": ch}, headers=h)
        assert resp.status_code == 400


class TestChapterSort:
    def test_batch_sort(self, client, db):
        t = create_user(db, UserRole.teacher, _seq=3)
        h = auth_headers(t)
        r = client.post("/api/v1/courses", json={"title": "C"}, headers=h)
        cid = r.json()["data"]["id"]

        ids = []
        for i, name in enumerate(["C", "A", "B"]):
            r = client.post(f"/api/v1/courses/{cid}/chapters", json={"title": name, "sort_order": i}, headers=h)
            ids.append(r.json()["data"]["id"])

        resp = client.put(
            f"/api/v1/courses/{cid}/chapters/sort",
            json={"items": [{"id": ids[0], "sort_order": 3}, {"id": ids[1], "sort_order": 1}, {"id": ids[2], "sort_order": 2}]},
            headers=h,
        )
        assert resp.status_code == 200

        tree = client.get(f"/api/v1/courses/{cid}/chapters").json()["data"]
        titles = [ch["title"] for ch in tree]
        assert titles == ["A", "B", "C"]
