"""验证 18 张表的字段与索引（原始 SQL，无 ORM）。"""
import pymysql
from app.core.config import settings

TABLES = [
    "users", "categories", "courses", "chapters", "courseware", "enrollments",
    "learning_records", "notes", "favorites", "learning_calendar", "knowledge_points",
    "questions", "question_knowledge_points", "exams", "exam_questions", "exam_records",
    "wrong_questions", "qa_history",
]

conn = pymysql.connect(
    host=settings.DB_HOST, port=settings.DB_PORT, user=settings.DB_USER,
    password=settings.DB_PASSWORD, database=settings.DB_NAME, charset="utf8mb4",
)
cur = conn.cursor()
cur.execute("SHOW TABLES")
present = {r[0] for r in cur.fetchall()}
print(f"present tables: {len(present)}")

for t in TABLES:
    cur.execute("DESCRIBE `%s`" % t)
    cols = [(r[0], r[1], r[2]) for r in cur.fetchall()]
    cur.execute("SHOW INDEX FROM `%s`" % t)
    idxs = [(r[2], r[4], r[1]) for r in cur.fetchall()]  # name, col, non_unique
    print(f"\n=== {t}: {len(cols)} cols, {len(idxs)} idx ===")
    for c in cols:
        print(f"   {c[0]:24} {c[1]:20} {'NULL' if c[2]=='YES' else 'NOT NULL'}")
    print("   -- indexes:")
    for name, col, nu in idxs:
        print(f"      {name:32} {col:24} {'UNIQUE' if nu==0 else ''}")

conn.close()
