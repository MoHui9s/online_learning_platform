"""M13 RAG spike：单份 PDF 手工跑通 解析 → 切片 → 向量化 → ChromaDB 检索 → LLM 生成。

用法（backend/ 下）:
    python scripts/rag_spike.py <PDF路径> [提问内容]

验证目标（对应施工手册 Day2 BE-C 任务）：
1. pypdf 能解析中文 PDF；
2. RecursiveCharacterTextSplitter 切片（chunk_size=500, overlap=50）；
3. Embedding 接口（.env LLM_API_BASE/LLM_API_KEY/EMBEDDING_MODEL）可用；
4. ChromaDB（docker 宿主端口 8001）可写入/检索，按课程隔离 collection；
5. LLM（.env LLM_MODEL）能基于检索上下文回答并流式输出。

仅为 spike 脚本，不属于正式模块；结论沉淀到 rag_service.py 正式实现。
"""
import sys
import time

# 确保能 import app 包（脚本在 backend/scripts/ 下）
sys.path.insert(0, ".")

from app.core.config import settings  # noqa: E402

COLLECTION = "spike_course_0"  # 模拟按课程隔离：course_{id}


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/rag_spike.py <PDF路径> [提问内容]")
        sys.exit(1)
    pdf_path = sys.argv[1]
    question = sys.argv[2] if len(sys.argv) > 2 else "请概括这份文档的主要内容"

    # ---------- 1. 解析 ----------
    t0 = time.time()
    from langchain_community.document_loaders import PyPDFLoader

    docs = PyPDFLoader(pdf_path).load()
    total_chars = sum(len(d.page_content) for d in docs)
    print(f"[1/5] 解析 OK: {len(docs)} 页, {total_chars} 字符, {time.time()-t0:.1f}s")

    # ---------- 2. 切片 ----------
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    print(f"[2/5] 切片 OK: {len(chunks)} 块 (chunk_size=500, overlap=50)")

    # ---------- 3. 向量化 + 入 ChromaDB ----------
    t0 = time.time()
    from langchain_openai import OpenAIEmbeddings
    import chromadb

    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        check_embedding_ctx_length=False,  # 兼容非 OpenAI 官方后端
    )
    # 注意：客户端与容器统一钉 chromadb==0.5.3（0.5.4/0.5.5 被 langchain-chroma
    # 显式拉黑，全家改钉 0.5.3，见 requirements.txt）。正式实现可经 langchain-chroma
    # 0.1.3 桥接；spike 里用 chromadb 原生客户端直连以缩短链路。
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    # spike 可重复执行：先清旧 collection
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
    texts = [c.page_content for c in chunks]
    vectors = embeddings.embed_documents(texts)
    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=vectors,
        documents=texts,
        metadatas=[{"page": c.metadata.get("page", -1)} for c in chunks],
    )
    print(f"[3/5] 向量化+入库 OK: collection={COLLECTION}, dim={len(vectors[0])}, {time.time()-t0:.1f}s")

    # ---------- 4. 检索 ----------
    t0 = time.time()
    q_vec = embeddings.embed_query(question)
    res = collection.query(query_embeddings=[q_vec], n_results=3)
    hit_docs = res["documents"][0]
    hit_metas = res["metadatas"][0]
    hit_dists = res["distances"][0]
    print(f"[4/5] 检索 OK: top{len(hit_docs)}, {time.time()-t0:.1f}s")
    for i, (text, meta, dist) in enumerate(zip(hit_docs, hit_metas, hit_dists), 1):
        print(f"  #{i} distance={dist:.4f} page={meta.get('page')}: {text[:60]!r}...")

    # ---------- 5. LLM 流式生成 ----------
    t0 = time.time()
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_API_BASE,
        temperature=0.3,
        streaming=True,
    )
    context = "\n\n".join(hit_docs)
    prompt = (
        "你是课程答疑助手。仅根据下面的课程资料回答问题，"
        "资料中没有的内容请回答不知道。\n\n"
        f"【课程资料】\n{context}\n\n【问题】{question}"
    )
    print(f"[5/5] LLM 流式回答（model={settings.LLM_MODEL}）:")
    n_tokens = 0
    for chunk in llm.stream(prompt):
        text = chunk.content or ""
        n_tokens += 1
        print(text, end="", flush=True)
    print(f"\n\n=== SPIKE 全链路通过: {n_tokens} 个流式片段, LLM 耗时 {time.time()-t0:.1f}s ===")


if __name__ == "__main__":
    main()
