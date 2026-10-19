import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  MessageSquare,
  Send,
  Search,
  User,
  Users,
  Clock,
  CheckCheck,
  Shield,
  MapPin,
  Building,
  Plus,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import { chatService } from "../../services/chatService.js";
import { useAuth } from "../../context/AuthContext.jsx";
import ChatWindow from "../../components/ChatWindow.jsx";
import Loader from "../../components/Loader.jsx";
import { getRoleDisplayName } from "../../utils/constants.js";

export default function ChatPage() {
  const { itemId } = useParams();
  const [searchParams] = useSearchParams();
  const targetUserId = searchParams.get("userId") || searchParams.get("user_id");
  const targetUserName = searchParams.get("name") || "";
  const { user } = useAuth();

  // If opened for a Lost & Found item, preserve existing item chat interface
  if (itemId) {
    return (
      <main className="p-4 h-[75vh]">
        <div className="flex items-center gap-2 mb-4">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
            Lost & Found Chat
          </h2>
        </div>
        <div className="border border-slate-200 dark:border-slate-800 rounded-xl h-full overflow-hidden bg-white dark:bg-slate-900 shadow-sm">
          <ChatWindow itemId={itemId} />
        </div>
      </main>
    );
  }

  // Personal 1:1 Chat State
  const [conversations, setConversations] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("conversations"); // "conversations" | "contacts"
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  const messagesEndRef = useRef(null);

  const scrollToBottom = (behavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: "end" });
  };

  // Load initial conversations & contacts
  const loadData = async () => {
    setError("");
    try {
      const [convRes, contactsRes] = await Promise.all([
        chatService.getConversations({ type: "personal" }).catch(() => ({ data: [] })),
        chatService.getContacts().catch(() => ({ data: [] })),
      ]);
      const personalOnly = (convRes.data || []).filter(
        (c) => c.type === "personal" && (c.other_user_role || "").toLowerCase() !== "student"
      );
      setConversations(personalOnly);
      setContacts(contactsRes.data || []);
    } catch (err) {
      setError("Failed to load chat conversations. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Auto-connect to target user if specified in URL query
  useEffect(() => {
    if (!targetUserId || loading) return;

    // 1. Check if conversation already exists with this user
    const existing = conversations.find((c) => c.other_user_id === targetUserId);
    if (existing) {
      setSelectedConversation(existing);
      setActiveTab("conversations");
      return;
    }

    // 2. Start personal chat with this user
    async function initPersonalChat() {
      try {
        const resp = await chatService.startPersonalChat(targetUserId);
        const convData = resp.data;
        const matchingContact = contacts.find((c) => c.user_id === targetUserId);
        const convObj = {
          conversation_id: convData.conversation_id,
          other_user_id: targetUserId,
          other_user_name: matchingContact?.name || targetUserName || targetUserId,
          other_user_role: matchingContact?.role || "coordinator",
          other_user_email: matchingContact?.email || "",
          last_message: "",
          last_at: new Date().toISOString(),
          unread_count: 0,
          type: "personal",
        };
        setConversations((prev) => {
          if (!prev.some((c) => c.conversation_id === convData.conversation_id)) {
            return [convObj, ...prev];
          }
          return prev;
        });
        setSelectedConversation(convObj);
        setActiveTab("conversations");
      } catch (err) {
        console.error("Unable to start personal chat with coordinator:", err);
      }
    }

    initPersonalChat();
  }, [targetUserId, loading, conversations.length]);

  // When a conversation is selected, load its messages
  useEffect(() => {
    if (!selectedConversation?.conversation_id) return;
    let mounted = true;

    async function fetchMessages() {
      try {
        const resp = await chatService.listMessages(
          selectedConversation.conversation_id,
        );
        if (!mounted) return;
        setMessages(resp.data || []);
        // Update unread count in conversations list
        setConversations((prev) =>
          prev.map((c) =>
            c.conversation_id === selectedConversation.conversation_id
              ? { ...c, unread_count: 0 }
              : c,
          ),
        );
        setTimeout(() => scrollToBottom("auto"), 50);
      } catch (err) {
        console.error("Failed to load messages", err);
      }
    }

    fetchMessages();
    return () => {
      mounted = false;
    };
  }, [selectedConversation?.conversation_id]);

  // Real-time WebSocket message listener
  useEffect(() => {
    function onNotification(e) {
      const payload = e.detail;
      if (!payload || payload.event !== "chat_message") return;
      const newMsg = payload.data;
      if (!newMsg) return;

      // If active conversation matches, append message
      if (
        selectedConversation &&
        newMsg.conversation_id === selectedConversation.conversation_id
      ) {
        setMessages((prev) => {
          if (prev.some((m) => m.message_id === newMsg.message_id)) return prev;
          return [...prev, newMsg];
        });
        setTimeout(() => scrollToBottom("smooth"), 50);
      }

      // Update conversations list with latest message preview & unread count
      setConversations((prev) => {
        const existing = prev.find(
          (c) => c.conversation_id === newMsg.conversation_id,
        );
        if (existing) {
          return prev.map((c) => {
            if (c.conversation_id === newMsg.conversation_id) {
              const isActive =
                selectedConversation?.conversation_id === newMsg.conversation_id;
              return {
                ...c,
                last_message: newMsg.content,
                last_sender: newMsg.sender_id,
                last_at: newMsg.created_at,
                unread_count: isActive ? 0 : (c.unread_count || 0) + 1,
              };
            }
            return c;
          });
        }
        // If not in list, reload conversations
        loadData();
        return prev;
      });
    }

    window.addEventListener("campus-pulse-notification", onNotification);
    return () =>
      window.removeEventListener("campus-pulse-notification", onNotification);
  }, [selectedConversation]);

  // Handle starting a new conversation with a contact
  const handleSelectContact = async (contact) => {
    setError("");
    try {
      const resp = await chatService.startPersonalChat(contact.user_id);
      const convData = resp.data;
      const convObj = {
        conversation_id: convData.conversation_id,
        other_user_id: contact.user_id,
        other_user_name: contact.name,
        other_user_role: contact.role,
        other_user_email: contact.email,
        last_message: "",
        last_at: new Date().toISOString(),
        unread_count: 0,
        type: "personal",
      };

      // Add to conversations list if not present
      setConversations((prev) => {
        if (!prev.some((c) => c.conversation_id === convData.conversation_id)) {
          return [convObj, ...prev];
        }
        return prev;
      });

      setSelectedConversation(convObj);
      setActiveTab("conversations");
    } catch (err) {
      setError("Unable to initiate chat with selected staff member.");
    }
  };

  // Send message handler
  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || !selectedConversation?.conversation_id || sending)
      return;

    const content = inputText.trim();
    setInputText("");
    setSending(true);

    try {
      const resp = await chatService.postMessage(
        selectedConversation.conversation_id,
        content,
      );
      const savedMsg = resp.data;

      if (savedMsg) {
        setMessages((prev) => {
          if (prev.some((m) => m.message_id === savedMsg.message_id)) return prev;
          return [...prev, savedMsg];
        });
      }

      // Update conversations list last message
      setConversations((prev) =>
        prev.map((c) =>
          c.conversation_id === selectedConversation.conversation_id
            ? {
                ...c,
                last_message: content,
                last_sender: user?.user_id,
                last_at: new Date().toISOString(),
              }
            : c,
        ),
      );

      setTimeout(() => scrollToBottom("smooth"), 50);
    } catch (err) {
      setError("Failed to send message. Please verify network connectivity.");
    } finally {
      setSending(false);
    }
  };

  // Format timestamp nicely
  const formatTime = (isoString) => {
    if (!isoString) return "";
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return "";
    }
  };

  const getRoleBadgeColor = (role) => {
    const r = (role || "").toLowerCase();
    if (r === "administrator")
      return "bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 border-rose-200 dark:border-rose-800/40";
    if (r === "app_manager")
      return "bg-purple-100 text-purple-800 dark:bg-purple-950/40 dark:text-purple-300 border-purple-200 dark:border-purple-800/40";
    if (r === "location_in_charge")
      return "bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border-amber-200 dark:border-amber-800/40";
    if (r === "coordinator")
      return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800/40";
    return "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 border-slate-200 dark:border-slate-700";
  };

  const getRoleLabel = (role) => {
    return getRoleDisplayName(role) || "Staff";
  };

  // Filtered conversations & contacts
  const filteredConversations = useMemo(() => {
    if (!searchQuery.trim()) return conversations;
    const q = searchQuery.toLowerCase();
    return conversations.filter(
      (c) =>
        (c.other_user_name || "").toLowerCase().includes(q) ||
        (c.last_message || "").toLowerCase().includes(q) ||
        (c.other_user_role || "").toLowerCase().includes(q),
    );
  }, [conversations, searchQuery]);

  const filteredContacts = useMemo(() => {
    if (!searchQuery.trim()) return contacts;
    const q = searchQuery.toLowerCase();
    return contacts.filter(
      (c) =>
        (c.name || "").toLowerCase().includes(q) ||
        (c.email || "").toLowerCase().includes(q) ||
        (c.role || "").toLowerCase().includes(q) ||
        (c.department_name || "").toLowerCase().includes(q) ||
        (c.location_name || "").toLowerCase().includes(q),
    );
  }, [contacts, searchQuery]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader label="Loading personal chat..." />
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-7xl mx-auto h-[calc(100vh-5rem)] flex flex-col">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-2 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-2 bg-primary/10 rounded-xl text-primary">
            <MessageSquare className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Personal Staff Chat
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Real-time 1-to-1 messaging between Admins, App Managers, Wardens, and Coordinators
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="self-start sm:self-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors shadow-sm"
          title="Refresh Conversations"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-3 p-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800/50 rounded-xl text-rose-700 dark:text-rose-300 text-sm flex items-center gap-2 shrink-0">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Chat Container */}
      <div className="flex-1 min-h-0 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden flex flex-col md:flex-row">
        {/* Left Panel: Conversation & Contact Directory */}
        <div className="w-full md:w-80 lg:w-96 border-b md:border-b-0 md:border-r border-slate-200 dark:border-slate-800 flex flex-col shrink-0 h-full">
          {/* Tabs: Recent Chats vs Staff Directory */}
          <div className="p-3 border-b border-slate-200 dark:border-slate-800 flex items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab("conversations")}
              className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
                activeTab === "conversations"
                  ? "bg-primary text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Recent Chats
              {conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0) >
                0 && (
                <span className="ml-1 px-1.5 py-0.2 bg-white text-primary text-[10px] font-bold rounded-full">
                  {conversations.reduce((sum, c) => sum + (c.unread_count || 0), 0)}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("contacts")}
              className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
                activeTab === "contacts"
                  ? "bg-primary text-white shadow-sm"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700"
              }`}
            >
              <Users className="h-3.5 w-3.5" />
              New Chat ({contacts.length})
            </button>
          </div>

          {/* Search Bar */}
          <div className="p-3 border-b border-slate-200 dark:border-slate-800">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder={
                  activeTab === "conversations"
                    ? "Search conversations..."
                    : "Search staff members..."
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 text-slate-900 dark:text-white placeholder-slate-400"
              />
            </div>
          </div>

          {/* List Content */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800/60">
            {activeTab === "conversations" ? (
              filteredConversations.length === 0 ? (
                <div className="p-8 text-center text-slate-400 dark:text-slate-500">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p className="text-xs">No active conversations found.</p>
                  <button
                    onClick={() => setActiveTab("contacts")}
                    className="mt-2 text-xs text-primary font-semibold hover:underline"
                  >
                    Start a chat from Directory &rarr;
                  </button>
                </div>
              ) : (
                filteredConversations.map((conv) => {
                  const isSelected =
                    selectedConversation?.conversation_id === conv.conversation_id;
                  return (
                    <button
                      key={conv.conversation_id}
                      onClick={() => setSelectedConversation(conv)}
                      className={`w-full text-left p-3.5 flex items-start gap-3 transition-colors ${
                        isSelected
                          ? "bg-primary/5 dark:bg-primary/10 border-l-4 border-primary"
                          : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                      }`}
                    >
                      {/* Avatar */}
                      <div className="relative shrink-0">
                        <div className="h-10 w-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300 text-sm">
                          {conv.other_user_name
                            ? conv.other_user_name.charAt(0).toUpperCase()
                            : "U"}
                        </div>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1 mb-1">
                          <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                            {conv.other_user_name || conv.other_user_id}
                          </h4>
                          {conv.last_at && (
                            <span className="text-[10px] text-slate-400 shrink-0">
                              {formatTime(conv.last_at)}
                            </span>
                          )}
                        </div>

                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                            {conv.last_message || (
                              <span className="italic text-slate-400">
                                Conversation started
                              </span>
                            )}
                          </p>
                          {conv.unread_count > 0 && (
                            <span className="px-1.5 py-0.5 bg-primary text-white text-[10px] font-bold rounded-full shrink-0">
                              {conv.unread_count}
                            </span>
                          )}
                        </div>

                        {conv.other_user_role && (
                          <div className="mt-1">
                            <span
                              className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold border ${getRoleBadgeColor(
                                conv.other_user_role,
                              )}`}
                            >
                              {getRoleLabel(conv.other_user_role)}
                            </span>
                          </div>
                        )}
                      </div>
                    </button>
                  );
                })
              )
            ) : filteredContacts.length === 0 ? (
              <div className="p-8 text-center text-slate-400 dark:text-slate-500">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-30" />
                <p className="text-xs">No contacts match your query.</p>
              </div>
            ) : (
              filteredContacts.map((contact) => (
                <div
                  key={contact.user_id}
                  className="p-3.5 flex items-center justify-between gap-3 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="relative shrink-0">
                      <div className="h-10 w-10 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center font-bold text-slate-600 dark:text-slate-300 text-sm">
                        {contact.name.charAt(0).toUpperCase()}
                      </div>
                      {contact.is_online && (
                        <span className="absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-slate-900" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <h4 className="text-xs font-bold text-slate-900 dark:text-white truncate">
                        {contact.name}
                      </h4>
                      <p className="text-[11px] text-slate-400 truncate">
                        {contact.email}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1">
                        <span
                          className={`inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold border ${getRoleBadgeColor(
                            contact.role,
                          )}`}
                        >
                          {getRoleLabel(contact.role)}
                        </span>
                        {contact.location_name && (
                          <span className="text-[10px] text-slate-400 truncate flex items-center gap-0.5">
                            <MapPin className="h-2.5 w-2.5" />
                            {contact.location_name}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleSelectContact(contact)}
                    className="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors shrink-0"
                    title={`Start chat with ${contact.name}`}
                  >
                    <Plus className="h-4 w-4" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Panel: Active Chat View */}
        <div className="flex-1 flex flex-col h-full min-w-0 bg-slate-50/50 dark:bg-slate-950/20">
          {selectedConversation ? (
            <>
              {/* Active Conversation Top Bar */}
              <div className="p-3.5 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center justify-between gap-3 shrink-0">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="h-10 w-10 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm shrink-0">
                    {selectedConversation.other_user_name
                      ? selectedConversation.other_user_name.charAt(0).toUpperCase()
                      : "U"}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-bold text-slate-900 dark:text-white truncate">
                        {selectedConversation.other_user_name ||
                          selectedConversation.other_user_id}
                      </h3>
                      {selectedConversation.other_user_role && (
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border shrink-0 ${getRoleBadgeColor(
                            selectedConversation.other_user_role,
                          )}`}
                        >
                          {getRoleLabel(selectedConversation.other_user_role)}
                        </span>
                      )}
                    </div>
                    {selectedConversation.other_user_email && (
                      <p className="text-[11px] text-slate-400 truncate">
                        {selectedConversation.other_user_email}
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-[11px] text-slate-400 font-mono hidden sm:block">
                  {selectedConversation.conversation_id}
                </div>
              </div>

              {/* Message Stream */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-slate-400 dark:text-slate-500 py-12">
                    <MessageSquare className="h-10 w-10 mb-2 opacity-30" />
                    <p className="text-sm font-medium">No messages in this conversation yet.</p>
                    <p className="text-xs">Send a message below to start coordinating!</p>
                  </div>
                ) : (
                  messages.map((m, idx) => {
                    const isMe = m.sender_id === user?.user_id;
                    return (
                      <div
                        key={m.message_id || idx}
                        className={`flex flex-col ${
                          isMe ? "items-end" : "items-start"
                        }`}
                      >
                        <div
                          className={`max-w-[85%] sm:max-w-[70%] px-4 py-2.5 rounded-2xl shadow-sm text-sm ${
                            isMe
                              ? "bg-primary text-white rounded-br-xs"
                              : "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-200 dark:border-slate-700/60 rounded-bl-xs"
                          }`}
                        >
                          <p className="whitespace-pre-wrap break-words leading-relaxed">
                            {m.content}
                          </p>
                        </div>
                        <span className="text-[10px] text-slate-400 mt-1 px-1">
                          {formatTime(m.created_at)}
                        </span>
                      </div>
                    );
                  })
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Composer */}
              <form
                onSubmit={handleSendMessage}
                className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center gap-2 shrink-0"
              >
                <input
                  type="text"
                  placeholder="Type your message... (Press Enter to send)"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  disabled={sending}
                  className="flex-1 px-4 py-2.5 text-xs sm:text-sm bg-slate-50 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 text-slate-900 dark:text-white placeholder-slate-400"
                />
                <button
                  type="submit"
                  disabled={!inputText.trim() || sending}
                  className="px-4 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-xl font-semibold text-xs sm:text-sm flex items-center gap-1.5 transition-colors disabled:opacity-40 disabled:cursor-not-allowed shadow-sm shrink-0"
                >
                  <Send className="h-4 w-4" />
                  <span className="hidden sm:inline">Send</span>
                </button>
              </form>
            </>
          ) : (
            /* Empty State */
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400 dark:text-slate-500">
              <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-2xl mb-4">
                <MessageSquare className="h-12 w-12 text-slate-300 dark:text-slate-600" />
              </div>
              <h3 className="text-base font-bold text-slate-700 dark:text-slate-300 mb-1">
                Select a Conversation
              </h3>
              <p className="text-xs max-w-sm text-slate-500 dark:text-slate-400 mb-4">
                Choose an existing chat from the left panel or click "New Chat" to begin a 1-to-1 conversation with any staff coordinator or manager.
              </p>
              <button
                type="button"
                onClick={() => setActiveTab("contacts")}
                className="px-4 py-2 bg-primary text-white rounded-xl text-xs font-semibold hover:bg-primary-hover transition-colors shadow-sm"
              >
                Open Staff Directory
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
