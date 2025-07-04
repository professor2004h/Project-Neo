'use client';

import React, { useState, Suspense, useEffect, useRef } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { useRouter, useSearchParams } from 'next/navigation';
import { Menu, Check } from 'lucide-react';
import {
  ChatInput,
  ChatInputHandles,
} from '@/components/thread/chat-input/chat-input';
import { BillingError } from '@/lib/api';
import { useIsMobile } from '@/hooks/use-mobile';
import { useSidebar } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useBillingError } from '@/hooks/useBillingError';
import { BillingErrorAlert } from '@/components/billing/usage-limit-alert';
import { useAccounts } from '@/hooks/use-accounts';
import { config } from '@/lib/config';
import { useInitiateAgentWithInvalidation } from '@/hooks/react-query/dashboard/use-initiate-agent';
import { ModalProviders } from '@/providers/modal-providers';
import { AgentSelector } from '@/components/dashboard/agent-selector';
import { cn } from '@/lib/utils';
import { useModal } from '@/hooks/use-modal-store';
import { Examples } from './suggestions/examples';
import { useThreadQuery } from '@/hooks/react-query/threads/use-threads';
import { normalizeFilenameToNFC } from '@/lib/utils/unicode';
import { toast } from 'sonner';
import { createClient } from '@/lib/supabase/client';
import { TypingText } from '@/components/animate-ui/text/typing';
import { GradientText } from '@/components/animate-ui/text/gradient';
import { useAgents } from '@/hooks/react-query/agents/use-agents';

const PENDING_PROMPT_KEY = 'pendingAgentPrompt';

export function DashboardContent() {
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [autoSubmit, setAutoSubmit] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const [nameInput, setNameInput] = useState('');
  const [isNameFocused, setIsNameFocused] = useState(false);
  const [isLoadingUserName, setIsLoadingUserName] = useState(true);
  const [selectedAgentId, setSelectedAgentId] = useState<string | undefined>();
  const [initiatedThreadId, setInitiatedThreadId] = useState<string | null>(
    null,
  );
  const { billingError, handleBillingError, clearBillingError } =
    useBillingError();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isMobile = useIsMobile();
  const { setOpenMobile } = useSidebar();
  const { data: accounts } = useAccounts();
  const personalAccount = accounts?.find((account) => account.personal_account);
  const chatInputRef = useRef<ChatInputHandles>(null);
  const initiateAgentMutation = useInitiateAgentWithInvalidation();
  const { onOpen } = useModal();

  const threadQuery = useThreadQuery(initiatedThreadId || '');
  
  // Get agents to access selected agent's name
  const { data: agentsResponse } = useAgents({
    limit: 100,
    sort_by: 'name',
    sort_order: 'asc'
  });
  
  const agents = agentsResponse?.agents || [];
  const selectedAgent = agents?.find(a => a.agent_id === selectedAgentId);
  const defaultAgent = agents?.find(a => a.is_default);
  
  // Set default agent if no agent is selected
  useEffect(() => {
    if (!selectedAgentId && defaultAgent && agents.length > 0) {
      setSelectedAgentId(defaultAgent.agent_id);
    }
  }, [selectedAgentId, defaultAgent, agents.length]);

  // Load user name from Supabase auth and listen for changes
  useEffect(() => {
    const supabase = createClient();
    
    const loadUserName = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        const name = user?.user_metadata?.name;
        if (name) {
          setUserName(name);
          setNameInput(name);
        }
      } catch (error) {
        console.error('Error loading user name:', error);
      } finally {
        setIsLoadingUserName(false);
      }
    };

    // Load initial user name
    loadUserName();

    // Listen for auth state changes (including user metadata updates)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (event === 'USER_UPDATED' || event === 'SIGNED_IN') {
          const name = session?.user?.user_metadata?.name;
          if (name) {
            setUserName(name);
            setNameInput(name);
          }
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    const agentIdFromUrl = searchParams.get('agent_id');
    if (agentIdFromUrl && agentIdFromUrl !== selectedAgentId) {
      setSelectedAgentId(agentIdFromUrl);
      const newUrl = new URL(window.location.href);
      newUrl.searchParams.delete('agent_id');
      router.replace(newUrl.pathname + newUrl.search, { scroll: false });
    }
  }, [searchParams, selectedAgentId, router]);

  // Handle meeting attachment
  useEffect(() => {
    const attachMeetingId = searchParams.get('attachMeeting');
    if (attachMeetingId) {
      // Load meeting transcript and attach it as a file
      import('@/lib/api-meetings').then(async ({ getMeeting }) => {
        try {
          const meeting = await getMeeting(attachMeetingId);
          if (meeting.transcript) {
            // Format transcript with enhanced metadata header
            const createdAt = new Date(meeting.created_at);
            const now = new Date();
            const formattedTranscript = `Meeting Transcript

MEETING INFORMATION:
- Title: ${meeting.title}
- Meeting Created: ${createdAt.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })} at ${createdAt.toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
            })}
- File Generated: ${now.toLocaleDateString('en-US', {
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })} at ${now.toLocaleTimeString('en-US', {
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
            })}

FULL TRANSCRIPT:
${meeting.transcript || '(No transcript available)'}`;

            console.log(
              'Formatted transcript for operator:',
              formattedTranscript.substring(0, 500) + '...',
            );

            // Create a file from the formatted transcript
            const blob = new Blob([formattedTranscript], {
              type: 'text/plain',
            });
            const file = new File([blob], `${meeting.title}_transcript.txt`, {
              type: 'text/plain',
            });

            // Add file to chat input
            if (chatInputRef.current) {
              chatInputRef.current.addExternalFile(file);
            }

            // Set initial prompt
            setInputValue(
              `I have a meeting transcript from "${meeting.title}". Please help me analyze it.`,
            );

            // Remove the query parameter
            const newUrl = new URL(window.location.href);
            newUrl.searchParams.delete('attachMeeting');
            router.replace(newUrl.pathname + newUrl.search, { scroll: false });
          }
        } catch (error) {
          console.error('Error loading meeting:', error);
        }
      });
    }
  }, [searchParams, router]);

  useEffect(() => {
    if (threadQuery.data && initiatedThreadId) {
      const thread = threadQuery.data;
      console.log('Thread data received:', thread);
      if (thread.project_id) {
        router.push(
          `/projects/${thread.project_id}/thread/${initiatedThreadId}`,
        );
      } else {
        router.push(`/agents/${initiatedThreadId}`);
      }
      setInitiatedThreadId(null);
    }
  }, [threadQuery.data, initiatedThreadId, router]);

  const secondaryGradient =
    'bg-gradient-to-r from-blue-500 to-blue-500 bg-clip-text text-transparent';

  const handleSaveName = async () => {
    const trimmed = nameInput.trim();
    if (!trimmed) return;
    
    try {
      const supabase = createClient();
      const { error } = await supabase.auth.updateUser({
        data: { name: trimmed },
      });

      if (error) {
        toast.error('Failed to save name: ' + error.message);
        return;
      }

      setUserName(trimmed);
      setIsNameFocused(false);
      toast.success(`Nice to meet you, ${trimmed}! 🎉`);
    } catch (error) {
      toast.error('Failed to save name');
      console.error('Error saving name:', error);
    }
  };

  const handleNameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSaveName();
    }
    if (e.key === 'Escape') {
      setIsNameFocused(false);
      setNameInput('');
    }
  };

  const handleSubmit = async (
    message: string,
    options?: {
      model_name?: string;
      enable_thinking?: boolean;
      reasoning_effort?: string;
      stream?: boolean;
      enable_context_manager?: boolean;
    },
  ) => {
    if (
      (!message.trim() && !chatInputRef.current?.getPendingFiles().length) ||
      isSubmitting
    )
      return;

    setIsSubmitting(true);

    try {
      const files = chatInputRef.current?.getPendingFiles() || [];
      localStorage.removeItem(PENDING_PROMPT_KEY);

      const formData = new FormData();
      formData.append('prompt', message);

      // Add selected agent if one is chosen
      if (selectedAgentId) {
        formData.append('agent_id', selectedAgentId);
      }

      files.forEach((file, index) => {
        const normalizedName = normalizeFilenameToNFC(file.name);
        formData.append('files', file, normalizedName);
      });

      if (options?.model_name)
        formData.append('model_name', options.model_name);
      formData.append(
        'enable_thinking',
        String(options?.enable_thinking ?? false),
      );
      formData.append('reasoning_effort', options?.reasoning_effort ?? 'low');
      formData.append('stream', String(options?.stream ?? true));
      formData.append(
        'enable_context_manager',
        String(options?.enable_context_manager ?? false),
      );
      if (userName) {
        formData.append('user_name', userName);
      }

      console.log('FormData content:', Array.from(formData.entries()));

      const result = await initiateAgentMutation.mutateAsync(formData);
      console.log('Agent initiated:', result);

      if (result.thread_id) {
        setInitiatedThreadId(result.thread_id);
      } else {
        throw new Error('Agent initiation did not return a thread_id.');
      }
      chatInputRef.current?.clearPendingFiles();
    } catch (error: any) {
      console.error('Error during submission process:', error);
      if (error instanceof BillingError) {
        console.log('Handling BillingError:', error.detail);
        onOpen('paymentRequiredDialog');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      const pendingPrompt = localStorage.getItem(PENDING_PROMPT_KEY);

      if (pendingPrompt) {
        setInputValue(pendingPrompt);
        setAutoSubmit(true);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (autoSubmit && inputValue && !isSubmitting) {
      const timer = setTimeout(() => {
        handleSubmit(inputValue);
        setAutoSubmit(false);
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [autoSubmit, inputValue, isSubmitting]);

  return (
    <>
      <ModalProviders />
      <div className="flex flex-col h-screen w-full relative">
        {/* Animated Background */}
        <div className="absolute inset-0 z-0 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-blue-950/20 dark:via-indigo-950/20 dark:to-purple-950/20"></div>
          <div className="absolute inset-0 opacity-30">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-400/20 to-indigo-400/20 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute top-3/4 right-1/4 w-80 h-80 bg-gradient-to-r from-purple-400/20 to-pink-400/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-gradient-to-r from-indigo-400/15 to-blue-400/15 rounded-full blur-2xl animate-bounce"></div>
          </div>
          <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_25%,rgba(255,255,255,.05)_25%,rgba(255,255,255,.05)_50%,transparent_50%,transparent_75%,rgba(255,255,255,.05)_75%)] bg-[length:60px_60px] animate-pulse"></div>
        </div>
        
        {isMobile && (
          <div className="absolute top-4 left-4 z-20">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setOpenMobile(true)}
                >
                  <Menu className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Open menu</TooltipContent>
            </Tooltip>
          </div>
        )}

        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[650px] max-w-[90%] z-10 relative">
          <div className="flex flex-col items-center text-center w-full bg-background/80 backdrop-blur-sm rounded-2xl p-8 border border-border/20">
            {isLoadingUserName ? (
              <div className="flex items-center gap-2 flex-wrap justify-center">
                <h1 className="tracking-tight text-4xl text-muted-foreground leading-tight">
                  Hey there, I am
                </h1>
                <AgentSelector
                  selectedAgentId={selectedAgentId}
                  onAgentSelect={setSelectedAgentId}
                  variant="heading"
                />
              </div>
            ) : (
              <div className="flex items-center gap-2 flex-wrap justify-center">
                <TypingText
                  text={`Hey ${userName || 'there'}, my name is `}
                  className="tracking-tight text-4xl text-muted-foreground leading-tight"
                  duration={80}
                  delay={500}
                />
                <AgentSelector
                  selectedAgentId={selectedAgentId}
                  onAgentSelect={setSelectedAgentId}
                  variant="heading"
                />
                
                {/* Name editing section for users without a name */}
                {!userName && (
                  <div className="relative mt-4">
                    {!isNameFocused ? (
                      <button
                        onClick={() => setIsNameFocused(true)}
                        className="tracking-tight text-2xl text-muted-foreground hover:text-foreground leading-tight underline decoration-dashed underline-offset-4 transition-colors duration-200"
                      >
                        Click here to set your name
                      </button>
                    ) : (
                      <div className="relative">
                        <Input
                          value={nameInput}
                          onChange={(e) => setNameInput(e.target.value)}
                          onKeyDown={handleNameKeyDown}
                          onBlur={() => {
                            if (!nameInput.trim()) {
                              setIsNameFocused(false);
                            }
                          }}
                          placeholder="your name"
                          className="h-12 w-40 text-2xl text-center font-medium bg-transparent border-0 border-b-2 border-muted-foreground/30 focus:border-primary rounded-none shadow-none focus:shadow-none transition-colors duration-200 px-0"
                          autoFocus
                        />
                        {nameInput.trim() && (
                          <button
                            onClick={handleSaveName}
                            className="absolute -right-8 top-1/2 -translate-y-1/2 p-1 rounded-full bg-primary hover:bg-primary/90 transition-colors duration-200"
                          >
                            <Check className="h-4 w-4 text-primary-foreground" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
            <p className="tracking-tight text-3xl font-normal text-muted-foreground/80 mt-2">
              What would you like to do today?
            </p>
          </div>

          <div className={cn('w-full mb-2', 'max-w-full', 'sm:max-w-3xl')}>
            <ChatInput
              ref={chatInputRef}
              onSubmit={handleSubmit}
              loading={isSubmitting}
              placeholder="Describe what you need help with..."
              value={inputValue}
              onChange={setInputValue}
              hideAttachments={false}
            />
          </div>

          <Examples onSelectPrompt={setInputValue} />
        </div>

        <div className="relative z-20">
          <BillingErrorAlert
            message={billingError?.message}
            currentUsage={billingError?.currentUsage}
            limit={billingError?.limit}
            accountId={personalAccount?.account_id}
            onDismiss={clearBillingError}
            isOpen={!!billingError}
          />
        </div>
      </div>
    </>
  );
}
