import { useEffect, useRef, useState } from "react";
import { chatService } from "../services/chatService";

export default function ChatWindow({ otherUserId, itemId }) {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [readOnly, setReadOnly] = useState(false);
  const listRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function init() {
      try {
        // Start conversation via item-based flow
        const resp = await chatService.startConversation(itemId);
        const convId =
          resp.data.conversation_id || resp.data.conversationId || resp.data.id;
        const ro = resp.data.read_only || resp.data.readOnly || false;
        if (!mounted) return;
        setConversationId(convId);
        setReadOnly(!!ro);
        const msgs = await chatService.listMessages(convId);
        if (!mounted) return;
        setMessages(msgs.data || msgs.data?.messages || msgs.data?.items || []);
        // scroll to bottom
        setTimeout(
          () =>
            listRef.current?.scrollIntoView({
              behavior: "smooth",
              block: "end",
            }),
          50,
        );
      } catch (err) {
        console.error("Could not start conversation", err);
      }
    }
    init();
    return () => {
      mounted = false;
    };
  }, [itemId]);

  useEffect(() => {
    function onNotification(e) {
      const payload = e.detail;
      if (!payload) return;
      if (
        payload.event === "chat_message" &&
        payload.data?.conversation_id &&
        payload.data.conversation_id === conversationId
      ) {
        setMessages((m) => [...m, payload.data]);
        // scroll
        setTimeout(
          () =>
            listRef.current?.scrollIntoView({
              behavior: "smooth",
              block: "end",
            }),
          50,
        );
      }
    }
    window.addEventListener("campus-pulse-notification", onNotification);
    return () =>
      window.removeEventListener("campus-pulse-notification", onNotification);
  }, [conversationId]);

  const send = async () => {
    if (!text || !conversationId) return;
    if (readOnly) return;
    const payload = text;
    setText("");
    try {
      const resp = await chatService.postMessage(conversationId, payload);
      // server may return saved message
      const msg = resp.data || resp.data?.message || null;
      if (msg) setMessages((m) => [...m, msg]);
      else {
        // optimistic append
        setMessages((m) => [
          ...m,
          {
            conversation_id: conversationId,
            sender_id: "me",
            content: payload,
            created_at: new Date().toISOString(),
          },
        ]);
      }
      setTimeout(
        () =>
          listRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }),
        50,
      );
    } catch (err) {
      console.error("send failed", err);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {readOnly && (
        <div className="bg-yellow-100 text-yellow-900 px-3 py-2 text-sm font-semibold">
          This conversation is read-only (case closed).
        </div>
      )}
      <div className="flex-1 overflow-auto p-4">
        {messages.length === 0 && (
          <div className="text-sm text-gray-500">No messages yet.</div>
        )}
        <ul className="space-y-3">
          {messages.map((m, idx) => (
            <li
              key={idx}
              className={`p-2 rounded ${m.sender_id === "me" ? "bg-blue-100 self-end" : "bg-gray-100"}`}
            >
              <div className="text-sm text-gray-800">{m.content}</div>
              <div className="text-xs text-gray-500 mt-1">
                {new Date(m.created_at).toLocaleString()}
              </div>
            </li>
          ))}
        </ul>
        <div ref={listRef} />
      </div>
      <div className="p-3 border-t flex items-center gap-2">
        <input
          disabled={readOnly}
          className="flex-1 p-2 border rounded"
          placeholder={readOnly ? "Conversation closed" : "Type a message"}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") send();
          }}
        />
        <button
          disabled={readOnly}
          className={`px-4 py-2 text-white rounded ${readOnly ? "bg-gray-400" : "bg-blue-600"}`}
          onClick={send}
        >
          Send
        </button>
      </div>
    </div>
  );
}
