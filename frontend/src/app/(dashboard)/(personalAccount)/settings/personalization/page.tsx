import { redirect } from 'next/navigation';

export default async function PersonalAccountPersonalizationPage() {
  // Redirect to the main settings page where personalization is now located
  redirect('/settings');
}