---
description: Plan to simplify project structure and improve code readability
---

# Project Simplification & Readability Improvement Plan

## Executive Summary

This plan outlines a comprehensive approach to simplify the Unibase Agent SDK project structure and improve code readability while maintaining all existing functionality. The plan is organized into phases with prioritized tasks.

---

## Current State Analysis

### Project Structure Overview
```
unibase-agent-sdk/
├── unibase_agent_sdk/
│   ├── __init__.py          (73 lines) - Main exports
│   ├── a2a/                  - A2A Protocol implementation
│   │   ├── types.py          (692 lines) ⚠️ Too large
│   │   ├── server.py         (445 lines) 
│   │   ├── client.py         (large)
│   │   └── agent_card.py
│   ├── adapters/             - LLM provider adapters
│   │   ├── claude_adapter.py
│   │   ├── openai_adapter.py
│   │   └── langchain_adapter.py
│   ├── agents/               - Framework agent wrappers
│   │   ├── crewai_agent.py
│   │   ├── autogen_agent.py
│   │   ├── phidata_agent.py
│   │   └── llamaindex_agent.py
│   ├── core/                 - Core types and base classes
│   │   ├── types.py          (100 lines) ✓ Clean
│   │   ├── base_agent.py     (138 lines) ✓ Clean
│   │   ├── base_memory.py    (small)
│   │   ├── proxy_utils.py    (242 lines) ✓ Well documented
│   │   └── exceptions.py
│   ├── memory/               - Memory management
│   │   ├── manager.py
│   │   ├── membase_client.py
│   │   ├── da_uploader.py
│   │   └── middlewares/      - 12 middleware implementations
│   ├── registry/             - Agent registry
│   │   ├── registry.py       (469 lines) ⚠️ Too large, mixes concerns
│   │   ├── identity.py
│   │   ├── auth.py
│   │   └── wallet.py
│   └── utils/                - Utilities
│       ├── logger.py
│       └── config.py (empty)
├── examples/                 - 6 example files
└── tests/                    - 6 test files
```

### Identified Issues

1. **Large Files with Mixed Responsibilities**
   - `registry.py` (469 lines) - Mixes registration, A2A discovery, AIP, Membase
   - `a2a/types.py` (692 lines) - All A2A types in one file

2. **Inconsistent Naming & Patterns**
   - Mix of Chinese and English comments
   - Inconsistent class naming (some factories, some direct classes)
   - Some files use `HAS_<LIB>` pattern, others don't

3. **Documentation Gaps**
   - Missing module-level docstrings in some files
   - Inconsistent docstring styles
   - Some TODO comments that need resolution

4. **Redundant Code**
   - Similar patterns across agent wrappers could be abstracted
   - Similar patterns across memory middlewares

5. **Organization Issues**
   - `utils/config.py` is nearly empty (27 bytes)
   - `a2a/` could be better organized

---

## Phase 1: Documentation & Comments Standardization (Low Risk)

### 1.1 Standardize Language in Comments
**Priority:** High  
**Risk:** Very Low  
**Effort:** Medium

- [ ] Convert all Chinese comments to English for consistency
- [ ] Affected files:
  - `core/base_agent.py` - "透明Agent代理" → "Transparent Agent Proxy"
  - `memory/manager.py` - "增强的Memory管理器" → "Enhanced Memory Manager"
  - `memory/middlewares/base.py` - All Chinese comments
  - `registry/registry.py` - All Chinese comments
  - `registry/identity.py` - All Chinese comments
  - `core/types.py` - "Agent类型枚举" etc.
  - `adapters/claude_adapter.py` - "Claude透明适配器"
  - All adapter and agent files

### 1.2 Add Missing Module Docstrings
**Priority:** Medium  
**Risk:** Very Low  
**Effort:** Low

- [ ] Add comprehensive module docstrings to:
  - `registry/__init__.py`
  - `memory/__init__.py`
  - `memory/middlewares/__init__.py`
  - `core/__init__.py`

### 1.3 Improve Inline Documentation
**Priority:** Medium  
**Risk:** Very Low  
**Effort:** Medium

- [ ] Add docstrings following Google style consistently
- [ ] Document all public methods with Args, Returns, Raises
- [ ] Add usage examples to complex classes

---

## Phase 2: Refactor Large Files (Medium Risk)

### 2.1 Split `registry/registry.py`
**Priority:** High  
**Risk:** Medium  
**Effort:** High

The `AgentRegistry` class has too many responsibilities. Split into:

```python
# registry/registry.py - Core registry (keep ~200 lines)
class AgentRegistry:
    """Core agent registration and lifecycle management."""
    - register_agent()
    - register_agent_instance()
    - get_agent()
    - get_identity()
    - list_agents()
    - update_agent_metadata()
    - close()

# registry/a2a_bridge.py - A2A integration (new, ~150 lines)
class A2ABridge:
    """A2A protocol integration for AgentRegistry."""
    - discover_a2a_agent()
    - list_discovered_agents()
    - send_a2a_task()
    - get_a2a_task()
    - cancel_a2a_task()

# registry/aip_client.py - AIP integration (new, ~100 lines)
class AIPClient:
    """AIP protocol client for agent registration."""
    - _register_to_aip()
    - _query_identity_from_aip()
    - _query_all_agents_from_aip()

# registry/membase_integration.py - Membase integration (new, ~50 lines)
class MembaseIntegration:
    """Membase memory space initialization."""
    - _initialize_membase()
```

### 2.2 Split `a2a/types.py`
**Priority:** Medium  
**Risk:** Medium  
**Effort:** Medium

The A2A types file is 692 lines. Organize by concept:

```python
# a2a/types/__init__.py - Re-exports all types
# a2a/types/base.py - Enums and basic parts (~100 lines)
  - TaskState, Role
  - TextPart, FilePart, DataPart, Part
  - part_to_dict(), dict_to_part()

# a2a/types/messages.py - Message-related types (~100 lines)
  - Message
  - Artifact
  - artifacts helpers

# a2a/types/tasks.py - Task-related types (~100 lines)
  - TaskStatus
  - Task
  - TaskSendParams, TaskQueryParams, etc.

# a2a/types/agent_card.py - Agent card types (~150 lines)
  - Skill
  - AgentCard
  - AgentAuthentication
  - AgentCapability
  - AgentProvider

# a2a/types/streaming.py - Streaming types (~100 lines)
  - StreamResponse
  - StreamingChunk
  - SSE helpers

# a2a/types/jsonrpc.py - JSON-RPC types (~100 lines)
  - JSONRPCRequest
  - JSONRPCResponse
  - JSONRPCError
  - A2AErrorCode
```

---

## Phase 3: Improve Agent Wrapper Consistency (Medium Risk)

### 3.1 Create Unified Agent Wrapper Base
**Priority:** Medium  
**Risk:** Medium  
**Effort:** Medium

Current agent wrappers have duplicated patterns. Create a shared mixin:

```python
# agents/base.py (new)
class UnibaseAgentMixin:
    """Mixin providing Unibase integration for agent wrappers."""
    
    _unibase_registry = None
    _unibase_memory = None
    _unibase_identity = None
    
    def _register_with_unibase(self, registry, agent_name: str, framework: str):
        """Register this agent with Unibase registry."""
        # Common registration logic
        
    @property
    def unibase_identity(self):
        """Get Unibase identity."""
        return self._unibase_identity
```

### 3.2 Standardize Factory Pattern
**Priority:** Low  
**Risk:** Medium  
**Effort:** Low

Standardize naming across all agent wrappers:
- `create_crewai_agent()` ✓
- `create_phi_agent()` ✓
- `create_autogen_assistant()` (rename from `AutoGenAssistant`)
- `create_llama_agent()` (rename from `LlamaAgent`)

---

## Phase 4: Remove Dead Code & TODOs (Low Risk)

### 4.1 Clean up Empty/Placeholder Files
**Priority:** Low  
**Risk:** Very Low  
**Effort:** Very Low

- [ ] `utils/config.py` - Either implement config loading or remove
- [ ] Review all `# TODO` comments and create GitHub issues

### 4.2 Review Type Annotations
**Priority:** Low  
**Risk:** Very Low  
**Effort:** Low

- [ ] Ensure all public APIs have complete type annotations
- [ ] Add `py.typed` marker for type checker support

---

## Phase 5: Improve Test Organization (Low Risk)

### 5.1 Organize Test Files
**Priority:** Low  
**Risk:** Very Low  
**Effort:** Low

Current test structure is flat. Consider:
```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_registry.py
│   ├── test_memory.py
│   └── test_types.py
├── integration/
│   ├── test_a2a_protocol.py
│   ├── test_agent_wrappers.py
│   └── test_all_sdks.py
└── examples/
    └── test_example_scripts.py
```

---

## Phase 6: Enhance Type System (Medium Risk)

### 6.1 Use Protocols for Better Typing
**Priority:** Low  
**Risk:** Low  
**Effort:** Medium

```python
# core/protocols.py (new)
from typing import Protocol, runtime_checkable

@runtime_checkable
class Agent(Protocol):
    """Protocol defining agent interface."""
    
    @property
    def agent_id(self) -> str: ...
    async def send_to_agent(self, to_agent_id: str, message: dict) -> dict: ...

@runtime_checkable
class MemoryProvider(Protocol):
    """Protocol defining memory provider interface."""
    
    async def save(self, record: 'MemoryRecord') -> str: ...
    async def retrieve(self, session_id: str, limit: int = 10) -> list: ...
```

---

## Implementation Priority Order

### Immediate (Week 1) ✅ COMPLETED
1. **Phase 1.1** - Standardize comments to English ✅
2. **Phase 4.1** - Clean up dead code ✅

### Short-term (Week 2-3)
3. **Phase 1.2** - Add missing docstrings
4. **Phase 2.1** - Split registry.py (biggest impact)

### Medium-term (Week 4-5)
5. **Phase 2.2** - Split a2a/types.py
6. **Phase 3.1** - Create agent wrapper base

### Long-term (Week 6+)
7. **Phase 5.1** - Organize tests
8. **Phase 6.1** - Add Protocols
9. **Phase 3.2** - Standardize factory patterns

---

## Breaking Changes Watch List

### High Risk Changes (Require Export Aliases)
- Splitting `AgentRegistry` class
- Moving A2A types to subpackage
- Renaming agent wrappers

### Mitigation Strategy
For each breaking change:
1. Add deprecation warnings
2. Maintain backwards-compatible imports in `__init__.py`
3. Document migration in CHANGELOG.md
4. Keep old imports working for 2 minor versions

---

## Success Metrics

After implementing this plan:
- [ ] No file exceeds 300 lines (currently: registry.py=469, a2a/types.py=692)
- [ ] All comments in English
- [ ] 100% of public APIs have docstrings
- [ ] All tests pass
- [ ] No increase in cyclomatic complexity
- [ ] Examples still work without modification

---

## Appendix: Quick Reference

### Files to Modify
| File | Current Lines | Target Lines | Action |
|------|---------------|--------------|--------|
| registry/registry.py | 469 | ~200 | Split |
| a2a/types.py | 692 | ~100/each | Split into 6 files |
| agents/*.py | varies | same | Refactor pattern |
| memory/middlewares/*.py | varies | same | Comment cleanup |

### New Files to Create
- `registry/a2a_bridge.py`
- `registry/aip_client.py`
- `registry/membase_integration.py`
- `a2a/types/__init__.py`
- `a2a/types/base.py`
- `a2a/types/messages.py`
- `a2a/types/tasks.py`
- `a2a/types/agent_card.py`
- `a2a/types/streaming.py`
- `a2a/types/jsonrpc.py`
- `agents/base.py`
- `core/protocols.py`
