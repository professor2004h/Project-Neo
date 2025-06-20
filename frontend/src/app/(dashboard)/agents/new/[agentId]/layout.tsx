import { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { isFlagEnabled } from '@/lib/feature-flags';

export const metadata: Metadata = {
  title: 'Create Agent | Operator by OMNI',
  description: 'Interactive agent playground powered by Operator by OMNI',
  openGraph: {
    title: 'Agent Playground | Operator by OMNI',
    description: 'Interactive agent playground powered by Operator by OMNI',
    type: 'website',
  },
};

export default async function NewAgentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const agentPlaygroundEnabled = await isFlagEnabled('custom_agents');
  if (!agentPlaygroundEnabled) {
    redirect('/dashboard');
  }
  return <>{children}</>;
}
