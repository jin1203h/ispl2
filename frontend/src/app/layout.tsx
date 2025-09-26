import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'ISPL 보험 정책 AI',
  description: '보험약관 기반 Agentic AI - 자연어 질의로 빠른 보험 정보 검색',
  keywords: ['보험', '약관', 'AI', '검색', '보험료', '보장'],
  authors: [{ name: 'ISPL Team' }],
  icons: {
    icon: '/favicon.ico',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className={inter.className}>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}

