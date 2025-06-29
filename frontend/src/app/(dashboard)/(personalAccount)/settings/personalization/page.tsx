import EditPersonalAccountName from '@/components/basejump/edit-personal-account-name';
import EditUserName from '@/components/basejump/edit-user-name';
import { createClient } from '@/lib/supabase/server';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

export default async function PersonalizationPage() {
  const supabaseClient = await createClient();
  const { data: personalAccount } = await supabaseClient.rpc(
    'get_personal_account',
  );
  const { data } = await supabaseClient.auth.getUser();
  const currentName = data.user?.user_metadata?.name || 'Pookie';

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-card-title">Personalization</h3>
        <p className="text-sm text-foreground/70">
          Customize your personal preferences and account details.
        </p>
      </div>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">Your Name</CardTitle>
          <CardDescription>
            Update your display name that appears throughout the application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EditUserName currentName={currentName} />
        </CardContent>
      </Card>

      <Card className="border-subtle dark:border-white/10 bg-white dark:bg-background-secondary shadow-none">
        <CardHeader>
          <CardTitle className="text-base text-card-title">Account Name</CardTitle>
          <CardDescription>
            Update your personal account name for organization purposes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <EditPersonalAccountName account={personalAccount} />
        </CardContent>
      </Card>
    </div>
  );
}