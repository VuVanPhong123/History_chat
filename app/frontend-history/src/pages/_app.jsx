import Layout from '@/components/Layout/Layout';
import '@/styles/globals.css';
import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { authService } from '@/services/authService';

function MyApp({ Component, pageProps }) {
  const router = useRouter();

  useEffect(() => {
    const checkAuth = () => {
      if (router.pathname === '/settings' && !authService.isAuthenticated()) {
        if (typeof window !== 'undefined') {
          router.reload();
        }
      }
    };

    const interval = setInterval(checkAuth, 60000); // 1 phút
    return () => clearInterval(interval);
  }, [router]);

  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}

export default MyApp;