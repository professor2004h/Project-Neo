import { isFlagEnabled } from '@/lib/feature-flags';
import { Metadata } from 'next';
import { redirect } from 'next/navigation';

export const metadata: Metadata = {
  title: 'Agent Marketplace | Operator by OMNI',
  description: 'Browse and share agents on the Operator marketplace',
  openGraph: {
    title: 'Agent Marketplace | Operator by OMNI',
    description: 'Discover and add powerful AI agents created by the community to your personal library',
    type: 'website',
  },
};

export default async function MarketplaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const marketplaceEnabled = await isFlagEnabled('agent_marketplace');
  if (!marketplaceEnabled) {
    redirect('/dashboard');
  }
  return <>{children}</>;
}
