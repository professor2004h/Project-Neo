import { agentPlaygroundFlagFrontend } from '@/flags';
import { isFlagEnabled } from '@/lib/feature-flags';
import { Metadata } from 'next';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Agent Conversation | Leaker-Flow',
  description: 'Interactive agent conversation powered by Leaker-Flow',
  openGraph: {
    title: 'Agent Conversation | Leaker-Flow',
    description: 'Interactive agent conversation powered by Leaker-Flow',
    type: 'website',
  },
};

export default async function AgentsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
