import { MessageCircle, Settings, MoreVertical, Sun, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { useTheme } from '@/contexts/ThemeContext';

interface ChatHeaderProps {
  onClearChat: () => void;
}

const ChatHeader = ({ onClearChat }: ChatHeaderProps) => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <div className="bg-gradient-to-r from-blue-600 to-blue-700 dark:from-gray-800 dark:to-gray-900 text-white p-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 dark:bg-white/10 rounded-full flex items-center justify-center">
            <MessageCircle size={20} />
          </div>
          <div>
            <h1 className="font-semibold text-lg">Office Management Assistant</h1>
            <p className="text-blue-100 dark:text-gray-300 text-sm">AI-powered HR & Employee Support</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-2 mr-2">
            <Sun size={16} className={`transition-opacity ${isDark ? 'opacity-50' : 'opacity-100'}`} />
            <Switch
              checked={isDark}
              onCheckedChange={toggleTheme}
              className="data-[state=checked]:bg-gray-600 data-[state=unchecked]:bg-blue-300"
            />
            <Moon size={16} className={`transition-opacity ${isDark ? 'opacity-100' : 'opacity-50'}`} />
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearChat}
            className="text-white hover:bg-white/20 dark:hover:bg-white/10"
          >
            Clear Chat
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20 dark:hover:bg-white/10"
          >
            <Settings size={18} />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-white hover:bg-white/20 dark:hover:bg-white/10"
          >
            <MoreVertical size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;