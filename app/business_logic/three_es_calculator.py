"""
Business Logic Layer (Layer 3)
==============================
This layer contains the core business logic for calculating the Three E's:
- Energy: Magnitude of formal and informal communication
- Engagement: Degree of interaction and contribution
- Exploration: Cross-team communication and external engagement
"""

import logging
import numpy as np
import networkx as nx
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session
from ..data_access.repositories import (
    TeamRepository,
    TeamMemberRepository,
    CommunicationRepository,
    TeamMetricsRepository,
)
from ..database.models import Team, TeamMember, Communication

logger = logging.getLogger(__name__)


class ThreeEsCalculator:
    """
    Core calculator for the Three E's metrics based on MIT research.
    """

    def __init__(self, session: Session):
        self.session = session
        self.team_repo = TeamRepository(session)
        self.member_repo = TeamMemberRepository(session)
        self.comm_repo = CommunicationRepository(session)
        self.metrics_repo = TeamMetricsRepository(session)

    def calculate_energy(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate Energy Score: Magnitude of communication between team members.

        Energy is measured by:
        - Total volume of communications
        - Frequency of interactions
        - Duration of communications
        - Quality bonus for face-to-face interactions

        FIXED: Proper normalization to ensure scores stay within 0-100 range

        Returns:
            Dictionary with energy score and components
        """
        communications = self.comm_repo.get_by_team(team_id, start_date, end_date)
        members = self.member_repo.get_by_team(team_id)

        if not members or not communications:
            return {
                "energy_score": 0.0,
                "total_communications": 0,
                "avg_communications_per_member": 0.0,
                "total_duration_minutes": 0.0,
                "face_to_face_ratio": 0.0,
            }

        # Vectorized calculations using numpy
        durations = np.array([c.duration_minutes or 0 for c in communications])
        comm_types = np.array([c.communication_type for c in communications])

        total_comms = len(communications)
        total_duration = np.sum(durations)
        face_to_face_count = np.sum(comm_types == "face-to-face")

        logger.debug(
            f"Team {team_id}: {total_comms} communications, {face_to_face_count} face-to-face"
        )

        # Calculate per-member metrics
        num_members = len(members)
        days_in_period = (end_date - start_date).days or 1

        # Energy components
        communication_frequency = total_comms / (num_members * days_in_period)
        duration_per_member = total_duration / num_members if num_members > 0 else 0
        face_to_face_ratio = face_to_face_count / total_comms if total_comms > 0 else 0

        # FIXED: Normalize each component to 0-1 range before combining
        # Benchmarks based on organizational research:
        # - 5 communications per person per day is considered highly active
        # - 2 hours (120 minutes) per person per day is healthy engagement
        freq_normalized = min(communication_frequency / 5.0, 1.0)
        duration_per_day = (duration_per_member / days_in_period) if days_in_period > 0 else 0
        duration_normalized = min(duration_per_day / 120.0, 1.0)

        # Weighted energy score with normalized components (0-100 scale)
        # Higher weight for face-to-face per MIT research
        energy_score = (
            (freq_normalized * 20)  # Frequency: max 20 points
            + (duration_normalized * 30)  # Duration: max 30 points
            + (face_to_face_ratio * 50)  # Face-to-face: max 50 points
        )

        # Ensure within bounds
        energy_score = max(0, min(energy_score, 100.0))

        return {
            "energy_score": round(energy_score, 2),
            "total_communications": total_comms,
            "avg_communications_per_member": round(total_comms / num_members, 2),
            "total_duration_minutes": round(total_duration, 2),
            "face_to_face_ratio": round(face_to_face_ratio, 2),
            # Diagnostic info
            "frequency_normalized": round(freq_normalized, 2),
            "duration_normalized": round(duration_normalized, 2),
        }

    def _calculate_gini_coefficient(self, values: List[float]) -> float:
        """
        Calculate Gini coefficient for measuring inequality.

        More robust than coefficient of variation for communication distribution.

        Returns:
            float: 0 = perfect equality, 1 = total inequality
        """
        if not values or all(v == 0 for v in values):
            return 0.0

        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)

        if cumsum[-1] == 0:
            return 0.0

        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

    def calculate_engagement(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate Engagement Score: Degree of interaction and balanced participation.

        Engagement is measured by:
        - Distribution of communication (how balanced)
        - Participation rate (all members involved)
        - Two-way communication patterns
        - Avoiding dominance by single members

        FIXED: Uses Gini coefficient instead of CV for more robust balance measurement

        Returns:
            Dictionary with engagement score and components
        """
        communications = self.comm_repo.get_by_team(team_id, start_date, end_date)
        members = self.member_repo.get_by_team(team_id)

        if not members or not communications:
            return {
                "engagement_score": 0.0,
                "participation_rate": 0.0,
                "balance_score": 0.0,
                "two_way_communication_score": 0.0,
                "gini_coefficient": 0.0,
            }

        member_ids_set = {m.id for m in members}
        num_members = len(member_ids_set)

        # Vectorized extraction of communication data
        sender_ids = np.array([c.sender_id for c in communications])
        receiver_ids = np.array([c.receiver_id if c.receiver_id else -1 for c in communications])

        # Track participation - vectorized
        valid_senders = np.isin(sender_ids, list(member_ids_set))
        active_members = set(sender_ids[valid_senders])

        # Count communications per member
        member_comm_count = {mid: int(np.sum(sender_ids == mid)) for mid in member_ids_set}

        # Track two-way communications
        comm_pairs = {}
        valid_comms = [
            (s, r)
            for s, r in zip(sender_ids, receiver_ids)
            if s in member_ids_set and r in member_ids_set and r != -1
        ]
        for s, r in valid_comms:
            pair = tuple(sorted([s, r]))
            comm_pairs[pair] = comm_pairs.get(pair, 0) + 1

        # 1. Participation rate
        participation_rate = len(active_members) / num_members if num_members > 0 else 0

        # 2. FIXED: Balance score using Gini coefficient instead of CV
        # Lower Gini = more balanced = better engagement
        comm_counts = list(member_comm_count.values())
        if comm_counts:
            gini = self._calculate_gini_coefficient(comm_counts)
            balance_score = 1 - gini  # Invert so lower inequality = higher score
        else:
            gini = 0.0
            balance_score = 0.0

        # 3. Two-way communication (back-and-forth dialogue)
        # Check if communication pairs have multiple exchanges
        two_way_pairs = sum(1 for count in comm_pairs.values() if count >= 2)
        possible_pairs = (num_members * (num_members - 1)) / 2
        two_way_score = two_way_pairs / possible_pairs if possible_pairs > 0 else 0

        # Weighted engagement score (0-100 scale)
        engagement_score = (
            (participation_rate * 40)  # Everyone participates
            + (balance_score * 40)  # Balanced distribution
            + (two_way_score * 20)  # Two-way dialogue
        )

        return {
            "engagement_score": round(engagement_score, 2),
            "participation_rate": round(participation_rate, 2),
            "balance_score": round(balance_score, 2),
            "two_way_communication_score": round(two_way_score, 2),
            "gini_coefficient": round(gini, 3),  # Lower is better
        }

    def calculate_exploration(
        self, team_id: int, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """
        Calculate Exploration Score: Cross-team engagement and external learning.

        Exploration is measured by:
        - Number of cross-team communications
        - Diversity of external contacts
        - Information sharing back to team
        - Breadth of exploration

        Returns:
            Dictionary with exploration score and components
        """
        all_communications = self.comm_repo.get_by_team(team_id, start_date, end_date)
        members = self.member_repo.get_by_team(team_id)

        if not members:
            return {
                "exploration_score": 0.0,
                "cross_team_communications": 0,
                "exploration_ratio": 0.0,
                "members_exploring": 0,
            }

        # Vectorized cross-team detection
        is_cross_team = np.array([c.is_cross_team == 1 for c in all_communications])
        sender_ids = np.array([c.sender_id for c in all_communications])

        member_ids_set = {m.id for m in members}
        num_members = len(member_ids_set)
        total_comms = len(all_communications)

        # Track which members are exploring - vectorized
        cross_team_senders = sender_ids[is_cross_team]
        exploring_members = set(mid for mid in cross_team_senders if mid in member_ids_set)

        # Calculate metrics - vectorized
        cross_team_count = int(np.sum(is_cross_team))
        exploration_ratio = cross_team_count / total_comms if total_comms > 0 else 0
        member_exploration_rate = len(exploring_members) / num_members if num_members > 0 else 0
        avg_exploration = cross_team_count / num_members if num_members > 0 else 0

        logger.debug(f"Team {team_id}: {cross_team_count}/{total_comms} cross-team communications")

        # Weighted exploration score (0-100 scale)
        exploration_score = (
            (exploration_ratio * 40)  # Proportion of cross-team comms
            + (member_exploration_rate * 40)  # How many members explore
            + (min(avg_exploration / 5, 1) * 20)  # Volume of exploration (normalized)
        )

        return {
            "exploration_score": round(exploration_score, 2),
            "cross_team_communications": cross_team_count,
            "exploration_ratio": round(exploration_ratio, 2),
            "members_exploring": len(exploring_members),
            "member_exploration_rate": round(member_exploration_rate, 2),
        }

    def calculate_overall_performance(
        self, energy: float, engagement: float, exploration: float
    ) -> float:
        """
        Calculate overall team performance score based on the Three E's.

        Uses weighted average with slight emphasis on engagement and energy
        per MIT research findings.
        """
        # Weights based on research importance
        weights = {"energy": 0.35, "engagement": 0.40, "exploration": 0.25}

        overall = (
            energy * weights["energy"]
            + engagement * weights["engagement"]
            + exploration * weights["exploration"]
        )

        return round(overall, 2)

    def calculate_all_metrics(
        self,
        team_id: int,
        start_date: datetime = None,
        end_date: datetime = None,
        save_to_db: bool = True,
    ) -> Dict:
        """
        Calculate all Three E's metrics for a team and optionally save to database.

        Args:
            team_id: ID of the team to analyze
            start_date: Start of analysis period (defaults to 30 days ago)
            end_date: End of analysis period (defaults to now)
            save_to_db: Whether to save results to database

        Returns:
            Dictionary containing all metrics
        """
        # Default date range: last 30 days
        if end_date is None:
            end_date = datetime.now(timezone.utc)
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Calculate each E
        energy_data = self.calculate_energy(team_id, start_date, end_date)
        engagement_data = self.calculate_engagement(team_id, start_date, end_date)
        exploration_data = self.calculate_exploration(team_id, start_date, end_date)

        # Calculate overall performance
        overall = self.calculate_overall_performance(
            energy_data["energy_score"],
            engagement_data["engagement_score"],
            exploration_data["exploration_score"],
        )

        # Compile results
        results = {
            "team_id": team_id,
            "calculation_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "energy": energy_data,
            "engagement": engagement_data,
            "exploration": exploration_data,
            "overall_score": overall,
            "calculated_at": datetime.now(timezone.utc).isoformat(),
        }

        # Save to database if requested
        if save_to_db:
            stats = self.comm_repo.get_communication_stats(team_id, start_date, end_date)
            self.metrics_repo.create(
                team_id=team_id,
                energy_score=energy_data["energy_score"],
                engagement_score=engagement_data["engagement_score"],
                exploration_score=exploration_data["exploration_score"],
                overall_score=overall,
                calculation_period_start=start_date,
                calculation_period_end=end_date,
                total_communications=stats["total_communications"],
                participation_rate=engagement_data["participation_rate"],
                gini_coefficient=engagement_data.get("gini_coefficient", 0.0),
            )
            logger.info(f"Saved metrics for team {team_id}: overall={overall:.2f}")

        return results


class NetworkAnalyzer:
    """
    Analyzes team communication networks using graph theory.
    Provides additional insights into team dynamics.
    """

    def __init__(self, session: Session):
        self.session = session
        self.comm_repo = CommunicationRepository(session)
        self.member_repo = TeamMemberRepository(session)

    def build_communication_network(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> nx.Graph:
        """
        Build a network graph of team communications.

        Returns:
            NetworkX graph where nodes are team members and edges are communications
        """
        members = self.member_repo.get_by_team(team_id)
        communications = self.comm_repo.get_by_team(team_id, start_date, end_date)

        # Create graph
        G = nx.Graph()

        # Add nodes (members)
        for member in members:
            G.add_node(member.id, name=member.name, role=member.role)

        # Add edges (communications)
        for comm in communications:
            if comm.receiver_id and comm.receiver_id in [m.id for m in members]:
                if G.has_edge(comm.sender_id, comm.receiver_id):
                    G[comm.sender_id][comm.receiver_id]["weight"] += 1
                else:
                    G.add_edge(comm.sender_id, comm.receiver_id, weight=1)

        return G

    def analyze_network_metrics(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        """
        Analyze network metrics to understand team structure.

        Returns:
            Dictionary with network analysis metrics
        """
        G = self.build_communication_network(team_id, start_date, end_date)

        if G.number_of_nodes() == 0:
            return {"error": "No data available for analysis"}

        # Calculate network metrics
        density = nx.density(G)

        # Centrality measures
        try:
            betweenness = nx.betweenness_centrality(G)
            closeness = nx.closeness_centrality(G)

            # Find most central member
            most_central = (
                max(betweenness.items(), key=lambda x: x[1]) if betweenness else (None, 0)
            )

            # Check if network is connected
            is_connected = nx.is_connected(G)

            # Find potential bottlenecks (high betweenness) - vectorized
            betweenness_values = np.array(list(betweenness.values()))
            threshold = np.mean(betweenness_values) + np.std(betweenness_values)
            bottlenecks = [
                node for node, centrality in betweenness.items() if centrality > threshold
            ]

            logger.info(
                f"Team {team_id} network: density={density:.3f}, {len(bottlenecks)} bottlenecks"
            )

            return {
                "density": round(density, 3),
                "is_connected": is_connected,
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "most_central_member_id": most_central[0],
                "centrality_score": round(most_central[1], 3),
                "potential_bottlenecks": bottlenecks,
                "avg_betweenness": round(np.mean(list(betweenness.values())), 3),
            }
        except (nx.NetworkXError, nx.PowerIterationFailedConvergence, ValueError) as e:
            # Handle case where graph is too sparse or disconnected
            return {
                "density": round(density, 3),
                "num_nodes": G.number_of_nodes(),
                "num_edges": G.number_of_edges(),
                "note": f"Network too sparse for full analysis: {str(e)}",
            }

    def detect_communities(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        """
        Detect sub-communities within the team using community detection algorithms.

        Identifies potential silos or cliques that may hinder team cohesion.

        Returns:
            Dictionary with community information and modularity scores
        """
        from networkx.algorithms import community

        G = self.build_communication_network(team_id, start_date, end_date)

        if G.number_of_nodes() < 3:
            return {"error": "Need at least 3 members for community detection"}

        try:
            # Louvain community detection (greedy modularity optimization)
            communities = community.greedy_modularity_communities(G)

            # Calculate modularity (measure of how well-separated communities are)
            modularity = community.modularity(G, communities)

            # Convert to list format with member details
            community_list = []
            for i, comm in enumerate(communities):
                member_ids = list(comm)
                member_names = [
                    G.nodes[node]["name"] for node in member_ids if "name" in G.nodes[node]
                ]
                community_list.append(
                    {
                        "community_id": i + 1,
                        "member_ids": member_ids,
                        "member_names": member_names,
                        "size": len(member_ids),
                    }
                )

            # Interpret results
            interpretation = self._interpret_communities(
                len(communities), modularity, G.number_of_nodes()
            )

            return {
                "num_communities": len(communities),
                "communities": community_list,
                "modularity": round(modularity, 3),
                "is_siloed": modularity > 0.4,
                "interpretation": interpretation,
            }

        except Exception as e:
            return {"error": f"Community detection failed: {str(e)}"}

    def _interpret_communities(
        self, num_communities: int, modularity: float, num_members: int
    ) -> str:
        """Provide human-readable interpretation of community structure"""
        if num_communities == 1:
            return "Team is well-integrated with no distinct sub-groups."

        # Pythonic threshold-based interpretation using next()
        interpretations = [
            (
                modularity > 0.5,
                f"⚠️ Warning: Team has {num_communities} distinct silos (high modularity: {modularity:.2f}). Consider cross-group activities to improve collaboration.",
            ),
            (
                modularity > 0.3,
                f"Team has {num_communities} sub-groups but maintains good cross-communication (moderate modularity: {modularity:.2f}).",
            ),
            (
                True,
                f"Team has {num_communities} informal groupings with excellent cross-communication (low modularity: {modularity:.2f}).",
            ),
        ]
        return next(msg for condition, msg in interpretations if condition)

    def calculate_advanced_centrality(
        self, team_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict:
        """
        Calculate comprehensive centrality metrics to identify key players.

        Identifies:
        - Connectors (high betweenness): Bridge different parts of network
        - Influencers (high eigenvector): Connected to other important people
        - Hubs (high degree): Have most direct connections

        Returns:
            Dictionary with centrality metrics and key role identifications
        """
        G = self.build_communication_network(team_id, start_date, end_date)

        if G.number_of_nodes() == 0:
            return {"error": "No data available"}

        try:
            # Calculate all centrality measures
            degree_cent = nx.degree_centrality(G)
            betweenness_cent = nx.betweenness_centrality(G)
            closeness_cent = nx.closeness_centrality(G)

            # Eigenvector centrality (may fail for disconnected graphs)
            try:
                eigenvector_cent = nx.eigenvector_centrality(G, max_iter=1000)
            except (nx.PowerIterationFailedConvergence, nx.NetworkXError):
                eigenvector_cent = {node: 0 for node in G.nodes()}

            # Identify top performers in each category
            top_n = min(3, G.number_of_nodes())

            connectors = sorted(betweenness_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
            influencers = sorted(eigenvector_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]
            hubs = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:top_n]

            # Get member names
            def get_member_info(member_id):
                return {
                    "member_id": member_id,
                    "name": G.nodes[member_id].get("name", f"Member {member_id}"),
                    "role": G.nodes[member_id].get("role", "Unknown"),
                }

            return {
                "centrality_metrics": {
                    "degree": {k: round(v, 3) for k, v in degree_cent.items()},
                    "betweenness": {k: round(v, 3) for k, v in betweenness_cent.items()},
                    "closeness": {k: round(v, 3) for k, v in closeness_cent.items()},
                    "eigenvector": {k: round(v, 3) for k, v in eigenvector_cent.items()},
                },
                "key_roles": {
                    "connectors": [
                        {**get_member_info(k), "score": round(v, 3)} for k, v in connectors
                    ],
                    "influencers": [
                        {**get_member_info(k), "score": round(v, 3)} for k, v in influencers
                    ],
                    "hubs": [{**get_member_info(k), "score": round(v, 3)} for k, v in hubs],
                },
                "insights": self._generate_centrality_insights(
                    degree_cent, betweenness_cent, eigenvector_cent
                ),
            }

        except Exception as e:
            return {"error": f"Centrality calculation failed: {str(e)}"}

    def _generate_centrality_insights(
        self, degree_cent: Dict, betweenness_cent: Dict, eigenvector_cent: Dict
    ) -> List[str]:
        """Generate actionable insights from centrality metrics"""
        insights = []

        # Check for over-centralization
        if betweenness_cent:
            max_between = max(betweenness_cent.values())
            if max_between > 0.5:
                insights.append(
                    "⚠️ Network is highly centralized around one person - consider distributing communication responsibilities"
                )

        # Check for disconnected members
        if degree_cent:
            min_degree = min(degree_cent.values())
            if min_degree == 0:
                isolated = sum(1 for v in degree_cent.values() if v == 0)
                insights.append(f"⚠️ {isolated} member(s) are isolated with no connections")

        # Check for healthy distribution
        if betweenness_cent and len(betweenness_cent) > 3:
            avg_between = np.mean(list(betweenness_cent.values()))
            std_between = np.std(list(betweenness_cent.values()))
            if std_between / avg_between < 0.5 if avg_between > 0 else False:
                insights.append("✅ Communication responsibility is well-distributed across team")

        return insights if insights else ["Network structure appears healthy"]
