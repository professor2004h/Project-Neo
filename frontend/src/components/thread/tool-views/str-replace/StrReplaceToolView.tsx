import React, { useState, useEffect } from 'react';
import {
  FileDiff,
  CheckCircle,
  AlertTriangle,
  CircleDashed,
  Loader2,
  File,
  ChevronDown,
  ChevronUp,
  Minus,
  Plus,
} from 'lucide-react';

import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  generateLineDiff,
  generateCharDiff,
  calculateDiffStats,
  parseNewlines,
  extractFromNewFormat,
  extractFromLegacyFormat,
  type LineDiff,
  type DiffStats,
  type ExtractedData,
} from './_utils';
import { extractFilePath, extractStrReplaceContent, extractToolData, formatTimestamp, getToolTitle } from '../utils';
import { ToolViewProps } from '../types';
import { LoadingState } from '../shared/LoadingState';

const UnifiedDiffView: React.FC<{ lineDiff: LineDiff[] }> = ({ lineDiff }) => (
  <div className="bg-white dark:bg-zinc-950 font-mono text-sm overflow-x-auto -mt-2">
    <table className="w-full border-collapse">
      <tbody>
        {lineDiff.map((line, i) => (
          <tr
            key={i}
            className={cn(
              "hover:bg-zinc-50 dark:hover:bg-zinc-900",
              line.type === 'removed' && "bg-red-50 dark:bg-red-950/30",
              line.type === 'added' && "bg-emerald-50 dark:bg-emerald-950/30",
            )}
          >
            <td className="w-10 text-right select-none py-0.5 pr-1 pl-4 text-xs text-zinc-500 dark:text-zinc-400 border-r border-zinc-200 dark:border-zinc-800">
              {line.lineNumber}
            </td>
            <td className="pl-2 py-0.5 w-6 select-none">
              {line.type === 'removed' && <Minus className="h-3.5 w-3.5 text-red-500" />}
              {line.type === 'added' && <Plus className="h-3.5 w-3.5 text-emerald-500" />}
            </td>
            <td className="w-full px-3 py-0.5">
              <div className="overflow-x-auto max-w-full text-xs">
                {line.type === 'removed' && <span className="text-red-700 dark:text-red-400">{line.oldLine}</span>}
                {line.type === 'added' && <span className="text-emerald-700 dark:text-emerald-400">{line.newLine}</span>}
                {line.type === 'unchanged' && <span className="text-zinc-700 dark:text-zinc-300">{line.oldLine}</span>}
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const SplitDiffView: React.FC<{ lineDiff: LineDiff[] }> = ({ lineDiff }) => (
  <div className="bg-white dark:bg-zinc-950 font-mono text-sm overflow-x-auto -my-2">
    <table className="w-full border-collapse">
      <thead>
        <tr className="border-b border-zinc-200 dark:border-zinc-800 text-xs">
          <th className="p-2 text-left text-zinc-500 dark:text-zinc-400 w-1/2">Removed</th>
          <th className="p-2 text-left text-zinc-500 dark:text-zinc-400 w-1/2">Added</th>
        </tr>
      </thead>
      <tbody>
        {lineDiff.map((line, i) => (
          <tr key={i}>
            <td
              className={cn(
                "p-2 align-top",
                line.type === 'removed' ? 'bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-400' : '',
                line.oldLine === null ? 'bg-zinc-100 dark:bg-zinc-900' : ''
              )}
            >
              {line.oldLine !== null ? (
                <div className="flex">
                  <div className="w-8 text-right pr-2 select-none text-xs text-zinc-500 dark:text-zinc-400">
                    {line.lineNumber}
                  </div>
                  {line.type === 'removed' &&
                    <Minus className="h-3.5 w-3.5 text-red-500 mt-0.5 mr-2 flex-shrink-0" />
                  }
                  <div className="overflow-x-auto">
                    <span className="break-all">{line.oldLine}</span>
                  </div>
                </div>
              ) : null}
            </td>
            <td
              className={cn(
                "p-2 align-top",
                line.type === 'added' ? 'bg-emerald-50 dark:bg-emerald-950/30 text-emerald-700 dark:text-emerald-400' : '',
                line.newLine === null ? 'bg-zinc-100 dark:bg-zinc-900' : ''
              )}
            >
              {line.newLine !== null ? (
                <div className="flex">
                  <div className="w-8 text-right pr-2 select-none text-xs text-zinc-500 dark:text-zinc-400">
                    {line.lineNumber}
                  </div>
                  {line.type === 'added' &&
                    <Plus className="h-3.5 w-3.5 text-emerald-500 mt-0.5 mr-2 flex-shrink-0" />
                  }
                  <div className="overflow-x-auto">
                    <span className="break-all">{line.newLine}</span>
                  </div>
                </div>
              ) : null}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const ErrorState: React.FC<{ filePath?: string | null; hasPartialData?: boolean }> = ({ 
  filePath, 
  hasPartialData = false 
}) => (
  <div className="flex flex-col items-center justify-center h-full py-12 px-6 bg-gradient-to-b from-white to-zinc-50 dark:from-zinc-950 dark:to-zinc-900">
    <div className="text-center w-full max-w-md">
      <AlertTriangle className="h-16 w-16 mx-auto mb-6 text-amber-500" />
      <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100 mb-2">
        {hasPartialData ? 'Incomplete String Replacement Data' : 'Invalid String Replacement'}
      </h3>
      <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-4">
        {hasPartialData 
          ? 'Some replacement data was found but old or new string is missing.'
          : 'Could not extract the old string and new string from the request.'
        }
      </p>
      {filePath && (
        <div className="bg-zinc-100 dark:bg-zinc-800 rounded-lg p-3 mb-4">
          <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-1">File:</p>
          <code className="text-xs font-mono text-zinc-800 dark:text-zinc-200">{filePath}</code>
        </div>
      )}
      <details className="text-left">
        <summary className="text-xs text-zinc-500 dark:text-zinc-400 cursor-pointer hover:text-zinc-700 dark:hover:text-zinc-300">
          Show debugging information
        </summary>
        <div className="mt-2 text-xs text-zinc-400 dark:text-zinc-500">
          <p>• Check console for detailed extraction logs</p>
          <p>• Verify the tool response format is correct</p>
          <p>• Ensure old_str and new_str are properly formatted</p>
        </div>
      </details>
    </div>
  </div>
);

export function StrReplaceToolView({
  name = 'str-replace',
  assistantContent,
  toolContent,
  assistantTimestamp,
  toolTimestamp,
  isSuccess = true,
  isStreaming = false,
}: ToolViewProps): JSX.Element {
  
  const [expanded, setExpanded] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<'unified' | 'split'>('unified');
  
  // Simple delayed extraction state
  const [extractionAttempted, setExtractionAttempted] = useState<boolean>(false);
  
  // Trigger delayed extraction when streaming completes
  useEffect(() => {
    if (!isStreaming && !extractionAttempted) {
      // Longer delay to ensure content is fully received and settled
      const timer = setTimeout(() => {
        setExtractionAttempted(true);
      }, 600);
      
      return () => clearTimeout(timer);
    } else if (isStreaming) {
      setExtractionAttempted(false);
    }
  }, [isStreaming, extractionAttempted]);

  let filePath: string | null = null;
  let oldStr: string | null = null;
  let newStr: string | null = null;
  let actualIsSuccess = isSuccess;
  let actualToolTimestamp = toolTimestamp;
  let actualAssistantTimestamp = assistantTimestamp;
  
  // Always extract basic data for filePath
  let assistantNewFormat: ExtractedData = { filePath: null, oldStr: null, newStr: null };
  let toolNewFormat: ExtractedData = { filePath: null, oldStr: null, newStr: null };
  
  // Always attempt extraction when not streaming (with or without delay)
  const shouldExtract = !isStreaming && (extractionAttempted || !isStreaming);
  
  if (shouldExtract) {
    // Wrap the main logic in a try-catch to prevent crashes
    try {
      // Add detailed debugging for response format
      console.group('StrReplaceToolView: Detailed Response Analysis');
      console.log('assistantContent (raw):', assistantContent);
      console.log('toolContent (raw):', toolContent);
      console.log('assistantContent type:', typeof assistantContent);
      console.log('toolContent type:', typeof toolContent);
      
      assistantNewFormat = extractFromNewFormat(assistantContent);
      toolNewFormat = extractFromNewFormat(toolContent);

      console.log('assistantNewFormat result:', assistantNewFormat);
      console.log('toolNewFormat result:', toolNewFormat);
      console.groupEnd();

      // New format extraction
      filePath = assistantNewFormat.filePath || toolNewFormat.filePath;
      oldStr = assistantNewFormat.oldStr || toolNewFormat.oldStr;
      newStr = assistantNewFormat.newStr || toolNewFormat.newStr;

      if (toolNewFormat.success !== undefined) {
        actualIsSuccess = toolNewFormat.success;
      } else if (assistantNewFormat.success !== undefined) {
        actualIsSuccess = assistantNewFormat.success;
      }
      
      if (assistantNewFormat.timestamp) {
        actualAssistantTimestamp = assistantNewFormat.timestamp;
      }
      if (toolNewFormat.timestamp) {
        actualToolTimestamp = toolNewFormat.timestamp;
      }

      // Fallback to legacy format extraction if needed
      if (!filePath || !oldStr || !newStr) {
        const assistantLegacy = extractFromLegacyFormat(assistantContent, extractToolData, extractFilePath, extractStrReplaceContent);
        const toolLegacy = extractFromLegacyFormat(toolContent, extractToolData, extractFilePath, extractStrReplaceContent);

        filePath = filePath || assistantLegacy.filePath || toolLegacy.filePath;
        oldStr = oldStr || assistantLegacy.oldStr || toolLegacy.oldStr;
        newStr = newStr || assistantLegacy.newStr || toolLegacy.newStr;
      }

      // Final fallback for edge cases
      if (!filePath) {
        filePath = extractFilePath(assistantContent) || extractFilePath(toolContent);
      }
      if (!oldStr || !newStr) {
        const assistantStrReplace = extractStrReplaceContent(assistantContent);
        const toolStrReplace = extractStrReplaceContent(toolContent);
        oldStr = oldStr || assistantStrReplace.oldStr || toolStrReplace.oldStr;
        newStr = newStr || assistantStrReplace.newStr || toolStrReplace.newStr;
      }

    } catch (error) {
      console.error('StrReplaceToolView: Extraction error:', error);
    }
  } else {
    // When streaming, try to get at least filePath for display
    try {
      assistantNewFormat = extractFromNewFormat(assistantContent);
      toolNewFormat = extractFromNewFormat(toolContent);
      filePath = assistantNewFormat.filePath || toolNewFormat.filePath || extractFilePath(assistantContent) || extractFilePath(toolContent);
    } catch (error) {
      console.debug('StrReplaceToolView: Could not extract filePath during streaming');
    }
  }

  const toolTitle = getToolTitle(name);

  // Generate diff data (only if we have both strings)
  const lineDiff = oldStr && newStr ? generateLineDiff(oldStr, newStr) : [];
  const charDiff = oldStr && newStr ? generateCharDiff(oldStr, newStr) : [];

  // Calculate stats on changes
  const stats: DiffStats = calculateDiffStats(lineDiff);

  // Check if we should show error state
  const shouldShowError = !isStreaming && extractionAttempted && (!oldStr || !newStr) && (assistantContent || toolContent);
  
  // Enhanced logging for debugging
  if (shouldShowError) {
    console.group('StrReplaceToolView: Error state triggered');
    console.log('assistantContent:', assistantContent);
    console.log('toolContent:', toolContent);
    console.log('Extracted values:', { filePath, oldStr, newStr });
    console.log('assistantNewFormat:', assistantNewFormat);
    console.log('toolNewFormat:', toolNewFormat);
    console.groupEnd();
  }

  // More lenient error condition - only show error if we have content but no data at all
  const hasAnyContent = assistantContent || toolContent;
  const hasAnyExtractedData = filePath || oldStr || newStr;
  const shouldShowErrorState = !isStreaming && extractionAttempted && hasAnyContent && !hasAnyExtractedData;

  // Determine the overall state for consistent UI
  const hasPartialData = hasAnyExtractedData && (!oldStr || !newStr);
  const showMainContent = hasAnyExtractedData && oldStr && newStr;
  const showLoadingState = isStreaming || (!extractionAttempted && !isStreaming);
  
  // Override success state if we have backend success but parsing failed
  const displaySuccess = actualIsSuccess && (showMainContent || hasPartialData);
  const displayMessage = hasPartialData 
    ? 'Replacement completed (partial data)' 
    : actualIsSuccess 
      ? 'Replacement completed' 
      : 'Replacement failed';

  return (
    <Card className="gap-0 flex border shadow-none border-t border-b-0 border-x-0 p-0 rounded-none flex-col h-full overflow-hidden bg-white dark:bg-zinc-950">
      <CardHeader className="h-14 bg-zinc-50/80 dark:bg-zinc-900/80 backdrop-blur-sm border-b p-2 px-4 space-y-2">
        <div className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="relative p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-600/10 border border-purple-500/20">
              <FileDiff className="w-5 h-5 text-purple-500 dark:text-purple-400" />
            </div>
            <CardTitle className="text-base font-medium text-zinc-900 dark:text-zinc-100">
              {toolTitle}
            </CardTitle>
          </div>

          {!isStreaming && (
            <Badge
              variant="secondary"
              className={
                displaySuccess
                  ? "bg-gradient-to-b from-emerald-200 to-emerald-100 text-emerald-700 dark:from-emerald-800/50 dark:to-emerald-900/60 dark:text-emerald-300"
                  : "bg-gradient-to-b from-rose-200 to-rose-100 text-rose-700 dark:from-rose-800/50 dark:to-rose-900/60 dark:text-rose-300"
              }
            >
              {displaySuccess ? (
                <CheckCircle className="h-3.5 w-3.5 mr-1" />
              ) : (
                <AlertTriangle className="h-3.5 w-3.5 mr-1" />
              )}
              {displayMessage}
            </Badge>
          )}

          {isStreaming && (
            <Badge className="bg-gradient-to-b from-blue-200 to-blue-100 text-blue-700 dark:from-blue-800/50 dark:to-blue-900/60 dark:text-blue-300">
              <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" />
              Processing replacement
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="p-0 h-full flex-1 overflow-hidden relative">
        {showLoadingState ? (
          <LoadingState
            icon={FileDiff}
            iconColor="text-purple-500 dark:text-purple-400"
            bgColor="bg-gradient-to-b from-purple-100 to-purple-50 shadow-inner dark:from-purple-800/40 dark:to-purple-900/60 dark:shadow-purple-950/20"
            title="Processing String Replacement"
            filePath={filePath || 'Processing file...'}
            progressText="Analyzing text patterns"
            subtitle="Please wait while the replacement is being processed"
          />
        ) : shouldShowErrorState ? (
          <ErrorState filePath={filePath} hasPartialData={hasPartialData} />
        ) : showMainContent ? (
          <ScrollArea className="h-full w-full">
            <div className="p-4">
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg overflow-hidden mb-4">
                <div className="p-3 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 flex items-center justify-between">
                  <div className="flex items-center">
                    <File className="h-4 w-4 mr-2 text-zinc-500 dark:text-zinc-400" />
                    <code className="text-xs font-mono text-zinc-700 dark:text-zinc-300">
                      {filePath || 'Unknown file'}
                    </code>
                  </div>

                  <div className="flex items-center gap-2">
                    <div className="flex items-center text-xs text-zinc-500 dark:text-zinc-400 gap-3">
                      <div className="flex items-center">
                        <Plus className="h-3.5 w-3.5 text-emerald-500 mr-1" />
                        <span>{stats.additions}</span>
                      </div>
                      <div className="flex items-center">
                        <Minus className="h-3.5 w-3.5 text-red-500 mr-1" />
                        <span>{stats.deletions}</span>
                      </div>
                    </div>

                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 w-7 p-0"
                            onClick={() => setExpanded(!expanded)}
                          >
                            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{expanded ? 'Collapse' : 'Expand'}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                </div>

                {expanded && (
                  <div>
                    <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'unified' | 'split')} className="w-auto">
                      <div className="border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 p-2 flex justify-end">
                        <TabsList className="h-7 p-0.5">
                          <TabsTrigger value="unified" className="text-xs h-6 px-2">Unified</TabsTrigger>
                          <TabsTrigger value="split" className="text-xs h-6 px-2">Split</TabsTrigger>
                        </TabsList>
                      </div>

                      <TabsContent value="unified" className="m-0 pb-4">
                        <UnifiedDiffView lineDiff={lineDiff} />
                      </TabsContent>

                      <TabsContent value="split" className="m-0">
                        <SplitDiffView lineDiff={lineDiff} />
                      </TabsContent>
                    </Tabs>
                  </div>
                )}
              </div>
            </div>
          </ScrollArea>
        ) : hasPartialData ? (
          <div className="p-4 h-full flex flex-col">
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg p-4 mb-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-1">
                    Partial Replacement Data
                  </h3>
                  <p className="text-xs text-amber-700 dark:text-amber-300">
                    The operation completed successfully, but some display data could not be extracted.
                  </p>
                </div>
              </div>
            </div>
            
            {filePath && (
              <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <File className="h-4 w-4 mr-2 text-zinc-500 dark:text-zinc-400" />
                  <code className="text-xs font-mono text-zinc-700 dark:text-zinc-300">
                    {filePath}
                  </code>
                </div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400">
                  String replacement was {displaySuccess ? 'completed successfully' : 'attempted'} in this file.
                </p>
              </div>
            )}
          </div>
        ) : (
          <ErrorState filePath={filePath} hasPartialData={hasPartialData} />
        )}
      </CardContent>

      <div className="px-4 py-2 h-10 bg-gradient-to-r from-zinc-50/90 to-zinc-100/90 dark:from-zinc-900/90 dark:to-zinc-800/90 backdrop-blur-sm border-t border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
        <div className="h-full flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
          {!isStreaming && (
            <div className="flex items-center gap-1">
              {displaySuccess ? (
                <CheckCircle className="h-3.5 w-3.5 text-emerald-500 mr-1" />
              ) : (
                <AlertTriangle className="h-3.5 w-3.5 text-red-500 mr-1" />
              )}
              <span>
                {displayMessage}
              </span>
            </div>
          )}

          {isStreaming && (
            <div className="flex items-center gap-1">
              <CircleDashed className="h-3.5 w-3.5 text-blue-500 animate-spin mr-1" />
              <span>Processing replacement...</span>
            </div>
          )}
        </div>

        <div className="text-xs text-zinc-500 dark:text-zinc-400">
          {actualToolTimestamp && !isStreaming
            ? formatTimestamp(actualToolTimestamp)
            : actualAssistantTimestamp
              ? formatTimestamp(actualAssistantTimestamp)
              : ''}
        </div>
      </div>
    </Card>
  );
}