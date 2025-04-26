
import React from "react";
import { Message as MessageType } from "../types/types";
import { formatTimestamp } from "../utils/chatUtils";

interface MessageProps {
  message: MessageType;
}

const Message: React.FC<MessageProps> = ({ message }) => {
  return (
    <div
      className={`flex mb-3 ${message.isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`px-4 py-2 rounded-lg max-w-[85%] ${
          message.isUser
            ? "bg-blue-600 text-white rounded-br-none"
            : "bg-gray-100 text-gray-800 rounded-bl-none"
        }`}
      >
        <div className="flex justify-between items-baseline mb-1">
          <span className="font-medium text-sm">
            {message.isUser ? "You" : message.sender}
          </span>
          <span className="text-xs ml-2 opacity-75">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>
        <p className="text-sm">{message.text}</p>
      </div>
    </div>
  );
};

export default Message;
