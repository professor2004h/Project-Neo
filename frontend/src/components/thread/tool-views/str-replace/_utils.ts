export type DiffType = 'unchanged' | 'added' | 'removed';

export interface LineDiff {
  type: DiffType;
  oldLine: string | null;
  newLine: string | null;
  lineNumber: number;
}

export interface CharDiffPart {
  text: string;
  type: DiffType;
}

export interface DiffStats {
  additions: number;
  deletions: number;
}

export interface ExtractedData {
  filePath: string | null;
  oldStr: string | null;
  newStr: string | null;
  success?: boolean;
  timestamp?: string;
}


export const extractFromNewFormat = (content: any): ExtractedData => {
  if (!content) {
    return { filePath: null, oldStr: null, newStr: null };
  }

  if (typeof content === 'string') {
    // Only try to parse if it looks like JSON
    const trimmed = content.trim();
    if (trimmed.startsWith('{') || trimmed.startsWith('[')) {
      try {
        console.debug('StrReplaceToolView: Attempting to parse JSON string:', content.substring(0, 100) + '...');
        const parsed = JSON.parse(content);
        console.debug('StrReplaceToolView: Successfully parsed JSON:', parsed);
        return extractFromNewFormat(parsed);
      } catch (error) {
        console.error('StrReplaceToolView: JSON parse error:', error, 'Content:', content.substring(0, 200));
        return { filePath: null, oldStr: null, newStr: null };
      }
    } else {
      console.debug('StrReplaceToolView: String content does not look like JSON, skipping parse');
      return { filePath: null, oldStr: null, newStr: null };
    }
  }

  if (typeof content !== 'object') {
    return { filePath: null, oldStr: null, newStr: null };
  }

  // Enhanced string parsing with better JSON detection
  if (typeof content === 'string') {
    const trimmed = content.trim();
    
    // More robust JSON detection
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || 
        (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try {
        console.debug('StrReplaceToolView: Attempting to parse JSON string:', content.substring(0, 100) + '...');
        const parsed = JSON.parse(content);
        console.debug('StrReplaceToolView: Successfully parsed JSON:', parsed);
        return extractFromNewFormat(parsed);
      } catch (error) {
        console.error('StrReplaceToolView: JSON parse error:', error, 'Content:', content.substring(0, 200));
        // Don't return empty result immediately, try direct string extraction
      }
    }
    
    // Try parameter extraction first (handles incomplete streaming)  
    const filePathMatch = trimmed.match(/<parameter\s+name=["']file_path["']>(.*?)(?:<\/parameter>|$)/i);
    const oldStrMatch = trimmed.match(/<parameter\s+name=["']old_str["']>([\s\S]*?)(?:<\/parameter>|$)/i);
    const newStrMatch = trimmed.match(/<parameter\s+name=["']new_str["']>([\s\S]*?)(?:<\/parameter>|$)/i);
    
    if (filePathMatch || oldStrMatch || newStrMatch) {
      console.debug('StrReplaceToolView: Found parameter patterns in streaming content');
      return {
        filePath: filePathMatch ? filePathMatch[1].trim() : null,
        oldStr: oldStrMatch ? oldStrMatch[1] : null,
        newStr: newStrMatch ? newStrMatch[1] : null
      };
    }

    // Try direct string extraction for XML-like content
    const directExtraction = extractDirectFromString(trimmed);
    if (directExtraction.filePath || directExtraction.oldStr || directExtraction.newStr) {
      console.debug('StrReplaceToolView: Successfully extracted from string content:', directExtraction);
      return directExtraction;
    }
    
    console.debug('StrReplaceToolView: String content does not look like valid JSON or XML, returning empty');
    return { filePath: null, oldStr: null, newStr: null };
  }

  if (typeof content !== 'object' || content === null) {
    return { filePath: null, oldStr: null, newStr: null };
  }

  // Handle tool_execution format (new format)
  if ('tool_execution' in content && typeof content.tool_execution === 'object') {
    const toolExecution = content.tool_execution;
    const args = toolExecution.arguments || {};
    
    console.debug('StrReplaceToolView: Extracted from new format:', {
      filePath: args.file_path,
      oldStr: args.old_str ? `${args.old_str.substring(0, 50)}...` : null,
      newStr: args.new_str ? `${args.new_str.substring(0, 50)}...` : null,
      success: toolExecution.result?.success
    });
    
    return {
      filePath: args.file_path || null,
      oldStr: args.old_str || null,
      newStr: args.new_str || null,
      success: toolExecution.result?.success,
      timestamp: toolExecution.execution_details?.timestamp
    };
  }

  if ('role' in content && 'content' in content && typeof content.content === 'string') {
    console.debug('StrReplaceToolView: Found role/content structure with string content, parsing...');
    return extractFromNewFormat(content.content);
  }

  if ('role' in content && 'content' in content && typeof content.content === 'object') {
    console.debug('StrReplaceToolView: Found role/content structure with object content');
    return extractFromNewFormat(content.content);
  }

  return { filePath: null, oldStr: null, newStr: null };
};

// New helper function for direct string extraction
const extractDirectFromString = (content: string): ExtractedData => {
  let filePath: string | null = null;
  let oldStr: string | null = null;
  let newStr: string | null = null;

  // Extract file_path from various attribute patterns
  const filePathMatches = [
    content.match(/file_path=["'](.*?)["']/i),
    content.match(/file_path:\s*["'](.*?)["']/i),
    content.match(/<str-replace[^>]*file_path=["'](.*?)["']/i),
    content.match(/<str_replace[^>]*file_path=["'](.*?)["']/i)
  ];
  
  for (const match of filePathMatches) {
    if (match) {
      filePath = match[1];
      break;
    }
  }

  // Extract old_str with more flexible patterns
  const oldStrMatches = [
    // Complete patterns
    content.match(/<parameter\s+name=["']old_str["']>([\s\S]*?)<\/parameter>/i),
    content.match(/<old_str>([\s\S]*?)<\/old_str>/i),
    content.match(/<old-str>([\s\S]*?)<\/old-str>/i),
    content.match(/old_str:\s*["']([\s\S]*?)["']/i),
    content.match(/old_str=["']([\s\S]*?)["']/i),
    content.match(/"old_str":\s*"([\s\S]*?)"/i),
    // Incomplete streaming (parameter without closing tag)
    content.match(/<parameter\s+name=["']old_str["']>([\s\S]*?)(?=\s*$)/i)
  ];
  
  for (const match of oldStrMatches) {
    if (match) {
      oldStr = match[1];
      break;
    }
  }

  // Extract new_str with more flexible patterns
  const newStrMatches = [
    content.match(/<new_str>([\s\S]*?)<\/new_str>/i),
    content.match(/<new-str>([\s\S]*?)<\/new-str>/i),
    content.match(/new_str:\s*["']([\s\S]*?)["']/i),
    content.match(/new_str=["']([\s\S]*?)["']/i),
    content.match(/"new_str":\s*"([\s\S]*?)"/i)
  ];
  
  for (const match of newStrMatches) {
    if (match) {
      newStr = match[1];
      break;
    }
  }

  return { filePath, oldStr, newStr };
};


export const extractFromLegacyFormat = (content: any, extractToolData: any, extractFilePath: any, extractStrReplaceContent: any): ExtractedData => {
  // First try the tool data extraction
  try {
    const assistantToolData = extractToolData(content);
    
    if (assistantToolData?.toolResult) {
      const args = assistantToolData.arguments || {};
      
      console.debug('StrReplaceToolView: Extracted from legacy format (extractToolData):', {
        filePath: assistantToolData.filePath || args.file_path,
        oldStr: args.old_str ? `${args.old_str.substring(0, 50)}...` : null,
        newStr: args.new_str ? `${args.new_str.substring(0, 50)}...` : null
      });
      
      // Verify we have the essential data
      if ((args.old_str || args.old_string) && (args.new_str || args.new_string)) {
        return {
          filePath: assistantToolData.filePath || args.file_path || null,
          oldStr: args.old_str || args.old_string || null,
          newStr: args.new_str || args.new_string || null
        };
      }
    }
  } catch (error) {
    console.warn('StrReplaceToolView: Error in extractToolData, trying fallback:', error);
  }

  // Fallback to file path and str replace content extraction
  try {
    const legacyFilePath = extractFilePath(content);
    const strReplaceContent = extractStrReplaceContent(content);
    
    console.debug('StrReplaceToolView: Extracted from legacy format (fallback):', {
      filePath: legacyFilePath,
      oldStr: strReplaceContent.oldStr ? `${strReplaceContent.oldStr.substring(0, 50)}...` : null,
      newStr: strReplaceContent.newStr ? `${strReplaceContent.newStr.substring(0, 50)}...` : null
    });
    
    // Return even if some fields are missing - the component can handle partial data
    return {
      filePath: legacyFilePath,
      oldStr: strReplaceContent.oldStr,
      newStr: strReplaceContent.newStr
    };
  } catch (error) {
    console.warn('StrReplaceToolView: Error in fallback extraction:', error);
  }

  // Final fallback - try direct extraction if content is a string
  if (typeof content === 'string') {
    console.debug('StrReplaceToolView: Trying direct string extraction as final fallback');
    return extractDirectFromString(content);
  }

  // If content is an object, try to find the strings directly
  if (typeof content === 'object' && content !== null) {
    const result: ExtractedData = { filePath: null, oldStr: null, newStr: null };
    
    // Deep search for file_path, old_str, new_str in the object
    const findInObject = (obj: any, key: string): any => {
      if (typeof obj !== 'object' || obj === null) return null;
      
      if (key in obj) return obj[key];
      
      for (const value of Object.values(obj)) {
        if (typeof value === 'object' && value !== null) {
          const found = findInObject(value, key);
          if (found !== null) return found;
        }
      }
      return null;
    };
    
    result.filePath = findInObject(content, 'file_path') || findInObject(content, 'filePath');
    result.oldStr = findInObject(content, 'old_str') || findInObject(content, 'oldStr') || findInObject(content, 'old_string');
    result.newStr = findInObject(content, 'new_str') || findInObject(content, 'newStr') || findInObject(content, 'new_string');
    
    if (result.oldStr || result.newStr) {
      console.debug('StrReplaceToolView: Found data via deep object search:', result);
      return result;
    }
  }
  
  console.warn('StrReplaceToolView: All extraction methods failed, returning empty result');
  return { filePath: null, oldStr: null, newStr: null };
};


export const parseNewlines = (text: string): string => {
  return text.replace(/\\n/g, '\n');
};


export const generateLineDiff = (oldText: string, newText: string): LineDiff[] => {
  const parsedOldText = parseNewlines(oldText);
  const parsedNewText = parseNewlines(newText);
  
  const oldLines = parsedOldText.split('\n');
  const newLines = parsedNewText.split('\n');
  
  const diffLines: LineDiff[] = [];
  const maxLines = Math.max(oldLines.length, newLines.length);
  
  for (let i = 0; i < maxLines; i++) {
    const oldLine = i < oldLines.length ? oldLines[i] : null;
    const newLine = i < newLines.length ? newLines[i] : null;
    
    if (oldLine === newLine) {
      diffLines.push({ type: 'unchanged', oldLine, newLine, lineNumber: i + 1 });
    } else {
      if (oldLine !== null) {
        diffLines.push({ type: 'removed', oldLine, newLine: null, lineNumber: i + 1 });
      }
      if (newLine !== null) {
        diffLines.push({ type: 'added', oldLine: null, newLine, lineNumber: i + 1 });
      }
    }
  }
  
  return diffLines;
};

export const generateCharDiff = (oldText: string, newText: string): CharDiffPart[] => {
  const parsedOldText = parseNewlines(oldText);
  const parsedNewText = parseNewlines(newText);
  
  let prefixLength = 0;
  while (
    prefixLength < parsedOldText.length &&
    prefixLength < parsedNewText.length &&
    parsedOldText[prefixLength] === parsedNewText[prefixLength]
  ) {
    prefixLength++;
  }

  let oldSuffixStart = parsedOldText.length;
  let newSuffixStart = parsedNewText.length;
  while (
    oldSuffixStart > prefixLength &&
    newSuffixStart > prefixLength &&
    parsedOldText[oldSuffixStart - 1] === parsedNewText[newSuffixStart - 1]
  ) {
    oldSuffixStart--;
    newSuffixStart--;
  }

  const parts: CharDiffPart[] = [];

  if (prefixLength > 0) {
    parts.push({
      text: parsedOldText.substring(0, prefixLength),
      type: 'unchanged',
    });
  }

  if (oldSuffixStart > prefixLength) {
    parts.push({
      text: parsedOldText.substring(prefixLength, oldSuffixStart),
      type: 'removed',
    });
  }
  if (newSuffixStart > prefixLength) {
    parts.push({
      text: parsedNewText.substring(prefixLength, newSuffixStart),
      type: 'added',
    });
  }

  if (oldSuffixStart < parsedOldText.length) {
    parts.push({
      text: parsedOldText.substring(oldSuffixStart),
      type: 'unchanged',
    });
  }

  return parts;
};

export const calculateDiffStats = (lineDiff: LineDiff[]): DiffStats => {
  return {
    additions: lineDiff.filter(line => line.type === 'added').length,
    deletions: lineDiff.filter(line => line.type === 'removed').length
  };
};