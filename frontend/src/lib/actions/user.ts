'use server';

import { createClient } from '../supabase/server';

export async function editUserName(prevState: any, formData: FormData) {
  const name = formData.get('name') as string;
  const supabase = await createClient();

  const { error } = await supabase.auth.updateUser({
    data: { name },
  });

  if (error) {
    return { message: error.message };
  }
}
