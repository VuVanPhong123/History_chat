import { useState } from 'react';

export default function MessageInput({ onSendMessage, disabled }) {
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Nhập câu hỏi về lịch sử Việt Nam..."
        className="input-field flex-grow"
        disabled={disabled}
      />
      <button
        type="submit"
        className="btn-primary whitespace-nowrap"
        disabled={disabled || !message.trim()}
      >
        {disabled ? 'Đang gửi...' : 'Gửi'}
      </button>
    </form>
  );
}