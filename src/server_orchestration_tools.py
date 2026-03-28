"""
server_orchestration_tools.py — Register 9 agentic MCP tools (110-118) onto the FastMCP instance.

Tools 110-118 bring the MA2 MCP server's agentic capability up to the multi-agent
model: task decomposition, orchestrated execution, memory recall, token tracking,
object name resolution, and console state hydration.

Usage in server.py:
    from src.server_orchestration_tools import register_orchestration_tools
    register_orchestration_tools(mcp, _orchestrator, require_scope, _handle_errors, OAuthScope)
"""

from __future__ import annotations

from typing import Any
from mcp.server.fastmcp import FastMCP

from .orchestrator import Orchestrator
from .task_decomposer import TaskDecomposer
from .pool_name_index import ObjectRef, PoolNameIndex


def register_orchestration_tools(
    mcp: FastMCP,
    orchestrator: Orchestrator,
    require_scope_fn,
    handle_errors_fn,
    OAuthScope,
) -> None:
    """Register all orchestration MCP tools onto an existing FastMCP instance."""

    # ------------------------------------------------------------------ #
    # Tool 110: decompose_task                                            #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.DISCOVER)
    @handle_errors_fn
    async def decompose_task(
        goal: str,
        color: str = "",
        group: str = "",
        sequence: int = 1,
        cue: float = 1.0,
        preset: str = "",
    ) -> str:
        """
        Break a high-level lighting goal into an ordered multi-agent plan.

        Returns the plan summary and full step list so you can review
        before executing. Call run_task to actually execute.

        Args:
            goal:     Natural-language intent, e.g. 'blue wash on movers'
            color:    Target color name or hex
            group:    Fixture group name
            sequence: Target sequence number for cue storage
            cue:      Target cue number
            preset:   Preset name or ID to apply
        """
        import json
        params = {k: v for k, v in {
            "color": color, "group": group,
            "sequence": sequence, "cue": cue, "preset": preset,
        }.items() if v}

        decomposer = TaskDecomposer()
        plan = decomposer.decompose(goal, params)

        return json.dumps({
            "goal": plan.goal,
            "steps": len(plan.steps),
            "plan_summary": plan.summary(),
            "step_list": [
                {
                    "name": s.name,
                    "agent_role": s.agent_role,
                    "description": s.description,
                    "risk_tier": s.allowed_risk.value,
                    "tools": s.mcp_tools,
                    "depends_on": s.depends_on,
                    "eval_criteria": s.eval_criteria,
                    "requires_confirmation": s.allowed_risk.value == "DESTRUCTIVE",
                }
                for s in plan.ordered_steps()
            ],
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 111: run_task                                                  #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.CUE_STORE)
    @handle_errors_fn
    async def run_task(
        goal: str,
        color: str = "",
        group: str = "",
        sequence: int = 1,
        cue: float = 1.0,
        preset: str = "",
        auto_confirm_destructive: bool = False,
    ) -> str:
        """
        Execute a full multi-agent task from a natural-language goal.

        Orchestrates sub-agents with risk-tier isolation, working memory,
        and per-step evaluation.

        Args:
            goal: Natural-language show intent
            auto_confirm_destructive: Set True to allow DESTRUCTIVE steps
                without manual confirmation. Default False for safety.
        """
        import json
        params = {k: v for k, v in {
            "color": color, "group": group,
            "sequence": sequence, "cue": cue, "preset": preset,
        }.items() if v}

        result = await orchestrator.run(
            goal,
            params,
            auto_confirm_destructive=auto_confirm_destructive,
        )

        return json.dumps({
            "session_id": result.session_id,
            "outcome": result.outcome,
            "steps_done": result.steps_done,
            "steps_failed": result.steps_failed,
            "total_tokens": result.total_tokens,
            "elapsed_s": result.elapsed_s,
            "report": result.report(),
            "step_results": [
                {
                    "step": r.step_name,
                    "success": r.success,
                    "eval_passed": r.eval_passed,
                    "tokens": r.tokens_used,
                    "error": r.error or None,
                }
                for r in result.step_results
            ],
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 112: list_agent_sessions                                       #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.STATE_READ)
    @handle_errors_fn
    async def list_agent_sessions(limit: int = 10) -> str:
        """
        List recent multi-agent task sessions from long-term memory.

        Args:
            limit: Number of most recent sessions to return (default 10)
        """
        import json
        sessions = orchestrator.recent_sessions(limit)
        return json.dumps({"count": len(sessions), "sessions": sessions}, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 113: recall_agent_session                                      #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.STATE_READ)
    @handle_errors_fn
    async def recall_agent_session(session_id: str) -> str:
        """
        Restore the full WorkingMemory snapshot from a past agent session.

        Args:
            session_id: 8-char session ID from list_agent_sessions
        """
        import json
        snapshot = orchestrator.recall(session_id)
        if snapshot is None:
            return json.dumps({"error": f"Session '{session_id}' not found"})
        return json.dumps({
            "session_id": session_id,
            "task": snapshot.get("task_description"),
            "fixtures_tracked": len(snapshot.get("fixtures", {})),
            "completed_steps": snapshot.get("completed_steps", []),
            "failed_steps": snapshot.get("failed_steps", []),
            "tokens_consumed": snapshot.get("token_spend", 0),
            "snapshot": snapshot,
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 114: agent_token_report                                        #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.STATE_READ)
    @handle_errors_fn
    async def agent_token_report(limit: int = 20) -> str:
        """
        Report token consumption across recent agent sessions.

        Args:
            limit: Number of sessions to analyse
        """
        import json
        sessions = orchestrator.recent_sessions(limit)
        total = sum(s.get("tokens", 0) for s in sessions)
        avg   = round(total / max(len(sessions), 1))
        top   = sorted(sessions, key=lambda s: s.get("tokens", 0), reverse=True)[:3]

        return json.dumps({
            "sessions_analysed": len(sessions),
            "total_tokens": total,
            "avg_tokens_per_session": avg,
            "top_consuming_sessions": [
                {"id": s["id"], "task": s["task"], "tokens": s.get("tokens", 0)}
                for s in top
            ],
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 115: register_decomposition_rule                              #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.SYSTEM_ADMIN)
    @handle_errors_fn
    async def register_decomposition_rule(
        pattern: str,
        steps_json: str,
    ) -> str:
        """
        Register a new task decomposition rule at runtime (admin only).

        Args:
            pattern:    Regex pattern matched against natural-language goals
            steps_json: JSON array of step dicts with keys:
                        name, agent_role, description,
                        allowed_risk (SAFE_READ|SAFE_WRITE|DESTRUCTIVE),
                        mcp_tools (array), depends_on (array), eval_criteria
        """
        import json
        from .task_decomposer import SubTask, TaskPlan, RiskTier

        try:
            steps_raw = json.loads(steps_json)
        except Exception as exc:
            return json.dumps({"error": f"Invalid steps_json: {exc}"})

        def _builder(goal: str, params: dict) -> TaskPlan:
            steps = []
            for s in steps_raw:
                steps.append(SubTask(
                    name=s["name"],
                    agent_role=s.get("agent_role", "Agent"),
                    description=s.get("description", ""),
                    allowed_risk=RiskTier(s.get("allowed_risk", "SAFE_READ")),
                    mcp_tools=s.get("mcp_tools", []),
                    depends_on=s.get("depends_on", []),
                    eval_criteria=s.get("eval_criteria", ""),
                ))
            return TaskPlan(goal=goal, steps=steps)

        orchestrator.register_decomposition_rule(pattern, _builder)
        return json.dumps({
            "registered": True,
            "pattern": pattern,
            "steps": len(steps_raw),
            "message": f"Rule '{pattern}' will now match future decompose_task / run_task calls",
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 116: resolve_object_ref                                        #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.DISCOVER)
    @handle_errors_fn
    async def resolve_object_ref(
        object_type: str,
        name: str = "",
        id: int = 0,
        match_mode: str = "literal",
        preset_type: int = 0,
    ) -> str:
        """
        Resolve a pool object name or ID to a correctly-quoted MA2 command token.
        Uses in-memory index only — zero telnet cost.

        match_mode="literal" (default): quotes names with special chars; * is literal.
        match_mode="wildcard": * is active operator — may match multiple objects.

        Args:
            object_type: Group | Sequence | Preset | Macro | Effect | Timecode |
                         Timer | View | Layout | World | Filter | Page |
                         Executor | Fixture | Channel | Cue
            name:        Display name (use name OR id, not both)
            id:          Numeric ID (0 = not provided)
            match_mode:  "literal" (default) or "wildcard"
            preset_type: Required for Preset objects (1=Dimmer … 9=Video)
        """
        import json
        cs = orchestrator.last_snapshot
        if cs is None:
            return json.dumps({
                "error": "No console state snapshot available.",
                "hint": "Call hydrate_console_state first.",
            })

        resolved = cs.resolve(
            object_type,
            name=name or None,
            id=id or None,
            match_mode=match_mode,
            preset_type=preset_type or None,
        )
        return json.dumps(resolved.to_dict(), indent=2)

    # ------------------------------------------------------------------ #
    # Tool 117: list_pool_names                                           #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.DISCOVER)
    @handle_errors_fn
    async def list_pool_names(
        object_type: str,
        preset_type: int = 0,
    ) -> str:
        """
        List all known names and IDs for a pool type from the in-memory index.
        Zero telnet cost.

        Args:
            object_type: Any MA2 pool type (Group, Sequence, Macro, etc.)
            preset_type: For Preset objects only (1-9)
        """
        import json
        cs = orchestrator.last_snapshot
        if cs is None:
            return json.dumps({"error": "No snapshot available. Run hydrate_console_state first."})

        pt = preset_type or None
        entries = cs.name_index.all_entries(object_type, preset_type=pt)
        return json.dumps({
            "object_type": object_type,
            "preset_type": preset_type or None,
            "count": len(entries),
            "entries": entries,
            "indexed_types": cs.name_index.indexed_types(),
        }, indent=2)

    # ------------------------------------------------------------------ #
    # Tool 118: hydrate_console_state                                     #
    # ------------------------------------------------------------------ #
    @mcp.tool()
    @require_scope_fn(OAuthScope.STATE_READ)
    @handle_errors_fn
    async def hydrate_console_state(
        sequence_ids: str = "",
    ) -> str:
        """
        Trigger a fresh ConsoleStateSnapshot hydration on demand.
        Populates all 19 memory gaps + PoolNameIndex for all 16 pool types.

        Call this after load_show, new_show, or before DESTRUCTIVE multi-step tasks.

        Args:
            sequence_ids: Comma-separated sequence IDs for deep cue/part
                          hydration (e.g. "1,2,5"). Leave empty for fast path.
        """
        import json
        seq_ids = []
        if sequence_ids.strip():
            try:
                seq_ids = [int(x.strip()) for x in sequence_ids.split(",") if x.strip()]
            except ValueError:
                return json.dumps({"error": f"Invalid sequence_ids: {sequence_ids!r}"})

        snap = await orchestrator.hydrate_snapshot(sequence_ids=seq_ids or None)
        if snap is None:
            return json.dumps({"error": "Orchestrator has no telnet_send configured."})

        orchestrator.last_snapshot = snap

        return json.dumps({
            "hydrated": True,
            "duration_s": snap.hydration_duration_s,
            "partial": snap.partial,
            "errors": snap.hydration_errors,
            "summary": snap.summary(),
            "index_stats": snap.name_index.stats(),
            "indexed_types": snap.name_index.indexed_types(),
        }, indent=2)
