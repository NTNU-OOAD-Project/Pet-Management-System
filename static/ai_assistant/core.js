function includeAiAssistant() {
  const html = `
    <div id="ai-assistant-icon">
      <img src="/static/image/ai_chat.png" alt="AI智能助理" />
    </div>
    <div id="ai-chat-box">
      <div id="ai-chat-header">
        AI 智能助理
        <span id="ai-chat-close">✕</span>
      </div>
      <div id="ai-chat-content">
        <iframe src="/static/ai_assistant/ai_assistant.html"
          id="ai-assistant-frame" 
          style="width: 100%; height: 100%; border: none; border-radius: 10px;">
        </iframe>
      </div>
    </div>
  `;
  document.body.insertAdjacentHTML('beforeend', html);

  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = '/static/styles.css';
  document.head.appendChild(link);

  document.addEventListener("DOMContentLoaded", () => {
    const icon = document.querySelector("#ai-assistant-icon");
    const chatBox = document.querySelector("#ai-chat-box");
    const closeBtn = document.querySelector("#ai-chat-close");

    if (icon && chatBox && closeBtn) {
      icon.addEventListener("click", () => {
        chatBox.style.display = chatBox.style.display === "none" || chatBox.style.display === "" ? "flex" : "none";
      });
      closeBtn.addEventListener("click", () => {
        chatBox.style.display = "none";
      });
    }
  });
}

includeAiAssistant();