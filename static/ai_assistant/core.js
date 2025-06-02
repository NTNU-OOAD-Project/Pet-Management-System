function includeAiAssistant() {
  const container = document.createElement('div');
  container.id = 'ai-assistant-shadow-host';
  document.body.appendChild(container);

  // 建立 Shadow Root
  const shadowRoot = container.attachShadow({ mode: 'open' });

  shadowRoot.innerHTML = `
    <link rel="stylesheet" href="/static/styles.css">
    <style>
      #ai-assistant-icon {
        position: fixed;
        bottom: 24px;
        right: 24px;
        width: 56px;
        height: 56px;
        background: #007bff;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        z-index: 9999;
      }
      #ai-assistant-icon img {
        width: 28px;
        height: 28px;
      }
      #ai-chat-box {
        display: none;
        position: fixed;
        bottom: 90px;
        right: 24px;
        width: 480px;
        height: 800px;
        background: white;
        border-radius: 10px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        z-index: 10000;
        overflow: hidden;
        flex-direction: column;
      }
      #ai-chat-header {
        background: #007bff;
        color: white;
        padding: 12px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      #ai-chat-close {
        cursor: pointer;
        font-size: 20px;
      }
      #ai-chat-content {
        padding: 0;
        flex: 1;
        height: 100%;
        overflow: hidden;
      }
      iframe {
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 10px;
      }
    </style>
    <div id="ai-assistant-icon">
      <img src="/static/image/ai_chat.png" alt="AI智能助理" />
    </div>
    <div id="ai-chat-box">
      <div id="ai-chat-header">
        AI 智能助理
        <span id="ai-chat-close">✕</span>
      </div>
      <div id="ai-chat-content">
        <iframe src="/static/ai_assistant/ai_assistant.html" id="ai-assistant-frame"></iframe>
      </div>
    </div>
  `;

  const icon = shadowRoot.querySelector("#ai-assistant-icon");
  const chatBox = shadowRoot.querySelector("#ai-chat-box");
  const closeBtn = shadowRoot.querySelector("#ai-chat-close");

  if (icon && chatBox && closeBtn) {
    icon.addEventListener("click", () => {
      chatBox.style.display = chatBox.style.display === "none" || chatBox.style.display === "" ? "flex" : "none";
    });
    closeBtn.addEventListener("click", () => {
      chatBox.style.display = "none";
    });
  }
}

includeAiAssistant();
