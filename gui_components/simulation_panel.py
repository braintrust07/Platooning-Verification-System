"""
Simulation visualization panel
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class SimulationPanel:
    """Panel for real-time simulation visualization"""
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_panel()
    
    def setup_panel(self):
        """Setup the simulation visualization panel"""
        self.frame = ttk.Frame(self.parent)
        
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, self.frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initial empty plot
        self.ax.text(0.5, 0.5, 'Simulation visualization will appear here', 
                    ha='center', va='center', transform=self.ax.transAxes)
        self.ax.set_title('Real-time Platooning Simulation')
        self.canvas.draw()
    
    def update_plot(self, simulation_data):
        """Update the simulation plot with new data"""
        self.ax.clear()
        
        if simulation_data and 'vehicles' in simulation_data:
            vehicles = simulation_data['vehicles']
            
            # Plot each vehicle
            for i, (vid, vehicle) in enumerate(vehicles.items()):
                pos = vehicle['position']
                vel = vehicle['velocity']
                
                # Vehicle rectangle
                color = 'red' if vehicle['role'] == 'leader' else 'blue'
                self.ax.add_patch(plt.Rectangle((pos-2, i-0.3), 4, 0.6, 
                                              facecolor=color, alpha=0.7))
                
                # Vehicle info
                self.ax.text(pos, i, f"{vid}\n{vel:.1f}m/s", 
                           ha='center', va='center', fontsize=8)
            
            self.ax.set_xlim(0, max(100, max(v['position'] for v in vehicles.values()) + 20))
            self.ax.set_ylim(-0.5, len(vehicles) - 0.5)
            self.ax.set_xlabel('Position (m)')
            self.ax.set_ylabel('Vehicle')
            self.ax.grid(True, alpha=0.3)
        
        self.canvas.draw()
    
    def get_frame(self):
        """Get the panel frame"""
        return self.frame