'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Search, Folder, FileAudio, MoreHorizontal, Edit2, Trash2, Download, Share2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { toast } from 'sonner';
import { useRouter } from 'next/navigation';
import {
  getMeetings,
  getFolders,
  createMeeting,
  createFolder,
  deleteMeeting,
  deleteFolder,
  updateMeeting,
  updateFolder,
  searchMeetings,
  type Meeting,
  type MeetingFolder,
  type SearchResult,
} from '@/lib/api-meetings';
import { formatDistanceToNow } from 'date-fns';

export default function MeetingsPage() {
  const router = useRouter();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [folders, setFolders] = useState<MeetingFolder[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentFolderId, setCurrentFolderId] = useState<string | undefined>(undefined);
  const [breadcrumbs, setBreadcrumbs] = useState<{ id?: string; name: string }[]>([{ name: 'All Meetings' }]);
  
  // Dialog states
  const [showNewMeetingDialog, setShowNewMeetingDialog] = useState(false);
  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false);
  const [newMeetingTitle, setNewMeetingTitle] = useState('');
  const [newFolderName, setNewFolderName] = useState('');
  const [editingItem, setEditingItem] = useState<{ type: 'meeting' | 'folder'; id: string; name: string } | null>(null);

  // Load meetings and folders
  useEffect(() => {
    loadData();
  }, [currentFolderId]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [meetingsData, foldersData] = await Promise.all([
        getMeetings(currentFolderId),
        getFolders(currentFolderId),
      ]);
      setMeetings(meetingsData);
      setFolders(foldersData);
    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load meetings');
    } finally {
      setIsLoading(false);
    }
  };

  // Search functionality
  useEffect(() => {
    const searchTimeout = setTimeout(async () => {
      if (searchQuery.trim()) {
        setIsSearching(true);
        try {
          const results = await searchMeetings(searchQuery);
          setSearchResults(results);
        } catch (error) {
          console.error('Search error:', error);
          toast.error('Search failed');
        } finally {
          setIsSearching(false);
        }
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(searchTimeout);
  }, [searchQuery]);

  const handleCreateMeeting = async () => {
    if (!newMeetingTitle.trim()) return;

    try {
      const meeting = await createMeeting(newMeetingTitle, currentFolderId, 'local');
      setShowNewMeetingDialog(false);
      setNewMeetingTitle('');
      router.push(`/meetings/${meeting.meeting_id}`);
    } catch (error) {
      console.error('Error creating meeting:', error);
      toast.error('Failed to create meeting');
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) return;

    try {
      await createFolder(newFolderName, currentFolderId);
      setShowNewFolderDialog(false);
      setNewFolderName('');
      loadData();
      toast.success('Folder created');
    } catch (error) {
      console.error('Error creating folder:', error);
      toast.error('Failed to create folder');
    }
  };

  const handleDeleteMeeting = async (meetingId: string) => {
    try {
      await deleteMeeting(meetingId);
      loadData();
      toast.success('Meeting deleted');
    } catch (error) {
      console.error('Error deleting meeting:', error);
      toast.error('Failed to delete meeting');
    }
  };

  const handleDeleteFolder = async (folderId: string) => {
    try {
      await deleteFolder(folderId);
      loadData();
      toast.success('Folder deleted');
    } catch (error) {
      console.error('Error deleting folder:', error);
      toast.error('Failed to delete folder');
    }
  };

  const handleRename = async () => {
    if (!editingItem || !editingItem.name.trim()) return;

    try {
      if (editingItem.type === 'meeting') {
        await updateMeeting(editingItem.id, { title: editingItem.name });
      } else {
        await updateFolder(editingItem.id, { name: editingItem.name });
      }
      setEditingItem(null);
      loadData();
      toast.success(`${editingItem.type === 'meeting' ? 'Meeting' : 'Folder'} renamed`);
    } catch (error) {
      console.error('Error renaming:', error);
      toast.error('Failed to rename');
    }
  };

  const navigateToFolder = (folder: MeetingFolder) => {
    setCurrentFolderId(folder.folder_id);
    setBreadcrumbs([...breadcrumbs, { id: folder.folder_id, name: folder.name }]);
  };

  const navigateToBreadcrumb = (index: number) => {
    const newBreadcrumbs = breadcrumbs.slice(0, index + 1);
    setBreadcrumbs(newBreadcrumbs);
    setCurrentFolderId(newBreadcrumbs[newBreadcrumbs.length - 1].id);
  };

  const downloadTranscript = (meeting: Meeting) => {
    const blob = new Blob([meeting.transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${meeting.title.replace(/[^a-z0-9]/gi, '_')}_transcript.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-7xl mx-auto">
          <Skeleton className="h-8 w-48 mb-8" />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold">Meetings</h1>
            {/* Breadcrumbs */}
            <div className="flex items-center mt-2 text-sm text-muted-foreground">
              {breadcrumbs.map((crumb, index) => (
                <React.Fragment key={index}>
                  {index > 0 && <span className="mx-2">/</span>}
                  <button
                    onClick={() => navigateToBreadcrumb(index)}
                    className="hover:text-foreground transition-colors"
                  >
                    {crumb.name}
                  </button>
                </React.Fragment>
              ))}
            </div>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowNewFolderDialog(true)} variant="outline">
              <Folder className="h-4 w-4 mr-2" />
              New Folder
            </Button>
            <Button onClick={() => setShowNewMeetingDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Meeting
            </Button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-6">
          <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search meetings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Search Results */}
        {searchQuery && searchResults.length > 0 && (
          <div className="mb-6 bg-muted/50 rounded-lg p-4">
            <h3 className="font-semibold mb-3">Search Results</h3>
            <div className="space-y-2">
              {searchResults.map((result) => (
                <div
                  key={result.meeting_id}
                  className="p-3 bg-background rounded-md hover:bg-accent cursor-pointer transition-colors"
                  onClick={() => router.push(`/meetings/${result.meeting_id}`)}
                >
                  <div className="font-medium">{result.title}</div>
                  <div
                    className="text-sm text-muted-foreground mt-1"
                    dangerouslySetInnerHTML={{ __html: result.snippet }}
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Folders and Meetings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Folders */}
          {folders.map((folder) => (
            <div
              key={folder.folder_id}
              className="border rounded-lg p-4 hover:bg-accent/50 cursor-pointer transition-colors group"
              onClick={() => navigateToFolder(folder)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <Folder className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <h3 className="font-medium">{folder.name}</h3>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(folder.created_at), { addSuffix: true })}
                    </p>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation();
                      setEditingItem({ type: 'folder', id: folder.folder_id, name: folder.name });
                    }}>
                      <Edit2 className="h-4 w-4 mr-2" />
                      Rename
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteFolder(folder.folder_id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}

          {/* Meetings */}
          {meetings.map((meeting) => (
            <div
              key={meeting.meeting_id}
              className="border rounded-lg p-4 hover:bg-accent/50 cursor-pointer transition-colors group"
              onClick={() => router.push(`/meetings/${meeting.meeting_id}`)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <FileAudio className="h-5 w-5 text-muted-foreground" />
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium truncate">{meeting.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {formatDistanceToNow(new Date(meeting.created_at), { addSuffix: true })}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        meeting.status === 'active' ? 'bg-green-100 text-green-700' :
                        meeting.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {meeting.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {meeting.recording_mode === 'online' ? 'Online' : 'Local'}
                      </span>
                    </div>
                  </div>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                    <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation();
                      setEditingItem({ type: 'meeting', id: meeting.meeting_id, name: meeting.title });
                    }}>
                      <Edit2 className="h-4 w-4 mr-2" />
                      Rename
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation();
                      downloadTranscript(meeting);
                    }}>
                      <Download className="h-4 w-4 mr-2" />
                      Download Transcript
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={(e) => {
                      e.stopPropagation();
                      // TODO: Implement sharing
                      toast.info('Sharing coming soon');
                    }}>
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteMeeting(meeting.meeting_id);
                      }}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>

        {/* Empty state */}
        {meetings.length === 0 && folders.length === 0 && !searchQuery && (
          <div className="text-center py-12">
            <FileAudio className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No meetings yet</h3>
            <p className="text-muted-foreground mb-4">Create your first meeting to get started</p>
            <Button onClick={() => setShowNewMeetingDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              New Meeting
            </Button>
          </div>
        )}

        {/* New Meeting Dialog */}
        <Dialog open={showNewMeetingDialog} onOpenChange={setShowNewMeetingDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Meeting</DialogTitle>
              <DialogDescription>
                Enter a title for your new meeting
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="meeting-title">Meeting Title</Label>
                <Input
                  id="meeting-title"
                  value={newMeetingTitle}
                  onChange={(e) => setNewMeetingTitle(e.target.value)}
                  placeholder="e.g., Team Standup"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateMeeting()}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewMeetingDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateMeeting} disabled={!newMeetingTitle.trim()}>
                Create Meeting
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New Folder Dialog */}
        <Dialog open={showNewFolderDialog} onOpenChange={setShowNewFolderDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Folder</DialogTitle>
              <DialogDescription>
                Enter a name for your new folder
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="folder-name">Folder Name</Label>
                <Input
                  id="folder-name"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="e.g., Weekly Meetings"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateFolder()}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewFolderDialog(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateFolder} disabled={!newFolderName.trim()}>
                Create Folder
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Dialog */}
        <Dialog open={!!editingItem} onOpenChange={(open) => !open && setEditingItem(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Rename {editingItem?.type === 'meeting' ? 'Meeting' : 'Folder'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label htmlFor="edit-name">Name</Label>
                <Input
                  id="edit-name"
                  value={editingItem?.name || ''}
                  onChange={(e) => editingItem && setEditingItem({ ...editingItem, name: e.target.value })}
                  onKeyDown={(e) => e.key === 'Enter' && handleRename()}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditingItem(null)}>
                Cancel
              </Button>
              <Button onClick={handleRename} disabled={!editingItem?.name.trim()}>
                Save
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
} 