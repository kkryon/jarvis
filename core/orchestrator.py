from __future__ import annotations

import os
import json
import re
import html
from datetime import datetime
from typing import List, Dict, Any

import requests
from dotenv import load_dotenv

from core.config import (
    MAX_HISTORY_PAIRS, OPENROUTER_MODEL_NAME, OPENROUTER_API_URL, 
    MAX_TOOL_ITERATIONS, TOOL_CALL_PATTERN,
    VECTOR_DIR, EMBED_MODEL, MEMORY_REASONING_LLM_MODEL_NAME, DEBUG # Added DEBUG import
)
from agents import (
    RAGAgent,
    WebSearchAgent,
    FileSystemAgent,
    ComputationAgent,
    WebAPIAgent,
    KnowledgeToolsAgent,
    CodeDevelopmentAgent,
    DataAnalysisAgent,
    SystemEnvironmentAgent,
    ConversationMemoryAgent,
    UserPreferenceAgent,
    Agent # Base Agent class
)
from memory.memory_manager import MemoryManager # Added import

# ────────────────────────────────────────────────────────────────────────
# 3. ORCHESTRATOR
# ────────────────────────────────────────────────────────────────────────
class Orchestrator:
    def __init__(self, max_history: int = MAX_HISTORY_PAIRS):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            try:
                load_dotenv()
                self.api_key = os.getenv("OPENROUTER_API_KEY")
                if not self.api_key:
                    raise ValueError("OPENROUTER_API_KEY environment variable not set, and not found in .env file.")
                print("Orchestrator: Loaded OPENROUTER_API_KEY from .env file.")
            except ImportError:
                raise ValueError("OPENROUTER_API_KEY environment variable not set. Consider `pip install python-dotenv` to load from a .env file.")
            except ValueError as e:
                raise e

        self.max_history = max_history
        self.agents: Dict[str, Agent] = {}
        self.tool_to_agent_map: Dict[str, Agent] = {}
        self.all_tool_schemas: List[Dict[str, Any]] = []
        
        # Initialize MemoryManager early, as other agents might depend on it or its configuration
        self.memory_manager = MemoryManager(
            db_path=None, 
            chroma_path=VECTOR_DIR,
            embedding_model_name=EMBED_MODEL
        )
        print(f"Orchestrator: MemoryManager initialized with Chroma path: {VECTOR_DIR} and Embed Model: {EMBED_MODEL}")
        if DEBUG:
            try:
                convo_count = self.memory_manager.vector_store.get_conversation_collection_count()
                print(f"Orchestrator: Initial conversation collection ('{self.memory_manager.vector_store.convo_collection_name}') count: {convo_count}")
            except Exception as e:
                print(f"[WARN] Orchestrator: Could not get initial conversation collection count: {e}")

        self._register_agents()
        self._collect_all_tool_schemas()

        self.base_system_prompt_content = self._build_base_system_content()
        self.messages: List[Dict[str, Any]] = [{"role": "system", "content": self._get_effective_system_prompt()}]
        
        print(f"Orchestrator: Initialized to use OpenRouter API with model {OPENROUTER_MODEL_NAME}.")

    def _register_agents(self):
        print("Orchestrator: Registering agents...")
        common_kwargs = {"orchestrator": self}
        
        self.agents = {
            "rag": RAGAgent(**common_kwargs),
            "web_search": WebSearchAgent(**common_kwargs),
            "file_system": FileSystemAgent(**common_kwargs),
            "computation": ComputationAgent(**common_kwargs),
            "web_api": WebAPIAgent(**common_kwargs),
            "knowledge": KnowledgeToolsAgent(**common_kwargs),
            "code_dev": CodeDevelopmentAgent(**common_kwargs),
            "system_env": SystemEnvironmentAgent(**common_kwargs),
            "memory": ConversationMemoryAgent(**common_kwargs),
            "user_prefs": UserPreferenceAgent(**common_kwargs),
            "data_analysis": DataAnalysisAgent(**common_kwargs), 
        }
        print(f"Orchestrator: {len(self.agents)} agents registered.")

    def _collect_all_tool_schemas(self):
        self.all_tool_schemas = []
        self.tool_to_agent_map = {}
        for agent_name, agent_instance in self.agents.items():
            schemas = agent_instance.get_tool_json_schemas()
            for schema in schemas:
                tool_name = schema.get("name")
                if tool_name:
                    if tool_name in self.tool_to_agent_map:
                        # This is a significant warning, should probably stay or be logged robustly
                        print(f"[Warning] Duplicate tool name '{tool_name}' found. Agent '{agent_name}' overwriting previous.")
                    self.tool_to_agent_map[tool_name] = agent_instance
                    self.all_tool_schemas.append(schema)
        print(f"Orchestrator: Collected {len(self.all_tool_schemas)} tool schemas from agents.")

    def _build_base_system_content(self) -> str:
        return f"""You are **JARVIS**, a hyper-analytical, forward-thinking AI orchestrator running in a zero-trust sandbox.
            Your prime directive is to deliver the most accurate, actionable, and insight-rich answers possible by ruthlessly exploiting every tool at your disposal.

            **Mindset**
            Adopt a skeptical scientist's stance: question premises, hunt for hidden variables, and flag uncertainty explicitly.
            Form strong, defensible opinions—then actively try to break them.
            Sprinkle quick, clever humor where it sharpens attention (never where it clouds precision).

            **Cognitive Workflow (ReAct+)**
            1. **Reflect (<think>)**\u2003Draft a step-by-step plan before each action.
            2. **Search & Cross-Examine**\u2003Triangulate facts via multiple tools when stakes or ambiguity are high.
            3. **Execute (tool_call)**\u2003Invoke the set of tools needed to advance the plan, one block per call.
            4. **Verify**\u2003Compare tool outputs against expectations; retry or branch if anomalies surface.
            5. **Synthesize**\u2003Distill findings into a concise, technically rigorous answer that a domain expert would trust.
            6. **Meta-Review**\u2003Quick internal check: "Does this fully resolve the user's question? Did I miss a cheaper/better tool?"

            **Style Rules**
            Prefer dense, information-rich prose; banish fluff.
            Cite concrete numbers, dates, and references where relevant.
            When humor fits, keep it razor-sharp and one-liner-tight.
            Never expose chain-of-thought or raw tool outputs to the user—only polished conclusions.

            **Safety & Sanity**
            Treat shell commands as live explosives: refuse or request confirmation if destructive, interactive, or privileged.
            If a tool response seems suspicious, corrupt, or policy-violating, pause and request clarification instead of propagating error.

            **Memory**
            You have access to a comprehensive long-term memory system. 
            Accurate synthesized context from your long-term memory (documents or past conversations) is often provided to you for the current query. 
            You should generally trust and prioritize utilizing this information directly to answer the user or guide your next steps. 
            Only seek to re-verify facts from the synthesized context using tools if the context itself expresses uncertainty, 
            if the user's query explicitly asks for the absolute latest information superseding the context, 
            or if you have a strong, articulable reason to believe the context might be outdated for the specific question at hand. 
            Otherwise, assume the synthesized context is a reliable foundation.
            - **User Preferences:** You can store and recall specific user preferences (e.g., 'remember my favorite color is blue').
            - **Knowledge Base:** You can retrieve relevant information from a local knowledge base of documents.
            - **Conversation History:** You can semantically search through past conversation turns to recall context.
            Use the provided tools to interact with these memory functions. Store only conversation-relevant facts. Purge trivial or sensitive data quickly if not meant for long-term preference or knowledge. Today's date is {datetime.now().strftime('%Y-%m-%d')}.

            **Operational Context**
            Today's date: {datetime.now().strftime('%Y-%m-%d')}.
            """
    
    def _get_effective_system_prompt(self) -> str:
        base_content = self.base_system_prompt_content
        if not self.all_tool_schemas:
            return base_content

        formatted_tools_list = json.dumps(self.all_tool_schemas, indent=2)
        
        system_prompt_with_tools = (
            f"{base_content}\n\n"
            "# Tools\n"
            "## Available Tools\n"
            "You have access to the following tools:\n"
            "```json\n"
            f"{formatted_tools_list}\n"
            "```\n"
            "To use a tool, you must respond with a JSON object enclosed in a `<tool_call>` XML tag. "
            "The JSON object should have a 'name' key with the function name (string) and an 'arguments' key with a JSON object of the arguments. "
            "The arguments object should map parameter names (strings) to their values. All argument values should be of the correct type. "
            "If a tool has no arguments, provide an empty JSON object for 'arguments'.\n"
            "For example:\n"
            "<tool_call>\n"
            '{\\n'
            '  "name": "example_tool_name",\\n'
            '  "arguments": {\\n'
            '    "arg1": "value1",\\n'
            '    "arg2": 123\\n'
            '  }\\n'
            '}\\n'
            "</tool_call>\n"
            "If you need to call multiple tools, provide multiple <tool_call> blocks in your response, one after the other."
        )
        return system_prompt_with_tools

    def _handle_tool_calls(self, assistant_content: str) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if DEBUG:
            print(f"[DEBUG] _handle_tool_calls: Received assistant_content for parsing. Type: {type(assistant_content)}")
            print(f"[DEBUG] _handle_tool_calls: Using TOOL_CALL_PATTERN.pattern: {TOOL_CALL_PATTERN.pattern}")
            print(f"[DEBUG] _handle_tool_calls: repr(assistant_content): {repr(assistant_content)}")

        tool_calls_found = []
        tool_results_for_history = []

        matches = list(TOOL_CALL_PATTERN.finditer(assistant_content))
        
        if not matches:
            if DEBUG:
                print(f"[DEBUG] Orchestrator: No tool calls found by new TOOL_CALL_PATTERN in assistant_content. Content was:\n{assistant_content}")
            return [], [] 

        if DEBUG:
            print(f"Orchestrator: Detected {len(matches)} tool call(s) using new pattern.")

        for match in matches:
            tool_call_inner_content = match.group(1).strip()
            if DEBUG:
                print(f"[DEBUG] _handle_tool_calls: Stripped content from match.group(1): {repr(tool_call_inner_content)}")
            try:
                tool_call_data = json.loads(tool_call_inner_content)
                tool_calls_found.append(tool_call_data) 

                tool_name = tool_call_data.get("name")
                tool_args = tool_call_data.get("arguments", {})

                if not tool_name:
                    print(f"Orchestrator: Invalid tool call - missing name: {tool_call_inner_content}") # Error, keep
                    result_content = f"[Error: Tool call missing 'name'. Call: {tool_call_inner_content}]"
                elif tool_name in self.tool_to_agent_map:
                    agent = self.tool_to_agent_map[tool_name]
                    print(f"Orchestrator: Executing tool '{tool_name}' from agent {agent.__class__.__name__} with args: {tool_args}") # Info, keep
                    result_content = agent.execute_tool(tool_name, tool_args)
                    if DEBUG:
                        print(f"Orchestrator: Tool '{tool_name}' result (first 200 chars): {result_content[:200]}...")
                else:
                    print(f"Orchestrator: Tool '{tool_name}' not recognized.") # Error, keep
                    result_content = f"[Error: Tool '{tool_name}' is not recognized or not mapped to any agent.]"
                
                tool_results_for_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call_data.get("id", tool_name),
                    "name": tool_name,
                    "content": result_content
                })

            except json.JSONDecodeError:
                print(f"Orchestrator: Invalid JSON in tool call. Stripped content was: {repr(tool_call_inner_content)}") # Error, keep
                tool_results_for_history.append({
                    "role": "tool",
                    "tool_call_id": f"parse_error_{len(tool_results_for_history)}", 
                    "name": "json_parse_error",
                    "content": f"[Error: Invalid JSON in tool call. Stripped content: {tool_call_inner_content[:1000]}]"
                })
        
        assert isinstance(tool_calls_found, list), \
            f"_handle_tool_calls: tool_calls_found should be a list, got {type(tool_calls_found)}"
        assert all(isinstance(item, dict) for item in tool_calls_found), \
            "_handle_tool_calls: all items in tool_calls_found should be dicts"
        
        assert isinstance(tool_results_for_history, list), \
            f"_handle_tool_calls: tool_results_for_history should be a list, got {type(tool_results_for_history)}"
        assert all(isinstance(item, dict) for item in tool_results_for_history), \
            "_handle_tool_calls: all items in tool_results_for_history should be dicts (or list is empty)"

        return tool_calls_found, tool_results_for_history

    def _prune_history_for_api(self, messages_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        last_true_user_turn_idx = -1
        for i in range(len(messages_history) - 1, -1, -1):
            msg = messages_history[i]
            if msg.get("role") == "user" and not msg.get("content", "").strip().startswith("<tool_response>"):
                last_true_user_turn_idx = i
                break
        
        if DEBUG:
            print(f"[DEBUG] _prune_history_for_api: last_true_user_turn_idx found at {last_true_user_turn_idx}")
            if last_true_user_turn_idx != -1 and last_true_user_turn_idx < len(messages_history):
                print(f"[DEBUG] _prune_history_for_api: Last true user message content: '{messages_history[last_true_user_turn_idx].get('content', '')[:50]}...'")

        if last_true_user_turn_idx == -1:
            if DEBUG:
                print("[DEBUG] _prune_history_for_api: No last_true_user_turn_idx found or list empty, returning original history.")
            return messages_history 

        pruned_messages = []
        for i, msg in enumerate(messages_history):
            new_msg = msg.copy()
            if msg.get("role") == "assistant" and i < last_true_user_turn_idx:
                content_before = new_msg.get("content", "")
                if DEBUG:
                    print(f"[DEBUG] _prune_history_for_api: Attempting to prune <think> from assistant message at index {i} (content: '{content_before[:70]}...')")
                cleaned_content = re.sub(r"<think>.*?</think>\s*", "", content_before, flags=re.DOTALL).strip()
                new_msg["content"] = cleaned_content
                if DEBUG and content_before != cleaned_content:
                    print(f"[DEBUG] _prune_history_for_api: Pruned <think> block. Index {i}. Before: '{content_before[:70]}...', After: '{cleaned_content[:70]}...'")
                elif DEBUG and content_before == cleaned_content:
                     print(f"[DEBUG] _prune_history_for_api: No <think> block found or pruned for assistant message at index {i}. Content: '{content_before[:70]}...'")
            pruned_messages.append(new_msg)
        
        return pruned_messages

    def chat(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})

        synthesized_context_for_main_llm = ""
        try:
            if DEBUG:
                print("[DEBUG] Orchestrator: Proactively retrieving and synthesizing memory context...")
            doc_snippets = self.memory_manager.query_knowledge_base(user_input, n_results=3) 
            convo_snippets = self.memory_manager.recall_relevant_interactions(user_input, n_results=3)
            
            if doc_snippets or convo_snippets:
                if DEBUG:
                    print(f"[DEBUG] Orchestrator: Found {len(doc_snippets)} doc snippets and {len(convo_snippets)} convo snippets for contextualization.")
                synthesized_context_for_main_llm = self._invoke_memory_reasoning_llm(user_input)
                if synthesized_context_for_main_llm and DEBUG:
                    print(f"[DEBUG] Orchestrator: Successfully synthesized memory context: {synthesized_context_for_main_llm[:200]}...")
            elif DEBUG:
                print("[DEBUG] Orchestrator: No initial document or conversation snippets found for query.")
        except Exception as e:
            print(f"[ERROR] Orchestrator: Error during proactive memory synthesis: {e}") # Error, keep

        if len(self.messages) > (self.max_history * 2 + 1):
            self.messages = [self.messages[0]] + self.messages[-(self.max_history * 2):]

        final_llm_output_for_user_processing = ""

        current_llm_response_text_for_history, current_llm_response_content_for_tool_parse = self._get_llm_response(
            self.messages, 
            synthesized_context=synthesized_context_for_main_llm
        )

        for iteration in range(MAX_TOOL_ITERATIONS):
            if DEBUG:
                print(f"\n[DEBUG] Orchestrator: Tool Processing Iteration {iteration + 1}")
                print(f"[DEBUG] Orchestrator: LLM Response (for history) for this iteration:\n{current_llm_response_text_for_history[:500]}...")
                print(f"[DEBUG] Orchestrator: LLM Content (for tool parsing) for this iteration:\n{current_llm_response_content_for_tool_parse[:500]}...")

            think_block_match = re.search(r"<think>(.*?)</think>", current_llm_response_text_for_history, re.DOTALL)
            if think_block_match and DEBUG: # Make display of think block conditional
                print(f"\n<think>{think_block_match.group(1).strip()}</think>\n")
            
            requested_tool_calls_by_llm, tool_results_for_next_llm_prompt = self._handle_tool_calls(current_llm_response_content_for_tool_parse)

            assistant_message_for_history = {"role": "assistant", "content": current_llm_response_text_for_history}
            if requested_tool_calls_by_llm:
                assistant_message_for_history["tool_calls"] = requested_tool_calls_by_llm
            self.messages.append(assistant_message_for_history)

            if tool_results_for_next_llm_prompt:
                for tool_result_msg in tool_results_for_next_llm_prompt:
                    self.messages.append(tool_result_msg)

                if len(self.messages) > (self.max_history * 3 + 1 + len(tool_results_for_next_llm_prompt)): 
                     self.messages = [self.messages[0]] + self.messages[-(self.max_history * 3 + len(tool_results_for_next_llm_prompt)):]

                current_llm_response_text_for_history, current_llm_response_content_for_tool_parse = self._get_llm_response(
                    self.messages,
                    synthesized_context=synthesized_context_for_main_llm 
                )
            else:
                final_llm_output_for_user_processing = current_llm_response_text_for_history
                if DEBUG:
                    print(f"[DEBUG] Orchestrator: No further tool calls or results. Exiting tool loop. Iteration {iteration + 1}.")
                break
        else: 
            print(f"[WARN] Orchestrator: Exceeded max tool iterations ({MAX_TOOL_ITERATIONS}). Using last assistant response as final.") # Warning, keep

        text_to_clean = final_llm_output_for_user_processing
        last_think_end_idx = text_to_clean.rfind("</think>")
        if last_think_end_idx != -1:
            text_to_clean = text_to_clean[last_think_end_idx + len("</think>"):].lstrip()
        else:
            think_start_idx = text_to_clean.find("<think>")
            if think_start_idx != -1: 
                if text_to_clean.strip().startswith("<think>"): 
                    text_to_clean = "" 
                else: 
                    text_to_clean = text_to_clean[:think_start_idx].rstrip()
        
        text_to_clean = TOOL_CALL_PATTERN.sub("", text_to_clean)
        
        text_to_clean = text_to_clean.replace("<|im_end|>", "")
        text_to_clean = text_to_clean.replace("<|im_start|>", "")

        final_user_visible_response = text_to_clean.strip()
        try:
            self.memory_manager.log_interaction(
                user_utterance=user_input, 
                agent_response=final_user_visible_response
            )
            if DEBUG:
                print(f"[DEBUG] Orchestrator: Logged interaction to MemoryManager. User: '{user_input[:50]}...' Agent: '{final_user_visible_response[:50]}...'")
        except Exception as e:
            print(f"[ERROR] Orchestrator: Failed to log interaction to MemoryManager: {e}") # Error, keep

        return html.unescape(final_user_visible_response)

    def _invoke_memory_reasoning_llm(self, main_user_query: str, max_mem_reasoning_iterations: int = 15) -> str:
        if DEBUG:
            print(f"[DEBUG] Orchestrator: Invoking Memory Reasoning LLM for query: '{main_user_query[:100]}...'")

        memory_reasoner_system_prompt = (
            "You are a specialized Memory Analysis AI. Your sole purpose is to deeply understand a provided 'Main User Query' "
            "and then use a limited set of tools to find the most relevant information from long-term memory (past conversations and documents). "
            "After retrieving information, critically analyze and synthesize it into a single, concise, factual summary paragraph. "
            "This summary will be passed to another, primary AI to help it answer the Main User Query. "
            "Focus on extracting key facts, entities, past conclusions, or context that directly bears on the Main User Query. "
            "Prioritize information that seems most useful for the primary AI to formulate its own response. "
            "Your primary task is to use your search tools. Attempt to find relevant information for most queries. "
            "Only if your focused search attempts (try at least one relevant tool call if unsure) yield no useful information, "
            "or if the query is exceptionally trivial and clearly unrelated to past data (e.g. 'hello'), "
            "should you then output *exclusively and only* the following phrase: 'No specific memory context deemed necessary or found.' "
            "If you output this specific phrase, your response for that turn MUST contain nothing else (no tool calls, no other text). "
            "Otherwise, provide ONLY your synthesized summary (if you are done searching) or ONLY tool calls (if you need more information). "
            "Do not add any conversational fluff, greetings, or attempt to answer the Main User Query yourself."
        )
        memory_reasoner_tools = [
            {
                "name": "search_past_conversations",
                "description": "Searches through long-term conversation history for interactions semantically similar to the search_query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {"type": "string", "description": "The specific query or topic to search for in past conversation history. This query has to be well crafted to retrieve relevant information."},
                        "num_results": {"type": "integer", "description": "Number of relevant interactions to retrieve.", "default": 3}
                    },
                    "required": ["search_query"]
                }
            },
            {
                "name": "search_documents",
                "description": "Searches through the indexed document knowledge base for information relevant to the search_query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_query": {"type": "string", "description": "The specific query or topic to search for in documents."},
                        "num_results": {"type": "integer", "description": "Number of relevant document snippets to retrieve.", "default": 3}
                    },
                    "required": ["search_query"]
                }
            }
        ]
        formatted_memory_tools = json.dumps(memory_reasoner_tools, indent=2)
        memory_reasoner_system_prompt_with_tools = (
            f"{memory_reasoner_system_prompt}\n\n"
            "# Memory Search Tools\n"
            "You have access to the following tools to search memory. Use them as needed.\n"
            "```json\n"
            f"{formatted_memory_tools}\n"
            "```\n"
            "To use a tool, you MUST respond with a JSON object enclosed in a <tool_call> XML tag. "
            "The JSON object should have a 'name' key with the function name (string) and an 'arguments' key with a JSON object of the arguments. "
            "The arguments object should map parameter names (strings) to their values. All argument values should be of the correct type as specified in the tool's parameters. "
            "If a tool has no arguments, provide an empty JSON object for 'arguments'. "
            "Ensure the closing tag is correctly formatted as </tool_call>.\n"
            "For example:\n"
            "<tool_call>\n"
            '{\n'
            '  "name": "search_past_conversations",\n'
            '  "arguments": {\n'
            '    "search_query": "details about project X",\n'
            '    "num_results": 2\n'
            '  }\n'
            '}\n'
            "</tool_call>"
        )

        memory_reasoner_messages = [
            {"role": "system", "content": memory_reasoner_system_prompt_with_tools},
            {"role": "user", "content": f"Main User Query to analyze: \"{main_user_query}\""}
        ]
        final_synthesis = ""

        for i in range(max_mem_reasoning_iterations):
            if DEBUG:
                print(f"[DEBUG] Memory Reasoning LLM - Iteration {i+1}")
            payload = {
                "model": MEMORY_REASONING_LLM_MODEL_NAME,
                "messages": memory_reasoner_messages,
                "temperature": 0.6, 
                "max_tokens": 4096,
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

            if DEBUG:
                print(f"\n--- MR LLM API REQUEST (Iteration {i+1}) ---")
                try:
                    print(json.dumps(payload, indent=2))
                except TypeError:
                     print("[WARN] MR LLM Payload not fully serializable for pretty print, printing as dict:")
                     print(payload)
                print("--- END MR LLM API REQUEST ---\n")

            try:
                response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(payload), timeout=120)
                response.raise_for_status()
                response_data = response.json()

                if DEBUG:
                    print(f"\n--- MR LLM API RESPONSE (Iteration {i+1}) ---")
                    try:
                        print(json.dumps(response_data, indent=2))
                    except TypeError:
                        print("[WARN] MR LLM Response not fully serializable for pretty print, printing as dict:")
                        print(response_data)
                    print("--- END MR LLM API RESPONSE ---")

                assistant_response_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if DEBUG:
                    print(f"[DEBUG] Memory Reasoning LLM response content (Iteration {i+1}): {assistant_response_content[:300]}...")

                memory_reasoner_messages.append({"role": "assistant", "content": assistant_response_content})
                tool_calls = list(TOOL_CALL_PATTERN.finditer(assistant_response_content))
                if not tool_calls:
                    final_synthesis = assistant_response_content
                    break 
                
                for tool_call_match in tool_calls:
                    tool_call_content = tool_call_match.group(1).strip()
                    try:
                        tool_call_data = json.loads(tool_call_content)
                        tool_name = tool_call_data.get("name")
                        tool_args = tool_call_data.get("arguments", {})
                        result_content = "[Error: Tool not recognized by Memory Reasoner]"

                        if tool_name == "search_past_conversations":
                            query = tool_args.get("search_query", main_user_query)
                            num = tool_args.get("num_results", 3)
                            snippets = self.memory_manager.recall_relevant_interactions(query, n_results=num)
                            result_content = json.dumps(snippets) if snippets else "[No relevant conversation snippets found.]"
                        elif tool_name == "search_documents":
                            query = tool_args.get("search_query", main_user_query)
                            num = tool_args.get("num_results", 3)
                            snippets = self.memory_manager.query_knowledge_base(query, n_results=num)
                            result_content = json.dumps(snippets) if snippets else "[No relevant document snippets found.]"
                        
                        memory_reasoner_messages.append({"role": "tool", "name": tool_name, "content": result_content, "tool_call_id": tool_call_data.get("id",tool_name) })
                    except json.JSONDecodeError:
                        memory_reasoner_messages.append({"role": "tool", "name": "json_error", "content": "[Error: Invalid JSON in tool call]", "tool_call_id": "json_error_0"})
            
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Memory Reasoning LLM API request failed: {e}") # Error, keep
                final_synthesis = "[Memory reasoning failed due to API error.]"
                break
            except Exception as e:
                print(f"[ERROR] Unexpected error during Memory Reasoning LLM interaction: {e}") # Error, keep
                final_synthesis = "[Memory reasoning failed due to unexpected error.]"
                break
        else: 
            if not final_synthesis and memory_reasoner_messages[-1]["role"] == "assistant":
                 final_synthesis = memory_reasoner_messages[-1]["content"]
            elif not final_synthesis:
                final_synthesis = "[Memory reasoning reached max iterations without a clear synthesis.]"
        
        if final_synthesis and list(TOOL_CALL_PATTERN.finditer(final_synthesis)) and DEBUG:
            print(f"[WARN] Orchestrator: Memory Reasoning LLM's final output was a tool call, not a synthesis: {final_synthesis[:300]}...")
            final_synthesis = "[Memory reasoning process concluded with an unprocessed tool call instead of a textual summary.]"

        if "No specific memory context deemed necessary or found." in final_synthesis:
            if DEBUG: print("[DEBUG] Memory Reasoning LLM deemed no context necessary.")
            return "" 

        if not final_synthesis.strip(): 
            if DEBUG: print("[DEBUG] Orchestrator: Synthesized context is empty or became empty after processing.")
            return ""

        if DEBUG:
            print(f"[DEBUG] Orchestrator: Final synthesized context from Memory Reasoning LLM: {final_synthesis[:300]}...")
            print("\n--- FINAL MR LLM Conversation History (for this invocation) ---")
            try:
                print(json.dumps(memory_reasoner_messages, indent=2))
            except TypeError:
                print("[WARN] MR LLM Messages not fully serializable for pretty print, printing as list:")
                print(memory_reasoner_messages)
            print("--- END FINAL MR LLM Conversation History ---")

        if self.memory_manager and memory_reasoner_messages:
            try:
                current_user_id = self.memory_manager.default_user_id 
                self.memory_manager.log_reasoning_trace(
                    reasoning_messages=memory_reasoner_messages,
                    trace_type="memory_reasoner_dialogue",
                    user_id=current_user_id, 
                    related_query=main_user_query
                )
                if DEBUG:
                    print(f"[DEBUG] Orchestrator: Logged memory_reasoner_messages to MemoryManager.")
            except Exception as e:
                print(f"[ERROR] Orchestrator: Failed to log memory_reasoner_messages: {e}") # Error, keep

        return final_synthesis.strip()

    def _get_llm_response(self, current_messages_for_prompt: List[Dict[str, Any]], synthesized_context: str | None = None) -> tuple[str, str]:
        pruned_history_for_api = self._prune_history_for_api(current_messages_for_prompt)
        api_payload_messages = []
        api_payload_messages.append({"role": "system", "content": self._get_effective_system_prompt()})
        
        if synthesized_context and synthesized_context.strip():
            if DEBUG:
                print(f"[DEBUG] Orchestrator: Injecting synthesized memory context into main LLM prompt: {synthesized_context}")
            api_payload_messages.append({
                "role": "system", 
                "name": "memory_synthesis", 
                "content": f"HINT: The following synthesized memory context may be relevant to the user's query:\n<synthesized_context>\n{synthesized_context.strip()}\n</synthesized_context>\nRemember to critically evaluate this hint alongside other information and tools."
            })

        start_index = 0
        if pruned_history_for_api and pruned_history_for_api[0].get("role") == "system":
            start_index = 1 
        
        for i in range(start_index, len(pruned_history_for_api)):
            msg = pruned_history_for_api[i]
            role = msg.get("role")

            if role == "tool":
                tool_output_string = msg.get('content', '')
                if not isinstance(tool_output_string, str):
                    if DEBUG: # This is a notable warning, could be just DEBUG
                        print(f"[WARN] _get_llm_response: 'tool' role message content is not a string. Converting. Original type: {type(tool_output_string)}. Value: {tool_output_string}")
                    tool_output_string = str(tool_output_string)

                if tool_output_string and not tool_output_string.strip().endswith("."):
                    tool_output_string += "."
                
                api_message_content = f"<tool_response>\n{tool_output_string.strip()}\n</tool_response>"
                api_payload_messages.append({"role": "user", "content": api_message_content})
            elif role == "assistant":
                api_payload_messages.append({"role": "assistant", "content": msg.get("content", "")})
            elif role == "user":
                api_payload_messages.append({"role": "user", "content": msg.get("content", "")})
            elif DEBUG: # Log skipped messages only in debug
                print(f"[Warning] _get_llm_response: Skipping message with unknown role: {role}")

        payload = {
            "model": OPENROUTER_MODEL_NAME,
            "messages": api_payload_messages,
            "temperature": 0.6, 
            "top_p": 0.9,
            "max_tokens": 4096,
        }
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        if DEBUG:
            print(f"\n--- API REQUEST TO OPENROUTER ---")
            try:
                print(f"URL: {OPENROUTER_API_URL}") # URL might be sensitive for non-debug
                print(f"Headers: {headers}") # Headers contain API key, definitely debug only
                print(f"Payload: {json.dumps(payload, indent=2)}")
            except TypeError:
                 print("[WARN] API Payload not fully serializable for pretty print, printing as dict:")
                 print(payload)
            print("--- END API REQUEST ---\n")

        try:
            response = requests.post(OPENROUTER_API_URL, headers=headers, data=json.dumps(payload), timeout=180)
            response.raise_for_status()
            response_data = response.json()

            if DEBUG:
                print(f"\n--- API RESPONSE FROM OPENROUTER ---")
                try:
                    print(json.dumps(response_data, indent=2))
                except TypeError:
                    print("[WARN] API Response not fully serializable for pretty print, printing as dict:")
                    print(response_data)
                print("--- END API RESPONSE ---\n")
            
            choice = response_data.get("choices", [{}])[0]
            message_from_api = choice.get("message", {})
            api_content = message_from_api.get("content", "")
            api_reasoning = message_from_api.get("reasoning")
            llm_generated_text = api_content if api_content is not None else ""

            if api_reasoning and isinstance(api_reasoning, str) and api_reasoning.strip():
                if DEBUG:
                    print(f"[DEBUG] Orchestrator: API response included a 'reasoning' field: '{api_reasoning[:100]}...'")
                think_block_from_reasoning = f"<think>\n{api_reasoning.strip()}\n</think>"
                current_content_for_check = api_content if api_content is not None else ""
                if current_content_for_check.strip().startswith(think_block_from_reasoning):
                    if DEBUG:
                        print(f"[DEBUG] Orchestrator: Reasoning field content appears to be already at the start of main content. Using main content as is.")
                    llm_generated_text = current_content_for_check
                else:
                    separator = "\n" if llm_generated_text else ""
                    llm_generated_text = f"{think_block_from_reasoning}{separator}{llm_generated_text}"
                    if DEBUG:
                        print(f"[DEBUG] Orchestrator: Prepended reasoning to content.")
            
            llm_generated_text_for_history = llm_generated_text
            api_content_for_tool_parsing = api_content

            return llm_generated_text_for_history, api_content_for_tool_parsing

        except requests.exceptions.Timeout:
            print(f"Orchestrator: OpenRouter API request timed out after {180} seconds.") # Error, keep
            return "[Error: API request timed out.]", "[Error: API request timed out.]"
        except requests.exceptions.RequestException as e: # Error, keep
            error_content = ""
            if e.response is not None:
                try:
                    error_details = e.response.json()
                    error_content = f" Status: {e.response.status_code}, Details: {json.dumps(error_details)}"
                except json.JSONDecodeError:
                    error_content = f" Status: {e.response.status_code}, Raw: {e.response.text[:500]}"
            print(f"Orchestrator: OpenRouter API request failed: {e}{error_content}")
            error_message = f"[Error: API request failed.{error_content or str(e)}]"
            return error_message, error_message
        except json.JSONDecodeError as e: # Error, keep
            print(f"Orchestrator: Failed to decode JSON response from OpenRouter API: {e}")
            error_message = f"[Error: Could not parse API response. Detail: {e}]"
            return error_message, error_message
        except Exception as e: # Error, keep
            import traceback
            print(f"Orchestrator: Unexpected error in _get_llm_response: {type(e).__name__} - {e}\n{traceback.format_exc()}")
            error_message = f"[Error: An unexpected error occurred while contacting the API. Detail: {type(e).__name__} - {e}]"
            return error_message, error_message 