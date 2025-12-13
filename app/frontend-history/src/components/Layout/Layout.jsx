import Header from './Header';
import { Toaster } from 'react-hot-toast';

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8">
        {children}
      </main>
      <Toaster position="top-right" />
      <footer className="bg-gray-800 text-white py-4">
        <div className="container mx-auto px-4 text-center">
          <p>History Chat & Quiz Server - Dự án bài tập lớn</p>
        </div>
      </footer>
    </div>
  );
}