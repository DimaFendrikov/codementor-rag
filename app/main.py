from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import REPOS_DIR
from app.schemas import (
    AskRequest,
    AskResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    RepoIndexRequest,
    RepoIndexResponse,
    RepositoryListResponse,
    SearchRequest,
    SearchResponse,
    SetActiveRepositoryRequest,
)
from app.services.chunk_registry import save_repository_chunks
from app.services.chunker import chunk_repository_files
from app.services.embeddings import EmbeddingService
from app.services.file_reader import read_repository_files
from app.services.github_loader import clone_or_update_repository
from app.services.llm import LLMService
from app.services.quiz_generator import QuizGeneratorService
from app.services.repository_registry import (
    get_active_repo_id,
    list_repositories,
    register_repository,
    resolve_repo_id,
    set_active_repo_id,
)
from app.services.retrieval import RetrievalService
from app.services.vector_store import VectorStore

app = FastAPI(
    title="CodeMentor RAG",
    description="An AI assistant for understanding GitHub repositories with RAG.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

embedding_service = EmbeddingService()
vector_store = VectorStore()
retrieval_service = RetrievalService(vector_store)
llm_service = LLMService()
quiz_generator_service = QuizGeneratorService()


@app.get("/")
def root():
    return {"message": "CodeMentor RAG is running", "app_url": "/app"}


@app.get("/app")
def frontend_app():
    return FileResponse("app/static/index.html")


@app.get("/repositories", response_model=RepositoryListResponse)
def get_repositories():
    return RepositoryListResponse(
        repositories=list_repositories(),
        active_repo_id=get_active_repo_id(),
    )


@app.post("/repositories/active")
def set_active_repository(request: SetActiveRepositoryRequest):
    try:
        set_active_repo_id(request.repo_id)
        return {
            "status": "success",
            "message": "Active repository updated",
            "active_repo_id": request.repo_id,
        }
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error))


@app.post("/repositories/index", response_model=RepoIndexResponse)
def index_repository(request: RepoIndexRequest):
    try:
        repo_info = clone_or_update_repository(
            repo_url=request.repo_url,
            target_dir=REPOS_DIR,
        )
        repo_id = repo_info["repo_id"]
        repo_path = repo_info["repo_path"]

        files_data = read_repository_files(repo_path)
        chunks = chunk_repository_files(files_data)
        save_repository_chunks(repo_id=repo_id, chunks=chunks)
        register_repository(repo_info)

        if not chunks:
            return RepoIndexResponse(
                status="warning",
                message="Repository was loaded, but no readable chunks were created.",
                repo_id=repo_id,
                repo_name=repo_info["repo_name"],
                repo_path=str(repo_path),
                action=repo_info["action"],
                files_processed=len(files_data),
                chunks_created=0,
            )

        embeddings = embedding_service.embed_texts([chunk["content"] for chunk in chunks])

        vector_store.clear_repository(repo_id)
        vector_store.add_chunks(repo_id=repo_id, chunks=chunks, embeddings=embeddings)

        return RepoIndexResponse(
            status="success",
            message="Repository indexed successfully.",
            repo_id=repo_id,
            repo_name=repo_info["repo_name"],
            repo_path=str(repo_path),
            action=repo_info["action"],
            files_processed=len(files_data),
            chunks_created=len(chunks),
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/search", response_model=SearchResponse)
def search_repository(request: SearchRequest):
    try:
        repo_id = resolve_repo_id(request.repo_id)
        query_embedding = embedding_service.embed_query(request.question)
        results = retrieval_service.retrieve(
            repo_id=repo_id,
            query=request.question,
            query_embedding=query_embedding,
            semantic_top_k=request.top_k,
        )
        return SearchResponse(repo_id=repo_id, question=request.question, results=results)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/ask", response_model=AskResponse)
def ask_repository(request: AskRequest):
    try:
        repo_id = resolve_repo_id(request.repo_id)
        query_embedding = embedding_service.embed_query(request.question)
        context_chunks = retrieval_service.retrieve(
            repo_id=repo_id,
            query=request.question,
            query_embedding=query_embedding,
            semantic_top_k=request.top_k,
        )
        answer = llm_service.generate_answer(
            question=request.question,
            context_chunks=context_chunks,
            include_check_question=request.include_check_question,
        )
        sources = sorted({chunk["file_path"] for chunk in context_chunks})

        return AskResponse(
            repo_id=repo_id,
            question=request.question,
            answer=answer,
            sources=sources,
            context_chunks=context_chunks,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/quiz/generate", response_model=QuizGenerateResponse)
def generate_quiz(request: QuizGenerateRequest):
    try:
        repo_id = resolve_repo_id(request.repo_id)
        retrieval_query = f"Quiz about {request.topic}: key concepts, files, implementation, usage, and structure."
        query_embedding = embedding_service.embed_query(retrieval_query)
        context_chunks = retrieval_service.retrieve(
            repo_id=repo_id,
            query=retrieval_query,
            query_embedding=query_embedding,
            semantic_top_k=request.top_k,
        )
        questions = quiz_generator_service.generate_quiz(
            topic=request.topic,
            difficulty=request.difficulty,
            num_questions=request.num_questions,
            context_chunks=context_chunks,
        )
        sources = sorted({chunk["file_path"] for chunk in context_chunks})

        return QuizGenerateResponse(
            repo_id=repo_id,
            topic=request.topic,
            difficulty=request.difficulty,
            questions=questions,
            sources=sources,
            context_chunks=context_chunks,
        )
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))
