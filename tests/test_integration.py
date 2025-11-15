"""
Integration tests for formal platooning system
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from src.simulation.environment import PlatooningSimulation
from src.core.verified_controller import FormalPlatooningController, VehicleRole
from src.core.safety_monitor import SafetyMonitor
from src.formal.proof_checker import FormalProofChecker

class TestIntegration:
    """Integration tests for complete system"""
    
    def test_complete_system_integration(self):
        """Test complete system integration"""
        # Create simulation
        sim = PlatooningSimulation(num_vehicles=3)
        
        # Run for 10 steps
        for _ in range(10):
            sim.step()
        
        # Verify system state
        assert len(sim.vehicles) == 3
        assert len(sim.controllers) == 3
        assert sim.time > 0
        
        # Check all vehicles have controllers
        for vehicle_id in sim.vehicles:
            assert vehicle_id in sim.controllers
    
    def test_safety_monitor_integration(self):
        """Test safety monitor integration"""
        sim = PlatooningSimulation(num_vehicles=3)
        
        # Run simulation
        sim.run(duration=5.0)
        
        # Check safety monitor is active
        violations = sim.safety_monitor.verify_safety(sim._get_platoon_states())
        assert isinstance(violations, list)
        
        # Get safety stats
        stats = sim.get_safety_stats()
        assert 'safety_percentage' in stats
        assert 'total_emergencies' in stats
    
    def test_emergency_recovery(self):
        """Test emergency scenario and recovery"""
        sim = PlatooningSimulation(num_vehicles=3)
        
        # Create EXTREME emergency situation - vehicles MUCH closer than safe distance (7m)
        # Using 5m gaps to ensure emergencies are triggered
        sim.vehicles['vehicle_0']['position'] = 100
        sim.vehicles['vehicle_1']['position'] = 95   # Only 5m gap - unsafe!
        sim.vehicles['vehicle_2']['position'] = 90   # Only 5m gap - unsafe!
        
        # Also set velocities to ensure emergency
        sim.vehicles['vehicle_0']['velocity'] = 20
        sim.vehicles['vehicle_1']['velocity'] = 20  
        sim.vehicles['vehicle_2']['velocity'] = 20
        
        # Update controller states
        for vid, controller in sim.controllers.items():
            controller.update_state(
                sim.vehicles[vid]['position'],
                sim.vehicles[vid]['velocity'], 
                sim.vehicles[vid]['acceleration']
            )
        
        # Run one step - should trigger emergency
        sim.step()
        
        # Check emergency handling
        last_actions = sim.history[-1]['actions']
        emergency_count = sum(1 for action in last_actions.values() if action['emergency'])
        
        assert emergency_count > 0, f"Expected emergencies for 5m gaps but got {emergency_count}"
    
    def test_formal_verification_integration(self):
        """Test formal verification integration"""
        proof_checker = FormalProofChecker()
        
        # Verify controller parameters
        controller_params = {
            'max_deceleration': 4.0,
            'reaction_time': 0.2,
            'min_safe_distance': 3.0
        }
        
        collision_free = proof_checker.verify_collision_freedom(controller_params)
        velocity_bounds = proof_checker.verify_velocity_bounds(35.0)
        
        assert collision_free == True
        assert velocity_bounds == True
        
        report = proof_checker.get_verification_report()
        assert report['all_properties_verified'] == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])