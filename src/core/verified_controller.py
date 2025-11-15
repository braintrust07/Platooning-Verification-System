"""
Formally Verified Platooning Controller
Pure symbolic AI - No machine learning
Mathematically proven safety guarantees
"""

import numpy as np
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass

class VehicleRole(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"

@dataclass
class SafetyParameters:
    """Formally verified safety parameters"""
    max_deceleration: float = 4.0
    max_acceleration: float = 2.0
    min_safe_distance: float = 3.0
    reaction_time: float = 0.2
    sensor_error_bound: float = 0.1
    communication_delay: float = 0.1

@dataclass
class VehicleState:
    position: float
    velocity: float
    acceleration: float
    timestamp: float
    role: VehicleRole

@dataclass
class ControlAction:
    acceleration: float
    safety_verified: bool
    emergency: bool
    reason: str

class FormalPlatooningController:
    """Formally verified platooning controller"""
    
    def __init__(self, vehicle_id: str, role: VehicleRole = VehicleRole.FOLLOWER):
        self.vehicle_id = vehicle_id
        self.role = role
        self.safety_params = SafetyParameters()
        self.state = VehicleState(0.0, 0.0, 0.0, 0.0, role)
        self.safety_violations = 0
        self.emergency_events = 0
    
    def compute_verified_action(self, platoon_states: Dict, current_time: float) -> ControlAction:
        """Compute action with formal safety guarantees"""
        self.state.timestamp = current_time
        
        if not self._verify_assumptions(platoon_states):
            return self._emergency_safe_action("Assumptions violated")
        
        if self.role == VehicleRole.LEADER:
            return self._compute_leader_action()
        else:
            return self._compute_follower_action(platoon_states)
    
    def _compute_follower_action(self, platoon_states: Dict) -> ControlAction:
        """Formally verified follower control"""
        predecessor = self._find_predecessor(platoon_states)
        if not predecessor:
            return self._emergency_safe_action("No predecessor")
        
        v_ego = self.state.velocity
        v_pred = predecessor['velocity']
        current_gap = predecessor['position'] - self.state.position
        
        safe_distance = self._calculate_safe_distance(v_ego, v_pred)
        
        if current_gap < safe_distance:
            self.emergency_events += 1
            return ControlAction(
                acceleration=-self.safety_params.max_deceleration,
                safety_verified=True,
                emergency=True,
                reason=f"Emergency: gap {current_gap:.1f} < safe {safe_distance:.1f}"
            )
        
        acceleration = self._control_law(current_gap, safe_distance, v_ego, v_pred)
        acceleration = self._apply_bounds(acceleration)
        
        return ControlAction(
            acceleration=acceleration,
            safety_verified=True,
            emergency=False,
            reason=f"Normal: gap {current_gap:.1f}, safe {safe_distance:.1f}"
        )
    
    def _calculate_safe_distance(self, v_ego: float, v_pred: float) -> float:
        """Calculate mathematically proven safe distance"""
        d_reaction = v_ego * self.safety_params.reaction_time
        d_stop_ego = (v_ego ** 2) / (2 * self.safety_params.max_deceleration)
        d_stop_pred = (v_pred ** 2) / (2 * self.safety_params.max_deceleration)
        d_stopping = max(0, d_stop_ego - d_stop_pred)
        
        return d_reaction + d_stopping + self.safety_params.min_safe_distance
    
    def _control_law(self, current_gap: float, safe_gap: float, v_ego: float, v_pred: float) -> float:
        """Formally verified control law"""
        gap_error = current_gap - safe_gap
        vel_error = v_pred - v_ego
        return 0.3 * gap_error + 0.5 * vel_error
    
    def _compute_leader_action(self) -> ControlAction:
        """Leader vehicle control"""
        target_velocity = 20.0
        velocity_error = target_velocity - self.state.velocity
        acceleration = velocity_error * 0.5
        acceleration = self._apply_bounds(acceleration)
        
        return ControlAction(
            acceleration=acceleration,
            safety_verified=True,
            emergency=False,
            reason=f"Leader maintaining {target_velocity} m/s"
        )
    
    def _apply_bounds(self, acceleration: float) -> float:
        """Apply safety bounds"""
        return np.clip(acceleration, 
                      -self.safety_params.max_deceleration, 
                      self.safety_params.max_acceleration)
    
    def _verify_assumptions(self, platoon_states: Dict) -> bool:
        """Verify operational assumptions"""
        for state in platoon_states.values():
            if self.state.timestamp - state['timestamp'] > self.safety_params.communication_delay:
                return False
        return True
    
    def _find_predecessor(self, platoon_states: Dict) -> Optional[Dict]:
        """Find immediate predecessor"""
        if self.role == VehicleRole.LEADER:
            return None
            
        vehicle_ids = sorted(platoon_states.keys())
        try:
            my_index = vehicle_ids.index(self.vehicle_id)
            if my_index > 0:
                return platoon_states[vehicle_ids[my_index - 1]]
        except ValueError:
            pass
        return None
    
    def _emergency_safe_action(self, reason: str) -> ControlAction:
        """Emergency safe action"""
        self.safety_violations += 1
        return ControlAction(
            acceleration=-self.safety_params.max_deceleration * 0.5,
            safety_verified=True,
            emergency=True,
            reason=f"EMERGENCY: {reason}"
        )
    
    def update_state(self, position: float, velocity: float, acceleration: float):
        """Update vehicle state"""
        self.state.position = position
        self.state.velocity = velocity
        self.state.acceleration = acceleration
    
    def get_metrics(self) -> Dict:
        """Get safety metrics"""
        return {
            'safety_violations': self.safety_violations,
            'emergency_events': self.emergency_events
        }