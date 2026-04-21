"""
Business Logic Layer (Layer 3)
==============================
Orchestrates Three E's scoring and network analysis.

Pure math lives in netsmith.ona — this layer owns ORM access and persistence.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import networkx as nx
import numpy as np
from sqlalchemy.orm import Session

from netsmith.ona import Communication as NsComm
from netsmith.ona import score_team, detect_silos
from netsmith.ona.three_es import gini_coefficient

from ..data_access.repositories import (
    CommunicationRepository,
    TeamMemberRepository,
    TeamMetricsRepository,
    TeamRepository,
)
from ..database.models import Communication, Team, TeamMember

logger = logging.getLogger(__name__)


# ── ORM → netsmith.ona adapter ────────────────────────────────────────────────

def _to_ns_comms(orm_comms: List[Communication]) -> List[NsComm]:
    """Convert SQLAlchemy Communication rows to netsmith.ona.Communication dataclasses."""
    return [
        NsComm(
            sender_id=c.sender_id,
            receiver_id=c.receiver_id,
            duration_minutes=c.duration_minutes or 0.0,
            comm_type=c.communication_type or "email",
            is_cross_team=bool(c.is_cross_team),
        )
        for c in orm_comms
    ]


# ── ThreeEsCalculator ─────────────────────────────────────────────────────────

class ThreeEsCalculator:
    """
    Coordinates Three E's metric calculation for a team.

    Fetches data via repositories, delegates scoring to netsmith.ona,
    and persists results back to the database.
    """

    def __init__(self, session: Session):
        self.session = session
        self.team_repo = TeamRepository(session)
        self.member_repo = TeamMemberRepository(session)
        self.comm_repo = CommunicationRepository(session)
        self.metrics_repo = TeamMetricsRepository(session)

    # ── Individual E calculators (kept for API compatibility) ─────────────────
    # Key names are mapped back to the original API contract so callers don't break.

    def calculate_energy(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict:
        from netsmith.ona.three_es import energy_score as _energy
        members = self.member_repo.get_by_team(team_id)
        comms = self.comm_repo.get_by_team(team_id, start_date, end_date)
        days = max((end_date - start_date).days, 1)
        score, d = _energy(_to_ns_comms(comms), [m.id for m in members], days)
        return {
            "energy_score": score,
            "total_communications": d["total_comms"],
            "avg_communications_per_member": round(d["total_comms"] / max(len(members), 1), 2),
            "total_duration_minutes": d["total_duration_min"],
            "face_to_face_ratio": d["face_to_face_ratio"],
            "frequency_normalized": d.get("freq_normalized", 0.0),
            "duration_normalized": d.get("duration_normalized", 0.0),
        }

    def calculate_engagement(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict:
        from netsmith.ona.three_es import engagement_score as _engagement
        members = self.member_repo.get_by_team(team_id)
        comms = self.comm_repo.get_by_team(team_id, start_date, end_date)
        score, d = _engagement(_to_ns_comms(comms), [m.id for m in members])
        return {
            "engagement_score": score,
            "participation_rate": d["participation_rate"],
            "balance_score": d["balance_score"],
            "two_way_communication_score": d["two_way_rate"],
            "gini_coefficient": d["gini"],
        }

    def calculate_exploration(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict:
        from netsmith.ona.three_es import exploration_score as _exploration
        members = self.member_repo.get_by_team(team_id)
        comms = self.comm_repo.get_by_team(team_id, start_date, end_date)
        score, d = _exploration(_to_ns_comms(comms), [m.id for m in members])
        return {
            "exploration_score": score,
            "cross_team_communications": d["cross_team_count"],
            "exploration_ratio": d["exploration_ratio"],
            "members_exploring": d["explorers"],
            "member_exploration_rate": d["explorer_rate"],
        }

    def calculate_overall_performance(
        self, energy: float, engagement: float, exploration: float
    ) -> float:
        from netsmith.ona.three_es import overall_score
        return overall_score(energy, engagement, exploration)

    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        return gini_coefficient(values)

    # ── Main entry point ──────────────────────────────────────────────────────

    def calculate_all_metrics(
        self,
        team_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        save_to_db: bool = True,
    ) -> Dict:
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        members = self.member_repo.get_by_team(team_id)
        comms = self.comm_repo.get_by_team(team_id, start_date, end_date)
        days = max((end_date - start_date).days, 1)

        result = score_team(_to_ns_comms(comms), [m.id for m in members], days)

        if save_to_db:
            stats = self.comm_repo.get_communication_stats(team_id, start_date, end_date)
            self.metrics_repo.create(
                team_id=team_id,
                energy_score=result.energy,
                engagement_score=result.engagement,
                exploration_score=result.exploration,
                overall_score=result.overall,
                calculation_period_start=start_date,
                calculation_period_end=end_date,
                total_communications=stats["total_communications"],
                participation_rate=result.detail["engagement"].get("participation_rate", 0.0),
                gini_coefficient=result.detail["engagement"].get("gini", 0.0),
            )
            logger.info(f"Saved metrics for team {team_id}: overall={result.overall:.2f}")

        return {
            "team_id": team_id,
            "calculation_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "energy":      {"energy_score":      result.energy,      **result.detail["energy"]},
            "engagement":  {"engagement_score":  result.engagement,  **result.detail["engagement"]},
            "exploration": {"exploration_score": result.exploration, **result.detail["exploration"]},
            "overall_score": result.overall,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }


# ── NetworkAnalyzer ───────────────────────────────────────────────────────────
# Kept intact — uses networkx directly since this is graph topology, not Three E's math.

class NetworkAnalyzer:
    """Graph topology analysis — centrality, bottlenecks, community detection."""

    def __init__(self, session: Session):
        self.session = session
        self.comm_repo = CommunicationRepository(session)
        self.member_repo = TeamMemberRepository(session)

    def build_communication_network(
        self,
        team_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> nx.Graph:
        members = self.member_repo.get_by_team(team_id)
        communications = self.comm_repo.get_by_team(team_id, start_date, end_date)

        G = nx.Graph()
        for member in members:
            G.add_node(member.id, name=member.name, role=member.role)

        member_ids = {m.id for m in members}
        for comm in communications:
            if comm.receiver_id and comm.receiver_id in member_ids:
                if G.has_edge(comm.sender_id, comm.receiver_id):
                    G[comm.sender_id][comm.receiver_id]["weight"] += 1
                else:
                    G.add_edge(comm.sender_id, comm.receiver_id, weight=1)
        return G

    def analyze_network_metrics(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        G = self.build_communication_network(team_id, start_date, end_date)
        if G.number_of_nodes() == 0:
            return {"error": "No data available for analysis"}

        density = nx.density(G)
        try:
            betweenness = nx.betweenness_centrality(G)
            closeness = nx.closeness_centrality(G)
            most_central = max(betweenness.items(), key=lambda x: x[1]) if betweenness else (None, 0)
            bv = np.array(list(betweenness.values()))
            bottlenecks = [n for n, c in betweenness.items() if c > bv.mean() + bv.std()]
            return {
                "density": round(density, 3),
                "is_connected": nx.is_connected(G),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "most_central_member_id": most_central[0],
                "centrality_score": round(most_central[1], 3),
                "potential_bottlenecks": bottlenecks,
                "avg_betweenness": round(float(bv.mean()), 3),
            }
        except (nx.NetworkXError, nx.PowerIterationFailedConvergence, ValueError) as e:
            return {
                "density": round(density, 3),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "note": f"Network too sparse for full analysis: {e}",
            }

    def detect_communities(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        from networkx.algorithms import community

        G = self.build_communication_network(team_id, start_date, end_date)
        if G.number_of_nodes() < 3:
            return {"error": "Need at least 3 members for community detection"}

        try:
            communities = community.greedy_modularity_communities(G)
            modularity = community.modularity(G, communities)
            community_list = [
                {
                    "community_id": i + 1,
                    "member_ids": list(comm),
                    "member_names": [G.nodes[n]["name"] for n in comm if "name" in G.nodes[n]],
                    "size": len(comm),
                }
                for i, comm in enumerate(communities)
            ]
            return {
                "num_communities": len(communities),
                "communities": community_list,
                "modularity": round(modularity, 3),
                "is_siloed": modularity > 0.4,
                "interpretation": self._interpret_communities(
                    len(communities), modularity, G.number_of_nodes()
                ),
            }
        except Exception as e:
            return {"error": f"Community detection failed: {e}"}

    def _interpret_communities(self, num_communities: int, modularity: float, _: int) -> str:
        if num_communities == 1:
            return "Team is well-integrated with no distinct sub-groups."
        interpretations = [
            (modularity > 0.5, f"⚠️ Warning: {num_communities} distinct silos (modularity {modularity:.2f}). Consider cross-group activities."),
            (modularity > 0.3, f"Team has {num_communities} sub-groups with good cross-communication (modularity {modularity:.2f})."),
            (True,             f"Team has {num_communities} informal groupings with excellent cross-communication (modularity {modularity:.2f})."),
        ]
        return next(msg for cond, msg in interpretations if cond)

    def calculate_advanced_centrality(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        G = self.build_communication_network(team_id, start_date, end_date)
        if G.number_of_nodes() == 0:
            return {"error": "No data available"}

        try:
            degree_cent = nx.degree_centrality(G)
            betweenness_cent = nx.betweenness_centrality(G)
            closeness_cent = nx.closeness_centrality(G)
            try:
                eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
            except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
                eigenvector_cent = {n: 0.0 for n in G.nodes()}

            top_n = min(3, G.number_of_nodes())

            def member_info(mid):
                return {"member_id": mid, "name": G.nodes[mid].get("name", f"Member {mid}"), "role": G.nodes[mid].get("role", "Unknown")}

            return {
                "centrality_metrics": {
                    "degree":      {k: round(v, 3) for k, v in degree_cent.items()},
                    "betweenness": {k: round(v, 3) for k, v in betweenness_cent.items()},
                    "closeness":   {k: round(v, 3) for k, v in closeness_cent.items()},
                    "eigenvector": {k: round(v, 3) for k, v in eigenvector_cent.items()},
                },
                "key_roles": {
                    "connectors":  [{**member_info(k), "score": round(v, 3)} for k, v in sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]],
                    "influencers": [{**member_info(k), "score": round(v, 3)} for k, v in sorted(eigenvector_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]],
                    "hubs":        [{**member_info(k), "score": round(v, 3)} for k, v in sorted(degree_cent.items(),      key=lambda x: x[1], reverse=True)[:top_n]],
                },
                "insights": self._centrality_insights(degree_cent, betweenness_cent),
            }
        except Exception as e:
            return {"error": f"Centrality calculation failed: {e}"}

    def _centrality_insights(self, degree_cent: Dict, betweenness_cent: Dict) -> List[str]:
        insights = []
        if betweenness_cent and max(betweenness_cent.values()) > 0.5:
            insights.append("⚠️ Network is highly centralized — consider distributing communication responsibilities")
        isolated = sum(1 for v in degree_cent.values() if v == 0) if degree_cent else 0
        if isolated:
            insights.append(f"⚠️ {isolated} member(s) are isolated with no connections")
        bv = np.array(list(betweenness_cent.values())) if betweenness_cent else np.array([])
        if bv.size > 3 and bv.mean() > 0 and bv.std() / bv.mean() < 0.5:
            insights.append("✅ Communication responsibility is well-distributed across team")
        return insights or ["Network structure appears healthy"]
