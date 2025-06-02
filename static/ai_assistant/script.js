// API 設定變數
const apiConfig = {
    key: '', // 請替換為你的 xAI API 金鑰
    endpoint: 'https://api.x.ai/v1/chat/completions', // Grok API 端點
    model: 'grok-beta', // 使用 grok-beta 模型（可改為 grok-2-1212 等，視可用性）
    maxTokens: 130000, // 最大回應 token 數
    temperature: 0.7 // 控制回應隨機性（0.0-1.0）
};

const firebaseConfig = {
    apiKey: "AIzaSyAu9XMkGMbRlmAKlckJKp0shovPVB3Y988",
    authDomain: "secretlookup.firebaseapp.com",
    databaseURL: "https://secretlookup-default-rtdb.asia-southeast1.firebasedatabase.app",
    projectId: "secretlookup",
    storageBucket: "secretlookup.firebasestorage.app",
    messagingSenderId: "707709670835",
    appId: "1:707709670835:web:bdc21c8e7b0b13f046e7c6"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.database();

// 儲存對話紀錄
let conversations = JSON.parse(localStorage.getItem('conversations')) || {};
let currentConversationId = null;
let thinkMode = false;
let deepSearchMode = false;
let pendingDeleteId = null;

function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
        console.log('Sidebar classList:', sidebar.classList);
    } else {
        console.error('Sidebar element not found');
    }
}

// 載入對話列表
function loadConversationList() {
    const list = document.getElementById('conversation-list');
    list.innerHTML = '';
    Object.keys(conversations).forEach(id => {
        const li = document.createElement('li');
        li.dataset.id = id;
        const titleSpan = document.createElement('span');
        titleSpan.textContent = conversations[id].title;
        titleSpan.onclick = () => loadConversation(id);
        // 雙擊編輯標題
        titleSpan.ondblclick = () => {
            const input = document.createElement('input');
            input.value = conversations[id].title;
            input.onblur = () => {
                const newTitle = input.value.trim() || '新對話';
                conversations[id].title = newTitle;
                localStorage.setItem('conversations', JSON.stringify(conversations));
                loadConversationList();
            };
            input.onkeydown = (e) => {
                if (e.key === 'Enter') {
                    input.blur();
                }
            };
            li.replaceChild(input, titleSpan);
            input.focus();
        };
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = '✕';
        deleteBtn.onclick = () => showDeleteConfirm(id);
        li.appendChild(titleSpan);
        li.appendChild(deleteBtn);
        list.appendChild(li);
    });
}

function updateApiKey() {
    const pwd = document.getElementById("passwordInput").value;
    db.ref('sec/' + pwd).once('value').then(snapshot => {
        if (snapshot.exists()) {
            apiConfig.key = snapshot.val();
        } 
      });
    
}

// 載入特定對話
function loadConversation(id) {
    currentConversationId = id;
    const messages = conversations[id].messages;
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML = '';
    messages.forEach(msg => {
        addMessage(msg.content, msg.sender, msg.timestamp);
    });
    // 高亮側邊欄
    document.querySelectorAll('#conversation-list li').forEach(li => {
        li.classList.remove('active');
        if (li.dataset.id === id) li.classList.add('active');
    });
}

// 新增訊息到畫面
function addMessage(content, sender, timestamp = new Date().toLocaleTimeString(), isTyping = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}${isTyping ? ' typing' : ''}`;
    const contentSpan = document.createElement('span');
    if (isTyping) {
        contentSpan.innerHTML = 'Grok 正在回應';
    } else {
        // 確保換行符號正確渲染
        const markdownHtml = marked.parse(content, {
            breaks: true // 啟用 GFM 風格換行
        });
        contentSpan.innerHTML = DOMPurify.sanitize(markdownHtml);
    }
    const timeSpan = document.createElement('span');
    timeSpan.className = 'timestamp';
    timeSpan.textContent = timestamp;
    messageDiv.appendChild(contentSpan);
    if (!isTyping) {
        messageDiv.appendChild(timeSpan);
    }
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageDiv;
}

// 移除提示泡泡
function removeTypingMessage() {
    const typingMessage = document.querySelector('.message.typing');
    if (typingMessage) {
        typingMessage.remove();
    }
}

// 進階主題生成（使用 Grok API）
async function generateConversationTitle(messages) {
    if (messages.length < 5) {
        return `對話 ${new Date().toLocaleString()}`;
    }
    try {
        const content = messages.map(m => m.content).join('\n');
        const payload = {
            model: apiConfig.model,
            messages: [{
                role: 'user',
                content: `請用10字以內總結以下對話的主題：\n${content}`
            }],
            max_tokens: 20,
            temperature: 0.5
        };
        const response = await fetch(apiConfig.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiConfig.key}`
            },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data.choices[0].message.content.trim() || `對話 ${new Date().toLocaleString()}`;
    } catch (error) {
        console.error('生成標題錯誤:', error);
        return `對話 ${new Date().toLocaleString()}`;
    }
}

// 顯示刪除確認框
function showDeleteConfirm(id) {
    pendingDeleteId = id;
    const modal = document.getElementById('confirm-modal');
    const modalText = document.getElementById('modal-text');
    modalText.textContent = `確定要刪除對話 "${conversations[id].title}" 嗎？`;
    modal.style.display = 'flex';
}

// 確認刪除
function confirmDelete() {
    if (pendingDeleteId) {
        delete conversations[pendingDeleteId];
        localStorage.setItem('conversations', JSON.stringify(conversations));
        if (currentConversationId === pendingDeleteId) {
            currentConversationId = null;
            document.getElementById('chat-messages').innerHTML = '';
        }
        loadConversationList();
        cancelDelete();
    }
}

// 取消刪除
function cancelDelete() {
    pendingDeleteId = null;
    document.getElementById('confirm-modal').style.display = 'none';
}

// 新增新對話
function startNewConversation() {
    // 生成新對話 ID
    currentConversationId = Date.now().toString();
    conversations[currentConversationId] = {
        title: `對話 ${new Date().toLocaleString()}`,
        messages: []
    };
    // 清空聊天區域
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('user-input').value = '';
    // 更新側邊欄
    localStorage.setItem('conversations', JSON.stringify(conversations));
    loadConversationList();
    // 高亮新對話
    loadConversation(currentConversationId);
}

// 發送訊息到 Grok API
async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (!message) return;

    if (!currentConversationId) {
        currentConversationId = Date.now().toString();
        conversations[currentConversationId] = {
            title: `對話 ${new Date().toLocaleString()}`,
            messages: []
        };
    }

    const timestamp = new Date().toLocaleTimeString();
    conversations[currentConversationId].messages.push({ content: message, sender: 'user', timestamp });
    addMessage(message, 'user', timestamp);
    userInput.value = '';

    // 顯示回應提示泡泡
    const typingMessage = addMessage('', 'ai', '', true);

    try {
        const payload = {
            model: apiConfig.model,
            messages: [
                {
                    role: 'system',
                    content: 'You are Grok, a helpful AI assistant created by xAI.'
                },
                {
                    role: 'user',
                    content: message
                }
            ],
            max_tokens: apiConfig.maxTokens,
            temperature: apiConfig.temperature,
            thinkMode,
            deepSearch: deepSearchMode
        };

        const response = await fetch(apiConfig.endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiConfig.key}`
            },
            body: JSON.stringify(payload)
        });

        // 移除提示泡泡
        removeTypingMessage();

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const aiResponse = data.choices[0].message.content;
        const aiTimestamp = new Date().toLocaleTimeString();
        conversations[currentConversationId].messages.push({ content: aiResponse, sender: 'ai', timestamp: aiTimestamp });
        addMessage(aiResponse, 'ai', aiTimestamp);

        // 檢查是否達到 5 條訊息，更新標題
        const messages = conversations[currentConversationId].messages;
        if (messages.length >= 5 && conversations[currentConversationId].title.startsWith('對話 ')) {
            const newTitle = await generateConversationTitle(messages);
            conversations[currentConversationId].title = newTitle;
            localStorage.setItem('conversations', JSON.stringify(conversations));
            loadConversationList();
        }
    } catch (error) {
        // 移除提示泡泡，顯示錯誤
        removeTypingMessage();
        console.error('API 錯誤:', error);
        const errorMessage = `錯誤：無法連接到 Grok API - ${error.message}`;
        conversations[currentConversationId].messages.push({ 
            content: errorMessage, 
            sender: 'error', 
            timestamp: new Date().toLocaleTimeString() 
        });
        addMessage(errorMessage, 'error');
    }

    localStorage.setItem('conversations', JSON.stringify(conversations));
    loadConversationList();
}

// 更新 Think 模式狀態
function updateThinkMode() {
    thinkMode = document.getElementById('think-toggle').checked;
}

// 更新 DeepSearch 模式狀態
function updateDeepSearch() {
    deepSearchMode = document.getElementById('deepsearch-toggle').checked;
}

// 上傳檔案
async function uploadFile(file) {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        const timestamp = new Date().toLocaleTimeString();
        addMessage(`檔案上傳成功：${data.message}`, 'ai', timestamp);
        if (currentConversationId) {
            conversations[currentConversationId].messages.push({ 
                content: `上傳檔案：${file.name}`, 
                sender: 'user', 
                timestamp 
            });
            localStorage.setItem('conversations', JSON.stringify(conversations));
        }
    } catch (error) {
        addMessage('檔案上傳失敗', 'error');
    }
}

// 拖放檔案處理
function setupDropZone() {
    const dropZone = document.getElementById('drop-zone');
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && (
            ['image/jpeg', 'image/png', "image/*"].includes(file.type)
            || file.name.endsWith('.js') || file.name.endsWith('.html')
        )) {
            uploadFile(file);
        } else {
            addMessage('請上傳支援的檔案類型（圖片、PDF、TXT）', 'error');
        }
    });
}

// 更新模型選擇
function updateModel() {
    const modelSelect = document.getElementById('model-select');
    apiConfig.model = modelSelect.value;
}

// 初始化
window.onload = () => {
    // 配置 marked.js 以支援換行
    marked.setOptions({
        breaks: true, // 啟用 GFM 風格換行（單換行轉 <br>）
        gfm: true // 啟用 GitHub Flavored Markdown
    });

    loadConversationList();
    setupDropZone();

    const toggleBtn = document.getElementById('toggle-sidebar-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleSidebar);
    } else {
        console.error('Toggle sidebar button not found');
    }

    const userInput = document.getElementById('user-input');
    // 支援繁體中文輸入法
    userInput.addEventListener('compositionstart', () => {
        userInput.isComposing = true;
    });
    userInput.addEventListener('compositionend', () => {
        userInput.isComposing = false;
    });
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey && !userInput.isComposing) {
            e.preventDefault();
            sendMessage();
        }
    });

    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = `${Math.min(this.scrollHeight, 150)}px`;
    });
};