"use client";


import { useState } from "react";

type Message = {
  role: "user" | "assistant";
  content: string;
};

const URL = "http://localhost:3000";


const generateTimeBasedId = (): string => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 6);
  return `conv_${timestamp}_${random}`;
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: "Hola! Como puedo ayudarte hoy?" },
  ]);
  const [sources, setSources] = useState<
    { title: string; company: string; location: string; description: string; id: string }[]
  >([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSend = async () => {
    if (!message.trim()) return;

    // Add user message to the conversation
    const userMessage = { role: "user" as const, content: message };
    setMessages(prev => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);

    try {

      const response = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: message }),
      });

      const data = await response.json();
      console.log("Respuesta del backend:", data);

      if (data.error) {
        const aiMessage = { role: "assistant" as const, content: data.error };
        setMessages(prev => [...prev, aiMessage]);
        return;
      }

      const aiMessage = {
        role: "assistant" as const,
        content: data.answer || "No se pudo generar respuesta",
      };

      setMessages(prev => [...prev, aiMessage]);
      setSources(data.sources ?? []);

    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleShare = async () => {


    const id = generateTimeBasedId();
    console.log("id", id);

    try {
      const response = await fetch(`/api/history`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ id, messages }),
      });
      const data = await response.json();


      setIsModalOpen(true);

      console.log("data", data);
    } catch (error) {
      console.error("Error:", error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      <div className="w-full bg-gray-100 border-b border-gray-400 p-4">
        <div className="flex justify-between items-center max-w-3xl mx-auto">
          <h1 className="text-xl text-black">Jobby</h1>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pb-32 pt-4">
        <div className="max-w-3xl mx-auto px-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-2 mb-4 ${
                msg.role === "assistant"
                  ? "justify-start"
                  : "justify-end flex-row-reverse"
              }`}
            >
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                {msg.role !== "assistant" ? (
                  <svg
                    className="w-5 h-5"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M12 0C13.1 0 14 0.9 14 2V3H20C21.1 3 22 3.9 22 5V19C22 20.1 21.1 21 20 21H4C2.9 21 2 20.1 2 19V5C2 3.9 2.9 3 4 3H10V2C10 0.9 10.9 0 12 0ZM4 5V19H20V5H4Z"
                    />
                  </svg>
                ) : (
                  <svg
                    className="w-5 h-5"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      clipRule="evenodd"
                      d="M12 0C13.1 0 14 0.9 14 2V3H20C21.1 3 22 3.9 22 5V19C22 20.1 21.1 21 20 21H4C2.9 21 2 20.1 2 19V5C2 3.9 2.9 3 4 3H10V2C10 0.9 10.9 0 12 0ZM4 5V19H20V5H4Z"
                    />
                  </svg>
                )}
              </div>
              <div
                className={`px-4 py-2 rounded-2xl max-w-[80%] ${
                  msg.role === "assistant"
                    ? "bg-blue-200 text-black"
                    : "bg-blue-500 text-white ml-auto"
                }`}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {/* Empleos sugeridos */}
          {sources.length > 0 && (
            <div className="mt-4">
              <h3 className="text-gray-700 mb-2">🔎 Empleos sugeridos:</h3>
              <div className="grid gap-3">
                {sources.map((job, i) => (
                  <div key={i} className="p-4 border rounded-xl bg-gray-50">
                    <h4 className="font-bold text-blue-700">{job.title}</h4>
                    <p className="text-sm text-gray-800">🏢 {job.company}</p>
                    <p className="text-sm text-gray-600">📍 {job.location}</p>
                    <p className="text-sm text-gray-700 mt-2">📝 {job.description}</p>
                    <a
                      className="text-blue-500 text-sm underline mt-1 inline-block"
                      href={`https://pucp-csm.symplicity.com/students/app/jobs/detail/${job.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Ver oferta ↗
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isLoading && (
            <div className="flex gap-4 mb-4">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                <svg
                  className="w-5 h-5"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 0C13.1 0 14 0.9 14 2V3H20C21.1 3 22 3.9 22 5V19C22 20.1 21.1 21 20 21H4C2.9 21 2 20.1 2 19V5C2 3.9 2.9 3 4 3H10V2C10 0.9 10.9 0 12 0ZM4 5V19H20V5H4Z"
                  />
                </svg>
              </div>
              <div className="px-4 py-2 rounded-2xl bg-blue-500 border border-gray-700 text-gray-100">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2 h-2 bg-white rounded-full animate-bounce" />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="fixed bottom-0 w-full bg-gray-100 border-t border-gray-500 p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-center">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type your message..."
              className="flex-1 rounded-xl border border-blue-700 bg-white px-4 py-3 text-black focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent placeholder-gray-400"
            />
            <button
              onClick={handleSend}
              disabled={isLoading}
              className="bg-blue-500 text-white px-5 py-3 rounded-xl hover:bg-cyan-700 transition-all disabled:bg-cyan-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? "Sending..." : "Send"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}