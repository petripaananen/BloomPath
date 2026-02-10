"""
L3 Dreaming Engine — What-If Scenario Simulator for BloomPath.

Enables the system to "dream" potential futures by running simulations
on snapshotted sprint data. Results are visualized as semi-transparent
"ghost gardens" in UE5, showing projected outcomes without modifying
the real project state.

Implements Phase 8 (Thesis Core) of the Feature Roadmap:
  - Resource Stress-Testing
  - Scope Creep Simulation
  - Priority Shifting
"""

import os
import json
import time
import logging
import copy
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("BloomPath.DreamingEngine")

# Gemini API for narrative forecast generation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"

SCENARIOS_PATH = os.path.join(os.path.dirname(__file__), "config", "scenarios.json")
DREAMS_DIR = os.path.join(os.path.dirname(__file__), "data", "dreams")


@dataclass
class DreamResult:
    """Result of a what-if simulation."""
    scenario_type: str
    scenario_params: Dict[str, Any]
    timestamp: int
    dream_id: str

    # Simulation outputs
    original_velocity: float = 0.0
    projected_velocity: float = 0.0
    risk_score: float = 0.0           # 0.0 (safe) to 1.0 (critical)
    impact_summary: str = ""          # AI-generated narrative
    affected_issues: List[str] = field(default_factory=list)

    # UE5 visualization params
    ghost_intensity: float = 0.5      # Opacity for ghost overlay
    visual_effects: List[Dict[str, Any]] = field(default_factory=list)


class DreamingEngine:
    """
    The Dreaming Engine runs what-if simulations on sprint data.

    It snapshots the current state, applies scenario mutations,
    calculates projected outcomes, and generates AI-powered narrative
    forecasts. Results are sent to UE5 as ghost garden overlays.
    """

    def __init__(self):
        self.scenarios_config = self._load_scenarios()
        os.makedirs(DREAMS_DIR, exist_ok=True)

    def _load_scenarios(self) -> Dict[str, Any]:
        """Load scenario templates from config."""
        try:
            if os.path.exists(SCENARIOS_PATH):
                with open(SCENARIOS_PATH, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load scenarios config: {e}")
        return {}

    def dream(
        self,
        scenario_type: str,
        sprint_data: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None
    ) -> DreamResult:
        """
        Run a what-if simulation.

        Args:
            scenario_type: One of 'resource_stress', 'scope_creep', 'priority_shift'
            sprint_data: Current sprint state dict with keys:
                - issues: List of issue dicts (id, status, assignee, priority, epic)
                - team_members: List of team member names
                - velocity: Current velocity (issues completed per sprint)
                - days_remaining: Days left in sprint
            params: Override default scenario parameters

        Returns:
            DreamResult with projected outcomes and UE5 visual instructions
        """
        # Merge params with defaults
        scenario_config = self.scenarios_config.get(scenario_type, {})
        effective_params = {**scenario_config.get("default_params", {}), **(params or {})}

        dream_id = f"dream_{scenario_type}_{int(time.time())}"
        logger.info(f"🌙 Starting dream: {dream_id} ({scenario_type})")

        # Deep copy sprint data to avoid mutations
        simulated_data = copy.deepcopy(sprint_data)

        # Run scenario-specific simulation
        if scenario_type == "resource_stress":
            result = self._simulate_resource_stress(simulated_data, effective_params, dream_id)
        elif scenario_type == "scope_creep":
            result = self._simulate_scope_creep(simulated_data, effective_params, dream_id)
        elif scenario_type == "priority_shift":
            result = self._simulate_priority_shift(simulated_data, effective_params, dream_id)
        else:
            logger.error(f"Unknown scenario type: {scenario_type}")
            result = DreamResult(
                scenario_type=scenario_type,
                scenario_params=effective_params,
                timestamp=int(time.time()),
                dream_id=dream_id,
                impact_summary=f"Unknown scenario type: {scenario_type}",
                risk_score=0.0
            )

        # Generate AI narrative forecast
        result.impact_summary = self._generate_forecast(result, sprint_data)

        # Save dream result
        self._save_dream(result)

        logger.info(f"🌙 Dream complete: {dream_id} | Risk: {result.risk_score:.2f}")
        return result

    # ── Scenario Simulators ──────────────────────────────────────────

    def _simulate_resource_stress(
        self,
        data: Dict[str, Any],
        params: Dict[str, Any],
        dream_id: str
    ) -> DreamResult:
        """
        Simulate losing team members.

        Impact: Reduced velocity, unassigned issues, longer projected completion.
        Visual: Narrowing paths, slowed growth animations.
        """
        team = data.get("team_members", [])
        issues = data.get("issues", [])
        velocity = data.get("velocity", 1.0)
        remove_count = min(params.get("remove_count", 1), len(team))

        if not team:
            return DreamResult(
                scenario_type="resource_stress",
                scenario_params=params,
                timestamp=int(time.time()),
                dream_id=dream_id,
                risk_score=0.0,
                impact_summary="No team members to remove."
            )

        # Remove N members (highest workload first)
        workload = {}
        for issue in issues:
            assignee = issue.get("assignee", "unassigned")
            workload[assignee] = workload.get(assignee, 0) + 1

        sorted_members = sorted(team, key=lambda m: workload.get(m, 0), reverse=True)
        removed = sorted_members[:remove_count]
        remaining = sorted_members[remove_count:]

        # Calculate impact
        orphaned_issues = [
            issue["id"] for issue in issues
            if issue.get("assignee") in removed
            and issue.get("status") != "done"
        ]

        # Velocity reduction proportional to removed capacity
        capacity_ratio = len(remaining) / max(len(team), 1)
        projected_velocity = velocity * capacity_ratio

        # Risk score based on orphaned work and capacity loss
        orphan_ratio = len(orphaned_issues) / max(len(issues), 1)
        risk_score = min(1.0, (1 - capacity_ratio) * 0.6 + orphan_ratio * 0.4)

        return DreamResult(
            scenario_type="resource_stress",
            scenario_params=params,
            timestamp=int(time.time()),
            dream_id=dream_id,
            original_velocity=velocity,
            projected_velocity=projected_velocity,
            risk_score=risk_score,
            affected_issues=orphaned_issues,
            ghost_intensity=0.3 + (risk_score * 0.5),
            visual_effects=[
                {"type": "narrow_paths", "intensity": risk_score},
                {"type": "slow_growth", "factor": capacity_ratio},
                {"type": "wilted_leaves", "issue_ids": orphaned_issues}
            ]
        )

    def _simulate_scope_creep(
        self,
        data: Dict[str, Any],
        params: Dict[str, Any],
        dream_id: str
    ) -> DreamResult:
        """
        Simulate adding unplanned work mid-sprint.

        Impact: Overloaded sprint, reduced completion rate, stress indicators.
        Visual: Overburdened trees, drooping branches, wilted leaves.
        """
        issues = data.get("issues", [])
        velocity = data.get("velocity", 1.0)
        days_remaining = data.get("days_remaining", 5)
        additional = params.get("additional_issues", 5)
        issue_priority = params.get("priority", 3)

        current_open = len([i for i in issues if i.get("status") != "done"])
        total_after = current_open + additional

        # Can the team absorb the new work?
        daily_throughput = velocity / max(days_remaining, 1)
        projected_completion = daily_throughput * days_remaining
        overload_ratio = total_after / max(projected_completion, 1)

        # Higher priority additions cause more disruption
        priority_weight = {1: 1.5, 2: 1.3, 3: 1.0, 4: 0.8}.get(issue_priority, 1.0)
        risk_score = min(1.0, (overload_ratio - 1.0) * 0.5 * priority_weight)
        risk_score = max(0.0, risk_score)

        projected_velocity = velocity / max(overload_ratio, 1.0)

        # Generate synthetic issue IDs for visualization
        synthetic_ids = [f"DREAM-{i+1}" for i in range(additional)]

        return DreamResult(
            scenario_type="scope_creep",
            scenario_params=params,
            timestamp=int(time.time()),
            dream_id=dream_id,
            original_velocity=velocity,
            projected_velocity=projected_velocity,
            risk_score=risk_score,
            affected_issues=synthetic_ids,
            ghost_intensity=0.4 + (risk_score * 0.4),
            visual_effects=[
                {"type": "overburdened_trees", "load_factor": overload_ratio},
                {"type": "drooping_branches", "count": additional},
                {"type": "ghost_issues", "issue_ids": synthetic_ids}
            ]
        )

    def _simulate_priority_shift(
        self,
        data: Dict[str, Any],
        params: Dict[str, Any],
        dream_id: str
    ) -> DreamResult:
        """
        Simulate reallocating resources between epics.

        Impact: Some epics accelerate, others stall.
        Visual: Firefly rerouting (glowing particles moving between garden zones).
        """
        issues = data.get("issues", [])
        velocity = data.get("velocity", 1.0)
        target_epic = params.get("target_epic")
        shift_pct = params.get("shift_percentage", 30) / 100.0

        # Group issues by epic
        epics: Dict[str, List[Dict]] = {}
        for issue in issues:
            epic = issue.get("epic", "no_epic")
            epics.setdefault(epic, []).append(issue)

        if not target_epic and epics:
            # Default: shift to the epic with most open issues
            target_epic = max(
                epics.keys(),
                key=lambda e: len([i for i in epics[e] if i.get("status") != "done"])
            )

        # Calculate reallocation impact
        starved_epics = [e for e in epics if e != target_epic]
        starved_issues = []
        for epic_key in starved_epics:
            open_in_epic = [i for i in epics[epic_key] if i.get("status") != "done"]
            starved_count = int(len(open_in_epic) * shift_pct)
            starved_issues.extend([i["id"] for i in open_in_epic[:starved_count]])

        # Risk: how much work is being deprioritized
        risk_score = min(1.0, len(starved_issues) / max(len(issues), 1) + shift_pct * 0.3)

        return DreamResult(
            scenario_type="priority_shift",
            scenario_params=params,
            timestamp=int(time.time()),
            dream_id=dream_id,
            original_velocity=velocity,
            projected_velocity=velocity,  # Total velocity unchanged, just redistributed
            risk_score=risk_score,
            affected_issues=starved_issues,
            ghost_intensity=0.3 + (risk_score * 0.3),
            visual_effects=[
                {"type": "firefly_reroute", "from_epics": starved_epics, "to_epic": target_epic},
                {"type": "accelerated_growth", "epic": target_epic, "boost": shift_pct},
                {"type": "stalled_growth", "issue_ids": starved_issues}
            ]
        )

    # ── AI Narrative Forecast ────────────────────────────────────────

    def _generate_forecast(self, result: DreamResult, original_data: Dict[str, Any]) -> str:
        """
        Use Gemini to generate a human-readable narrative forecast
        from the simulation results.
        """
        if not GEMINI_API_KEY:
            return self._fallback_summary(result)

        prompt = f"""You are a project management AI advisor. Based on this simulation data, provide a concise 2-3 sentence forecast of the likely outcome.

Scenario: {result.scenario_type}
Parameters: {json.dumps(result.scenario_params)}
Original velocity: {result.original_velocity} issues/sprint
Projected velocity: {result.projected_velocity} issues/sprint
Risk score: {result.risk_score:.2f} (0=safe, 1=critical)
Affected issues count: {len(result.affected_issues)}
Team size: {len(original_data.get('team_members', []))}
Days remaining: {original_data.get('days_remaining', 'unknown')}

Respond with ONLY the forecast text, no formatting or headers."""

        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 256}
            }
            headers = {"Content-Type": "application/json"}
            url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()

            result_json = response.json()
            candidates = result_json.get("candidates", [])
            if candidates:
                return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        except Exception as e:
            logger.warning(f"Gemini forecast failed, using fallback: {e}")

        return self._fallback_summary(result)

    def _fallback_summary(self, result: DreamResult) -> str:
        """Generate a simple summary when Gemini is unavailable."""
        risk_level = "low" if result.risk_score < 0.3 else "moderate" if result.risk_score < 0.7 else "high"
        velocity_change = result.projected_velocity - result.original_velocity

        summaries = {
            "resource_stress": (
                f"Removing resources would reduce velocity by {abs(velocity_change):.1f} issues/sprint "
                f"({risk_level} risk). {len(result.affected_issues)} issues would become unassigned."
            ),
            "scope_creep": (
                f"Adding {result.scenario_params.get('additional_issues', 0)} issues mid-sprint "
                f"creates {risk_level} risk. Projected velocity drops to {result.projected_velocity:.1f}."
            ),
            "priority_shift": (
                f"Shifting {result.scenario_params.get('shift_percentage', 0)}% of resources "
                f"would deprioritize {len(result.affected_issues)} issues ({risk_level} risk)."
            )
        }
        return summaries.get(result.scenario_type, f"Simulation complete. Risk: {risk_level}.")

    # ── Persistence ──────────────────────────────────────────────────

    def _save_dream(self, result: DreamResult) -> None:
        """Save dream result to disk."""
        filepath = os.path.join(DREAMS_DIR, f"{result.dream_id}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(asdict(result), f, indent=2)
            logger.info(f"💾 Dream saved: {result.dream_id}")
        except Exception as e:
            logger.error(f"Failed to save dream: {e}")

    def list_dreams(self) -> List[Dict[str, Any]]:
        """List all saved dream results (metadata only)."""
        dreams = []
        try:
            for filename in sorted(os.listdir(DREAMS_DIR), reverse=True):
                if not filename.endswith(".json"):
                    continue
                filepath = os.path.join(DREAMS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                dreams.append({
                    "dream_id": data.get("dream_id"),
                    "scenario_type": data.get("scenario_type"),
                    "timestamp": data.get("timestamp"),
                    "risk_score": data.get("risk_score"),
                    "impact_summary": data.get("impact_summary", "")[:100]
                })
        except Exception as e:
            logger.error(f"Failed to list dreams: {e}")
        return dreams

    def load_dream(self, dream_id: str) -> Optional[DreamResult]:
        """Load a full dream result from disk."""
        filepath = os.path.join(DREAMS_DIR, f"{dream_id}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return DreamResult(**data)
        except Exception as e:
            logger.error(f"Failed to load dream {dream_id}: {e}")
            return None

    # ── UE5 Ghost Visualization ──────────────────────────────────────

    def visualize_dream(self, result: DreamResult) -> Dict[str, Any]:
        """
        Send ghost garden visualization commands to UE5.

        Returns dict of triggered effects and their status.
        """
        triggered = {}

        try:
            from ue5_interface import (
                trigger_ue5_ghost_overlay,
                trigger_ue5_ghost_growth,
                trigger_ue5_clear_ghosts
            )

            # Clear any previous ghost overlays
            trigger_ue5_clear_ghosts()
            triggered["clear"] = "ok"

            # Apply the main ghost overlay
            trigger_ue5_ghost_overlay(result.dream_id, result.ghost_intensity)
            triggered["overlay"] = "ok"

            # Apply per-issue ghost effects
            for effect in result.visual_effects:
                effect_type = effect.get("type", "")
                issue_ids = effect.get("issue_ids", [])

                for issue_id in issue_ids:
                    try:
                        # Ghost growth uses opacity from intensity
                        trigger_ue5_ghost_growth(
                            branch_id=issue_id,
                            growth_type="leaf",
                            opacity=result.ghost_intensity
                        )
                        triggered[f"ghost_{issue_id}"] = "ok"
                    except Exception as e:
                        triggered[f"ghost_{issue_id}"] = f"error: {e}"

        except ImportError:
            logger.warning("UE5 ghost functions not available")
            triggered["status"] = "ue5_unavailable"
        except Exception as e:
            logger.error(f"Failed to visualize dream: {e}")
            triggered["error"] = str(e)

        return triggered


# Module-level singleton
dreaming_engine = DreamingEngine()
