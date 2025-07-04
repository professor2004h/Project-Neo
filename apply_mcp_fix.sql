-- Apply MCP sharing fix for marketplace agents
-- This updates the add_agent_to_library function to properly handle custom_mcps

-- Update add_agent_to_library function to include custom_mcps and respect sharing preferences
DROP FUNCTION IF EXISTS add_agent_to_library(UUID, UUID);

CREATE OR REPLACE FUNCTION add_agent_to_library(
    p_original_agent_id UUID,
    p_user_account_id UUID
)
RETURNS UUID
SECURITY DEFINER
LANGUAGE plpgsql
AS $$
DECLARE
    v_new_agent_id UUID;
    v_original_agent agents%ROWTYPE;
    v_sharing_prefs JSONB;
    v_knowledge_bases JSONB;
    v_configured_mcps JSONB;
    v_custom_mcps JSONB;
BEGIN
    SELECT * INTO v_original_agent
    FROM agents 
    WHERE agent_id = p_original_agent_id AND is_public = true;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Agent not found or not public';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM user_agent_library 
        WHERE user_account_id = p_user_account_id 
        AND original_agent_id = p_original_agent_id
    ) THEN
        RAISE EXCEPTION 'Agent already in your library';
    END IF;
    
    -- Get sharing preferences
    v_sharing_prefs := COALESCE(v_original_agent.sharing_preferences, '{"include_knowledge_bases": true, "include_custom_mcp_tools": true}'::jsonb);
    
    -- Apply sharing preferences
    v_knowledge_bases := CASE 
        WHEN (v_sharing_prefs->>'include_knowledge_bases')::boolean = true 
        THEN COALESCE(v_original_agent.knowledge_bases, '[]'::jsonb)
        ELSE '[]'::jsonb
    END;
    
    v_configured_mcps := CASE 
        WHEN (v_sharing_prefs->>'include_custom_mcp_tools')::boolean = true 
        THEN COALESCE(v_original_agent.configured_mcps, '[]'::jsonb)
        ELSE '[]'::jsonb
    END;
    
    v_custom_mcps := CASE 
        WHEN (v_sharing_prefs->>'include_custom_mcp_tools')::boolean = true 
        THEN COALESCE(v_original_agent.custom_mcps, '[]'::jsonb)
        ELSE '[]'::jsonb
    END;
    
    INSERT INTO agents (
        account_id,
        name,
        description,
        system_prompt,
        configured_mcps,
        custom_mcps,
        agentpress_tools,
        knowledge_bases,
        is_default,
        is_public,
        tags,
        avatar,
        avatar_color
    ) VALUES (
        p_user_account_id,
        v_original_agent.name || ' (from marketplace)',
        v_original_agent.description,
        v_original_agent.system_prompt,
        v_configured_mcps,
        v_custom_mcps,
        v_original_agent.agentpress_tools,
        v_knowledge_bases,
        false,
        false,
        v_original_agent.tags,
        v_original_agent.avatar,
        v_original_agent.avatar_color
    ) RETURNING agent_id INTO v_new_agent_id;
    
    INSERT INTO user_agent_library (
        user_account_id,
        original_agent_id,
        agent_id
    ) VALUES (
        p_user_account_id,
        p_original_agent_id,
        v_new_agent_id
    );
    
    UPDATE agents 
    SET download_count = download_count + 1 
    WHERE agent_id = p_original_agent_id;
    
    RETURN v_new_agent_id;
END;
$$;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION add_agent_to_library(UUID, UUID) TO authenticated; 