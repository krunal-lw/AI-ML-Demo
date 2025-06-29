import { useState, useEffect } from 'react';
import { Download, Bot, User } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ChatMessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    type?: string;
    file_generated?: boolean;
    filename?: string;
    download_url?: string;
  };
  isLatest?: boolean;
}

const ChatMessage = ({ message, isLatest = false }: ChatMessageProps) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const isBot = message.role === 'assistant';
  
  useEffect(() => {
    if (isBot && isLatest) {
      setIsTyping(true);
      setDisplayedText('');
      
      let index = 0;
      const text = message.content;
      
      const typeWriter = setInterval(() => {
        if (index < text.length) {
          setDisplayedText(text.slice(0, index + 1));
          index++;
        } else {
          setIsTyping(false);
          clearInterval(typeWriter);
        }
      }, 30);
      
      return () => clearInterval(typeWriter);
    } else {
      setDisplayedText(message.content);
      setIsTyping(false);
    }
  }, [message.content, isBot, isLatest]);

  const handleDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(`http://localhost:5000${url}`);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-4 animate-fade-in`}>
      <div className={`max-w-[70%] ${isBot ? 'order-2' : 'order-1'}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isBot
              ? 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200'
              : 'bg-blue-500 dark:bg-blue-600 text-white'
          } shadow-sm`}
        >
          <div className="flex items-start gap-2">
            {isBot && (
              <div className="flex-shrink-0 mt-1">
                <Bot size={16} className="text-blue-500 dark:text-blue-400" />
              </div>
            )}
            <div className="flex-1">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {displayedText}
                {isTyping && (
                  <span className="inline-block w-2 h-4 bg-gray-400 dark:bg-gray-500 ml-1 animate-pulse" />
                )}
              </p>
              
              {message.file_generated && message.download_url && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                  <Button
                    onClick={() => handleDownload(message.download_url!, message.filename!)}
                    size="sm"
                    className="flex items-center gap-2 bg-green-500 hover:bg-green-600 dark:bg-green-600 dark:hover:bg-green-700"
                  >
                    <Download size={14} />
                    Download {message.filename}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className={`text-xs text-gray-500 dark:text-gray-400 mt-1 ${isBot ? 'text-left' : 'text-right'}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
      
      {!isBot && (
        <div className="flex-shrink-0 ml-2 order-2">
          <div className="w-8 h-8 bg-blue-500 dark:bg-blue-600 rounded-full flex items-center justify-center">
            <User size={16} className="text-white" />
          </div>
        </div>
      )}
      
      {isBot && (
        <div className="flex-shrink-0 mr-2 order-1">
          <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-blue-500 dark:text-blue-400" />
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;