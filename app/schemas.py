from pydantic import BaseModel, Field


class RepoIndexRequest(BaseModel):
    repo_url: str


class RepoIndexResponse(BaseModel):
    status: str
    message: str
    repo_id: str
    repo_name: str
    repo_path: str
    action: str
    files_processed: int
    chunks_created: int


class RepositoryInfo(BaseModel):
    repo_id: str
    repo_name: str
    repo_url: str
    repo_path: str


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryInfo]
    active_repo_id: str | None


class SetActiveRepositoryRequest(BaseModel):
    repo_id: str


class SearchRequest(BaseModel):
    question: str
    repo_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=15)


class SearchResult(BaseModel):
    repo_id: str
    file_path: str
    chunk_index: int
    chunk_type: str
    symbol_name: str
    content: str
    distance: float


class SearchResponse(BaseModel):
    repo_id: str
    question: str
    results: list[SearchResult]


class AskRequest(BaseModel):
    question: str
    repo_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=15)
    include_check_question: bool = False


class AskResponse(BaseModel):
    repo_id: str
    question: str
    answer: str
    sources: list[str]
    context_chunks: list[SearchResult]


class QuizGenerateRequest(BaseModel):
    topic: str
    repo_id: str | None = None
    num_questions: int = Field(default=5, ge=1, le=10)
    difficulty: str = "medium"
    top_k: int = Field(default=8, ge=1, le=15)


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str
    explanation: str


class QuizGenerateResponse(BaseModel):
    repo_id: str
    topic: str
    difficulty: str
    questions: list[QuizQuestion]
    sources: list[str]
    context_chunks: list[SearchResult]
