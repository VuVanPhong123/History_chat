import ChatWindow from '@/components/Chat/ChatWindow';

export default function HomePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Chat với AI về Lịch sử Việt Nam</h1>
      <ChatWindow />
    </div>
  );
}