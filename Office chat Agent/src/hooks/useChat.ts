
import { useState, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  type?: string;
  file_generated?: boolean;
  filename?: string;
  download_url?: string;
}

interface ChatResponse {
  message: string;
  type: string;
  file_generated: boolean;
  filename?: string;
  download_url?: string;
  session_id: string;
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');

  const sendMessage = useCallback(async (userMessage: string) => {
    const userMsg: Message = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data: ChatResponse = await response.json();
      
      setSessionId(data.session_id);

      const assistantMsg: Message = {
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString(),
        type: data.type,
        file_generated: data.file_generated,
        filename: data.filename,
        download_url: data.download_url
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMsg: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString(),
        type: 'error'
      };

      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  const clearChat = useCallback(async () => {
    if (sessionId) {
      try {
        await fetch(`http://localhost:5000/api/chat/clear/${sessionId}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.error('Error clearing chat:', error);
      }
    }
    
    setMessages([]);
    setSessionId('');
  }, [sessionId]);

  return {
    messages,
    isLoading,
    sendMessage,
    clearChat
  };
}
