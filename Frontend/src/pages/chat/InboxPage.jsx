import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import axios from "../../api/axios";
import { useAuth } from "../../context/AuthContext.jsx";

export default function InboxPage() {
  const [conversations, setConversations] = useState([]);
  const { user } = useAuth();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const resp = await axios.get("/chat/conversations");
        if (!mounted) return;
        setConversations(resp.data || []);
      } catch (err) {
        console.error("Could not load conversations", err);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <main className="p-4">
      <h2 className="text-xl font-semibold mb-4">Inbox</h2>
      {conversations.length === 0 && (
        <div className="text-sm text-gray-500">No conversations yet.</div>
      )}
      <ul className="space-y-2">
        {conversations.map((c) => (
          <li
            key={c.conversation_id}
            className="p-3 border rounded flex justify-between items-center"
          >
            <div>
              <div className="font-medium">
                Conversation for item {c.item_id}
              </div>
              <div className="text-sm text-gray-600">{c.last_message}</div>
            </div>
            <div>
              <Link
                to={`/chat/item/${c.item_id}`}
                className="px-3 py-1 bg-blue-600 text-white rounded"
              >
                Open
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </main>
  );
}
