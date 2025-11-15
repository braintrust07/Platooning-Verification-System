"""
Analysis graphs panel
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class GraphsPanel:
    """Panel for analysis graphs"""
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_panel()
    
    def setup_panel(self):
        """Setup the graphs panel"""
        self.frame = ttk.Frame(self.parent)
        
        # Graph selection buttons
        self.setup_graph_buttons()
        
        # Graph display area
        self.graph_frame = ttk.Frame(self.frame)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current graph
        self.current_fig = None
        self.current_canvas = None
    
    def setup_graph_buttons(self):
        """Setup graph selection buttons"""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        graphs = [
            ("Safety Analysis", "📊"),
            ("Positions", "🚗"), 
            ("Velocities", "📈"),
            ("Distances", "📏"),
            ("Emergencies", "🚨")
        ]
        
        for text, icon in graphs:
            ttk.Button(button_frame, text=f"{icon} {text}", 
                      command=lambda t=text: self.show_graph(t)).pack(side=tk.LEFT, padx=5)
    
    def show_graph(self, graph_type):
        """Show selected graph type"""
        # Clear previous graph
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
        
        # Create new graph
        self.current_fig, ax = plt.subplots(figsize=(10, 6))
        
        # Sample data - in real implementation, this would use simulation data
        if graph_type == "Safety Analysis":
            self.create_safety_analysis(ax)
        elif graph_type == "Positions":
            self.create_positions_graph(ax)
        elif graph_type == "Velocities":
            self.create_velocities_graph(ax)
        elif graph_type == "Distances":
            self.create_distances_graph(ax)
        elif graph_type == "Emergencies":
            self.create_emergencies_graph(ax)
        
        # Display graph
        self.current_canvas = FigureCanvasTkAgg(self.current_fig, self.graph_frame)
        self.current_canvas.draw()
        self.current_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_safety_analysis(self, ax):
        """Create safety analysis graph"""
        ax.text(0.5, 0.5, 'Safety Analysis Graph\n(Run simulation to see data)', 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Safety Analysis')
    
    def create_positions_graph(self, ax):
        """Create positions graph"""
        ax.text(0.5, 0.5, 'Vehicle Positions Over Time\n(Run simulation to see data)', 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Vehicle Positions')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Position (m)')
    
    def create_velocities_graph(self, ax):
        """Create velocities graph"""
        ax.text(0.5, 0.5, 'Vehicle Velocities\n(Run simulation to see data)', 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Vehicle Velocities')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Velocity (m/s)')
    
    def create_distances_graph(self, ax):
        """Create following distances graph"""
        ax.text(0.5, 0.5, 'Following Distances\n(Run simulation to see data)', 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Following Distances')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Distance (m)')
    
    def create_emergencies_graph(self, ax):
        """Create emergencies graph"""
        ax.text(0.5, 0.5, 'Emergency Events\n(Run simulation to see data)', 
               ha='center', va='center', transform=ax.transAxes, fontsize=12)
        ax.set_title('Emergency Events')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Emergency Status')
    
    def update_graphs(self, simulation_data):
        """Update graphs with simulation data"""
        # This would update graphs with real data when simulation runs
        pass
    
    def get_frame(self):
        """Get the panel frame"""
        return self.frame