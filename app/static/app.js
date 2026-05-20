const repoUrlInput = document.getElementById("repoUrl");
const indexRepoBtn = document.getElementById("indexRepoBtn");
const indexStatus = document.getElementById("indexStatus");
const repoSelect = document.getElementById("repoSelect");
const refreshReposBtn = document.getElementById("refreshReposBtn");
const activeRepoInfo = document.getElementById("activeRepoInfo");
const topKInput = document.getElementById("topK");
const includeCheckQuestionInput = document.getElementById("includeCheckQuestion");
const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const answerArea = document.getElementById("answerArea");
const quizTopicInput = document.getElementById("quizTopic");
const quizDifficultyInput = document.getElementById("quizDifficulty");
const quizNumQuestionsInput = document.getElementById("quizNumQuestions");
const generateQuizBtn = document.getElementById("generateQuizBtn");
const quizArea = document.getElementById("quizArea");

function escapeHtml(text) {
    return String(text)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function setStatus(element, message, type = "loading") {
    element.classList.remove("hidden", "error", "success", "loading");
    element.classList.add(type);
    element.innerHTML = message;
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, {
        headers: {"Content-Type": "application/json", ...(options.headers || {})},
        ...options,
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail));
    }

    return data;
}

function getSelectedRepoId() {
    return repoSelect.value || null;
}

function getTopK() {
    const value = Number(topKInput.value);
    return Number.isFinite(value) && value > 0 ? value : 5;
}

async function loadRepositories() {
    const data = await apiRequest("/repositories");
    repoSelect.innerHTML = "";

    if (!data.repositories.length) {
        repoSelect.innerHTML = '<option value="">No repositories yet</option>';
        activeRepoInfo.textContent = "Index a GitHub repository first.";
        return;
    }

    for (const repo of data.repositories) {
        const option = document.createElement("option");
        option.value = repo.repo_id;
        option.textContent = `${repo.repo_name} (${repo.repo_id})`;
        option.selected = repo.repo_id === data.active_repo_id;
        repoSelect.appendChild(option);
    }

    activeRepoInfo.textContent = data.active_repo_id
        ? `Active repository: ${data.active_repo_id}`
        : "No active repository selected.";
}

async function setActiveRepository(repoId) {
    if (!repoId) return;

    await apiRequest("/repositories/active", {
        method: "POST",
        body: JSON.stringify({repo_id: repoId}),
    });
    activeRepoInfo.textContent = `Active repository: ${repoId}`;
}

async function indexRepository() {
    const repoUrl = repoUrlInput.value.trim();

    if (!repoUrl) {
        setStatus(indexStatus, "Please paste a GitHub repository URL.", "error");
        return;
    }

    indexRepoBtn.disabled = true;
    setStatus(indexStatus, "Indexing repository. This can take a moment...", "loading");

    try {
        const data = await apiRequest("/repositories/index", {
            method: "POST",
            body: JSON.stringify({repo_url: repoUrl}),
        });
        setStatus(
            indexStatus,
            `<strong>${escapeHtml(data.message)}</strong><br>` +
            `Repo ID: ${escapeHtml(data.repo_id)}<br>` +
            `Action: ${escapeHtml(data.action)}<br>` +
            `Files: ${data.files_processed}<br>` +
            `Chunks: ${data.chunks_created}`,
            data.status === "success" ? "success" : "loading"
        );
        await loadRepositories();
    } catch (error) {
        setStatus(indexStatus, `Indexing error: ${escapeHtml(error.message)}`, "error");
    } finally {
        indexRepoBtn.disabled = false;
    }
}

function renderSources(sources) {
    if (!sources?.length) return "<p>No sources found.</p>";

    return `<div class="sources">${sources.map(source => `<span class="source-pill">${escapeHtml(source)}</span>`).join("")}</div>`;
}

function renderContextChunks(chunks) {
    if (!chunks?.length) return "<p>No context chunks found.</p>";

    return `
        <details class="context-list">
            <summary>Show retrieved chunks (${chunks.length})</summary>
            ${chunks.map(chunk => `
                <div class="context-item">
                    <div class="context-meta">
                        <strong>${escapeHtml(chunk.file_path)}</strong>
                        · chunk ${chunk.chunk_index}
                        · ${escapeHtml(chunk.chunk_type)}
                        ${chunk.symbol_name ? `· ${escapeHtml(chunk.symbol_name)}` : ""}
                        · distance: ${Number(chunk.distance).toFixed(4)}
                    </div>
                    <div class="context-content">${escapeHtml(chunk.content)}</div>
                </div>
            `).join("")}
        </details>`;
}

async function askRepository() {
    const question = questionInput.value.trim();
    const repoId = getSelectedRepoId();

    if (!question) {
        answerArea.classList.remove("hidden");
        answerArea.innerHTML = '<div class="answer-box error">Write a question first.</div>';
        return;
    }
    if (!repoId) {
        answerArea.classList.remove("hidden");
        answerArea.innerHTML = '<div class="answer-box error">Select or index a repository first.</div>';
        return;
    }

    askBtn.disabled = true;
    answerArea.classList.remove("hidden");
    answerArea.innerHTML = '<div class="answer-box loading">Preparing an answer...</div>';

    try {
        const data = await apiRequest("/ask", {
            method: "POST",
            body: JSON.stringify({
                repo_id: repoId,
                question,
                top_k: getTopK(),
                include_check_question: includeCheckQuestionInput.checked,
            }),
        });
        answerArea.innerHTML = `
            <h3>Answer</h3>
            <div class="answer-box">${escapeHtml(data.answer)}</div>
            <h3>Sources</h3>
            ${renderSources(data.sources)}
            ${renderContextChunks(data.context_chunks)}
        `;
    } catch (error) {
        answerArea.innerHTML = `<div class="answer-box error">Answer error: ${escapeHtml(error.message)}</div>`;
    } finally {
        askBtn.disabled = false;
    }
}

function renderQuizQuestions(questions) {
    if (!questions?.length) return "<p>No questions were generated.</p>";

    window.currentQuizQuestions = questions;

    return questions.map((item, questionIndex) => `
        <div class="quiz-question">
            <h4>${questionIndex + 1}. ${escapeHtml(item.question)}</h4>
            <div class="quiz-options">
                ${item.options.map(option => `
                    <label class="quiz-option">
                        <input type="radio" name="quiz-question-${questionIndex}" value="${escapeHtml(option)}">
                        <span>${escapeHtml(option)}</span>
                    </label>
                `).join("")}
            </div>
            <button class="secondary-btn check-answer-btn" type="button" onclick="checkQuizAnswer(${questionIndex})">Check answer</button>
            <div id="quizFeedback-${questionIndex}" class="quiz-feedback hidden"></div>
        </div>
    `).join("");
}

function checkQuizAnswer(questionIndex) {
    const question = window.currentQuizQuestions?.[questionIndex];
    const selectedInput = document.querySelector(`input[name="quiz-question-${questionIndex}"]:checked`);
    const feedback = document.getElementById(`quizFeedback-${questionIndex}`);

    if (!question || !feedback) return;

    feedback.classList.remove("hidden", "success", "error");

    if (!selectedInput) {
        feedback.classList.add("error");
        feedback.innerHTML = "Please choose an answer first.";
        return;
    }

    const isCorrect = selectedInput.value === question.correct_answer;
    feedback.classList.add(isCorrect ? "success" : "error");
    feedback.innerHTML = `
        <strong>${isCorrect ? "Correct." : "Incorrect."}</strong><br>
        Correct answer: ${escapeHtml(question.correct_answer)}<br>
        Explanation: ${escapeHtml(question.explanation)}
    `;
}

async function generateQuiz() {
    const repoId = getSelectedRepoId();
    const topic = quizTopicInput.value.trim();

    if (!topic) {
        quizArea.classList.remove("hidden");
        quizArea.innerHTML = '<div class="answer-box error">Enter a quiz topic.</div>';
        return;
    }
    if (!repoId) {
        quizArea.classList.remove("hidden");
        quizArea.innerHTML = '<div class="answer-box error">Select or index a repository first.</div>';
        return;
    }

    generateQuizBtn.disabled = true;
    quizArea.classList.remove("hidden");
    quizArea.innerHTML = '<div class="answer-box loading">Generating quiz...</div>';

    try {
        const data = await apiRequest("/quiz/generate", {
            method: "POST",
            body: JSON.stringify({
                repo_id: repoId,
                topic,
                difficulty: quizDifficultyInput.value,
                num_questions: Number(quizNumQuestionsInput.value),
                top_k: getTopK(),
            }),
        });
        quizArea.innerHTML = `
            <h3>Quiz: ${escapeHtml(data.topic)}</h3>
            <p>Difficulty: <strong>${escapeHtml(data.difficulty)}</strong></p>
            ${renderQuizQuestions(data.questions)}
            <h3>Sources</h3>
            ${renderSources(data.sources)}
            ${renderContextChunks(data.context_chunks)}
        `;
    } catch (error) {
        quizArea.innerHTML = `<div class="answer-box error">Quiz generation error: ${escapeHtml(error.message)}</div>`;
    } finally {
        generateQuizBtn.disabled = false;
    }
}

function setupTabs() {
    document.querySelectorAll(".tab-btn").forEach(button => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(item => item.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(item => item.classList.remove("active"));
            button.classList.add("active");
            document.getElementById(button.dataset.tab).classList.add("active");
        });
    });
}

indexRepoBtn.addEventListener("click", indexRepository);
refreshReposBtn.addEventListener("click", loadRepositories);
repoSelect.addEventListener("change", () => setActiveRepository(repoSelect.value));
askBtn.addEventListener("click", askRepository);
generateQuizBtn.addEventListener("click", generateQuiz);

setupTabs();
loadRepositories().catch(error => {
    activeRepoInfo.textContent = `Repository loading error: ${error.message}`;
});
