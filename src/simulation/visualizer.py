"""
Visualization for platooning simulation
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict

class PlatoonVisualizer:
    """Visualize platooning simulation results"""
    
    @staticmethod
    def plot_platoon_history(history: List[Dict], save_path: str = None):
        """Plot comprehensive platooning analysis"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        times = [step['time'] for step in history]
        vehicle_ids = list(history[0]['vehicles'].keys())
        
        # Plot 1: Positions
        for vid in vehicle_ids:
            positions = [step['vehicles'][vid]['position'] for step in history]
            ax1.plot(times, positions, label=vid, linewidth=2)
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Position (m)')
        ax1.set_title('Vehicle Positions')
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Velocities
        for vid in vehicle_ids:
            velocities = [step['vehicles'][vid]['velocity'] for step in history]
            ax2.plot(times, velocities, label=vid, linewidth=2)
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Velocity (m/s)')
        ax2.set_title('Vehicle Velocities')
        ax2.legend()
        ax2.grid(True)
        
        # Plot 3: Following distances
        if len(vehicle_ids) > 1:
            gaps = []
            for step in history:
                positions = [step['vehicles'][vid]['position'] for vid in vehicle_ids]
                step_gaps = [positions[i] - positions[i+1] for i in range(len(positions)-1)]
                gaps.append(step_gaps)
            
            gaps = np.array(gaps)
            for i in range(gaps.shape[1]):
                ax3.plot(times, gaps[:, i], label=f'Gap {i+1}', linewidth=2)
            ax3.set_xlabel('Time (s)')
            ax3.set_ylabel('Distance (m)')
            ax3.set_title('Inter-Vehicle Distances')
            ax3.legend()
            ax3.grid(True)
        
        # Plot 4: Safety status
        emergencies = []
        for step in history:
            has_emergency = any(action['emergency'] for action in step['actions'].values())
            emergencies.append(1 if has_emergency else 0)
        
        ax4.plot(times, emergencies, 'r-', linewidth=2, label='Emergency')
        ax4.set_xlabel('Time (s)')
        ax4.set_ylabel('Emergency Status')
        ax4.set_title('Safety Events')
        ax4.set_ylim(-0.1, 1.1)
        ax4.legend()
        ax4.grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Plot saved to {save_path}")
        
        plt.show()
    
    @staticmethod
    def print_safety_report(stats: Dict, history: List[Dict]):
        """Print safety report"""
        print("\n" + "="*50)
        print("FORMAL SAFETY VERIFICATION REPORT")
        print("="*50)
        print(f"Simulation Duration: {stats['simulation_time']:.1f}s")
        print(f"Total Emergency Events: {stats['total_emergencies']}")
        print(f"Safety Violations: {stats['safety_violations']}")
        print(f"Monitor Violations: {stats['monitor_violations']}")
        print(f"Safety Performance: {stats['safety_percentage']:.1f}%")
        print("="*50)