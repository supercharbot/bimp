import { createContext, useContext, useState } from 'react';

const ChatContext = createContext(null);

export function ChatProvider({ children }) {
  const [chatActive, setChatActive] = useState(false);
  return (
    <ChatContext.Provider value={{ chatActive, setChatActive }}>
      {children}
    </ChatContext.Provider>
  );
}

export const useChat = () => useContext(ChatContext);
