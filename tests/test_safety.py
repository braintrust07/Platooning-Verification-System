"""
Unit tests for formal safety verification
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.core.verified_controller import FormalPlatooningController, VehicleRole
from src.core.safety_monitor import SafetyMonitor

class TestFormalSafety:
    """Test formal safety guarantees"""
    
    def test_safe_distance_calculation(self):
        """Test proven safe distance calculation"""
        controller = FormalPlatooningController("test_vehicle")
        
        # Test various scenarios
        test_cases = [
            (20.0, 20.0),  # Same velocity
            (20.0, 15.0),  # Ego faster
            (15.0, 20.0),  # Predecessor faster
        ]
        
        for v_ego, v_pred in test_cases:
            safe_dist = controller._calculate_safe_distance(v_ego, v_pred)
            assert safe_dist > 0
            assert safe_dist >= 3.0  # min_safe_distance
    
    def test_emergency_braking(self):
        """Test emergency braking scenarios"""
        controller = FormalPlatooningController("test_vehicle")
        
        # Create unsafe scenario - vehicles extremely close (5m gap)
        platoon_states = {
            'vehicle_0': {'position': 50, 'velocity': 20, 'acceleration': 0, 
                         'timestamp': 0, 'role': VehicleRole.LEADER},
            'test_vehicle': {'position': 45, 'velocity': 20, 'acceleration': 0,  # Only 5m gap - definitely unsafe!
                           'timestamp': 0, 'role': VehicleRole.FOLLOWER}
        }
        
        action = controller.compute_verified_action(platoon_states, 0.0)
        
        assert action.emergency == True
        assert action.acceleration < 0
        assert action.safety_verified == True
    
    def test_safety_monitor(self):
        """Test safety monitoring"""
        monitor = SafetyMonitor()
        
        # Create TRULY unsafe scenario - 5m gap (less than 7m safe distance)
        platoon_states = {
            'v1': {'position': 100, 'velocity': 20, 'acceleration': 0},
            'v2': {'position': 95, 'velocity': 20, 'acceleration': 0}  # Only 5m gap - definitely unsafe!
        }
        
        violations = monitor.verify_safety(platoon_states)
        assert len(violations) > 0, f"Expected violations for 5m gap (safe distance: 7m)"
        assert violations[0]['type'] == 'SAFE_DISTANCE_VIOLATION'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])