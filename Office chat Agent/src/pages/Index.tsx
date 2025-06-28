
import { useEffect, useRef } from 'react';
import ChatHeader from '@/components/ChatHeader';
import ChatMessage from '@/components/ChatMessage';
import TypingIndicator from '@/components/TypingIndicator';
import ChatInput from '@/components/ChatInput';
import { useChat } from '@/hooks/useChat';

const Index = () => {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = (message: string) => {
    sendMessage(message);
  };

  const handleClearChat = () => {
    clearChat();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <ChatHeader onClearChat={handleClearChat} />
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <div className="w-8 h-8 bg-blue-500 rounded-full" />
            </div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">
              Welcome to Office Management Assistant
            </h2>
            <p className="text-gray-600 mb-6 max-w-md mx-auto">
              I can help you with employee information, generate salary slips, and answer 
              questions about your office operations.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              <div 
                className="p-4 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSendMessage("Generate salary slip for LWE103")}
              >
                <h3 className="font-medium text-gray-800 mb-1">Generate Salary Slip</h3>
                <p className="text-sm text-gray-600">Create PDF salary slips for employees</p>
              </div>
              <div 
                className="p-4 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSendMessage("Show me employee details")}
              >
                <h3 className="font-medium text-gray-800 mb-1">Employee Information</h3>
                <p className="text-sm text-gray-600">Get details about employees and departments</p>
              </div>
              <div 
                className="p-4 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSendMessage("What's the average salary in IT department?")}
              >
                <h3 className="font-medium text-gray-800 mb-1">Salary Queries</h3>
                <p className="text-sm text-gray-600">Ask about salaries and compensation</p>
              </div>
              <div 
                className="p-4 bg-white rounded-lg border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
                onClick={() => handleSendMessage("How can you help me?")}
              >
                <h3 className="font-medium text-gray-800 mb-1">General Help</h3>
                <p className="text-sm text-gray-600">Learn about my capabilities</p>
              </div>
            </div>
          </div>
        )}
        
        {messages.map((message, index) => (
          <ChatMessage 
            key={index} 
            message={message} 
            isLatest={index === messages.length - 1}
          />
        ))}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  );
};

export default Index;
