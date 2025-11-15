#!/usr/bin/env python3
"""
Basic platooning scenario example
"""

import sys
import os
# Fix the path - go up one level from examples directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.simulation.environment import PlatooningSimulation
from src.simulation.visualizer import PlatoonVisualizer

def main():
    """Run basic platooning scenario"""
    print("Basic Platooning Scenario")
    print("=" * 40)
    
    # Create and run simulation
    sim = PlatooningSimulation(num_vehicles=3)
    sim.run(duration=30.0)
    
    # Display results
    stats = sim.get_safety_stats()
    
    print("\n" + "=" * 50)
    print("BASIC PLATOONING RESULTS")
    print("=" * 50)
    print(f"Simulation Duration: {stats['simulation_time']:.1f}s")
    print(f"Emergency Events: {stats['total_emergencies']}")
    print(f"Safety Violations: {stats['safety_violations']}")
    print(f"Safety Performance: {stats['safety_percentage']:.1f}%")
    print("=" * 50)
    
    # Create visualization
    PlatoonVisualizer.plot_platoon_history(sim.history)

if __name__ == "__main__":
    main()