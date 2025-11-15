#!/usr/bin/env python3
"""
FORMAL PLATOONING VERIFICATION SYSTEM
Pure Symbolic AI - No Machine Learning
"""

import sys
import os
import time

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.simulation.enhanced_environment import EnhancedPlatooningSimulation

def main():
    print("=" * 70)
    print("FORMAL PLATOONING VERIFICATION SYSTEM")
    print("Pure Symbolic AI - No Machine Learning")
    print("=" * 70)
    
    # Initialize simulation
    print("\n🚗 Initializing 4-vehicle platoon...")
    sim = EnhancedPlatooningSimulation(num_vehicles=4, dt=0.1)
    
    # Set which vehicle will trigger emergency braking
    sim.set_emergency_vehicle("vehicle_0")
    
    print("\n🔄 Running simulation for 60 seconds...")
    
    # Run simulation steps
    total_steps = int(60.0 / 0.1)
    emergency_triggered = False
    
    for step in range(total_steps):
        sim.step()
        
        # Trigger emergency at 3 seconds
        if step == 30 and not emergency_triggered:  # 3 seconds at 0.1 dt
            print("🚨 EMERGENCY: Triggering leader hard braking!")
            sim.trigger_emergency()  # No argument needed now
            emergency_triggered = True
        
        # Print progress every 5 seconds
        if step % 50 == 0:
            time_elapsed = step * 0.1
            print(f"⏱️  Time: {time_elapsed:.1f}s - Vehicles: {len(sim.vehicles)}")
            
            # Show current positions
            for vid, vehicle in sim.vehicles.items():
                if hasattr(vehicle, 'x'):
                    print(f"   {vid}: pos=({vehicle.x:.1f}, {vehicle.y:.1f}), vel={vehicle.velocity:.1f}m/s")
                else:
                    print(f"   {vid}: pos={vehicle.get('position', 0):.1f}, vel={vehicle.get('velocity', 0):.1f}m/s")
    
    # Get final statistics
    stats = sim.get_safety_stats()
    
    print("\n" + "=" * 70)
    print("SIMULATION COMPLETE - SAFETY ANALYSIS")
    print("=" * 70)
    print(f"📊 Safety Performance: {stats['safety_percentage']:.1f}%")
    print(f"💥 Total Collisions: {stats['total_collisions']}")
    print(f"🚨 Emergency Events: {stats['emergency_events']}")
    print(f"⏱️  Total Time: {sim.time:.1f}s")
    print(f"🚗 Vehicles Simulated: {len(sim.vehicles)}")
    
    if stats['safety_percentage'] >= 95:
        print("✅ EXCELLENT: All safety requirements satisfied!")
    elif stats['safety_percentage'] >= 80:
        print("⚠️  GOOD: Basic safety requirements met")
    else:
        print("🚨 CRITICAL: Safety requirements violated!")
    
    print("=" * 70)

if __name__ == "__main__":
    main()