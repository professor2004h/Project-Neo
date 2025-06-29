import EditPersonalAccountName from '@/components/basejump/edit-personal-account-name';
import EditUserName from '@/components/basejump/edit-user-name';
import { createClient } from '@/lib/supabase/server';

export default async function PersonalAccountSettingsPage() {
  const supabaseClient = await createClient();
  const { data: personalAccount } = await supabaseClient.rpc(
    'get_personal_account',
  );
  const { data } = await supabaseClient.auth.getUser();
  const currentName = data.user?.user_metadata?.name || 'Pookie';

  return (
    <div className="space-y-6">
      <EditUserName currentName={currentName} />
      <EditPersonalAccountName account={personalAccount} />
    </div>
  );
}
