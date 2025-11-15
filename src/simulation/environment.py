"""
Basic Platooning Simulation (Fallback)
"""

import numpy as np
from enum import Enum
from typing import Dict, List, Tuple
from dataclasses import dataclass

class VehicleRole(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"

@dataclass
class VehicleAction:
    acceleration: float
    emergency: bool = False
    reason: str = ""
    safety_verified: bool = True

class PlatooningSimulation:
    """Basic 1D platooning simulation (fallback)"""
    
    def __init__(self, num_vehicles: int = 4, dt: float = 0.1):
        self.dt = dt
        self.time = 0.0
        self.vehicles = {}
        self.controllers = {}
        self.history = []
        
        # Initialize vehicles
        self._initialize_vehicles(num_vehicles)
        
    def _initialize_vehicles(self, num_vehicles: int):
        """Initialize vehicles in a line"""
        for i in range(num_vehicles):
            vid = f"vehicle_{i}"
            role = VehicleRole.LEADER if i == 0 else VehicleRole.FOLLOWER
            
            self.vehicles[vid] = {
                'role': role,
                'position': 50.0 - i * 15.0,  # Staggered start
                'velocity': 20.0 if i == 0 else 18.0,
                'acceleration': 0.0
            }
            
            # Simple controller
            self.controllers[vid] = BasicController(vid, role)
    
    def step(self):
        """Execute one simulation step"""
        # Get platoon states
        platoon_states = self._get_platoon_states()
        
        # Compute actions
        actions = {}
        for vid, controller in self.controllers.items():
            action = controller.compute_verified_action(platoon_states, self.time)
            actions[vid] = {
                'acceleration': action.acceleration,
                'emergency': action.emergency,
                'reason': action.reason
            }
            
            # Apply action
            self.vehicles[vid]['acceleration'] = action.acceleration
        
        # Update physics
        for vid, vehicle in self.vehicles.items():
            vehicle['velocity'] += vehicle['acceleration'] * self.dt
            vehicle['velocity'] = max(0, vehicle['velocity'])
            vehicle['position'] += vehicle['velocity'] * self.dt
        
        # Store history
        self.history.append({
            'time': self.time,
            'vehicles': {vid: dict(vehicle) for vid, vehicle in self.vehicles.items()},
            'actions': actions
        })
        
        self.time += self.dt
    
    def _get_platoon_states(self):
        """Get platoon states for controllers"""
        return self.vehicles
    
    def trigger_emergency(self, vehicle_id: str = "vehicle_0"):
        """Trigger emergency braking"""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['acceleration'] = -6.0
    
    def get_safety_stats(self):
        """Get basic safety statistics"""
        if not self.history:
            return {'safety_percentage': 100.0, 'total_emergencies': 0}
        
        emergencies = sum(1 for step in self.history 
                         if any(action['emergency'] for action in step['actions'].values()))
        
        safety_percentage = 100 - (emergencies * 5)  # Simple penalty
        
        return {
            'safety_percentage': safety_percentage,
            'total_emergencies': emergencies
        }

    # Add run method for compatibility
    def run(self, duration: float = 60.0):
        """Run simulation for specified duration"""
        total_steps = int(duration / self.dt)
        
        for step in range(total_steps):
            self.step()
            
            # Trigger emergency at 3 seconds for demonstration
            if step == 30:  # 3 seconds at 0.1 dt
                self.trigger_emergency("vehicle_0")

class BasicController:
    """Basic controller for fallback simulation"""
    
    def __init__(self, vehicle_id: str, role: VehicleRole):
        self.vehicle_id = vehicle_id
        self.role = role
    
    def compute_verified_action(self, platoon_states: Dict, current_time: float) -> VehicleAction:
        """Compute basic action"""
        if self.role == VehicleRole.LEADER:
            return VehicleAction(0.0, reason="Leader maintaining speed")
        else:
            return VehicleAction(0.0, reason="Follower maintaining distance")