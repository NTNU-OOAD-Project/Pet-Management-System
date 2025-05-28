export class Message {
  constructor(sender, content, timestamp = new Date().toLocaleTimeString()) {
    this.sender = sender;
    this.content = content;
    this.timestamp = timestamp;
  }

  render(isTyping = false) {
    const div = document.createElement('div');
    div.className = `message ${this.sender}${isTyping ? ' typing' : ''}`;

    const span = document.createElement('span');
    if (isTyping) {
      span.innerHTML = 'Grok 正在回應';
    } else {
      const html = marked.parse(this.content, { breaks: true });
      span.innerHTML = DOMPurify.sanitize(html);
    }
    div.appendChild(span);

    if (!isTyping) {
      const timeSpan = document.createElement('span');
      timeSpan.className = 'timestamp';
      timeSpan.textContent = this.timestamp;
      div.appendChild(timeSpan);
    }

    return div;
  }
}
