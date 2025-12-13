import { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import { chatService } from '@/services/chatService';
import toast from 'react-hot-toast';

export default function ChatWindow() {
    const [messages, setMessages] = useState([]);
    const [sessionId, setSessionId] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentBotMessage, setCurrentBotMessage] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, currentBotMessage]);

    const handleSendMessage = async (message) => {
        if (!message.trim()) return;

        const userMessage = {
            id: Date.now(),
            role: 'user',
            content: message,
            timestamp: new Date().toISOString(),
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        setCurrentBotMessage('');

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Giữ lại phần chưa hoàn chỉnh
                
                for (const line of lines) {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            
                            if (data.status === 'streaming' && data.chunk) {
                                setCurrentBotMessage(prev => prev + data.chunk);
                            } 
                            else if (data.status === 'completed' && data.session_id) {
                                // Tạo tin nhắn hoàn chỉnh từ bot
                                const botMessage = {
                                    id: Date.now() + 1,
                                    role: 'assistant',
                                    content: data.message,
                                    timestamp: new Date().toISOString(),
                                };
                                
                                setMessages(prev => [...prev, botMessage]);
                                setCurrentBotMessage('');
                                
                                // Cập nhật session ID nếu cần
                                if (!sessionId && data.session_id) {
                                    setSessionId(data.session_id);
                                }
                            }
                            else if (data.status === 'error') {
                                toast.error('Có lỗi xảy ra: ' + data.message);
                                setCurrentBotMessage('');
                            }
                        } catch (e) {
                            console.error('Error parsing stream data:', e);
                        }
                    }
                }
            }
            
        } catch (error) {
            toast.error('Có lỗi xảy ra khi gửi tin nhắn');
            console.error('[ChatWindow] Lỗi chi tiết:', error);
            setCurrentBotMessage('');
        } finally {
            setIsLoading(false);
        }
    };

    const startNewChat = () => {
        setMessages([]);
        setSessionId(null);
        setCurrentBotMessage('');
    };

    // Render tin nhắn tạm thời từ bot
    const allMessages = [...messages];
    if (currentBotMessage) {
        allMessages.push({
            id: 'temp-bot',
            role: 'assistant',
            content: currentBotMessage,
            timestamp: new Date().toISOString(),
            isTemporary: true
        });
    }

    return (
        <div className="flex flex-col h-[calc(100vh-300px)]">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold">Chat về Lịch sử Việt Nam</h2>
                <button
                    onClick={startNewChat}
                    className="btn-secondary text-sm"
                >
                    Cuộc trò chuyện mới
                </button>
            </div>

            <div className="flex-grow overflow-y-auto mb-4 border border-gray-200 rounded-lg p-4 bg-gray-50">
                <MessageList messages={allMessages} isLoading={isLoading} />
                <div ref={messagesEndRef} />
            </div>

            <MessageInput onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>
    );
}