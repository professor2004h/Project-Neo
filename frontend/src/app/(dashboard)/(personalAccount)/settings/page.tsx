import { redirect } from 'next/navigation';

export default async function PersonalAccountSettingsPage() {
  // Redirect to personalization as the default settings page
  redirect('/settings/personalization');
}
