'use client';

import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import EditUserName from '@/components/basejump/edit-user-name';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuth } from '@/components/AuthProvider';
import { Skeleton } from '@/components/ui/skeleton';

type Props = {
  accountId: string;
  returnUrl: string;
};

export default function AccountPersonalization({ accountId, returnUrl }: Props) {
  const { session, isLoading: authLoading } = useAuth();
  const [currentUserName, setCurrentUserName] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchUserName() {
      if (authLoading || !session) return;

      try {
        const supabaseClient = createClient();
        const { data } = await supabaseClient.auth.getUser();
        const name = data.user?.user_metadata?.name || 'Pookie';
        setCurrentUserName(name);
        setError(null);
      } catch (err) {
        console.error('Failed to get user name:', err);
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load user data',
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchUserName();
  }, [session, authLoading]);

  if (isLoading || authLoading) {
    return (
      <div className="rounded-xl border shadow-sm bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Personalization</h2>
        <div className="space-y-4">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border shadow-sm bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Personalization</h2>
        <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-center">
          <p className="text-sm text-destructive">Error loading user data: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border shadow-sm bg-card p-6">
      <h2 className="text-xl font-semibold mb-4">Personalization</h2>

      <div className="mb-6">
        <div className="rounded-lg border bg-background p-4">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-foreground/90">
              Current Display Name
            </span>
            <span className="text-sm font-medium text-card-title">
              {currentUserName}
            </span>
          </div>
        </div>
      </div>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">Display Name</CardTitle>
          <CardDescription>
            Update your display name that appears throughout the application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EditUserName currentName={currentUserName} />
        </CardContent>
      </Card>
    </div>
  );
}