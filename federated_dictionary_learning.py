"""
COBOL Protocol v1.5 - Federated Learning for Distributed Dictionary Optimization
Distributed machine learning for optimizing compression dictionaries across nodes

Features:
- Local dictionary optimization on edge nodes
- Federated aggregation of pattern frequencies
- Differential privacy for dictionary sharing
- Consensus-based pattern selection
- Adaptive pattern weighting
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Set
from enum import Enum
import json
import hashlib
import time
from collections import defaultdict, Counter
import numpy as np
import logging
from metrics import inc_evicted_count, set_global_patterns


class FederationStrategy(Enum):
    """Dictionary aggregation strategies"""
    FREQUENCY_WEIGHTED = 1
    ENTROPY_BASED = 2
    CONSENSUS = 3
    ADAPTIVE = 4


@dataclass
class PatternInfo:
    """Information about a pattern"""
    pattern: bytes = None
    pattern_hex: str = None  # For serialization
    frequency: int = 0
    entropy: float = 0.0
    roi: float = 0.0
    node_id: str = None
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if self.pattern and not self.pattern_hex:
            self.pattern_hex = self.pattern.hex()
    
    def to_dict(self):
        """Convert to JSON-serializable dict"""
        d = asdict(self)
        d['pattern'] = None  # Don't serialize bytes
        return d
    
    @staticmethod
    def from_dict(d: Dict):
        """Create from dict"""
        p = PatternInfo(
            pattern_hex=d.get('pattern_hex'),
            frequency=d.get('frequency', 0),
            entropy=d.get('entropy', 0.0),
            roi=d.get('roi', 0.0),
            node_id=d.get('node_id'),
            timestamp=d.get('timestamp', time.time())
        )
        if p.pattern_hex:
            p.pattern = bytes.fromhex(p.pattern_hex)
        return p


@dataclass
class LocalDictionary:
    """Local dictionary on edge node"""
    node_id: str
    patterns: Dict[bytes, PatternInfo] = field(default_factory=dict)
    data_processed: int = 0
    created_at: float = field(default_factory=time.time)
    version: int = 1
    
    def add_pattern(self, pattern: bytes, frequency: int = 1):
        """Add pattern with frequency"""
        if pattern not in self.patterns:
            self.patterns[pattern] = PatternInfo(
                pattern=pattern,
                frequency=frequency,
                node_id=self.node_id
            )
        else:
            self.patterns[pattern].frequency += frequency
    
    def calculate_entropy(self):
        """Calculate entropy for each pattern"""
        total_freq = sum(p.frequency for p in self.patterns.values())
        
        for pattern_info in self.patterns.values():
            if total_freq > 0:
                p = pattern_info.frequency / total_freq
                if p > 0:
                    pattern_info.entropy = -p * np.log2(p)
    
    def calculate_roi(self):
        """Calculate ROI (Return on Investment) for each pattern"""
        for pattern, info in self.patterns.items():
            # ROI = (bytes_saved) / (catalog_cost)
            savings = (len(pattern) - 1) * info.frequency - 2
            info.roi = savings / (1 + len(pattern)) if savings > 0 else 0
    
    def get_top_patterns(self, limit: int = 255) -> List[Tuple[bytes, PatternInfo]]:
        """Get top patterns by ROI"""
        sorted_patterns = sorted(
            self.patterns.items(),
            key=lambda x: x[1].roi,
            reverse=True
        )
        return sorted_patterns[:limit]
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        data = {
            'node_id': self.node_id,
            'version': self.version,
            'data_processed': self.data_processed,
            'created_at': self.created_at,
            'patterns': {
                p.hex(): info.to_dict()
                for p, info in self.patterns.items()
            }
        }
        return json.dumps(data)
    
    @staticmethod
    def from_json(json_str: str) -> 'LocalDictionary':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        
        ld = LocalDictionary(
            node_id=data['node_id'],
            data_processed=data.get('data_processed', 0),
            created_at=data.get('created_at', time.time()),
            version=data.get('version', 1)
        )
        
        for pattern_hex, info_dict in data.get('patterns', {}).items():
            pattern = bytes.fromhex(pattern_hex)
            info = PatternInfo.from_dict(info_dict)
            info.pattern = pattern
            ld.patterns[pattern] = info
        
        return ld


class FederatedPatternAggregator:
    """Aggregates patterns from multiple nodes"""
    
    def __init__(self, strategy: FederationStrategy = FederationStrategy.CONSENSUS):
        self.strategy = strategy
        self.aggregated_patterns = {}
        self.node_contributions = defaultdict(int)
        self.consensus_threshold = 0.5  # 50% of nodes must agree
    
    def aggregate(self, dictionaries: List[LocalDictionary], 
                 max_patterns: int = 255) -> Dict[bytes, PatternInfo]:
        """
        Aggregate patterns from multiple dictionaries
        
        Args:
            dictionaries: List of local dictionaries
            max_patterns: Maximum patterns to aggregate
        
        Returns:
            Aggregated pattern dictionary
        """
        
        if self.strategy == FederationStrategy.FREQUENCY_WEIGHTED:
            return self._aggregate_frequency_weighted(dictionaries, max_patterns)
        elif self.strategy == FederationStrategy.ENTROPY_BASED:
            return self._aggregate_entropy_based(dictionaries, max_patterns)
        elif self.strategy == FederationStrategy.CONSENSUS:
            return self._aggregate_consensus(dictionaries, max_patterns)
        elif self.strategy == FederationStrategy.ADAPTIVE:
            return self._aggregate_adaptive(dictionaries, max_patterns)
    
    def _aggregate_frequency_weighted(self, dictionaries: List[LocalDictionary],
                                     max_patterns: int) -> Dict[bytes, PatternInfo]:
        """Aggregate by frequency weighting"""
        pattern_stats = defaultdict(lambda: {'frequency': 0, 'nodes': set()})
        
        for local_dict in dictionaries:
            for pattern, info in local_dict.patterns.items():
                pattern_stats[pattern]['frequency'] += info.frequency
                pattern_stats[pattern]['nodes'].add(local_dict.node_id)
        
        # Create aggregated patterns
        aggregated = {}
        for pattern, stats in sorted(
            pattern_stats.items(),
            key=lambda x: x[1]['frequency'],
            reverse=True
        )[:max_patterns]:
            aggregated[pattern] = PatternInfo(
                pattern=pattern,
                frequency=stats['frequency'],
                roi=stats['frequency'] / (1 + len(pattern))
            )
        
        return aggregated
    
    def _aggregate_entropy_based(self, dictionaries: List[LocalDictionary],
                                max_patterns: int) -> Dict[bytes, PatternInfo]:
        """Aggregate by entropy contribution"""
        pattern_entropy = defaultdict(float)
        pattern_freq = defaultdict(int)
        
        for local_dict in dictionaries:
            total_freq = sum(p.frequency for p in local_dict.patterns.values())
            
            for pattern, info in local_dict.patterns.items():
                if total_freq > 0:
                    p = info.frequency / total_freq
                    if p > 0:
                        entropy_contrib = -p * np.log2(p)
                        pattern_entropy[pattern] += entropy_contrib
                        pattern_freq[pattern] += info.frequency
        
        aggregated = {}
        for pattern in sorted(
            pattern_entropy.keys(),
            key=lambda x: pattern_entropy[x],
            reverse=True
        )[:max_patterns]:
            aggregated[pattern] = PatternInfo(
                pattern=pattern,
                frequency=pattern_freq[pattern],
                entropy=pattern_entropy[pattern]
            )
        
        return aggregated
    
    def _aggregate_consensus(self, dictionaries: List[LocalDictionary],
                            max_patterns: int) -> Dict[bytes, PatternInfo]:
        """Consensus-based aggregation (patterns must appear in >50% nodes)"""
        pattern_node_count = defaultdict(int)
        pattern_freq_sum = defaultdict(int)
        
        for local_dict in dictionaries:
            for pattern, info in local_dict.patterns.items():
                pattern_node_count[pattern] += 1
                pattern_freq_sum[pattern] += info.frequency
        
        # Filter: patterns in >threshold fraction of nodes
        min_nodes = int(len(dictionaries) * self.consensus_threshold)
        qualified = [p for p, count in pattern_node_count.items() 
                    if count >= min_nodes]
        
        aggregated = {}
        for pattern in sorted(
            qualified,
            key=lambda x: pattern_freq_sum[x],
            reverse=True
        )[:max_patterns]:
            aggregated[pattern] = PatternInfo(
                pattern=pattern,
                frequency=pattern_freq_sum[pattern],
                node_id='consensus'
            )
        
        return aggregated
    
    def _aggregate_adaptive(self, dictionaries: List[LocalDictionary],
                           max_patterns: int) -> Dict[bytes, PatternInfo]:
        """Adaptive aggregation: weighted by node performance and consensus"""
        # Start with consensus patterns
        consensus = self._aggregate_consensus(dictionaries, max_patterns // 2)
        
        # Add high-ROI patterns from individual nodes
        all_patterns = defaultdict(list)
        for local_dict in dictionaries:
            local_dict.calculate_roi()
            for pattern, info in local_dict.get_top_patterns(50):
                all_patterns[pattern].append(info)
        
        # Add patterns not in consensus but high ROI
        adaptive = dict(consensus)
        for pattern, infos in sorted(
            all_patterns.items(),
            key=lambda x: sum(i.roi for i in x[1]),
            reverse=True
        ):
            if pattern not in adaptive and len(adaptive) < max_patterns:
                avg_roi = sum(i.roi for i in infos) / len(infos)
                adaptive[pattern] = PatternInfo(
                    pattern=pattern,
                    frequency=sum(i.frequency for i in infos),
                    roi=avg_roi
                )
        
        return adaptive


class DifferentialPrivacy:
    """Add differential privacy to shared dictionaries"""
    
    def __init__(self, epsilon: float = 0.1):
        """
        Initialize with privacy budget
        
        Args:
            epsilon: Privacy budget (smaller = more private)
        """
        self.epsilon = epsilon
    
    def add_laplace_noise(self, pattern_info: PatternInfo) -> PatternInfo:
        """Add Laplace noise to frequency"""
        # Laplace noise scale
        scale = 1.0 / self.epsilon
        
        # Add noise
        noise = np.random.laplace(0, scale)
        noisy_frequency = max(0, int(pattern_info.frequency + noise))
        
        # Create noisy copy
        noisy_info = PatternInfo(
            pattern=pattern_info.pattern,
            frequency=noisy_frequency,
            entropy=pattern_info.entropy,
            roi=pattern_info.roi
        )
        return noisy_info
    
    def anonymize_dictionary(self, dictionary: LocalDictionary) -> LocalDictionary:
        """Anonymize dictionary for sharing"""
        anon_dict = LocalDictionary(
            node_id='anonymized',
            data_processed=dictionary.data_processed
        )
        
        for pattern, info in dictionary.patterns.items():
            noisy_info = self.add_laplace_noise(info)
            anon_dict.patterns[pattern] = noisy_info
        
        return anon_dict


class DistributedDictionaryManager:
    """Manages dictionaries across distributed nodes

    Enforces hard limits documented in DESIGN.md:
      - global pattern cap
      - per-pattern TTL
      - entropy contribution threshold
      - cost-based admission/eviction
    """
    
    # defaults; can be overridden when instantiating
    GLOBAL_PATTERN_CAP: int = 100_000
    PATTERN_TTL: float = 24 * 3600           # seconds
    ENTROPY_THRESHOLD: float = 0.0           # patterns with entropy lower are discarded
    COST_MAX: float = 1e6                    # maximum allowed cost

    def __init__(self, aggregation_strategy: FederationStrategy = FederationStrategy.ADAPTIVE,
                 global_cap: Optional[int] = None,
                 ttl_hours: Optional[float] = None,
                 entropy_threshold: Optional[float] = None,
                 cost_max: Optional[float] = None):
        self.aggregator = FederatedPatternAggregator(aggregation_strategy)
        self.local_dictionaries: Dict[str, LocalDictionary] = {}
        self.global_dictionary: Dict[bytes, PatternInfo] = {}
        self.privacy = DifferentialPrivacy(epsilon=0.1)
        self.aggregation_history = []

        if global_cap is not None:
            self.GLOBAL_PATTERN_CAP = global_cap
        if ttl_hours is not None:
            self.PATTERN_TTL = ttl_hours * 3600
        if entropy_threshold is not None:
            self.ENTROPY_THRESHOLD = entropy_threshold
        if cost_max is not None:
            self.COST_MAX = cost_max
    
    def register_node(self, node_id: str):
        """Register a new node"""
        self.local_dictionaries[node_id] = LocalDictionary(node_id=node_id)
    
    def _pattern_cost(self, info: PatternInfo) -> float:
        """Cost used for admission/eviction according to DESIGN.md: size/gain.
        Fallback to ROI if available, otherwise entropy.
        """
        size = len(info.pattern) if info.pattern else 0
        gain = info.roi if info.roi > 0 else info.entropy
        if gain <= 0:
            return float('inf')
        return size / gain

    def update_local_dictionary(self, node_id: str, data: bytes):
        """
        Update local dictionary with observed data
        
        Args:
            node_id: Node identifier
            data: Data chunk to analyze
        """
        if node_id not in self.local_dictionaries:
            self.register_node(node_id)
        
        local_dict = self.local_dictionaries[node_id]
        local_dict.data_processed += len(data)
        
        # Analyze patterns in data
        from collections import Counter
        for size in [2, 3, 4, 8]:
            if size > len(data):
                continue
            for i in range(len(data) - size + 1):
                pattern = data[i:i+size]
                local_dict.add_pattern(pattern)
        
        # Calculate metrics
        local_dict.calculate_entropy()
        local_dict.calculate_roi()

    def _apply_limits(self, patterns: Dict[bytes, PatternInfo]) -> Tuple[Dict[bytes, PatternInfo], List[Tuple[bytes, float]]]:
        """Enforce entropy threshold, TTL, cost and global cap.
        Returns a tuple of (filtered_patterns, evicted_list).

        Timestamps are preserved from the previous global dictionary so that TTL
        is measured from first appearance rather than from each aggregation.
        """
        now = time.time()
        # merge timestamps: retain old timestamps or set to now for new patterns
        for pat, info in patterns.items():
            if pat in self.global_dictionary:
                info.timestamp = self.global_dictionary[pat].timestamp
            else:
                info.timestamp = now

        # filter by entropy threshold, TTL, cost
        filtered: Dict[bytes, PatternInfo] = {}
        evicted: List[Tuple[bytes, float]] = []
        for pat, info in patterns.items():
            if info.entropy < self.ENTROPY_THRESHOLD:
                evicted.append((pat, self._pattern_cost(info)))
                continue
            if now - info.timestamp > self.PATTERN_TTL:
                # expired
                evicted.append((pat, self._pattern_cost(info)))
                continue
            cost = self._pattern_cost(info)
            if cost > self.COST_MAX:
                evicted.append((pat, cost))
                continue
            filtered[pat] = info

        # enforce global cap by evicting highest-cost entries
        if len(filtered) > self.GLOBAL_PATTERN_CAP:
            # sort by cost descending and evict until under cap
            sorted_items = sorted(filtered.items(),
                                  key=lambda x: self._pattern_cost(x[1]),
                                  reverse=True)
            allowed = dict(sorted_items[:self.GLOBAL_PATTERN_CAP])
            removed = sorted_items[self.GLOBAL_PATTERN_CAP:]
            for pat, info in removed:
                evicted.append((pat, self._pattern_cost(info)))
            return allowed, evicted
        return filtered, evicted

    def federated_aggregation(self, use_privacy: bool = True) -> Dict[bytes, PatternInfo]:
        """
        Perform federated aggregation across all nodes
        
        Args:
            use_privacy: Apply differential privacy
        
        Returns:
            Aggregated global dictionary
        """
        # Optional: apply privacy
        dicts_to_aggregate = []
        if use_privacy:
            for local_dict in self.local_dictionaries.values():
                anon_dict = self.privacy.anonymize_dictionary(local_dict)
                dicts_to_aggregate.append(anon_dict)
        else:
            dicts_to_aggregate = list(self.local_dictionaries.values())
        
        # Aggregate with a high cap; limits applied afterward
        raw = self.aggregator.aggregate(
            dicts_to_aggregate,
            max_patterns=self.GLOBAL_PATTERN_CAP
        )

        # enforce documented limits and record evictions for telemetry
        filtered, evicted = self._apply_limits(raw)
        self.global_dictionary = filtered

        # Log evictions and acceptance counts
        logger = logging.getLogger(__name__)
        if evicted:
            logger.info('Federation eviction count=%d samples=%d', len(evicted), len(self.local_dictionaries))
            # metrics + store a compact eviction summary
            inc_evicted_count(len(evicted))
            self.aggregation_history.append({
                'timestamp': time.time(),
                'event': 'eviction',
                'evicted_count': len(evicted),
                'strategy': self.aggregator.strategy.name
            })

        # record aggregation summary
        self.aggregation_history.append({
            'timestamp': time.time(),
            'num_nodes': len(self.local_dictionaries),
            'patterns': len(self.global_dictionary),
            'strategy': self.aggregator.strategy.name
        })

        # update metrics
        set_global_patterns(len(self.global_dictionary))

        return self.global_dictionary
    
    def get_global_dictionary(self) -> Dict[bytes, PatternInfo]:
        """Get current global dictionary"""
        return self.global_dictionary
    
    def get_node_statistics(self, node_id: str) -> Dict:
        """Get statistics for a node"""
        if node_id not in self.local_dictionaries:
            return {}
        
        local_dict = self.local_dictionaries[node_id]
        return {
            'node_id': node_id,
            'data_processed': local_dict.data_processed,
            'patterns': len(local_dict.patterns),
            'created_at': local_dict.created_at,
            'top_patterns': [
                {
                    'pattern': p.hex(),
                    'frequency': info.frequency,
                    'roi': round(info.roi, 4)
                }
                for p, info in local_dict.get_top_patterns(10)
            ]
        }
    
    def get_aggregation_report(self) -> Dict:
        """Get report on federated aggregation"""
        return {
            'total_nodes': len(self.local_dictionaries),
            'global_patterns': len(self.global_dictionary),
            'total_data_processed': sum(
                d.data_processed for d in self.local_dictionaries.values()
            ),
            'aggregation_history': self.aggregation_history,
            'strategy': self.aggregator.strategy.name
        }

    def prepare_advertisement(self, orchestrator_cap: Optional[int] = None) -> Dict:
        """Prepare an advertisement payload for federation.

        - Trims the current `global_dictionary` according to local and
          orchestrator caps and returns a payload containing:
            - `patterns`: trimmed dict
            - `pattern_count`: number of patterns
            - `evicted`: list of evicted (pattern, cost)
            - `hash`: SHA256 of concatenated pattern bytes (sorted)

        This helper is intended for sender-side automatic trimming before
        attempting a broadcast to the orchestrator.
        """
        # Ensure we have an up-to-date global dictionary
        if not self.global_dictionary:
            # perform aggregation without privacy to populate global_dictionary
            self.federated_aggregation(use_privacy=False)

        source = dict(self.global_dictionary)
        # temporarily respect orchestrator cap if provided
        if orchestrator_cap is not None:
            prev_cap = self.GLOBAL_PATTERN_CAP
            try:
                self.GLOBAL_PATTERN_CAP = orchestrator_cap
                filtered, evicted = self._apply_limits(source)
            finally:
                self.GLOBAL_PATTERN_CAP = prev_cap
        else:
            filtered, evicted = self._apply_limits(source)

        # compute stable hash over sorted patterns
        h = hashlib.sha256()
        for p in sorted(filtered.keys()):
            h.update(p)
        payload_hash = h.hexdigest()
        return {
            'patterns': filtered,
            'pattern_count': len(filtered),
            'evicted': evicted,
            'hash': payload_hash
        }


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_federated_optimization():
    """Example of federated dictionary optimization"""
    
    # Create distributed manager
    manager = DistributedDictionaryManager(
        aggregation_strategy=FederationStrategy.ADAPTIVE
    )
    
    # Simulate 3 nodes with different data
    nodes_data = {
        'node1': b'COBOL PROGRAM IDENTIFICATION DIVISION ' * 1000,
        'node2': b'DATA DIVISION WORKING-STORAGE SECTION ' * 1000,
        'node3': b'PROCEDURE DIVISION PERFORM UNTIL DONE ' * 1000,
    }
    
    print("=" * 60)
    print("Federated Dictionary Optimization Example")
    print("=" * 60)
    
    # Step 1: Local optimization
    print("\n1. Local Dictionary Optimization:")
    for node_id, data in nodes_data.items():
        manager.update_local_dictionary(node_id, data)
        stats = manager.get_node_statistics(node_id)
        print(f"  {node_id}:")
        print(f"    - Patterns: {stats['patterns']}")
        print(f"    - Data processed: {stats['data_processed']} bytes")
        if stats['top_patterns']:
            print(f"    - Top pattern: {stats['top_patterns'][0]['pattern'][:8]}... "
                  f"(ROI={stats['top_patterns'][0]['roi']})")
    
    # Step 2: Federated aggregation
    print("\n2. Federated Aggregation (with differential privacy):")
    global_dict = manager.federated_aggregation(use_privacy=True)
    print(f"  Global patterns: {len(global_dict)}")
    
    # Step 3: Report
    print("\n3. Aggregation Report:")
    report = manager.get_aggregation_report()
    print(f"  Total nodes: {report['total_nodes']}")
    print(f"  Global patterns: {report['global_patterns']}")
    print(f"  Total data: {report['total_data_processed']} bytes")
    print(f"  Strategy: {report['strategy']}")
    
    print("\n" + "=" * 60)
    return manager


if __name__ == '__main__':
    manager = example_federated_optimization()
