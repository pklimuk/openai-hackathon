import React, { useState, useRef, useEffect } from "react";
import { Message as MessageType } from "../types/types";
import Message from "./Message";
import ChatInput from "./ChatInput";
import { generateId } from "../utils/chatUtils";

interface ChatInterfaceProps {
  onSendQuestion: (text: string) => void;
  lessonStarted: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSendQuestion, lessonStarted }) => {
  const [messages, setMessages] = useState<MessageType[]>([
    {
      id: generateId(),
      text: "The topic of today's lesson is the relativity theory. Are you ready to start?",
      sender: "Albert Einstein",
      timestamp: new Date(),
      isUser: false,
    },
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSendMessage = async (text: string) => {
    const newMessage: MessageType = {
      id: generateId(),
      text,
      sender: "You",
      timestamp: new Date(),
      isUser: true,
    };
    setMessages((prevMessages) => [...prevMessages, newMessage]);
    onSendQuestion(text);
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full bg-white rounded-r-lg shadow-lg">
      <div className="bg-blue-600 text-white p-3 rounded-tr-lg">
        <h2 className="font-semibold">Chat</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {messages.map((msg) => (
          <Message key={msg.id} message={msg} />
        ))}
        {!lessonStarted && (
          <div className="text-center text-gray-500 mt-4">
            Type <span className="font-bold">Yes</span> to start the lesson.
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <ChatInput onSendMessage={handleSendMessage} />
    </div>
  );
};

export default ChatInterface;
