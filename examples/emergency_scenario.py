#!/usr/bin/env python3
"""
Emergency Braking Scenario
"""

import sys
import os
# Fix the path - go up one level from examples directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.simulation.environment import PlatooningSimulation
from src.simulation.visualizer import PlatoonVisualizer

def main():
    """Run emergency braking scenario"""
    print("🚨 EMERGENCY BRAKING SCENARIO")
    print("=" * 50)
    
    sim = PlatooningSimulation(num_vehicles=3, dt=0.1)
    
    print("Phase 1: Normal operation (5 seconds)")
    # Run normal operation
    for _ in range(50):
        sim.step()
    
    print("Phase 2: Sudden leader braking")
    # Simulate emergency - leader suddenly brakes hard
    sim.vehicles['vehicle_0']['velocity'] = 5.0
    print("   Leader velocity dropped to 5 m/s!")
    
    # Continue for emergency response
    for _ in range(100):
        sim.step()
    
    print("Phase 3: Analysis")
    # Comprehensive analysis
    stats = sim.get_safety_stats()
    
    print("\n" + "=" * 50)
    print("EMERGENCY SCENARIO RESULTS")
    print("=" * 50)
    print(f"Total simulation time: {stats['simulation_time']:.1f}s")
    print(f"Emergency events: {stats['total_emergencies']}")
    print(f"Safety violations: {stats['safety_violations']}")
    print(f"Final safety performance: {stats['safety_percentage']:.1f}%")
    
    # Create visualization
    PlatoonVisualizer.plot_platoon_history(
        sim.history, 
        save_path="emergency_scenario_analysis.png"
    )

if __name__ == "__main__":
    main()