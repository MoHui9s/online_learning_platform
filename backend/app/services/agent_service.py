"""AI 学习助手服务：个性化建议 / 举一反三。

依赖：LLM（OpenAI 兼容接口），复用 rag_service.get_llm_config()。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exam import WrongQuestion
from app.models.question import Question, QuestionKnowledgePoint
from app.models.knowledge_point import KnowledgePoint


def generate_suggestions(db: Session, user_id: int) -> dict:
    """基于用户错题/进度数据生成个性化学习建议。

    分析错题分布 → 识别薄弱知识点 → LLM 生成建议文本。
    若 LLM 不可用，降级为基于规则的统计反馈。
    """
    # 查询错题统计
    wrong_list = db.execute(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user_id, WrongQuestion.is_mastered == False
        )
    ).scalars().all()

    if not wrong_list:
        return {
            "summary": "暂无薄弱知识点，继续保持！",
            "weak_points": [],
            "suggestions": ["定期复习已学内容", "尝试完成一次模拟考试巩固知识"],
        }

    # 按知识点聚合错题
    kp_counter: dict[int, int] = {}
    for wq in wrong_list:
        qkps = db.execute(
            select(QuestionKnowledgePoint).where(
                QuestionKnowledgePoint.question_id == wq.question_id
            )
        ).scalars().all()
        for qkp in qkps:
            kp_counter[qkp.knowledge_point_id] = kp_counter.get(qkp.knowledge_point_id, 0) + 1

    # 获取知识点名称
    weak_points = []
    for kp_id, count in sorted(kp_counter.items(), key=lambda x: -x[1])[:5]:
        kp = db.get(KnowledgePoint, kp_id)
        if kp:
            weak_points.append(f"{kp.name}（错{count}次）")

    # TODO: 可接入 LLM 生成更个性化建议
    # llm_config = get_llm_config()
    # prompt = f"用户薄弱知识点: {weak_points}，请生成3条学习建议..."

    suggestions = [
        f"重点复习：{weak_points[0]}" if weak_points else "定期复习已学内容",
        "针对薄弱知识点做专项练习",
        "尝试重新作答错题本中的题目，检验掌握情况",
    ]

    return {
        "summary": f"你共有 {len(wrong_list)} 道未掌握错题，主要薄弱在 {len(kp_counter)} 个知识点",
        "weak_points": weak_points,
        "suggestions": suggestions,
    }


def generate_similar_questions(db: Session, wrong_question_id: int, user_id: int) -> dict | None:
    """基于错题生成变式题（举一反三）。

    获取错题关联的知识点 → 找同知识点其他题目 → 若不够则调用 LLM 生成。
    """
    wq = db.execute(
        select(WrongQuestion).where(
            WrongQuestion.id == wrong_question_id, WrongQuestion.user_id == user_id
        )
    ).scalar_one_or_none()
    if not wq:
        return None

    question = db.get(Question, wq.question_id)
    if not question:
        return None

    # 找同知识点的其他题目
    qkps = db.execute(
        select(QuestionKnowledgePoint).where(
            QuestionKnowledgePoint.question_id == wq.question_id
        )
    ).scalars().all()
    kp_ids = [qkp.knowledge_point_id for qkp in qkps]

    if kp_ids:
        similar_q = db.execute(
            select(Question)
            .join(QuestionKnowledgePoint, QuestionKnowledgePoint.question_id == Question.id)
            .where(
                QuestionKnowledgePoint.knowledge_point_id.in_(kp_ids),
                Question.id != wq.question_id,
            )
            .limit(3)
        ).scalars().all()
    else:
        similar_q = []

    if similar_q:
        q = similar_q[0]
        kp_name = None
        if kp_ids:
            kp = db.get(KnowledgePoint, kp_ids[0])
            kp_name = kp.name if kp else None

        return {
            "stem": q.stem,
            "options": q.options,
            "answer": q.answer,
            "analysis": q.analysis,
            "based_on_knowledge_point": kp_name,
        }

    # TODO: 题库无相似题时，调用 LLM 生成变式题
    # llm_config = get_llm_config()
    # prompt = f"原题：{question.stem}，知识点：{kp_name}，请生成一道变式题..."

    return {
        "stem": f"【变式】{question.stem}",
        "options": question.options,
        "answer": question.answer,
        "analysis": "当前题库暂无双类题，此为原题回顾。建议练习错题本中同知识点其他题目。",
        "based_on_knowledge_point": None,
    }
