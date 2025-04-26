
import React, { useState } from "react";
import { SendIcon } from "lucide-react";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage }) => {
  const [messageText, setMessageText] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (messageText.trim() === "") return;
    
    onSendMessage(messageText);
    setMessageText("");
  };

  return (
    <form 
      onSubmit={handleSubmit}
      className="border-t border-gray-200 bg-white p-4"
    >
      <div className="relative flex items-center">
        <input
          type="text"
          placeholder="Type a message..."
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          className="flex-1 border border-gray-300 rounded-full py-2 px-4 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <button
          type="submit"
          className="absolute right-2 p-1 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors"
          disabled={messageText.trim() === ""}
        >
          <SendIcon size={18} />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
