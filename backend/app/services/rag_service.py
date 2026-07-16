"""RAG 智能答疑服务：文档解析 → 切块 → 向量化 → 检索 → LLM 生成。

依赖：LangChain 0.1+、ChromaDB 0.5+、OpenAI 兼容接口。
chromadb 客户端版本与容器镜像 chromadb/chroma:0.5.5 对齐。
"""
from typing import AsyncIterator

from app.core.config import settings


# ---------- 知识库构建（BackgroundTasks 触发） ----------


async def build_knowledge_base(course_id: int) -> dict:
    """解析课程课件 → 文本切块 → 向量化 → 存入 ChromaDB。

    课件文件路径从 courseware 表获取，文档类型支持 PDF/PPT/DOC/TXT。
    按课程隔离 ChromaDB collection（名称: course_{course_id}）。
    """
    # TODO: 接入 LangChain Document Loaders
    # - PyPDFLoader / UnstructuredPowerPointLoader / UnstructuredWordDocumentLoader
    # - RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # - OpenAIEmbeddings（或 OllamaEmbeddings）→ Chroma.from_documents()
    # - BackgroundTasks 调用本函数（对齐决策 2）
    #
    # 示例框架:
    # from langchain_community.document_loaders import PyPDFLoader
    # from langchain_text_splitters import RecursiveCharacterTextSplitter
    # from langchain_openai import OpenAIEmbeddings
    # from langchain_chroma import Chroma
    #
    # loader = PyPDFLoader(file_path)
    # docs = loader.load()
    # splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    # chunks = splitter.split_documents(docs)
    # Chroma.from_documents(
    #     chunks,
    #     OpenAIEmbeddings(model=settings.EMBEDDING_MODEL, openai_api_key=settings.LLM_API_KEY),
    #     collection_name=f"course_{course_id}",
    #     persist_directory=settings.CHROMA_PERSIST_DIR,
    # )
    raise NotImplementedError("知识库构建待 LangChain 依赖安装后启用")


# ---------- RAG 检索增强生成 ----------


async def rag_query_stream(course_id: int | None, question: str) -> AsyncIterator[str]:
    """检索 ChromaDB → 拼 prompt → 调用 LLM → SSE 流式 yield。

    流式输出 token 片段，由路由层封装为 SSE text/event-stream。
    """
    # TODO: 接入 LangChain RetrievalQA + 流式
    # from langchain_openai import ChatOpenAI
    # from langchain_chroma import Chroma
    # from langchain_openai import OpenAIEmbeddings
    #
    # embeddings = OpenAIEmbeddings(...)
    # vectorstore = Chroma(
    #     collection_name=f"course_{course_id}" if course_id else "course_all",
    #     embedding_function=embeddings,
    #     persist_directory=settings.CHROMA_PERSIST_DIR,
    # )
    # retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    # llm = ChatOpenAI(
    #     model=settings.LLM_MODEL,
    #     openai_api_key=settings.LLM_API_KEY,
    #     openai_api_base=settings.LLM_API_BASE,
    #     streaming=True,
    # )
    # # 构建 prompt 模板 + RetrievalQA chain
    # # 流式生成 → yield token

    yield "data: 知识库未就绪，请先上传课件并构建知识库。\n\n"
    yield "event: done\ndata: [DONE]\n\n"
    raise NotImplementedError("RAG 流式问答待 LangChain 依赖安装后启用")


# ---------- 工具函数 ----------


def get_llm_config() -> dict:
    """获取 LLM 配置（供 agent_service 复用）。"""
    return {
        "model": settings.LLM_MODEL,
        "api_key": settings.LLM_API_KEY,
        "api_base": settings.LLM_API_BASE,
        "embedding_model": settings.EMBEDDING_MODEL,
    }
