"""
Enhanced Platooning Simulation with User-Controlled Scenarios
"""

import numpy as np
from enum import Enum
from typing import Dict, List, Tuple, Optional
import math
from dataclasses import dataclass

class VehicleRole(Enum):
    LEADER = "leader"
    FOLLOWER = "follower"
    PRIORITY = "priority"

class Lane(Enum):
    RIGHT = 0
    MIDDLE = 1
    LEFT = 2

class VehicleType(Enum):
    NORMAL = "normal"
    AMBULANCE = "ambulance"
    EMERGENCY = "emergency"

@dataclass
class EnhancedVehicleAction:
    acceleration: float
    target_lane: Optional['Lane'] = None
    emergency: bool = False
    reason: str = ""
    priority_override: bool = False
    
    def to_dict(self):
        return {
            'acceleration': self.acceleration,
            'target_lane': self.target_lane,
            'emergency': self.emergency,
            'reason': self.reason,
            'priority_override': self.priority_override
        }

class EnhancedVehicle:
    def __init__(self, vehicle_id: str, role: VehicleRole, vehicle_type: VehicleType = VehicleType.NORMAL, initial_lane: Lane = Lane.MIDDLE):
        self.id = vehicle_id
        self.role = role
        self.vehicle_type = vehicle_type
        self.lane = initial_lane
        self.lane_target_y = self._get_lane_center_y(initial_lane)
        
        # Position with more spacing
        self.x = 50.0 if role == VehicleRole.LEADER else 50.0 - (int(vehicle_id.split('_')[1]) * 25.0)
        self.y = self.lane_target_y
        self.velocity = 20.0
        self.acceleration = 0.0
        self.length = 4.5
        self.width = 1.8
        
        # Visual properties
        if vehicle_type == VehicleType.AMBULANCE:
            self.color = '#FF0000'
            self.symbol = "🚑"
        elif vehicle_type == VehicleType.EMERGENCY:
            self.color = '#FFA500'
            self.symbol = "🚨"
        else:
            self.color = '#4FC3F7'
            self.symbol = "🚗"
        
        if role == VehicleRole.LEADER and vehicle_type == VehicleType.NORMAL:
            self.color = '#FF6B6B'
        
        # Lane change
        self.is_changing_lane = False
        self.lane_change_progress = 0.0
        self.lane_change_speed = 2.0
        self.previous_lane = initial_lane
        
        # Emergency state
        self.emergency_braking = False
        self.emergency_start_time = 0.0
        
    def _get_lane_center_y(self, lane: Lane) -> float:
        lane_centers = {Lane.RIGHT: -4.0, Lane.MIDDLE: 0.0, Lane.LEFT: 4.0}
        return lane_centers[lane]
    
    def update_position(self, dt: float):
        # Update velocity with limits
        self.velocity += self.acceleration * dt
        self.velocity = max(0, min(self.velocity, 30.0))
        self.x += self.velocity * dt
        
        # Lane changing
        if self.is_changing_lane:
            self.lane_change_progress += self.lane_change_speed * dt
            if self.lane_change_progress >= 1.0:
                self.is_changing_lane = False
                self.lane_change_progress = 0.0
                self.y = self.lane_target_y
            else:
                start_y = self._get_lane_center_y(self.previous_lane)
                self.y = start_y + (self.lane_target_y - start_y) * self.lane_change_progress
    
    def initiate_lane_change(self, target_lane: Lane):
        if not self.is_changing_lane and target_lane != self.lane:
            self.previous_lane = self.lane
            self.lane = target_lane
            self.lane_target_y = self._get_lane_center_y(target_lane)
            self.is_changing_lane = True
            self.lane_change_progress = 0.0
    
    def trigger_emergency_braking(self, current_time: float):
        """Trigger emergency braking for this vehicle"""
        self.emergency_braking = True
        self.emergency_start_time = current_time
        self.acceleration = -8.0  # Hard braking
    
    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        return (
            self.x - self.length/2,
            self.x + self.length/2,
            self.y - self.width/2,
            self.y + self.width/2
        )

class EnhancedPlatooningController:
    def __init__(self, vehicle):
        self.vehicle = vehicle
        
        # Conservative parameters for safety
        self.safe_time_gap = 2.5
        self.min_distance = 10.0
        self.max_acceleration = 2.0
        self.max_braking = -6.0
        
    def compute_action(self, vehicle_states: Dict, current_time: float) -> EnhancedVehicleAction:
        # Check for emergency vehicles ahead first
        emergency_action = self._check_emergency_ahead(vehicle_states, current_time)
        if emergency_action:
            return emergency_action
        
        # Priority vehicle handling
        if self.vehicle.role == VehicleRole.PRIORITY:
            return self._compute_priority_action(vehicle_states)
        
        # Check for priority vehicles to yield to
        yield_action = self._check_priority_yield(vehicle_states)
        if yield_action:
            return yield_action
        
        # Normal driving
        if self.vehicle.role == VehicleRole.LEADER:
            return self._compute_leader_action()
        else:
            return self._compute_follower_action(vehicle_states)
    
    def _check_emergency_ahead(self, vehicle_states: Dict, current_time: float) -> Optional[EnhancedVehicleAction]:
        """Check if there's an emergency braking vehicle ahead that we need to react to"""
        closest_vehicle, distance, relative_velocity = self._find_closest_vehicle(vehicle_states)
        
        if closest_vehicle and closest_vehicle.emergency_braking:
            # Emergency vehicle ahead - react aggressively
            safe_distance = self._calculate_safe_distance(relative_velocity)
            time_since_emergency = current_time - closest_vehicle.emergency_start_time
            
            # More aggressive reaction if emergency just started
            reaction_multiplier = 2.0 if time_since_emergency < 1.0 else 1.0
            
            if distance < safe_distance * 1.5:
                # Try emergency lane change first
                target_lane = self._evaluate_emergency_lane_change(vehicle_states, distance, safe_distance)
                if target_lane:
                    return EnhancedVehicleAction(
                        acceleration=-4.0,
                        target_lane=target_lane,
                        emergency=True,
                        reason=f"Emergency lane change! {closest_vehicle.id} braking"
                    )
                else:
                    # Hard braking if no lane available
                    required_braking = min(self.max_braking, -6.0 * reaction_multiplier)
                    return EnhancedVehicleAction(
                        acceleration=required_braking,
                        emergency=True,
                        reason=f"🚨 EMERGENCY! {closest_vehicle.id} braking hard!"
                    )
        
        return None
    
    def _evaluate_emergency_lane_change(self, vehicle_states: Dict, current_distance: float, safe_distance: float) -> Optional[Lane]:
        """Evaluate lane change options during emergency"""
        if self.vehicle.is_changing_lane:
            return None
            
        current_lane = self.vehicle.lane
        adjacent_lanes = self._get_adjacent_lanes(current_lane)
        
        for lane in adjacent_lanes:
            if self._is_lane_clear_for_emergency(lane, vehicle_states):
                return lane
        return None
    
    def _is_lane_clear_for_emergency(self, target_lane: Lane, vehicle_states: Dict) -> bool:
        """Check if lane is clear for emergency lane change (stricter criteria)"""
        target_y = self._get_lane_center_y(target_lane)
        
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            if vehicle_obj.id == self.vehicle.id:
                continue
                
            if abs(vehicle_obj.y - target_y) < 2.5:  # Stricter lateral clearance
                longitudinal_distance = vehicle_obj.x - self.vehicle.x
                
                # Check both ahead and behind more conservatively
                if abs(longitudinal_distance) < 20.0:  # Smaller gap allowed in emergency
                    return False
        return True
    
    def _compute_priority_action(self, vehicle_states: Dict) -> EnhancedVehicleAction:
        target_velocity = 25.0
        current_velocity = self.vehicle.velocity
        
        # Find closest vehicle in front
        closest_vehicle, distance, relative_velocity = self._find_closest_vehicle(vehicle_states)
        
        if closest_vehicle:
            safe_distance = self._calculate_safe_distance(relative_velocity)
            
            if distance < safe_distance * 1.2:
                # Try to overtake
                target_lane = self._evaluate_lane_change(vehicle_states, distance, safe_distance)
                if target_lane:
                    return EnhancedVehicleAction(
                        acceleration=1.0,
                        target_lane=target_lane,
                        reason=f"Overtaking {closest_vehicle.id}"
                    )
                else:
                    # Follow at safe distance
                    acceleration = np.clip((distance - safe_distance) * 0.1, -2.0, 0)
                    return EnhancedVehicleAction(
                        acceleration=acceleration,
                        reason=f"Following {closest_vehicle.id}"
                    )
        
        # Maintain speed
        velocity_error = target_velocity - current_velocity
        acceleration = np.clip(velocity_error * 0.3, -1.5, 1.5)
        return EnhancedVehicleAction(
            acceleration=acceleration,
            reason="Priority vehicle maintaining speed"
        )
    
    def _check_priority_yield(self, vehicle_states: Dict) -> Optional[EnhancedVehicleAction]:
        """Check if we need to yield to a priority vehicle behind us"""
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            
            # Skip if it's not a priority vehicle or it's ourselves
            if (vehicle_obj.id == self.vehicle.id or 
                vehicle_obj.role != VehicleRole.PRIORITY):
                continue
                
            # Check if priority vehicle is behind us and in same/similar lane
            lateral_distance = abs(vehicle_obj.y - self.vehicle.y)
            longitudinal_distance = self.vehicle.x - vehicle_obj.x  # Positive if we're ahead
            
            # If priority vehicle is behind us, close laterally, and approaching
            if (longitudinal_distance > 0 and  # We're ahead of priority vehicle
                longitudinal_distance < 50.0 and  # Within 50 meters
                lateral_distance < 3.5 and  # In same/similar lane
                vehicle_obj.velocity > self.vehicle.velocity):  # Priority vehicle is faster
                
                # Try to change lane to yield
                target_lane = self._find_yield_lane(vehicle_states)
                if target_lane and target_lane != self.vehicle.lane:
                    return EnhancedVehicleAction(
                        acceleration=-1.0,  # Slow down slightly
                        target_lane=target_lane,
                        priority_override=True,
                        reason=f"Yielding to priority vehicle {vehicle_obj.id}"
                    )
                else:
                    # If no lane available, slow down significantly
                    return EnhancedVehicleAction(
                        acceleration=-3.0,
                        priority_override=True,
                        reason=f"Making space for priority vehicle {vehicle_obj.id}"
                    )
        
        return None
    
    def _find_priority_vehicle(self, vehicle_states: Dict):
        """Find the priority vehicle in the scenario"""
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            if vehicle_obj.role == VehicleRole.PRIORITY and vehicle_obj.id != self.vehicle.id:
                return vehicle_obj
        return None
    
    def _find_yield_lane(self, vehicle_states: Dict) -> Optional[Lane]:
        """Find a safe lane to yield to priority vehicle"""
        current_lane = self.vehicle.lane
        adjacent_lanes = self._get_adjacent_lanes(current_lane)
        
        # Prefer lanes away from the priority vehicle
        priority_vehicle = self._find_priority_vehicle(vehicle_states)
        if priority_vehicle:
            priority_lane = priority_vehicle.lane
            # Sort lanes by distance from priority vehicle's lane
            adjacent_lanes.sort(key=lambda lane: abs(lane.value - priority_lane.value))
        
        for lane in adjacent_lanes:
            if self._is_lane_clear_for_yield(lane, vehicle_states):
                return lane
        return None
    
    def _is_lane_clear_for_yield(self, target_lane: Lane, vehicle_states: Dict) -> bool:
        """Check if target lane is clear for yielding maneuver"""
        target_y = self._get_lane_center_y(target_lane)
        
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            if vehicle_obj.id == self.vehicle.id:
                continue
                
            # Check lateral proximity
            if abs(vehicle_obj.y - target_y) < 2.8:  # Slightly stricter for safety
                longitudinal_distance = vehicle_obj.x - self.vehicle.x
                
                # Check for vehicles in front in target lane
                if longitudinal_distance > 0 and longitudinal_distance < 25.0:
                    return False  # Vehicle too close ahead in target lane
                
                # Check for vehicles behind in target lane  
                if longitudinal_distance < 0 and abs(longitudinal_distance) < 15.0:
                    return False  # Vehicle too close behind in target lane
        
        return True
    
    def _compute_leader_action(self) -> EnhancedVehicleAction:
        target_velocity = 20.0
        current_velocity = self.vehicle.velocity
        velocity_error = target_velocity - current_velocity
        acceleration = np.clip(velocity_error * 0.2, -1.0, 1.0)
        return EnhancedVehicleAction(
            acceleration=acceleration,
            reason="Leader maintaining speed"
        )
    
    def _compute_follower_action(self, vehicle_states: Dict) -> EnhancedVehicleAction:
        # First check if we need to yield to priority vehicle
        yield_action = self._check_priority_yield(vehicle_states)
        if yield_action:
            return yield_action
        
        # Then proceed with normal following logic
        closest_vehicle, distance, relative_velocity = self._find_closest_vehicle(vehicle_states)
        
        if closest_vehicle is None:
            return EnhancedVehicleAction(acceleration=0.0, reason="No vehicle ahead")
        
        safe_distance = self._calculate_safe_distance(relative_velocity)
        
        # Conservative following
        if distance < safe_distance * 0.9:
            gap_error = distance - safe_distance
            acceleration = np.clip(gap_error * 0.3, self.max_braking, 0)
            reason = f"Maintaining distance to {closest_vehicle.id}"
        elif distance > safe_distance * 1.3:
            gap_error = distance - safe_distance
            acceleration = np.clip(gap_error * 0.05, 0, self.max_acceleration)
            reason = f"Closing gap to {closest_vehicle.id}"
        else:
            acceleration = 0.0
            reason = f"Maintaining distance to {closest_vehicle.id}"
        
        return EnhancedVehicleAction(acceleration=acceleration, reason=reason)
    
    def _find_closest_vehicle(self, vehicle_states: Dict):
        closest_vehicle = None
        min_distance = float('inf')
        relative_velocity = 0.0
        
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            if vehicle_obj.id == self.vehicle.id:
                continue
                
            distance = vehicle_obj.x - self.vehicle.x - self.vehicle.length
            lateral_distance = abs(vehicle_obj.y - self.vehicle.y)
            
            if lateral_distance < 4.0 and distance > 0 and distance < min_distance:
                min_distance = distance
                closest_vehicle = vehicle_obj
                relative_velocity = vehicle_obj.velocity - self.vehicle.velocity
        
        return closest_vehicle, min_distance, relative_velocity
    
    def _calculate_safe_distance(self, relative_velocity: float) -> float:
        return self.min_distance + max(0, self.vehicle.velocity) * self.safe_time_gap
    
    def _evaluate_lane_change(self, vehicle_states: Dict, current_distance: float, safe_distance: float) -> Optional[Lane]:
        if self.vehicle.is_changing_lane or current_distance > safe_distance * 0.8:
            return None
            
        current_lane = self.vehicle.lane
        adjacent_lanes = self._get_adjacent_lanes(current_lane)
        
        for lane in adjacent_lanes:
            if self._is_lane_clear(lane, vehicle_states):
                return lane
        return None
    
    def _is_lane_clear(self, target_lane: Lane, vehicle_states: Dict) -> bool:
        target_y = self._get_lane_center_y(target_lane)
        
        for vid, state in vehicle_states.items():
            vehicle_obj = state['object']
            if vehicle_obj.id == self.vehicle.id:
                continue
                
            if abs(vehicle_obj.y - target_y) < 2.2:
                longitudinal_distance = vehicle_obj.x - self.vehicle.x
                safe_distance = self._calculate_safe_distance(vehicle_obj.velocity - self.vehicle.velocity)
                
                if abs(longitudinal_distance) < safe_distance * 1.8:
                    return False
        return True
    
    def _get_adjacent_lanes(self, current_lane: Lane) -> List[Lane]:
        """Get available adjacent lanes for lane changing"""
        if current_lane == Lane.RIGHT:
            return [Lane.MIDDLE]
        elif current_lane == Lane.MIDDLE:
            return [Lane.LEFT, Lane.RIGHT]  # Left first, then right
        else:  # Lane.LEFT
            return [Lane.MIDDLE]
    
    def _get_lane_center_y(self, lane: Lane) -> float:
        lane_centers = {Lane.RIGHT: -4.0, Lane.MIDDLE: 0.0, Lane.LEFT: 4.0}
        return lane_centers[lane]

class EnhancedPlatooningSimulation:
    def __init__(self, num_vehicles: int = 4, dt: float = 0.1, scenario: str = "basic"):
        self.dt = dt
        self.time = 0.0
        self.vehicles = {}
        self.controllers = {}
        self.history = []
        self.scenario = scenario
        
        # User-controlled states
        self.emergency_vehicle = None
        self.priority_vehicle = None
        self.emergency_triggered = False
        self.priority_added = False
        
        self._initialize_vehicles(num_vehicles)
        
    def _initialize_vehicles(self, num_vehicles: int):
        lanes = [Lane.RIGHT, Lane.MIDDLE, Lane.LEFT]
        
        for i in range(num_vehicles):
            vid = f"vehicle_{i}"
            
            if i == 0:
                lane = Lane.MIDDLE
                role = VehicleRole.LEADER
            else:
                lane = lanes[i % len(lanes)]
                role = VehicleRole.FOLLOWER
            
            vehicle = EnhancedVehicle(vid, role, VehicleType.NORMAL, lane)
            self.vehicles[vid] = vehicle
            self.controllers[vid] = EnhancedPlatooningController(vehicle)
    
    def set_emergency_vehicle(self, vehicle_id: str):
        """Set which vehicle will perform emergency braking"""
        if vehicle_id in self.vehicles:
            self.emergency_vehicle = vehicle_id
    
    def set_priority_vehicle(self, vehicle_id: str):
        """Set which vehicle becomes priority vehicle"""
        if vehicle_id in self.vehicles and not self.priority_added:
            vehicle = self.vehicles[vehicle_id]
            vehicle.role = VehicleRole.PRIORITY
            vehicle.vehicle_type = VehicleType.AMBULANCE
            vehicle.color = '#FF0000'
            vehicle.symbol = "🚑"
            self.priority_vehicle = vehicle_id
            self.priority_added = True
    
    def trigger_emergency(self):
        """Trigger emergency braking on the selected vehicle"""
        if self.emergency_vehicle and not self.emergency_triggered:
            vehicle = self.vehicles[self.emergency_vehicle]
            vehicle.trigger_emergency_braking(self.time)
            self.emergency_triggered = True
            print(f"🚨 EMERGENCY: {self.emergency_vehicle} triggered hard braking at time {self.time:.1f}s!")
            return True
        return False
    
    def step(self):
        vehicle_states = self._get_vehicle_states()
        
        actions = {}
        for vid, controller in self.controllers.items():
            action = controller.compute_action(vehicle_states, self.time)
            actions[vid] = {'object': action, 'dict': action.to_dict()}
            
            vehicle = self.vehicles[vid]
            vehicle.acceleration = action.acceleration
            
            if action.target_lane and action.target_lane != vehicle.lane:
                vehicle.initiate_lane_change(action.target_lane)
        
        # Update positions
        for vehicle in self.vehicles.values():
            vehicle.update_position(self.dt)
        
        collisions = self._check_collisions()
        
        self.history.append({
            'time': self.time,
            'vehicles': {vid: self._get_vehicle_state(vid) for vid in self.vehicles.keys()},
            'actions': actions,
            'collisions': collisions
        })
        
        self.time += self.dt
    
    def _get_vehicle_states(self) -> Dict:
        return {vid: {'object': vehicle, **self._get_vehicle_state(vid)} 
                for vid, vehicle in self.vehicles.items()}
    
    def _get_vehicle_state(self, vehicle_id: str) -> Dict:
        vehicle = self.vehicles[vehicle_id]
        return {
            'id': vehicle.id,
            'role': vehicle.role,
            'vehicle_type': vehicle.vehicle_type,
            'x': vehicle.x,
            'y': vehicle.y,
            'velocity': vehicle.velocity,
            'acceleration': vehicle.acceleration,
            'lane': vehicle.lane,
            'is_changing_lane': vehicle.is_changing_lane,
            'length': vehicle.length,
            'width': vehicle.width,
            'color': vehicle.color,
            'symbol': vehicle.symbol,
            'emergency_braking': vehicle.emergency_braking
        }
    
    def _check_collisions(self) -> List[Tuple[str, str]]:
        collisions = []
        vehicles = list(self.vehicles.values())
        
        for i in range(len(vehicles)):
            for j in range(i + 1, len(vehicles)):
                v1, v2 = vehicles[i], vehicles[j]
                
                x1_min, x1_max, y1_min, y1_max = v1.get_bounding_box()
                x2_min, x2_max, y2_min, y2_max = v2.get_bounding_box()
                
                # Safety margin
                margin = 0.3
                x_overlap = (x1_min - margin) < (x2_max + margin) and (x1_max + margin) > (x2_min - margin)
                y_overlap = (y1_min - margin) < (y2_max + margin) and (y1_max + margin) > (y2_min - margin)
                
                if x_overlap and y_overlap:
                    collisions.append((v1.id, v2.id))
        
        return collisions
    
    def get_safety_stats(self) -> Dict:
        if not self.history:
            return {'safety_percentage': 100.0, 'total_collisions': 0, 'emergency_events': 0}
        
        total_collisions = sum(len(step['collisions']) for step in self.history)
        emergency_events = sum(1 for step in self.history 
                             if any(action_data['object'].emergency 
                                  for action_data in step['actions'].values()))
        
        safety_percentage = max(0, 100 - (total_collisions * 20))
        
        return {
            'safety_percentage': safety_percentage,
            'total_collisions': total_collisions,
            'emergency_events': emergency_events
        }

    def run(self, duration: float = 60.0):
        total_steps = int(duration / self.dt)
        
        for step in range(total_steps):
            self.step()
            
            # Auto-trigger if set
            if self.scenario == "emergency" and step == 30 and self.emergency_vehicle and not self.emergency_triggered:
                self.trigger_emergency()
            elif self.scenario == "priority" and step == 20 and self.priority_vehicle and not self.priority_added:
                self.set_priority_vehicle(self.priority_vehicle)
    
    def reset(self):
        """Reset simulation to clean state"""
        self.time = 0.0
        self.vehicles = {}
        self.controllers = {}
        self.history = []
        self.emergency_triggered = False
        self.priority_added = False
        self.emergency_vehicle = None
        self.priority_vehicle = None
        self._initialize_vehicles(4)  # Default to 4 vehicles