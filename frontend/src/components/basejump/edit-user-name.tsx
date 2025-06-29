'use client';

import { Input } from '@/components/ui/input';
import { SubmitButton } from '../ui/submit-button';
import { Label } from '../ui/label';
import { editUserName } from '@/lib/actions/user';

type Props = {
  currentName: string;
};

export default function EditUserName({ currentName }: Props) {
  return (
    <form className="animate-in space-y-4">
      <div className="flex flex-col gap-y-2">
        <Label
          htmlFor="name"
          className="text-sm font-medium text-foreground/90"
        >
          Your Name
        </Label>
        <Input
          defaultValue={currentName}
          name="name"
          id="name"
          placeholder="Pookie"
          required
          className="h-10 rounded-lg border-subtle dark:border-white/10 bg-white dark:bg-background-secondary"
        />
      </div>
      <div className="flex justify-end">
        <SubmitButton
          formAction={editUserName}
          pendingText="Updating..."
          className="rounded-lg bg-primary hover:bg-primary/90 text-white h-10"
        >
          Save Changes
        </SubmitButton>
      </div>
    </form>
  );
}
