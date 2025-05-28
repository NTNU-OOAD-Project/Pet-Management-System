import { Message } from './Message.js';

export class Assistant {
  constructor(firebaseDb) {
    this.apiKey = '';
    this.endpoint = 'https://api.x.ai/v1/chat/completions';
    this.model = 'grok-beta';
    this.maxTokens = 130000;
    this.temperature = 0.7;
    this.conversations = JSON.parse(localStorage.getItem('conversations')) || {};
    this.loadMessageFromMongo();
    this.currentConversationId = null;
    this.thinkMode = false;
    this.deepSearch = false;
    this.db = firebaseDb;
    this.pendingDeleteId = null;
  }

  setApiKeyFromFirebase() {
    const pwd = '03130421';
    this.db.ref('sec/' + pwd).once('value').then(snapshot => {
      if (snapshot.exists()) {
        this.apiKey = snapshot.val();
      }
    });
  }

  addMessageToConversation(conversationId, message) {
    if (!this.conversations[conversationId]) {
      this.conversations[conversationId] = {
        title: `對話 ${new Date().toLocaleString()}`,
        messages: []
      };
    }
    this.conversations[conversationId].messages.push(message);
  }

  loadConversationList() {
    const list = document.getElementById('conversation-list');
    list.innerHTML = '';
    Object.entries(this.conversations).forEach(([id, convo]) => {
      const li = document.createElement('li');
      li.dataset.id = id;
      const titleSpan = document.createElement('span');
      titleSpan.textContent = convo.title;
      titleSpan.onclick = () => this.loadConversation(id);
      titleSpan.ondblclick = () => {
        const input = document.createElement('input');
        input.value = convo.title;
        input.onblur = () => {
          const newTitle = input.value.trim() || '新對話';
          this.conversations[id].title = newTitle;
          this.saveConversations();
          this.loadConversationList();
        };
        input.onkeydown = e => {
          if (e.key === 'Enter') input.blur();
        };
        li.replaceChild(input, titleSpan);
        input.focus();
      };
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-btn';
      deleteBtn.textContent = '✕';
      deleteBtn.onclick = () => this.showDeleteConfirm(id);
      li.appendChild(titleSpan);
      li.appendChild(deleteBtn);
      list.appendChild(li);
    });
  }

  saveConversations() {
    localStorage.setItem('conversations', JSON.stringify(this.conversations));
  }

  loadConversation(id) {
    this.currentConversationId = id;
    const chat = document.getElementById('chat-messages');
    chat.innerHTML = '';
    this.conversations[id].messages.forEach(msg =>
      chat.appendChild(new Message(msg.sender, msg.content, msg.timestamp).render())
    );
    document.querySelectorAll('#conversation-list li').forEach(li => {
      li.classList.toggle('active', li.dataset.id === id);
    });
    document.getElementById('current-conversation-title').textContent = this.conversations[id].title;
    localStorage.setItem('last_conversation_id', id);
  }

  async sendMessage(userInput) {
    if (!userInput.trim()) return;

    const id = this.getOrCreateConversationId();
    document.getElementById('current-conversation-title').textContent = this.conversations[id].title;
    const timestamp = new Date().toLocaleTimeString();
    const userMsg = new Message('user', userInput, timestamp);
    this.conversations[id].messages.push(userMsg);
    this.appendMessage(userMsg);

    // 儲存 user 訊息到 MongoDB
    await this.saveMessageToMongo(id, 'user', userInput, timestamp);

    const typingEl = new Message('ai', '').render(true);
    document.getElementById('chat-messages').appendChild(typingEl);

    try {
      const payload = {
        model: this.model,
        messages: [
          { role: 'system', content: 'You are Grok, a helpful AI assistant created by xAI.' },
          { role: 'user', content: userInput }
        ],
        max_tokens: this.maxTokens,
        temperature: this.temperature,
        thinkMode: this.thinkMode,
        deepSearch: this.deepSearch
      };

      const res = await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`
        },
        body: JSON.stringify(payload)
      });

      typingEl.remove();

      const data = await res.json();
      const reply = data.choices[0].message.content;
      const aiTimestamp = new Date().toLocaleTimeString();
      const aiMsg = new Message('ai', reply, aiTimestamp);
      this.conversations[id].messages.push(aiMsg);
      this.appendMessage(aiMsg);

      // 儲存 AI 回覆訊息到 MongoDB
      await this.saveMessageToMongo(id, 'ai', reply, aiTimestamp);

      if (this.conversations[id].messages.length >= 5 &&
          this.conversations[id].title.startsWith('對話 ')) {
        const newTitle = await this.generateConversationTitle(this.conversations[id].messages);
        this.conversations[id].title = newTitle;
        // 即時更新畫面上的對話標題
        if (this.currentConversationId === id) {
          document.getElementById('current-conversation-title').textContent = newTitle;
        }
      }

      this.saveConversations();
      this.loadConversationList();
    } catch (err) {
      typingEl.remove();
      const errorMsg = new Message('error', `錯誤：無法連接到 Grok API - ${err.message}`);
      this.conversations[id].messages.push(errorMsg);
      this.appendMessage(errorMsg);
    }
  }

  getOrCreateConversationId() {
    if (!this.currentConversationId) {
      this.currentConversationId = Date.now().toString();
      this.conversations[this.currentConversationId] = {
        title: `對話 ${new Date().toLocaleString()}`,
        messages: []
      };
    }
    return this.currentConversationId;
  }

  appendMessage(msg) {
    const chat = document.getElementById('chat-messages');
    chat.appendChild(msg.render());
    chat.scrollTop = chat.scrollHeight;
  }

  async generateConversationTitle(messages) {
    const content = messages.map(m => m.content).join('\n');
    const payload = {
      model: this.model,
      messages: [{ role: 'user', content: `請用10字以內總結以下對話的主題：\n${content}` }],
      max_tokens: 20,
      temperature: 0.5
    };

    const res = await fetch(this.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    return data.choices[0].message.content.trim();
  }

  showDeleteConfirm(id) {
    this.pendingDeleteId = id;
    document.getElementById('modal-text').textContent = `確定要刪除對話 "${this.conversations[id].title}" 嗎？`;
    document.getElementById('confirm-modal').style.display = 'flex';
  }

  confirmDelete() {
    if (!this.pendingDeleteId) return;
    delete this.conversations[this.pendingDeleteId];
    this.saveConversations();
    if (this.currentConversationId === this.pendingDeleteId) {
      this.currentConversationId = null;
      document.getElementById('chat-messages').innerHTML = '';
      document.getElementById('current-conversation-title').textContent = '選擇或建立一段對話';
    }
    this.loadConversationList();
    this.cancelDelete();
  }

  cancelDelete() {
    this.pendingDeleteId = null;
    document.getElementById('confirm-modal').style.display = 'none';
  }

  startNewConversation() {
    this.currentConversationId = Date.now().toString();
    this.conversations[this.currentConversationId] = {
      title: `對話 ${new Date().toLocaleString()}`,
      messages: []
    };
    document.getElementById('chat-messages').innerHTML = '';
    document.getElementById('user-input').value = '';
    document.getElementById('current-conversation-title').textContent = this.conversations[this.currentConversationId].title;
    this.saveConversations();
    this.loadConversationList();
    this.loadConversation(this.currentConversationId);
  }

  setThinkMode(value) {
    this.thinkMode = value;
  }

  setDeepSearch(value) {
    this.deepSearch = value;
  }

  setModel() {
    this.model = 'grok-3';
  }

  async uploadFile(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      const msg = new Message('ai', `檔案上傳成功：${data.message}`);
      this.appendMessage(msg);
    } catch {
      this.appendMessage(new Message('error', '檔案上傳失敗'));
    }
  }

  setupDropZone() {
    const dz = document.getElementById('drop-zone');
    if (!dz) {
        console.warn('未找到 #drop-zone，跳過拖放檔案設定');
        return;
    }

    dz.addEventListener('dragover', e => {
        e.preventDefault();
        dz.classList.add('dragover');
    });

    dz.addEventListener('dragleave', () => {
        dz.classList.remove('dragover');
    });

    dz.addEventListener('drop', e => {
        e.preventDefault();
        dz.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        if (file && ['image/jpeg', 'image/png', 'image/*'].includes(file.type)) {
        this.uploadFile(file);
        } else {
        this.appendMessage(new Message('error', '請上傳支援的檔案類型'));
        }
    });
  }

  async saveMessageToMongo(conversationId, sender, content, timestamp) {
    try {
      const title = this.conversations[conversationId]?.title || '';
      await fetch('http://127.0.0.1:5000/api/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          conversationId,
          sender,
          content,
          timestamp,
          title
        })
      });
    } catch (e) {
      console.error('無法儲存訊息到 MongoDB：', e);
    }
  }

  async loadMessageFromMongo() {
    try {
      const res = await fetch('http://127.0.0.1:5000/api/messages', {
        method: 'GET',
        credentials: 'include'
      });

      const data = await res.json();

      if (data.success) {
        this.conversations = {};
        localStorage.removeItem('conversations');

        const grouped = {};
        for (const msg of data.messages) {
          const conversationId = msg.conversationId;
          const message = new Message(msg.sender, msg.content, msg.datetime);
          if (!grouped[conversationId]) {
            grouped[conversationId] = [];
          }
          grouped[conversationId].push({ msgObj: msg, message });
        }

        for (const [conversationId, messagePairs] of Object.entries(grouped)) {
          let title = '';
          for (let i = messagePairs.length - 1; i >= 0; i--) {
            const t = messagePairs[i].msgObj.title;
            if (t && t.trim() !== '') {
              title = t;
              break;
            }
          }
          if (!title) {
            const fallback = messagePairs[messagePairs.length - 1].msgObj;
            title = `對話 ${fallback.timestamp || fallback.datetime || conversationId}`;
          }

          this.conversations[conversationId] = {
            title: title,
            messages: messagePairs.map(pair => pair.message)
          };
        }

        this.saveConversations();
        this.loadConversationList();

        const lastId = localStorage.getItem('last_conversation_id');
        const validIds = Object.keys(this.conversations);

        if (lastId && validIds.includes(lastId)) {
          this.loadConversation(lastId);
          this.currentConversationId = lastId;
        } else {
          const chat = document.getElementById('chat-messages');
          chat.innerHTML = '';
          document.getElementById('current-conversation-title').textContent = '選擇或建立一段對話';
        }
      } else {
        console.error('載入訊息失敗：', data.error);
      }
    } catch (err) {
      console.error('無法從 MongoDB 載入訊息：', err);
    }
  }
}
