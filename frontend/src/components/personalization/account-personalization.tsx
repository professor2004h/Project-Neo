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

  const fetchUserName = async () => {
    if (authLoading || !session) return;

    try {
      setIsLoading(true);
      const supabaseClient = createClient();
      const { data } = await supabaseClient.auth.getUser();
      const name = data.user?.user_metadata?.name || '';
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
  };

  useEffect(() => {
    fetchUserName();
  }, [session, authLoading]);

  // Function to refresh user data after update
  const handleNameUpdate = () => {
    fetchUserName();
  };

  if (isLoading || authLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-card-title">Personalization</h3>
          <p className="text-sm text-foreground/70">
            Manage your personal profile information and preferences.
          </p>
        </div>
        <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
          <CardHeader>
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-24" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h3 className="text-lg font-medium text-card-title">Personalization</h3>
          <p className="text-sm text-foreground/70">
            Manage your personal profile information and preferences.
          </p>
        </div>
        <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
          <CardContent className="pt-6">
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-center">
              <p className="text-sm text-destructive">Error loading user data: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-card-title">Personalization</h3>
        <p className="text-sm text-foreground/70">
          Manage your personal profile information and preferences.
        </p>
      </div>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">Display Name</CardTitle>
          <CardDescription>
            Update your display name that appears throughout the application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EditUserName currentName={currentUserName} onUpdate={handleNameUpdate} />
        </CardContent>
      </Card>
    </div>
  );
}