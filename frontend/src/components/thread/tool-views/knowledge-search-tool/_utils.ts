import { normalizeContentToString, extractToolData } from '../utils';

export interface KnowledgeSearchResult {
  rank: number;
  score: number;
  text: string;
  metadata: Record<string, any>;
}

export interface KnowledgeSearchData {
  query: string | null;
  results: KnowledgeSearchResult[];
  indexName: string | null;
  knowledgeBaseName: string | null;
  description: string | null;
  actualIsSuccess: boolean;
  actualToolTimestamp: string | null;
  actualAssistantTimestamp: string | null;
}

/**
 * Extract knowledge search data from tool content
 */
export function extractKnowledgeSearchData(
  assistantContent: any,
  toolContent: any,
  isSuccess: boolean,
  toolTimestamp?: string,
  assistantTimestamp?: string
): KnowledgeSearchData {
  
  // Initialize default values
  let query: string | null = null;
  let results: KnowledgeSearchResult[] = [];
  let indexName: string | null = null;
  let knowledgeBaseName: string | null = null;
  let description: string | null = null;
  let actualIsSuccess = isSuccess;
  let actualToolTimestamp: string | null = toolTimestamp || null;
  let actualAssistantTimestamp: string | null = assistantTimestamp || null;

  // Debug logging
  console.log('Knowledge Search Debug:', {
    assistantContent,
    toolContent,
    isSuccess,
    toolTimestamp,
    assistantTimestamp
  });

  // Extract query from assistant content
  const assistantToolData = extractToolData(assistantContent);
  if (assistantToolData.toolResult) {
    query = assistantToolData.query || assistantToolData.arguments?.query || null;
  } else {
    // Fallback extraction for legacy format
    const contentStr = normalizeContentToString(assistantContent);
    if (contentStr) {
      // Try to extract from XML-style tags
      const queryMatch = contentStr.match(/<parameter name="query">([^<]+)<\/parameter>/);
      if (queryMatch) {
        query = queryMatch[1];
      }
      
      // Try to extract from function call arguments
      const argsMatch = contentStr.match(/query['":\s]*['"]([^'"]+)['"]/);
      if (argsMatch) {
        query = argsMatch[1];
      }
    }
  }

  // Extract data from tool content
  const toolContentStr = normalizeContentToString(toolContent);
  console.log('Tool Content String:', toolContentStr);
  
  if (toolContentStr) {
    try {
      // Try to parse as JSON first
      let toolData: any;
      
      // Handle different response formats
      if (toolContentStr.includes('ToolResult')) {
        console.log('Found ToolResult format');
        // Extract ToolResult content
        const toolResultMatch = toolContentStr.match(/ToolResult\([^)]*output=['"](.*?)['"][^)]*\)/);
        if (toolResultMatch) {
          try {
            // Clean up escaped JSON
            const cleanJson = toolResultMatch[1]
              .replace(/\\"/g, '"')
              .replace(/\\n/g, '\n')
              .replace(/\\t/g, '\t');
            toolData = JSON.parse(cleanJson);
          } catch (e) {
            console.warn('Failed to parse ToolResult output as JSON:', e);
          }
        }
      } else {
        console.log('Trying direct JSON parsing');
        // Try direct JSON parsing
        toolData = JSON.parse(toolContentStr);
      }

      console.log('Parsed tool data:', toolData);

      if (toolData) {
        // Extract from direct format
        if (toolData.output) {
          const output = toolData.output;
          results = output.results || [];
          indexName = output.index || null;
          description = output.description || null;
          query = query || output.query || null;
          actualIsSuccess = toolData.success !== false;
        } else if (toolData.results) {
          // Direct results format
          results = toolData.results || [];
          indexName = toolData.index || null;
          description = toolData.description || null;
          query = query || toolData.query || null;
          actualIsSuccess = toolData.success !== false;
        } else {
          // Check if toolData itself contains the result fields
          if (Array.isArray(toolData)) {
            // toolData is an array of results
            results = toolData;
          } else {
            // Check for other possible formats
            results = toolData.data || toolData.search_results || [];
            indexName = toolData.index || toolData.index_name || null;
            description = toolData.description || null;
            query = query || toolData.query || null;
            actualIsSuccess = toolData.success !== false;
          }
        }

        // Try to extract knowledge base name from description or index name
        if (description && description.includes('This is the')) {
          // Extract name from description like "This is the NECA Manual..."
          const nameMatch = description.match(/This is the ([^,]+)/);
          if (nameMatch) {
            knowledgeBaseName = nameMatch[1].trim();
          }
        }

        // If no name from description, try to clean up index name
        if (!knowledgeBaseName && indexName) {
          knowledgeBaseName = indexName
            .replace(/-/g, ' ')
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        }
      }

    } catch (e) {
      console.warn('Failed to parse knowledge search tool content:', e);
      
      // Fallback: try to extract basic info from raw content
      const resultsMatch = toolContentStr.match(/"results":\s*\[([^\]]*(?:\[[^\]]*\][^\]]*)*)\]/);
      if (resultsMatch) {
        try {
          const resultsStr = '[' + resultsMatch[1] + ']';
          results = JSON.parse(resultsStr);
        } catch (e2) {
          console.warn('Failed to parse fallback results:', e2);
        }
      }

      const indexMatch = toolContentStr.match(/"index":\s*"([^"]+)"/);
      if (indexMatch) {
        indexName = indexMatch[1];
      }

      const descMatch = toolContentStr.match(/"description":\s*"([^"]+)"/);
      if (descMatch) {
        description = descMatch[1];
      }
    }
  }

  // Ensure results are properly formatted
  if (results && Array.isArray(results)) {
    results = results.map((result, index) => ({
      rank: result.rank || index + 1,
      score: result.score || 0,
      text: result.text || '',
      metadata: result.metadata || {}
    }));
  } else {
    results = [];
  }

  const finalResult = {
    query,
    results,
    indexName,
    knowledgeBaseName,
    description,
    actualIsSuccess,
    actualToolTimestamp,
    actualAssistantTimestamp
  };

  console.log('Final Knowledge Search Result:', finalResult);
  
  return finalResult;
} 