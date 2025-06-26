'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { FileAudio, Download, Loader } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface AudioRendererProps {
  url: string;
  fileName: string;
  className?: string;
  onDownload?: () => void;
  isDownloading?: boolean;
}

export function AudioRenderer({
  url,
  fileName,
  className,
  onDownload,
  isDownloading = false,
}: AudioRendererProps) {
  const fileExtension = fileName.split('.').pop()?.toLowerCase() || '';
  
  // Handle download - use external handler if provided, fallback to direct URL
  const handleDownload = () => {
    if (onDownload) {
      onDownload();
    } else if (url) {
      console.log(`[AUDIO RENDERER] Using fallback download for ${fileName}`);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName.split('/').pop() || 'audio';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } else {
      console.error('[AUDIO RENDERER] No download URL or handler available');
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-6 space-y-6',
        className,
      )}
    >
      {/* Audio icon and file info */}
      <div className="flex flex-col items-center text-center">
        <div className="relative mb-4">
          <FileAudio className="h-16 w-16 text-blue-500" />
          <div className="absolute -bottom-1 -right-1 bg-background rounded-sm px-1.5 py-0.5 text-xs font-medium text-muted-foreground border">
            {fileExtension.toUpperCase()}
          </div>
        </div>
        
        <h3 className="text-lg font-semibold mb-2 text-center max-w-md break-words">
          {fileName.split('/').pop()}
        </h3>
      </div>

      {/* Audio player */}
      <div className="w-full max-w-md">
        <audio
          controls
          className="w-full"
          preload="metadata"
          style={{ height: '40px' }}
        >
          <source src={url} type={`audio/${fileExtension === 'webm' ? 'webm' : fileExtension}`} />
          <source src={url} type="audio/mpeg" />
          <source src={url} type="audio/wav" />
          Your browser does not support the audio element.
        </audio>
      </div>

      {/* Download button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleDownload}
        disabled={isDownloading}
        className="min-w-[120px]"
      >
        {isDownloading ? (
          <Loader className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Download className="h-4 w-4 mr-2" />
        )}
        Download
      </Button>
    </div>
  );
} 