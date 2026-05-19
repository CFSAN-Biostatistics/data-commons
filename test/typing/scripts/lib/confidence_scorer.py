"""
Assess confidence in metadata and generate scores for test case candidates.
"""

from typing import Dict, List


class ConfidenceScorer:
    """Score candidate test cases based on metadata quality and completeness."""

    @staticmethod
    def score_metadata_confidence(
        serotype_confidence: str,
        serotype_evidence: List[Dict],
        st_evidence: List[Dict],
        quality_metrics: Dict
    ) -> Dict:
        """
        Generate overall confidence score for a candidate.

        Args:
            serotype_confidence: Confidence level from metadata_parser
            serotype_evidence: List of serotype evidence
            st_evidence: List of ST evidence
            quality_metrics: Data quality metrics

        Returns:
            Score dictionary with overall score and breakdown
        """
        score = {
            "overall": 0.0,
            "breakdown": {
                "serotype_confidence": 0.0,
                "has_multiple_evidence": 0.0,
                "has_mlst": 0.0,
                "has_both_data_types": 0.0,
                "has_coverage_info": 0.0,
                "reputable_submitter": 0.0
            },
            "category": "low"
        }

        # Serotype confidence (0-30 points)
        if serotype_confidence == "high":
            score["breakdown"]["serotype_confidence"] = 30
        elif serotype_confidence == "medium":
            score["breakdown"]["serotype_confidence"] = 20
        elif serotype_confidence == "low":
            score["breakdown"]["serotype_confidence"] = 10
        else:  # conflict
            score["breakdown"]["serotype_confidence"] = 0

        # Multiple evidence sources (0-20 points)
        if len(serotype_evidence) >= 2:
            score["breakdown"]["has_multiple_evidence"] = 20
        elif len(serotype_evidence) == 1:
            score["breakdown"]["has_multiple_evidence"] = 10

        # MLST data available (0-15 points)
        if len(st_evidence) > 0:
            score["breakdown"]["has_mlst"] = 15

        # Both reads and assembly (0-15 points)
        if quality_metrics.get("has_reads") and quality_metrics.get("has_assembly"):
            score["breakdown"]["has_both_data_types"] = 15
        elif quality_metrics.get("has_reads") or quality_metrics.get("has_assembly"):
            score["breakdown"]["has_both_data_types"] = 8

        # Coverage information (0-10 points)
        if quality_metrics.get("reported_coverage"):
            score["breakdown"]["has_coverage_info"] = 10

        # Reputable submitter (0-10 points)
        submitter = quality_metrics.get("submitter", "").lower()
        reputable_keywords = ["fda", "cdc", "usda", "university", "ncbi", "refseq"]
        if any(keyword in submitter for keyword in reputable_keywords):
            score["breakdown"]["reputable_submitter"] = 10

        # Calculate overall score (0-100)
        score["overall"] = sum(score["breakdown"].values())

        # Categorize
        if score["overall"] >= 75:
            score["category"] = "high"
        elif score["overall"] >= 50:
            score["category"] = "medium"
        else:
            score["category"] = "low"

        return score

    @staticmethod
    def rank_candidates(candidates: List[Dict]) -> List[Dict]:
        """
        Rank candidates by confidence score.

        Args:
            candidates: List of candidate dictionaries with 'score' field

        Returns:
            Sorted list (highest score first)
        """
        return sorted(
            candidates,
            key=lambda c: c.get("score", {}).get("overall", 0),
            reverse=True
        )

    @staticmethod
    def filter_candidates(
        candidates: List[Dict],
        min_score: float = 50.0,
        require_serotype: bool = True
    ) -> List[Dict]:
        """
        Filter candidates by minimum criteria.

        Args:
            candidates: List of candidate dictionaries
            min_score: Minimum overall score (0-100)
            require_serotype: Whether serotype must be present

        Returns:
            Filtered list of candidates
        """
        filtered = []

        for candidate in candidates:
            score = candidate.get("score", {}).get("overall", 0)

            if score < min_score:
                continue

            if require_serotype:
                serotype = candidate.get("ground_truth", {}).get("serological", {}).get("serotype")
                if not serotype:
                    continue

            filtered.append(candidate)

        return filtered
