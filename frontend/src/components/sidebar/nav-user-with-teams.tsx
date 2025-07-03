'use client';

import * as React from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  BadgeCheck,
  Bell,
  ChevronDown,
  ChevronsUpDown,
  Command,
  CreditCard,
  LogOut,
  Palette,
  Plus,
  Settings,
  User,
  AudioWaveform,
  Sun,
  Moon,
} from 'lucide-react';
import { useAccounts } from '@/hooks/use-accounts';
import NewTeamForm from '@/components/basejump/new-team-form';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { createClient } from '@/lib/supabase/client';
import { useTheme } from 'next-themes';

export function NavUserWithTeams({
  user,
}: {
  user: {
    name: string;
    email: string;
    avatar: string;
  };
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isMobile } = useSidebar();
  const { data: accounts } = useAccounts();
  const [showNewTeamDialog, setShowNewTeamDialog] = React.useState(false);
  const { theme, setTheme } = useTheme();

  // Prepare personal account and team accounts
  const personalAccount = React.useMemo(
    () => accounts?.find((account) => account.personal_account),
    [accounts],
  );
  const teamAccounts = React.useMemo(
    () => accounts?.filter((account) => !account.personal_account),
    [accounts],
  );

  // Create a default list of teams with logos for the UI (will show until real data loads)
  const defaultTeams = [
    {
      name: personalAccount?.name || user.name,
      logo: Command,
      plan: 'Personal',
      account_id: personalAccount?.account_id,
      slug: personalAccount?.slug,
      personal_account: true,
      email: user.email,
      avatar: user.avatar,
    },
    ...(teamAccounts?.map((team) => ({
      name: team.name,
      logo: AudioWaveform,
      plan: 'Team',
      account_id: team.account_id,
      slug: team.slug,
      personal_account: false,
      email: `Team: ${team.name}`,
      avatar: user.avatar, // Keep same avatar for teams
    })) || []),
  ];

  // Detect current team from URL
  const currentTeamFromUrl = React.useMemo(() => {
    if (!accounts) return null;
    
    // Check if we're on a team route like /team-slug/...
    const pathSegments = pathname.split('/').filter(Boolean);
    if (pathSegments.length > 0) {
      const possibleSlug = pathSegments[0];
      const teamFromUrl = accounts.find(account => 
        !account.personal_account && account.slug === possibleSlug
      );
      if (teamFromUrl) {
        return {
          name: teamFromUrl.name,
          logo: AudioWaveform,
          plan: 'Team',
          account_id: teamFromUrl.account_id,
          slug: teamFromUrl.slug,
          personal_account: false,
          email: `Team: ${teamFromUrl.name}`,
          avatar: user.avatar,
        };
      }
    }
    
    // Default to personal account
    return {
      name: personalAccount?.name || user.name,
      logo: Command,
      plan: 'Personal',
      account_id: personalAccount?.account_id,
      slug: personalAccount?.slug,
      personal_account: true,
      email: user.email,
      avatar: user.avatar,
    };
  }, [pathname, accounts, personalAccount, user]);

  // Use the detected team from URL as activeTeam
  const [activeTeam, setActiveTeam] = React.useState(currentTeamFromUrl);

  // Update active team when URL changes or accounts load
  React.useEffect(() => {
    if (currentTeamFromUrl) {
      setActiveTeam(currentTeamFromUrl);
    }
  }, [currentTeamFromUrl]);

  // Handle team selection
  const handleTeamSelect = (team) => {
    setActiveTeam(team);

    // Navigate to the appropriate dashboard
    if (team.personal_account) {
      router.push('/dashboard');
    } else {
      router.push(`/${team.slug}`);
    }
  };

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push('/auth');
  };

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((part) => part.charAt(0))
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  if (!activeTeam) {
    return null;
  }

  // Use team info for display when in team context
  const displayName = activeTeam.name;
  const displayEmail = activeTeam.email;
  const displayAvatar = activeTeam.avatar;

  return (
    <Dialog open={showNewTeamDialog} onOpenChange={setShowNewTeamDialog}>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar className="h-8 w-8 rounded-lg">
                  <AvatarImage src={displayAvatar} alt={displayName} />
                  <AvatarFallback className="rounded-lg">
                    {getInitials(displayName)}
                  </AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{displayName}</span>
                  <span className="truncate text-xs">{displayEmail}</span>
                </div>
                <ChevronsUpDown className="ml-auto size-4" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
              side={isMobile ? 'bottom' : 'top'}
              align="start"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage src={displayAvatar} alt={displayName} />
                    <AvatarFallback className="rounded-lg">
                      {getInitials(displayName)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{displayName}</span>
                    <span className="truncate text-xs">{displayEmail}</span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />

              {/* Teams Section */}
              {personalAccount && (
                <>
                  <DropdownMenuLabel className="text-muted-foreground text-xs">
                    Personal Account
                  </DropdownMenuLabel>
                  <DropdownMenuItem
                    key={personalAccount.account_id}
                    onClick={() =>
                      handleTeamSelect({
                        name: personalAccount.name,
                        logo: Command,
                        plan: 'Personal',
                        account_id: personalAccount.account_id,
                        slug: personalAccount.slug,
                        personal_account: true,
                        email: user.email,
                        avatar: user.avatar,
                      })
                    }
                    className="gap-2 p-2"
                  >
                    <div className="flex size-6 items-center justify-center rounded-xs border">
                      <Command className="size-4 shrink-0" />
                    </div>
                    {personalAccount.name}
                    <DropdownMenuShortcut>⌘1</DropdownMenuShortcut>
                  </DropdownMenuItem>
                </>
              )}

              {teamAccounts?.length > 0 && (
                <>
                  <DropdownMenuLabel className="text-muted-foreground text-xs mt-2">
                    Teams
                  </DropdownMenuLabel>
                  {teamAccounts.map((team, index) => (
                    <DropdownMenuItem
                      key={team.account_id}
                      onClick={() =>
                        handleTeamSelect({
                          name: team.name,
                          logo: AudioWaveform,
                          plan: 'Team',
                          account_id: team.account_id,
                          slug: team.slug,
                          personal_account: false,
                          email: `Team: ${team.name}`,
                          avatar: user.avatar,
                        })
                      }
                      className="gap-2 p-2"
                    >
                      <div className="flex size-6 items-center justify-center rounded-xs border">
                        <AudioWaveform className="size-4 shrink-0" />
                      </div>
                      {team.name}
                      <DropdownMenuShortcut>⌘{index + 2}</DropdownMenuShortcut>
                    </DropdownMenuItem>
                  ))}
                </>
              )}

              <DropdownMenuSeparator />
              <DialogTrigger asChild>
                <DropdownMenuItem
                  className="gap-2 p-2"
                  onClick={() => {
                    setShowNewTeamDialog(true);
                  }}
                >
                  <div className="bg-background flex size-6 items-center justify-center rounded-md border">
                    <Plus className="size-4" />
                  </div>
                  <div className="text-muted-foreground font-medium">
                    Add team
                  </div>
                </DropdownMenuItem>
              </DialogTrigger>
              <DropdownMenuSeparator />

              {/* User Settings Section */}
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <Link href="/settings/billing">
                    <CreditCard className="h-4 w-4" />
                    Billing
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/settings/personalization">
                    <Palette className="h-4 w-4" />
                    Personalization
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
                >
                  <div className="flex items-center gap-2">
                    <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                    <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                    <span>Theme</span>
                  </div>
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive focus:bg-destructive/10"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4 text-destructive" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>

      <DialogContent className="sm:max-w-[425px] border bg-background rounded-2xl shadow-lg">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            Create a new team
          </DialogTitle>
          <DialogDescription className="text-foreground/70">
            Create a team to collaborate with others.
          </DialogDescription>
        </DialogHeader>
        <NewTeamForm />
      </DialogContent>
    </Dialog>
  );
}
