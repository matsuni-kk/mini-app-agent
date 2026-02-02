/**
 * RAG Chatbot - Main Application
 * フェーズ1: 検索モード（ファイル検索・選択）
 * フェーズ2: RAGモード（選択ファイルについて対話）
 * 左側: PDFフルビューア、右側: チャットボット
 */

'use strict';

// ==========================================================================
// Configuration
// ==========================================================================
const API = {
    search: '/api/search',
    load: '/api/load',
    chat: '/api/chat',
    pdf: '/api/pdf'
};

const MAX_SELECTED_FILES = 10;

// ==========================================================================
// DOM Elements
// ==========================================================================
const elements = {
    headerInfo: null,
    pdfPanel: null,
    chatPanel: null,
    pdfViewer: null,
    chatArea: null,
    messageInput: null,
    sendBtn: null,
    userMessageTemplate: null,
    botMessageTemplate: null,
    loadingTemplate: null,
    // Page navigation
    prevPageBtn: null,
    nextPageBtn: null,
    pageInfo: null,
    currentFileName: null,
    closePanelBtn: null
};

// ==========================================================================
// State
// ==========================================================================
const state = {
    phase: 'search', // 'search' or 'rag'
    loadedFiles: [], // 読み込まれたファイル一覧（ページ送り用）
    currentPageIndex: 0, // 現在表示中のページインデックス
    isLoading: false,
    isPdfPanelOpen: false // PDFパネルの開閉状態
};

// ==========================================================================
// Initialization
// ==========================================================================
function init() {
    cacheElements();
    bindEvents();
    updatePhaseUI();
}

function cacheElements() {
    elements.headerInfo = document.getElementById('headerInfo');
    elements.pdfPanel = document.getElementById('pdfPanel');
    elements.chatPanel = document.getElementById('chatPanel');
    elements.pdfViewer = document.getElementById('pdfViewer');
    elements.chatArea = document.getElementById('chatArea');
    elements.messageInput = document.getElementById('messageInput');
    elements.sendBtn = document.getElementById('sendBtn');
    elements.userMessageTemplate = document.getElementById('userMessageTemplate');
    elements.botMessageTemplate = document.getElementById('botMessageTemplate');
    elements.loadingTemplate = document.getElementById('loadingTemplate');
    // Page navigation elements
    elements.prevPageBtn = document.getElementById('prevPageBtn');
    elements.nextPageBtn = document.getElementById('nextPageBtn');
    elements.pageInfo = document.getElementById('pageInfo');
    elements.currentFileName = document.getElementById('currentFileName');
    elements.closePanelBtn = document.getElementById('closePanelBtn');
}

function bindEvents() {
    elements.sendBtn.addEventListener('click', handleSend);
    elements.messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // カテゴリボタンのイベント
    bindCategoryButtons();

    // ページナビゲーションのイベント
    elements.prevPageBtn.addEventListener('click', () => navigatePage(-1));
    elements.nextPageBtn.addEventListener('click', () => navigatePage(1));
    elements.closePanelBtn.addEventListener('click', closePdfPanel);
}

function bindCategoryButtons() {
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const category = btn.dataset.category;
            if (category && !state.isLoading) {
                handleCategorySearch(category);
            }
        });
    });
}

async function handleCategorySearch(category) {
    addUserMessage(category);
    showLoading(true);
    state.isLoading = true;
    updateSendButton();

    try {
        await handleSearchChat(category);
    } catch (error) {
        console.error('Error:', error);
        addBotMessage(`エラー: ${error.message}`);
    } finally {
        showLoading(false);
        state.isLoading = false;
        updateSendButton();
    }
}

// ==========================================================================
// Phase Management
// ==========================================================================
function updatePhaseUI() {
    const statusEl = elements.headerInfo.querySelector('.header__status');
    const phaseEl = elements.headerInfo.querySelector('.header__phase');

    if (state.loadedFiles.length > 0) {
        state.phase = 'rag';
        if (statusEl) statusEl.textContent = `${state.loadedFiles.length}件読み込み中`;
        if (phaseEl) {
            phaseEl.textContent = 'RAGモード';
            phaseEl.className = 'header__phase header__phase--rag';
        }
        elements.messageInput.placeholder = '質問を入力...（例: この事例の概要は？）';
    } else {
        state.phase = 'search';
        if (statusEl) statusEl.textContent = '';
        if (phaseEl) {
            phaseEl.textContent = '検索モード';
            phaseEl.className = 'header__phase header__phase--search';
        }
        elements.messageInput.placeholder = 'キーワードで検索...（例: AI推進、製造業）';
    }
}

// ==========================================================================
// PDF Panel Control
// ==========================================================================
function openPdfPanel() {
    state.isPdfPanelOpen = true;
    elements.pdfPanel.classList.remove('pdf-panel--hidden');
    elements.chatPanel.classList.remove('chat-panel--full');
    updatePageNavigation();
}

function closePdfPanel() {
    state.isPdfPanelOpen = false;
    elements.pdfPanel.classList.add('pdf-panel--hidden');
    elements.chatPanel.classList.add('chat-panel--full');
}

function navigatePage(direction) {
    const newIndex = state.currentPageIndex + direction;
    if (newIndex >= 0 && newIndex < state.loadedFiles.length) {
        state.currentPageIndex = newIndex;
        renderCurrentPDF();
        updatePageNavigation();
    }
}

function updatePageNavigation() {
    const total = state.loadedFiles.length;
    const current = state.currentPageIndex + 1;

    elements.pageInfo.textContent = `${current} / ${total}`;
    elements.prevPageBtn.disabled = state.currentPageIndex === 0;
    elements.nextPageBtn.disabled = state.currentPageIndex >= total - 1;

    if (state.loadedFiles.length > 0) {
        const currentFile = state.loadedFiles[state.currentPageIndex];
        elements.currentFileName.textContent = currentFile.displayName || currentFile.name;
    } else {
        elements.currentFileName.textContent = '';
    }
}

function renderCurrentPDF() {
    if (state.loadedFiles.length === 0 || state.currentPageIndex < 0) {
        return;
    }

    let iframe = elements.pdfViewer.querySelector('.pdf-panel__iframe');
    if (!iframe) {
        iframe = document.createElement('iframe');
        iframe.className = 'pdf-panel__iframe';
        elements.pdfViewer.appendChild(iframe);
    }

    const file = state.loadedFiles[state.currentPageIndex];
    // PDF名を取得（md_nameからpdf名に変換）
    const pdfName = file.name.replace('.md', '.pdf');
    iframe.src = `${API.pdf}/${encodeURIComponent(pdfName)}`;
}

// ==========================================================================
// Message Handling
// ==========================================================================
async function handleSend() {
    const message = elements.messageInput.value.trim();

    if (!message || state.isLoading) {
        return;
    }

    addUserMessage(message);
    elements.messageInput.value = '';
    showLoading(true);
    state.isLoading = true;
    updateSendButton();

    try {
        if (state.phase === 'rag' && !isSearchQuery(message)) {
            // RAGモード: 開いているドキュメントに対して質問
            await handleRAGChat(message);
        } else {
            // 検索モード: ファイル検索
            await handleSearchChat(message);
        }

    } catch (error) {
        console.error('Error:', error);
        addBotMessage(`エラー: ${error.message}`);
    } finally {
        showLoading(false);
        state.isLoading = false;
        updateSendButton();
    }
}

function isSearchQuery(message) {
    // 検索意図を示すキーワード
    const searchKeywords = ['検索', '探して', '探す', '見つけて', '資料', '事例を', 'に関する資料', 'の事例'];
    const lowerMessage = message.toLowerCase();

    for (const keyword of searchKeywords) {
        if (lowerMessage.includes(keyword)) {
            return true;
        }
    }

    return false;
}

// ==========================================================================
// Search Phase
// ==========================================================================
async function handleSearchChat(keyword) {
    const response = await fetch(API.search, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ keyword })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '検索に失敗しました');
    }

    const data = await response.json();
    const files = data.files || [];

    if (files.length === 0) {
        addBotMessage(`「${keyword}」に該当するファイルが見つかりませんでした。\n\n別のキーワードで試してください。\n例: AI推進、データ整形、物流、不動産`);
        return;
    }

    // 検索結果を全て一括読み込み
    await loadAllSearchResults(keyword, files);
}

async function loadAllSearchResults(keyword, files) {
    showLoading(true);
    state.isLoading = true;

    try {
        // 全ファイルを一括読み込み
        const fileNames = files.slice(0, MAX_SELECTED_FILES).map(f => f.name);

        const response = await fetch(API.load, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ files: fileNames })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || '読み込みに失敗しました');
        }

        const data = await response.json();
        const loadedFiles = data.files || [];

        if (loadedFiles.length === 0) {
            throw new Error('ファイルの読み込みに失敗しました');
        }

        // 状態を更新
        state.loadedFiles = loadedFiles;
        state.currentPageIndex = 0;

        // PDFパネルを開く
        openPdfPanel();
        renderCurrentPDF();

        updatePhaseUI();

        // 読み込み完了メッセージ
        addBotMessage(`📄 「${keyword}」で ${loadedFiles.length}件 読み込みました。\n\n左側でページ送り（◀▶）ができます。\n全${loadedFiles.length}件がRAG対象です。質問してください。\n\n例: 「この事例の概要は？」「課題と成果を教えて」「共通点は何？」`);

    } catch (error) {
        console.error('Load error:', error);
        addBotMessage(`エラー: ${error.message}`);
    } finally {
        showLoading(false);
        state.isLoading = false;
        updateSendButton();
    }
}

// ==========================================================================
// RAG Phase
// ==========================================================================
async function handleRAGChat(message) {
    const response = await fetch(API.chat, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || '回答の生成に失敗しました');
    }

    const data = await response.json();
    addBotMessageWithSources(data.response, data.sources || []);
}

function addBotMessageWithSources(text, sources) {
    const template = elements.botMessageTemplate.content.cloneNode(true);
    const messageEl = template.querySelector('.message');
    const contentEl = messageEl.querySelector('.message__content');
    const actionsEl = messageEl.querySelector('.message__actions');

    contentEl.textContent = text;

    // 参照ソースをボタンとして追加
    if (sources && sources.length > 0) {
        const sourcesLabel = document.createElement('span');
        sourcesLabel.className = 'sources-label';
        sourcesLabel.textContent = '📎 参照: ';
        actionsEl.appendChild(sourcesLabel);

        sources.forEach(source => {
            const btn = document.createElement('button');
            btn.className = 'file-btn file-btn--source';
            btn.type = 'button';
            btn.textContent = source.displayName || source.name;

            btn.addEventListener('click', () => {
                // 該当ファイルのページへ移動
                switchToFile(source.name);
            });

            actionsEl.appendChild(btn);
        });
    }

    elements.chatArea.appendChild(messageEl);
    scrollToBottom();
}

// ==========================================================================
// PDF Viewer (Page Navigation)
// ==========================================================================
function switchToFile(fileName) {
    // loadedFiles内でファイルを探す
    const index = state.loadedFiles.findIndex(f => {
        return f.name === fileName ||
               f.md_name === fileName ||
               f.name.replace('.md', '.pdf') === fileName;
    });

    if (index !== -1) {
        state.currentPageIndex = index;
        renderCurrentPDF();
        updatePageNavigation();

        // PDFパネルが閉じていたら開く
        if (!state.isPdfPanelOpen) {
            openPdfPanel();
        }
    }
}

// ==========================================================================
// UI Functions
// ==========================================================================
function updateSendButton() {
    elements.sendBtn.disabled = state.isLoading;
    elements.messageInput.disabled = state.isLoading;
}

function addUserMessage(content) {
    const template = elements.userMessageTemplate.content.cloneNode(true);
    const messageEl = template.querySelector('.message');
    const contentEl = messageEl.querySelector('.message__content');

    contentEl.textContent = content;
    elements.chatArea.appendChild(messageEl);
    scrollToBottom();
}

function addBotMessage(content) {
    const template = elements.botMessageTemplate.content.cloneNode(true);
    const messageEl = template.querySelector('.message');
    const contentEl = messageEl.querySelector('.message__content');

    contentEl.textContent = content;
    elements.chatArea.appendChild(messageEl);
    scrollToBottom();
}

function showLoading(show) {
    const existingLoading = elements.chatArea.querySelector('.loading');
    if (existingLoading) existingLoading.remove();

    if (show) {
        const template = elements.loadingTemplate.content.cloneNode(true);
        elements.chatArea.appendChild(template);
        scrollToBottom();
    }
}

function scrollToBottom() {
    elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
}

// ==========================================================================
// Initialize
// ==========================================================================
document.addEventListener('DOMContentLoaded', init);
