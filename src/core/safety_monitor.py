"""
Runtime Safety Monitor for Formal Verification
"""

from typing import Dict, List
import time

class SafetyMonitor:
    """Runtime safety verification monitor"""
    
    def __init__(self):
        self.violation_history = []
        self.assumption_checks = []
    
    def verify_safety(self, platoon_states: Dict) -> List[Dict]:
        """Verify all safety conditions"""
        violations = []
        
        # Check safe distances
        vehicle_ids = sorted(platoon_states.keys())
        for i in range(len(vehicle_ids) - 1):
            front = platoon_states[vehicle_ids[i]]
            rear = platoon_states[vehicle_ids[i + 1]]
            
            actual_gap = front['position'] - rear['position']
            safe_gap = self._calculate_safe_distance(rear['velocity'], front['velocity'])
            
            if actual_gap < safe_gap:
                violations.append({
                    'type': 'SAFE_DISTANCE_VIOLATION',
                    'vehicles': (vehicle_ids[i], vehicle_ids[i + 1]),
                    'actual_gap': actual_gap,
                    'safe_gap': safe_gap,
                    'timestamp': time.time()
                })
        
        # Check velocity bounds
        for vid, state in platoon_states.items():
            if state['velocity'] < 0:
                violations.append({
                    'type': 'NEGATIVE_VELOCITY',
                    'vehicle': vid,
                    'velocity': state['velocity'],
                    'timestamp': time.time()
                })
        
        # Log violations
        self.violation_history.extend(violations)
        return violations
    
    def _calculate_safe_distance(self, v_ego: float, v_pred: float) -> float:
        """Calculate safe distance (same as controller)"""
        reaction_time = 0.2
        max_decel = 4.0
        min_distance = 3.0
        
        d_reaction = v_ego * reaction_time
        d_stop_ego = (v_ego ** 2) / (2 * max_decel)
        d_stop_pred = (v_pred ** 2) / (2 * max_decel)
        d_stopping = max(0, d_stop_ego - d_stop_pred)
        
        return d_reaction + d_stopping + min_distance
    
    def get_safety_stats(self) -> Dict:
        """Get safety statistics"""
        total_violations = len(self.violation_history)
        distance_violations = len([v for v in self.violation_history 
                                 if v['type'] == 'SAFE_DISTANCE_VIOLATION'])
        
        return {
            'total_violations': total_violations,
            'distance_violations': distance_violations,
            'last_violation': self.violation_history[-1] if self.violation_history else None
        }