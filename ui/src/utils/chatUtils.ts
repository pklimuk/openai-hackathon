
import { Message } from "../types/types";

export const formatTimestamp = (date: Date): string => {
  const hours = date.getHours();
  const minutes = date.getMinutes();
  const formattedMinutes = minutes < 10 ? `0${minutes}` : minutes;
  return `${hours}:${formattedMinutes}`;
};

export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 11);
};

export const simulateSendToServer = (message: Message): Promise<void> => {
  // This function simulates sending a message to a server
  // In a real app, this would make an API call
  console.log("Sending message to server:", message);
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve();
    }, 500);
  });
};
