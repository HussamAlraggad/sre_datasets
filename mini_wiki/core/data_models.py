"""
Core data models for mini_wiki
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


@dataclass
class DataRecord:
    """Single record from dataset"""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    relevance_score: Optional[float] = None
    importance_score: Optional[float] = None
    final_score: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "metadata": self.metadata,
            "relevance_score": self.relevance_score,
            "importance_score": self.importance_score,
            "final_score": self.final_score,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Dataset:
    """Collection of records"""

    name: str
    records: List[DataRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_record(self, record: DataRecord) -> None:
        """Add record to dataset"""
        self.records.append(record)
        self.updated_at = datetime.now()

    def get_record(self, record_id: str) -> Optional[DataRecord]:
        """Get record by ID"""
        for record in self.records:
            if record.id == record_id:
                return record
        return None

    def get_records_by_score(self, min_score: float = 0.0) -> List[DataRecord]:
        """Get records with score >= min_score"""
        return [r for r in self.records if r.final_score and r.final_score >= min_score]

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataset to dictionary"""
        return {
            "name": self.name,
            "record_count": len(self.records),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class RankingResult:
    """Result of ranking operation"""

    query: str
    results: List[DataRecord] = field(default_factory=list)
    total_count: int = 0
    filtered_count: int = 0
    ranking_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def get_top_k(self, k: int) -> List[DataRecord]:
        """Get top K results"""
        return self.results[:k]

    def get_results_by_score(self, min_score: float) -> List[DataRecord]:
        """Get results with score >= min_score"""
        return [r for r in self.results if r.final_score and r.final_score >= min_score]

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "query": self.query,
            "total_count": self.total_count,
            "filtered_count": self.filtered_count,
            "result_count": len(self.results),
            "ranking_config": self.ranking_config,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class AIReference:
    """AI teaching documentation"""

    dataset_context: Dict[str, Any] = field(default_factory=dict)
    ranking_methodology: Dict[str, Any] = field(default_factory=dict)
    top_content: List[Dict[str, Any]] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert reference to dictionary"""
        return {
            "dataset_context": self.dataset_context,
            "ranking_methodology": self.ranking_methodology,
            "top_content": self.top_content,
            "quality_metrics": self.quality_metrics,
            "generated_at": self.generated_at.isoformat(),
        }

    def to_yaml(self) -> str:
        """Convert reference to YAML format"""
        import yaml

        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        """Convert reference to JSON format"""
        import json

        return json.dumps(self.to_dict(), indent=2, default=str)
