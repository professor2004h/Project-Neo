'use client';

import { useMemo } from 'react';
import { usePathname } from 'next/navigation';
import { useAccounts } from './use-accounts';

export interface CurrentAccount {
  account_id: string;
  name: string;
  personal_account: boolean;
  slug?: string;
  is_team_context: boolean;
}

/**
 * Hook to determine the current account context based on URL path
 * Returns the appropriate account_id for API calls
 */
export function useCurrentAccount(): CurrentAccount | null {
  const pathname = usePathname();
  const { data: accounts } = useAccounts();

  return useMemo(() => {
    if (!accounts) return null;

    // Extract team slug from URL path - match any team route
    const teamMatch = pathname?.match(/^\/([^\/]+)(?:\/|$)/);
    const teamSlug = teamMatch?.[1];

    // Skip if it's a known non-team route
    const nonTeamRoutes = ['dashboard', 'agents', 'projects', 'settings', 'marketplace', 'meetings', 'api', 'auth', 'legal', 'share', 'invitation', 'monitoring'];
    if (!teamSlug || nonTeamRoutes.includes(teamSlug)) {
      // Default to personal account for non-team routes
      const personalAccount = accounts.find((account) => account.personal_account);
      
      if (personalAccount) {
        return {
          account_id: personalAccount.account_id,
          name: personalAccount.name,
          personal_account: true,
          slug: personalAccount.slug,
          is_team_context: false,
        };
      }
      return null;
    }

    // Check if this slug matches a team account
    const teamAccount = accounts.find(
      (account) => !account.personal_account && account.slug === teamSlug
    );
    
    if (teamAccount) {
      return {
        account_id: teamAccount.account_id,
        name: teamAccount.name,
        personal_account: false,
        slug: teamAccount.slug,
        is_team_context: true,
      };
    }

    // If no team found, default to personal account
    const personalAccount = accounts.find((account) => account.personal_account);
    
    if (personalAccount) {
      return {
        account_id: personalAccount.account_id,
        name: personalAccount.name,
        personal_account: true,
        slug: personalAccount.slug,
        is_team_context: false,
      };
    }

    return null;
  }, [pathname, accounts]);
} 