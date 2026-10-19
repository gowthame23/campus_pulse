import axios from "../api/axios";

export const chatService = {
  // 1:1 Personal Chat methods
  getContacts: () => axios.get("/chat/users"),
  getConversations: (params) => axios.get("/chat/conversations", { params }),
  getUnreadCount: () => axios.get("/chat/unread-count"),
  startPersonalChat: (recipientId) =>
    axios.post("/chat/personal/start", { recipient_id: recipientId }),

  // Lost & Found item chat
  startConversation: (itemId) => axios.post("/chat/start", { item_id: itemId }),

  // Messaging & conversation retrieval
  postMessage: (conversationId, content) =>
    axios.post("/chat/message", { conversation_id: conversationId, content }),
  listMessages: (conversationId) => axios.get(`/chat/${conversationId}`),
};
