from __future__ import annotations

import math
from typing import Any, Callable, Mapping

from scene_exchange.intake.demand_contract import DomainRecord, RuleResult, bounded, finite_number, normalized_text

RuleFunction = Callable[[DomainRecord, Mapping[str, Any]], RuleResult]

def _number(record: DomainRecord, field: str) -> float:
    value = record.payload.get(field)
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, (int, float)):
        return finite_number(value)
    text = normalized_text(value)
    if not text:
        return 0.0
    try:
        return finite_number(text)
    except ValueError:
        return float(sum(ord(ch) for ch in text) % 101)

def _context_number(context: Mapping[str, Any], key: str, default: float) -> float:
    try:
        return finite_number(context.get(key, default))
    except ValueError:
        return default

def _result(code: str, value: float, threshold: float, higher_is_better: bool, message: str, evidence: dict[str, Any]) -> RuleResult:
    distance = (value - threshold) if higher_is_better else (threshold - value)
    passed = distance >= 0
    scale = max(1.0, abs(threshold))
    score = bounded(0.5 + distance / (2.0 * scale))
    severity = 'info' if passed else ('critical' if score < 0.2 else 'error')
    return RuleResult(code, passed, score, severity, message, evidence)

def check_sector_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_sector_presence_threshold', 10.333)
    return _result('check_sector_presence', adjusted, threshold, True, 'validates sector presence',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_sector_range_threshold', 12.667)
    return _result('check_sector_range', adjusted, threshold, True, 'validates sector range',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_sector_stability_threshold', 15.0)
    return _result('check_sector_stability', adjusted, threshold, False, 'validates sector stability',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_sector_freshness_threshold', 17.333)
    return _result('check_sector_freshness', adjusted, threshold, True, 'validates sector freshness',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_sector_coverage_threshold', 19.667)
    return _result('check_sector_coverage', adjusted, threshold, True, 'validates sector coverage',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_sector_consistency_threshold', 22.0)
    return _result('check_sector_consistency', adjusted, threshold, False, 'validates sector consistency',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_sector_risk_threshold', 24.333)
    return _result('check_sector_risk', adjusted, threshold, True, 'validates sector risk',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_sector_confidence_threshold', 26.667)
    return _result('check_sector_confidence', adjusted, threshold, True, 'validates sector confidence',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_sector_dependency_threshold', 29.0)
    return _result('check_sector_dependency', adjusted, threshold, False, 'validates sector dependency',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_sector_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'sector')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_sector_readiness_threshold', 31.333)
    return _result('check_sector_readiness', adjusted, threshold, True, 'validates sector readiness',
                   {'field': 'sector', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_problem_severity_presence_threshold', 9.333)
    return _result('check_problem_severity_presence', adjusted, threshold, True, 'validates problem_severity presence',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_problem_severity_range_threshold', 11.667)
    return _result('check_problem_severity_range', adjusted, threshold, False, 'validates problem_severity range',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_problem_severity_stability_threshold', 14.0)
    return _result('check_problem_severity_stability', adjusted, threshold, True, 'validates problem_severity stability',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_problem_severity_freshness_threshold', 16.333)
    return _result('check_problem_severity_freshness', adjusted, threshold, True, 'validates problem_severity freshness',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_problem_severity_coverage_threshold', 18.667)
    return _result('check_problem_severity_coverage', adjusted, threshold, False, 'validates problem_severity coverage',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_problem_severity_consistency_threshold', 21.0)
    return _result('check_problem_severity_consistency', adjusted, threshold, True, 'validates problem_severity consistency',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_problem_severity_risk_threshold', 23.333)
    return _result('check_problem_severity_risk', adjusted, threshold, True, 'validates problem_severity risk',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_problem_severity_confidence_threshold', 25.667)
    return _result('check_problem_severity_confidence', adjusted, threshold, False, 'validates problem_severity confidence',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_problem_severity_dependency_threshold', 28.0)
    return _result('check_problem_severity_dependency', adjusted, threshold, True, 'validates problem_severity dependency',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_problem_severity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'problem_severity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_problem_severity_readiness_threshold', 30.333)
    return _result('check_problem_severity_readiness', adjusted, threshold, True, 'validates problem_severity readiness',
                   {'field': 'problem_severity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_data_readiness_presence_threshold', 8.333)
    return _result('check_data_readiness_presence', adjusted, threshold, False, 'validates data_readiness presence',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_data_readiness_range_threshold', 10.667)
    return _result('check_data_readiness_range', adjusted, threshold, True, 'validates data_readiness range',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_data_readiness_stability_threshold', 13.0)
    return _result('check_data_readiness_stability', adjusted, threshold, True, 'validates data_readiness stability',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_data_readiness_freshness_threshold', 15.333)
    return _result('check_data_readiness_freshness', adjusted, threshold, False, 'validates data_readiness freshness',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_data_readiness_coverage_threshold', 17.667)
    return _result('check_data_readiness_coverage', adjusted, threshold, True, 'validates data_readiness coverage',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_data_readiness_consistency_threshold', 20.0)
    return _result('check_data_readiness_consistency', adjusted, threshold, True, 'validates data_readiness consistency',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_data_readiness_risk_threshold', 22.333)
    return _result('check_data_readiness_risk', adjusted, threshold, False, 'validates data_readiness risk',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_data_readiness_confidence_threshold', 24.667)
    return _result('check_data_readiness_confidence', adjusted, threshold, True, 'validates data_readiness confidence',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_data_readiness_dependency_threshold', 27.0)
    return _result('check_data_readiness_dependency', adjusted, threshold, True, 'validates data_readiness dependency',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_data_readiness_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'data_readiness')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_data_readiness_readiness_threshold', 29.333)
    return _result('check_data_readiness_readiness', adjusted, threshold, False, 'validates data_readiness readiness',
                   {'field': 'data_readiness', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_deployment_window_presence_threshold', 31.667)
    return _result('check_deployment_window_presence', adjusted, threshold, True, 'validates deployment_window presence',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_deployment_window_range_threshold', 9.667)
    return _result('check_deployment_window_range', adjusted, threshold, True, 'validates deployment_window range',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_deployment_window_stability_threshold', 12.0)
    return _result('check_deployment_window_stability', adjusted, threshold, False, 'validates deployment_window stability',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_deployment_window_freshness_threshold', 14.333)
    return _result('check_deployment_window_freshness', adjusted, threshold, True, 'validates deployment_window freshness',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_deployment_window_coverage_threshold', 16.667)
    return _result('check_deployment_window_coverage', adjusted, threshold, True, 'validates deployment_window coverage',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_deployment_window_consistency_threshold', 19.0)
    return _result('check_deployment_window_consistency', adjusted, threshold, False, 'validates deployment_window consistency',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_deployment_window_risk_threshold', 21.333)
    return _result('check_deployment_window_risk', adjusted, threshold, True, 'validates deployment_window risk',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_deployment_window_confidence_threshold', 23.667)
    return _result('check_deployment_window_confidence', adjusted, threshold, True, 'validates deployment_window confidence',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_deployment_window_dependency_threshold', 26.0)
    return _result('check_deployment_window_dependency', adjusted, threshold, False, 'validates deployment_window dependency',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_deployment_window_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'deployment_window')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_deployment_window_readiness_threshold', 28.333)
    return _result('check_deployment_window_readiness', adjusted, threshold, True, 'validates deployment_window readiness',
                   {'field': 'deployment_window', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_budget_band_presence_threshold', 30.667)
    return _result('check_budget_band_presence', adjusted, threshold, True, 'validates budget_band presence',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_budget_band_range_threshold', 8.667)
    return _result('check_budget_band_range', adjusted, threshold, False, 'validates budget_band range',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_budget_band_stability_threshold', 11.0)
    return _result('check_budget_band_stability', adjusted, threshold, True, 'validates budget_band stability',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_budget_band_freshness_threshold', 13.333)
    return _result('check_budget_band_freshness', adjusted, threshold, True, 'validates budget_band freshness',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_budget_band_coverage_threshold', 15.667)
    return _result('check_budget_band_coverage', adjusted, threshold, False, 'validates budget_band coverage',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_budget_band_consistency_threshold', 18.0)
    return _result('check_budget_band_consistency', adjusted, threshold, True, 'validates budget_band consistency',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_budget_band_risk_threshold', 20.333)
    return _result('check_budget_band_risk', adjusted, threshold, True, 'validates budget_band risk',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_budget_band_confidence_threshold', 22.667)
    return _result('check_budget_band_confidence', adjusted, threshold, False, 'validates budget_band confidence',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_budget_band_dependency_threshold', 25.0)
    return _result('check_budget_band_dependency', adjusted, threshold, True, 'validates budget_band dependency',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_budget_band_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'budget_band')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_budget_band_readiness_threshold', 27.333)
    return _result('check_budget_band_readiness', adjusted, threshold, True, 'validates budget_band readiness',
                   {'field': 'budget_band', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_safety_class_presence_threshold', 29.667)
    return _result('check_safety_class_presence', adjusted, threshold, False, 'validates safety_class presence',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_safety_class_range_threshold', 32.0)
    return _result('check_safety_class_range', adjusted, threshold, True, 'validates safety_class range',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_safety_class_stability_threshold', 10.0)
    return _result('check_safety_class_stability', adjusted, threshold, True, 'validates safety_class stability',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_safety_class_freshness_threshold', 12.333)
    return _result('check_safety_class_freshness', adjusted, threshold, False, 'validates safety_class freshness',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_safety_class_coverage_threshold', 14.667)
    return _result('check_safety_class_coverage', adjusted, threshold, True, 'validates safety_class coverage',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_safety_class_consistency_threshold', 17.0)
    return _result('check_safety_class_consistency', adjusted, threshold, True, 'validates safety_class consistency',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_safety_class_risk_threshold', 19.333)
    return _result('check_safety_class_risk', adjusted, threshold, False, 'validates safety_class risk',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_safety_class_confidence_threshold', 21.667)
    return _result('check_safety_class_confidence', adjusted, threshold, True, 'validates safety_class confidence',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_safety_class_dependency_threshold', 24.0)
    return _result('check_safety_class_dependency', adjusted, threshold, True, 'validates safety_class dependency',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_safety_class_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'safety_class')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_safety_class_readiness_threshold', 26.333)
    return _result('check_safety_class_readiness', adjusted, threshold, False, 'validates safety_class readiness',
                   {'field': 'safety_class', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_localization_need_presence_threshold', 28.667)
    return _result('check_localization_need_presence', adjusted, threshold, True, 'validates localization_need presence',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_localization_need_range_threshold', 31.0)
    return _result('check_localization_need_range', adjusted, threshold, True, 'validates localization_need range',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_localization_need_stability_threshold', 9.0)
    return _result('check_localization_need_stability', adjusted, threshold, False, 'validates localization_need stability',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_localization_need_freshness_threshold', 11.333)
    return _result('check_localization_need_freshness', adjusted, threshold, True, 'validates localization_need freshness',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_localization_need_coverage_threshold', 13.667)
    return _result('check_localization_need_coverage', adjusted, threshold, True, 'validates localization_need coverage',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_localization_need_consistency_threshold', 16.0)
    return _result('check_localization_need_consistency', adjusted, threshold, False, 'validates localization_need consistency',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_localization_need_risk_threshold', 18.333)
    return _result('check_localization_need_risk', adjusted, threshold, True, 'validates localization_need risk',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_localization_need_confidence_threshold', 20.667)
    return _result('check_localization_need_confidence', adjusted, threshold, True, 'validates localization_need confidence',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_localization_need_dependency_threshold', 23.0)
    return _result('check_localization_need_dependency', adjusted, threshold, False, 'validates localization_need dependency',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_localization_need_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'localization_need')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_localization_need_readiness_threshold', 25.333)
    return _result('check_localization_need_readiness', adjusted, threshold, True, 'validates localization_need readiness',
                   {'field': 'localization_need', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_integration_count_presence_threshold', 27.667)
    return _result('check_integration_count_presence', adjusted, threshold, True, 'validates integration_count presence',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_integration_count_range_threshold', 30.0)
    return _result('check_integration_count_range', adjusted, threshold, False, 'validates integration_count range',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_integration_count_stability_threshold', 8.0)
    return _result('check_integration_count_stability', adjusted, threshold, True, 'validates integration_count stability',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_integration_count_freshness_threshold', 10.333)
    return _result('check_integration_count_freshness', adjusted, threshold, True, 'validates integration_count freshness',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_integration_count_coverage_threshold', 12.667)
    return _result('check_integration_count_coverage', adjusted, threshold, False, 'validates integration_count coverage',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_integration_count_consistency_threshold', 15.0)
    return _result('check_integration_count_consistency', adjusted, threshold, True, 'validates integration_count consistency',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_integration_count_risk_threshold', 17.333)
    return _result('check_integration_count_risk', adjusted, threshold, True, 'validates integration_count risk',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_integration_count_confidence_threshold', 19.667)
    return _result('check_integration_count_confidence', adjusted, threshold, False, 'validates integration_count confidence',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_integration_count_dependency_threshold', 22.0)
    return _result('check_integration_count_dependency', adjusted, threshold, True, 'validates integration_count dependency',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_integration_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'integration_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_integration_count_readiness_threshold', 24.333)
    return _result('check_integration_count_readiness', adjusted, threshold, True, 'validates integration_count readiness',
                   {'field': 'integration_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_supplier_capacity_presence_threshold', 26.667)
    return _result('check_supplier_capacity_presence', adjusted, threshold, False, 'validates supplier_capacity presence',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_supplier_capacity_range_threshold', 29.0)
    return _result('check_supplier_capacity_range', adjusted, threshold, True, 'validates supplier_capacity range',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_supplier_capacity_stability_threshold', 31.333)
    return _result('check_supplier_capacity_stability', adjusted, threshold, True, 'validates supplier_capacity stability',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_supplier_capacity_freshness_threshold', 9.333)
    return _result('check_supplier_capacity_freshness', adjusted, threshold, False, 'validates supplier_capacity freshness',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_supplier_capacity_coverage_threshold', 11.667)
    return _result('check_supplier_capacity_coverage', adjusted, threshold, True, 'validates supplier_capacity coverage',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_supplier_capacity_consistency_threshold', 14.0)
    return _result('check_supplier_capacity_consistency', adjusted, threshold, True, 'validates supplier_capacity consistency',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_supplier_capacity_risk_threshold', 16.333)
    return _result('check_supplier_capacity_risk', adjusted, threshold, False, 'validates supplier_capacity risk',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_supplier_capacity_confidence_threshold', 18.667)
    return _result('check_supplier_capacity_confidence', adjusted, threshold, True, 'validates supplier_capacity confidence',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_supplier_capacity_dependency_threshold', 21.0)
    return _result('check_supplier_capacity_dependency', adjusted, threshold, True, 'validates supplier_capacity dependency',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_supplier_capacity_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'supplier_capacity')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_supplier_capacity_readiness_threshold', 23.333)
    return _result('check_supplier_capacity_readiness', adjusted, threshold, False, 'validates supplier_capacity readiness',
                   {'field': 'supplier_capacity', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_evidence_strength_presence_threshold', 25.667)
    return _result('check_evidence_strength_presence', adjusted, threshold, True, 'validates evidence_strength presence',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_evidence_strength_range_threshold', 28.0)
    return _result('check_evidence_strength_range', adjusted, threshold, True, 'validates evidence_strength range',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_evidence_strength_stability_threshold', 30.333)
    return _result('check_evidence_strength_stability', adjusted, threshold, False, 'validates evidence_strength stability',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_evidence_strength_freshness_threshold', 8.333)
    return _result('check_evidence_strength_freshness', adjusted, threshold, True, 'validates evidence_strength freshness',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_evidence_strength_coverage_threshold', 10.667)
    return _result('check_evidence_strength_coverage', adjusted, threshold, True, 'validates evidence_strength coverage',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_evidence_strength_consistency_threshold', 13.0)
    return _result('check_evidence_strength_consistency', adjusted, threshold, False, 'validates evidence_strength consistency',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_evidence_strength_risk_threshold', 15.333)
    return _result('check_evidence_strength_risk', adjusted, threshold, True, 'validates evidence_strength risk',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_evidence_strength_confidence_threshold', 17.667)
    return _result('check_evidence_strength_confidence', adjusted, threshold, True, 'validates evidence_strength confidence',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_evidence_strength_dependency_threshold', 20.0)
    return _result('check_evidence_strength_dependency', adjusted, threshold, False, 'validates evidence_strength dependency',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_evidence_strength_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'evidence_strength')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_evidence_strength_readiness_threshold', 22.333)
    return _result('check_evidence_strength_readiness', adjusted, threshold, True, 'validates evidence_strength readiness',
                   {'field': 'evidence_strength', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_conflict_count_presence_threshold', 24.667)
    return _result('check_conflict_count_presence', adjusted, threshold, True, 'validates conflict_count presence',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_conflict_count_range_threshold', 27.0)
    return _result('check_conflict_count_range', adjusted, threshold, False, 'validates conflict_count range',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_conflict_count_stability_threshold', 29.333)
    return _result('check_conflict_count_stability', adjusted, threshold, True, 'validates conflict_count stability',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_conflict_count_freshness_threshold', 31.667)
    return _result('check_conflict_count_freshness', adjusted, threshold, True, 'validates conflict_count freshness',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_conflict_count_coverage_threshold', 9.667)
    return _result('check_conflict_count_coverage', adjusted, threshold, False, 'validates conflict_count coverage',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_conflict_count_consistency_threshold', 12.0)
    return _result('check_conflict_count_consistency', adjusted, threshold, True, 'validates conflict_count consistency',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_conflict_count_risk_threshold', 14.333)
    return _result('check_conflict_count_risk', adjusted, threshold, True, 'validates conflict_count risk',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_conflict_count_confidence_threshold', 16.667)
    return _result('check_conflict_count_confidence', adjusted, threshold, False, 'validates conflict_count confidence',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_conflict_count_dependency_threshold', 19.0)
    return _result('check_conflict_count_dependency', adjusted, threshold, True, 'validates conflict_count dependency',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_conflict_count_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'conflict_count')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 0.0
    threshold = _context_number(context, 'check_conflict_count_readiness_threshold', 21.333)
    return _result('check_conflict_count_readiness', adjusted, threshold, True, 'validates conflict_count readiness',
                   {'field': 'conflict_count', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_presence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'presence_weight', 1.1)
    adjusted = raw * weight + 0.17
    threshold = _context_number(context, 'check_expected_benefit_presence_threshold', 23.667)
    return _result('check_expected_benefit_presence', adjusted, threshold, False, 'validates expected_benefit presence',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_range(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'range_weight', 1.2)
    adjusted = raw * weight + 0.34
    threshold = _context_number(context, 'check_expected_benefit_range_threshold', 26.0)
    return _result('check_expected_benefit_range', adjusted, threshold, True, 'validates expected_benefit range',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_stability(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'stability_weight', 1.3)
    adjusted = raw * weight + 0.51
    threshold = _context_number(context, 'check_expected_benefit_stability_threshold', 28.333)
    return _result('check_expected_benefit_stability', adjusted, threshold, True, 'validates expected_benefit stability',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_freshness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'freshness_weight', 1.4)
    adjusted = raw * weight + 0.68
    threshold = _context_number(context, 'check_expected_benefit_freshness_threshold', 30.667)
    return _result('check_expected_benefit_freshness', adjusted, threshold, False, 'validates expected_benefit freshness',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_coverage(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'coverage_weight', 1.0)
    adjusted = raw * weight + 0.8500000000000001
    threshold = _context_number(context, 'check_expected_benefit_coverage_threshold', 8.667)
    return _result('check_expected_benefit_coverage', adjusted, threshold, True, 'validates expected_benefit coverage',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_consistency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'consistency_weight', 1.1)
    adjusted = raw * weight + 1.02
    threshold = _context_number(context, 'check_expected_benefit_consistency_threshold', 11.0)
    return _result('check_expected_benefit_consistency', adjusted, threshold, True, 'validates expected_benefit consistency',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_risk(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'risk_weight', 1.2)
    adjusted = raw * weight + 1.1900000000000002
    threshold = _context_number(context, 'check_expected_benefit_risk_threshold', 13.333)
    return _result('check_expected_benefit_risk', adjusted, threshold, False, 'validates expected_benefit risk',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_confidence(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'confidence_weight', 1.3)
    adjusted = raw * weight + 1.36
    threshold = _context_number(context, 'check_expected_benefit_confidence_threshold', 15.667)
    return _result('check_expected_benefit_confidence', adjusted, threshold, True, 'validates expected_benefit confidence',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_dependency(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'dependency_weight', 1.4)
    adjusted = raw * weight + 1.53
    threshold = _context_number(context, 'check_expected_benefit_dependency_threshold', 18.0)
    return _result('check_expected_benefit_dependency', adjusted, threshold, True, 'validates expected_benefit dependency',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

def check_expected_benefit_readiness(record: DomainRecord, context: Mapping[str, Any]) -> RuleResult:
    raw = _number(record, 'expected_benefit')
    weight = _context_number(context, 'readiness_weight', 1.0)
    adjusted = raw * weight + 1.7000000000000002
    threshold = _context_number(context, 'check_expected_benefit_readiness_threshold', 20.333)
    return _result('check_expected_benefit_readiness', adjusted, threshold, False, 'validates expected_benefit readiness',
                   {'field': 'expected_benefit', 'raw': raw, 'weight': weight, 'adjusted': adjusted, 'threshold': threshold})

RULES: tuple[RuleFunction, ...] = (
    check_sector_presence,
    check_sector_range,
    check_sector_stability,
    check_sector_freshness,
    check_sector_coverage,
    check_sector_consistency,
    check_sector_risk,
    check_sector_confidence,
    check_sector_dependency,
    check_sector_readiness,
    check_problem_severity_presence,
    check_problem_severity_range,
    check_problem_severity_stability,
    check_problem_severity_freshness,
    check_problem_severity_coverage,
    check_problem_severity_consistency,
    check_problem_severity_risk,
    check_problem_severity_confidence,
    check_problem_severity_dependency,
    check_problem_severity_readiness,
    check_data_readiness_presence,
    check_data_readiness_range,
    check_data_readiness_stability,
    check_data_readiness_freshness,
    check_data_readiness_coverage,
    check_data_readiness_consistency,
    check_data_readiness_risk,
    check_data_readiness_confidence,
    check_data_readiness_dependency,
    check_data_readiness_readiness,
    check_deployment_window_presence,
    check_deployment_window_range,
    check_deployment_window_stability,
    check_deployment_window_freshness,
    check_deployment_window_coverage,
    check_deployment_window_consistency,
    check_deployment_window_risk,
    check_deployment_window_confidence,
    check_deployment_window_dependency,
    check_deployment_window_readiness,
    check_budget_band_presence,
    check_budget_band_range,
    check_budget_band_stability,
    check_budget_band_freshness,
    check_budget_band_coverage,
    check_budget_band_consistency,
    check_budget_band_risk,
    check_budget_band_confidence,
    check_budget_band_dependency,
    check_budget_band_readiness,
    check_safety_class_presence,
    check_safety_class_range,
    check_safety_class_stability,
    check_safety_class_freshness,
    check_safety_class_coverage,
    check_safety_class_consistency,
    check_safety_class_risk,
    check_safety_class_confidence,
    check_safety_class_dependency,
    check_safety_class_readiness,
    check_localization_need_presence,
    check_localization_need_range,
    check_localization_need_stability,
    check_localization_need_freshness,
    check_localization_need_coverage,
    check_localization_need_consistency,
    check_localization_need_risk,
    check_localization_need_confidence,
    check_localization_need_dependency,
    check_localization_need_readiness,
    check_integration_count_presence,
    check_integration_count_range,
    check_integration_count_stability,
    check_integration_count_freshness,
    check_integration_count_coverage,
    check_integration_count_consistency,
    check_integration_count_risk,
    check_integration_count_confidence,
    check_integration_count_dependency,
    check_integration_count_readiness,
    check_supplier_capacity_presence,
    check_supplier_capacity_range,
    check_supplier_capacity_stability,
    check_supplier_capacity_freshness,
    check_supplier_capacity_coverage,
    check_supplier_capacity_consistency,
    check_supplier_capacity_risk,
    check_supplier_capacity_confidence,
    check_supplier_capacity_dependency,
    check_supplier_capacity_readiness,
    check_evidence_strength_presence,
    check_evidence_strength_range,
    check_evidence_strength_stability,
    check_evidence_strength_freshness,
    check_evidence_strength_coverage,
    check_evidence_strength_consistency,
    check_evidence_strength_risk,
    check_evidence_strength_confidence,
    check_evidence_strength_dependency,
    check_evidence_strength_readiness,
    check_conflict_count_presence,
    check_conflict_count_range,
    check_conflict_count_stability,
    check_conflict_count_freshness,
    check_conflict_count_coverage,
    check_conflict_count_consistency,
    check_conflict_count_risk,
    check_conflict_count_confidence,
    check_conflict_count_dependency,
    check_conflict_count_readiness,
    check_expected_benefit_presence,
    check_expected_benefit_range,
    check_expected_benefit_stability,
    check_expected_benefit_freshness,
    check_expected_benefit_coverage,
    check_expected_benefit_consistency,
    check_expected_benefit_risk,
    check_expected_benefit_confidence,
    check_expected_benefit_dependency,
    check_expected_benefit_readiness,
)

RULE_INDEX = {rule.__name__: rule for rule in RULES}

def evaluate(record: DomainRecord, context: Mapping[str, Any] | None = None) -> tuple[RuleResult, ...]:
    context = context or {}
    return tuple(rule(record, context) for rule in RULES)

def summarize(results: tuple[RuleResult, ...]) -> dict[str, Any]:
    if not results:
        return {'score': 0.0, 'passed': 0, 'failed': 0, 'critical': 0}
    return {'score': sum(item.score for item in results) / len(results),
            'passed': sum(item.passed for item in results),
            'failed': sum(not item.passed for item in results),
            'critical': sum(item.severity == 'critical' for item in results)}
