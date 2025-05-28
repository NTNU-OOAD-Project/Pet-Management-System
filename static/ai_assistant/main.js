import { Assistant } from './Assistant.js';

const firebaseConfig = {
  apiKey: "AIzaSyAu9XMkGMbRlmAKlckJKp0shovPVB3Y988",
  authDomain: "secretlookup.firebaseapp.com",
  databaseURL: "https://secretlookup-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "secretlookup",
  storageBucket: "secretlookup.appspot.com",
  messagingSenderId: "707709670835",
  appId: "1:707709670835:web:bdc21c8e7b0b13f046e7c6"
};

firebase.initializeApp(firebaseConfig);
const db = firebase.database();
const assistant = new Assistant(db);

window.addEventListener('DOMContentLoaded', () => {
  marked.setOptions({ breaks: true, gfm: true });

  assistant.loadConversationList();
  assistant.setupDropZone();

  // 密碼輸入 → 設定 API 金鑰
  assistant.setApiKeyFromFirebase();

  // 模型選擇
  assistant.setModel();

  // 側欄開關
  document.getElementById('toggle-sidebar-btn')?.addEventListener('click', () => {
    document.querySelector('.sidebar')?.classList.toggle('active');
  });

  // 輸入框 enter 傳送訊息
  document.getElementById('user-input')?.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const text = e.target.value.trim();
      if (text) assistant.sendMessage(text);
      e.target.value = '';
    }
  });

  // Enter 按鈕送出訊息
  document.getElementById('send-btn')?.addEventListener('click', () => {
    const input = document.getElementById('user-input').value.trim();
    if (input) {
      assistant.sendMessage(input);
      document.getElementById('user-input').value = '';
    }
  });

  document.getElementById('new-conversation-btn')?.addEventListener('click', () => {
    assistant.startNewConversation();
  });

  document.getElementById('confirm-delete-btn')?.addEventListener('click', () => {
    assistant.confirmDelete();
  });

  document.getElementById('cancel-delete-btn')?.addEventListener('click', () => {
    assistant.cancelDelete();
  });
});
