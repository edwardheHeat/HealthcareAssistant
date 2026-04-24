"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  createChatSession,
  getChatSessions,
  getMessages,
  sendMessage,
} from "@/lib/apiClient";
import type { ChatMessage, ChatSession } from "@/types/chat";

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`chat-bubble ${isUser ? "user" : "assistant"}`}>
      <div className="bubble-role">{isUser ? "You" : "HealthAI"}</div>
      <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="chat-bubble assistant" style={{ padding: "12px 18px" }}>
      <div className="bubble-role">HealthAI</div>
      <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 8,
              height: 8,
              background: "var(--accent)",
              borderRadius: "50%",
              display: "inline-block",
              animation: `bounce 1.2s ${i * 0.2}s infinite ease-in-out`,
            }}
          />
        ))}
        <style>{`
          @keyframes bounce {
            0%, 60%, 100% { transform: translateY(0); }
            30% { transform: translateY(-6px); }
          }
        `}</style>
      </div>
    </div>
  );
}

function ChatPageInner() {
  const searchParams = useSearchParams();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [initError, setInitError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const didAutoSend = useRef(false);

  useEffect(() => {
    initSession();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const initSession = async () => {
    try {
      const sessions = await getChatSessions();
      let activeSession = sessions[0] ?? null;
      if (!activeSession) {
        activeSession = await createChatSession();
      }
      setSession(activeSession);
      const history = await getMessages(activeSession.id);
      setMessages(history);

      // Auto-send prompt from query param (e.g. from "Ask LLM" in alerts)
      const promptParam = searchParams.get("prompt");
      if (promptParam && !didAutoSend.current) {
        didAutoSend.current = true;
        await sendPromptMessage(activeSession, promptParam);
      }
    } catch (e: unknown) {
      setInitError(e instanceof Error ? e.message : "Failed to connect. Start the backend first.");
    }
  };

  const sendPromptMessage = async (activeSession: ChatSession, text: string) => {
    setLoading(true);
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      session_id: activeSession.id,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setTyping(true);
    try {
      const res = await sendMessage(activeSession.id, text);
      setMessages((prev) => [...prev, res.message]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          session_id: activeSession.id,
          role: "assistant",
          content: "⚠️ Something went wrong. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  const startNewSession = async () => {
    try {
      const newSession = await createChatSession();
      setSession(newSession);
      setMessages([]);
    } catch {}
  };

  const handleSend = async () => {
    if (!input.trim() || !session || loading) return;
    const userText = input.trim();
    setInput("");
    setLoading(true);

    // Optimistically add user message
    const tempUserMsg: ChatMessage = {
      id: Date.now(),
      session_id: session.id,
      role: "user",
      content: userText,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setTyping(true);

    try {
      const res = await sendMessage(session.id, userText);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== tempUserMsg.id),
        { ...tempUserMsg, id: tempUserMsg.id }, // keep user bubble
        res.message,
      ]);
    } catch (e: unknown) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          session_id: session.id,
          role: "assistant",
          content: "⚠️ Something went wrong. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
      setTyping(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (initError) {
    return (
      <div className="empty-state">
        <div className="empty-icon">🔌</div>
        <h3>Could not connect to backend</h3>
        <p style={{ marginTop: 8 }}>{initError}</p>
        <button
          className="btn btn-primary"
          style={{ marginTop: 20 }}
          onClick={() => { setInitError(null); initSession(); }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 80px)" }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 0, paddingBottom: 16, borderBottom: "1px solid var(--border)", display: "flex", alignItems: "flex-start", justifyContent: "space-between" }}>
        <div>
          <h1>AI Health Chat</h1>
          <p>Ask anything about your health — your data is always in context</p>
        </div>
        <button className="btn btn-ghost" style={{ marginTop: 4 }} onClick={startNewSession}>
          + New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="chat-messages" style={{ flex: 1 }}>
        {messages.length === 0 && !typing && (
          <div className="empty-state" style={{ paddingTop: 60 }}>
            <div className="empty-icon">🫀</div>
            <h3>How can I help you today?</h3>
            <p style={{ marginTop: 8, maxWidth: 400 }}>
              Ask me about your sleep, diet, exercise, or how you&apos;re feeling. I have access to your recent health data.
            </p>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "center", marginTop: 20 }}>
              {[
                "How has my sleep been this week?",
                "Am I eating enough protein?",
                "What does my BMI indicate?",
                "I've been feeling tired — why?",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  className="btn btn-ghost"
                  style={{ fontSize: "0.82rem", padding: "8px 14px" }}
                  onClick={() => setInput(suggestion)}
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {typing && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <div className="chat-input-bar">
        <textarea
          className="chat-input"
          rows={1}
          placeholder="Ask about your health…   (Enter to send, Shift+Enter for new line)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading || !session}
          style={{ maxHeight: 120 }}
        />
        <button
          className="btn btn-primary"
          onClick={handleSend}
          disabled={!input.trim() || loading || !session}
          style={{ flexShrink: 0, alignSelf: "flex-end" }}
        >
          {loading ? <span className="spinner" style={{ width: 18, height: 18, borderWidth: 2 }} /> : "Send →"}
        </button>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}><div className="spinner" /></div>}>
      <ChatPageInner />
    </Suspense>
  );
}
