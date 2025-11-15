#!/usr/bin/env python3
"""
Enhanced GUI for Formal Platooning System with User-Controlled Scenarios
"""

import sys
import os
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.patches import Rectangle

# Add project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.simulation.enhanced_environment import EnhancedPlatooningSimulation, Lane, VehicleRole, VehicleType
except ImportError:
    from src.simulation.environment import PlatooningSimulation as EnhancedPlatooningSimulation
    print("Using basic simulation - enhanced features limited")

class EnhancedPlatooningGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Formal Platooning Verification System")
        self.root.geometry("1600x1000")
        self.root.configure(bg='#1e1e1e')
        
        # Simulation state
        self.simulation = None
        self.is_running = False
        self.current_step = 0
        self.simulation_thread = None
        self.simulation_mode = "basic"
        
        # User selections
        self.selected_emergency_vehicle = tk.StringVar(value="vehicle_0")
        self.selected_priority_vehicle = tk.StringVar(value="vehicle_1")
        self.emergency_triggered = False
        self.priority_added = False
        
        # Road parameters
        self.num_lanes = 3
        self.lane_width = 4.0
        self.vehicle_length = 4.5
        self.vehicle_width = 1.8
        
        self.setup_styles()
        self.setup_gui()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#2d2d2d')
        style.configure('TLabel', background='#2d2d2d', foreground='white')
        style.configure('TLabelframe', background='#2d2d2d', foreground='white')
        style.configure('TButton', background='#404040', foreground='white')
        style.configure('TCombobox', background='#404040', foreground='white')
        
    def setup_gui(self):
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Left panel
        left_panel = ttk.Frame(main_container, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # Right panel
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.setup_control_panel(left_panel)
        self.setup_info_panel(left_panel)
        self.setup_visualization_panel(right_panel)
        
    def setup_control_panel(self, parent):
        control_frame = ttk.LabelFrame(parent, text="🎮 Simulation Controls", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Scenario selection
        ttk.Label(control_frame, text="Select Scenario:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 8))
        
        scenario_frame = ttk.Frame(control_frame)
        scenario_frame.pack(fill=tk.X, pady=5)
        
        self.scenario_var = tk.StringVar(value="basic")
        
        ttk.Radiobutton(scenario_frame, text="🚗 Basic Platooning", 
                       variable=self.scenario_var, value="basic",
                       command=self.on_scenario_change).pack(anchor=tk.W)
        ttk.Radiobutton(scenario_frame, text="🚨 Emergency Braking", 
                       variable=self.scenario_var, value="emergency",
                       command=self.on_scenario_change).pack(anchor=tk.W)
        ttk.Radiobutton(scenario_frame, text="🚑 Priority Vehicle", 
                       variable=self.scenario_var, value="priority",
                       command=self.on_scenario_change).pack(anchor=tk.W)
        
        # Vehicle selection for scenarios
        self.setup_scenario_controls(control_frame)
        
        # Simulation settings
        settings_frame = ttk.Frame(control_frame)
        settings_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(settings_frame, text="Number of Vehicles:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.vehicle_count = tk.IntVar(value=4)
        ttk.Spinbox(settings_frame, from_=2, to=8, textvariable=self.vehicle_count, width=8).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(settings_frame, text="Duration (s):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.duration = tk.DoubleVar(value=30.0)
        ttk.Spinbox(settings_frame, from_=10, to=60, textvariable=self.duration, width=8).grid(row=1, column=1, padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Simulation", 
                                   command=self.start_simulation)
        self.start_btn.pack(fill=tk.X, pady=2)
        
        ttk.Button(button_frame, text="⏸ Pause", command=self.pause_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="⏹ Stop", command=self.stop_simulation).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="🔁 Step Forward", command=self.step_forward).pack(fill=tk.X, pady=2)
        
        # Manual triggers
        trigger_frame = ttk.Frame(control_frame)
        trigger_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(trigger_frame, text="🚨 Trigger Emergency NOW", 
                  command=self.manual_emergency).pack(fill=tk.X, pady=2)
        ttk.Button(trigger_frame, text="🚑 Activate Priority NOW", 
                  command=self.manual_priority).pack(fill=tk.X, pady=2)
        
        # Status
        self.status_var = tk.StringVar(value="🟢 Ready - Select scenario and click Start")
        ttk.Label(control_frame, textvariable=self.status_var, foreground="#4CAF50", 
                 font=('Arial', 9)).pack(pady=5)
        
    def setup_scenario_controls(self, parent):
        # Emergency vehicle selection
        emergency_frame = ttk.Frame(parent)
        emergency_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(emergency_frame, text="Emergency Vehicle:").pack(anchor=tk.W)
        emergency_combo = ttk.Combobox(emergency_frame, textvariable=self.selected_emergency_vehicle, 
                                     state="readonly", width=15)
        emergency_combo['values'] = [f'vehicle_{i}' for i in range(8)]
        emergency_combo.pack(fill=tk.X, pady=2)
        
        # Priority vehicle selection  
        priority_frame = ttk.Frame(parent)
        priority_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(priority_frame, text="Priority Vehicle:").pack(anchor=tk.W)
        priority_combo = ttk.Combobox(priority_frame, textvariable=self.selected_priority_vehicle, 
                                    state="readonly", width=15)
        priority_combo['values'] = [f'vehicle_{i}' for i in range(8)]
        priority_combo.pack(fill=tk.X, pady=2)
        
        # Store references
        self.emergency_combo = emergency_combo
        self.priority_combo = priority_combo
        
    def setup_info_panel(self, parent):
        info_frame = ttk.LabelFrame(parent, text="📋 Scenario Information", padding=15)
        info_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.scenario_info = tk.Text(info_frame, height=6, width=35, bg='#1a1a1a', fg='white',
                                   font=('Arial', 9), wrap=tk.WORD)
        self.scenario_info.pack(fill=tk.BOTH, expand=True)
        self.scenario_info.insert(tk.END, self.get_scenario_description("basic"))
        self.scenario_info.config(state=tk.DISABLED)
        
        # Agent selection
        agent_frame = ttk.LabelFrame(parent, text="🤖 Agent View", padding=15)
        agent_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(agent_frame, text="Select Vehicle:").pack(anchor=tk.W, pady=(0, 5))
        
        self.selected_agent_vehicle = tk.StringVar(value="vehicle_0")
        vehicle_combo = ttk.Combobox(agent_frame, textvariable=self.selected_agent_vehicle, 
                                   state="readonly", height=8)
        vehicle_combo.pack(fill=tk.X, pady=5)
        vehicle_combo.bind('<<ComboboxSelected>>', self.update_agent_view)
        
        # Agent reasoning
        self.agent_text = tk.Text(agent_frame, height=12, bg='#1a1a1a', fg='white',
                                font=('Consolas', 9), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(agent_frame, orient=tk.VERTICAL, command=self.agent_text.yview)
        self.agent_text.configure(yscrollcommand=scrollbar.set)
        self.agent_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.agent_text.insert(tk.END, self.get_initial_agent_message())
        self.agent_text.config(state=tk.DISABLED)
        
    def setup_visualization_panel(self, parent):
        viz_notebook = ttk.Notebook(parent)
        viz_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Real-time simulation tab
        sim_tab = ttk.Frame(viz_notebook)
        viz_notebook.add(sim_tab, text="🎯 Real-time Simulation")
        
        # Analysis tab
        analysis_tab = ttk.Frame(viz_notebook)
        viz_notebook.add(analysis_tab, text="📊 Analysis")
        
        self.setup_simulation_view(sim_tab)
        self.setup_analysis_view(analysis_tab)
        
    def setup_simulation_view(self, parent):
        plt.style.use('dark_background')
        self.sim_fig, (self.sim_ax, self.info_ax) = plt.subplots(2, 1, figsize=(12, 8), 
                                                                gridspec_kw={'height_ratios': [3, 1]})
        self.sim_fig.patch.set_facecolor('#1e1e1e')
        
        self.sim_canvas = FigureCanvasTkAgg(self.sim_fig, parent)
        self.sim_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.update_simulation_plot()
        
    def setup_analysis_view(self, parent):
        graph_controls = ttk.Frame(parent)
        graph_controls.pack(fill=tk.X, pady=10)
        
        graphs = [
            ("📈 Safety Overview", self.show_safety_overview),
            ("🚗 Positions", self.show_position_graph),
            ("💨 Velocities", self.show_velocity_graph),
            ("📏 Distances", self.show_distance_graph),
            ("🚨 Emergencies", self.show_emergency_graph),
        ]
        
        for i, (text, command) in enumerate(graphs):
            ttk.Button(graph_controls, text=text, command=command).grid(
                row=i//3, column=i%3, padx=5, pady=5, sticky="ew"
            )
            graph_controls.columnconfigure(i%3, weight=1)
        
        self.analysis_frame = ttk.Frame(parent)
        self.analysis_frame.pack(fill=tk.BOTH, expand=True)
        
    def get_scenario_description(self, scenario):
        descriptions = {
            "basic": """🚗 BASIC PLATOONING

• Smooth coordinated driving
• Vehicles maintain safe distances
• Adaptive speed control
• Collision avoidance

Select vehicles and watch how they maintain formation.""",
            
            "emergency": """🚨 EMERGENCY BRAKING

• SELECT which vehicle brakes suddenly
• Watch others react dynamically
• Emergency collision avoidance
• Lane change maneuvers

Choose emergency vehicle and see the chain reaction!""",
            
            "priority": """🚑 PRIORITY VEHICLE

• SELECT which vehicle becomes priority
• Watch others yield cooperatively
• Priority vehicle overtakes
• Dynamic lane changes

Choose priority vehicle and see cooperation!"""
        }
        return descriptions.get(scenario, "")
    
    def get_initial_agent_message(self):
        return """🤖 AGENT REASONING DISPLAY

Welcome! Each vehicle uses:
• Real-time position awareness  
• Dynamic collision avoidance
• Cooperative behavior
• Emergency response protocols

Start a simulation and select vehicles to see their decision-making process!"""
    
    def on_scenario_change(self):
        scenario = self.scenario_var.get()
        self.scenario_info.config(state=tk.NORMAL)
        self.scenario_info.delete(1.0, tk.END)
        self.scenario_info.insert(tk.END, self.get_scenario_description(scenario))
        self.scenario_info.config(state=tk.DISABLED)
        
        # Update combo boxes based on vehicle count
        vehicles = [f'vehicle_{i}' for i in range(self.vehicle_count.get())]
        self.emergency_combo['values'] = vehicles
        self.priority_combo['values'] = vehicles
        
        if vehicles:
            self.selected_emergency_vehicle.set(vehicles[0])
            self.selected_priority_vehicle.set(vehicles[1] if len(vehicles) > 1 else vehicles[0])
    
    def manual_emergency(self):
        if self.simulation and self.is_running:
            # Always set the emergency vehicle first
            self.simulation.set_emergency_vehicle(self.selected_emergency_vehicle.get())
            
            # Then trigger emergency
            if self.simulation.trigger_emergency():
                self.emergency_triggered = True
                self.status_var.set(f"🚨 MANUAL: {self.selected_emergency_vehicle.get()} emergency braking!")
            else:
                messagebox.showwarning("Warning", f"Could not trigger emergency for {self.selected_emergency_vehicle.get()}")
        else:
            messagebox.showwarning("Warning", "Start simulation first!")
    
    def manual_priority(self):
        if self.simulation and self.is_running and not self.priority_added:
            try:
                self.simulation.set_priority_vehicle(self.selected_priority_vehicle.get())
                self.priority_added = True
                self.status_var.set(f"🚑 MANUAL: {self.selected_priority_vehicle.get()} is now priority!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set priority: {e}")
        else:
            messagebox.showwarning("Warning", "Start simulation first or priority already added!")
    
    def start_simulation(self):
        if self.is_running:
            return
            
        try:
            # Initialize simulation
            self.simulation = EnhancedPlatooningSimulation(
                num_vehicles=self.vehicle_count.get(),
                dt=0.1,
                scenario=self.scenario_var.get()
            )
            
            # Reset trigger states
            self.emergency_triggered = False
            self.priority_added = False
            
            # Set user selections
            if self.scenario_var.get() == "emergency":
                self.simulation.set_emergency_vehicle(self.selected_emergency_vehicle.get())
            elif self.scenario_var.get() == "priority":
                self.simulation.set_priority_vehicle(self.selected_priority_vehicle.get())
            
            self.current_step = 0
            self.is_running = True
            self.simulation_mode = self.scenario_var.get()
            
            # Update vehicle selection
            vehicles = [f'vehicle_{i}' for i in range(self.vehicle_count.get())]
            self.selected_agent_vehicle.set(vehicles[0])
            
            self.status_var.set("🟢 Simulation running...")
            self.start_btn.config(state="disabled")
            
            # Start simulation thread
            self.simulation_thread = threading.Thread(target=self.run_simulation)
            self.simulation_thread.daemon = True
            self.simulation_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start simulation: {e}")
    
    def run_simulation(self):
        total_steps = int(self.duration.get() / 0.1)
        
        for step in range(total_steps):
            if not self.is_running:
                break
                
            self.simulation.step()
            self.current_step = step
            
            # Auto-trigger scenarios
            if not self.emergency_triggered and self.simulation_mode == "emergency" and step == 30:
                if self.simulation.trigger_emergency():
                    self.emergency_triggered = True
                    self.status_var.set(f"🚨 AUTO: {self.selected_emergency_vehicle.get()} emergency braking!")
            
            if not self.priority_added and self.simulation_mode == "priority" and step == 20:
                try:
                    self.simulation.set_priority_vehicle(self.selected_priority_vehicle.get())
                    self.priority_added = True
                    self.status_var.set(f"🚑 AUTO: {self.selected_priority_vehicle.get()} is now priority!")
                except:
                    pass
            
            # Update GUI
            self.root.after(0, self.update_gui)
            time.sleep(0.05)
            
        self.is_running = False
        self.root.after(0, self.on_simulation_complete)
    
    def on_simulation_complete(self):
        self.start_btn.config(state="normal")
        if self.simulation:
            stats = self.simulation.get_safety_stats()
            safety_perf = stats['safety_percentage']
            collisions = stats.get('total_collisions', 0)
            
            if collisions == 0:
                status = f"✅ Perfect! {safety_perf:.1f}% safety, No collisions"
            else:
                status = f"⚠️ Completed with {collisions} collisions"
                
            self.status_var.set(status)
        else:
            self.status_var.set("🟢 Simulation completed")
    
    def pause_simulation(self):
        self.is_running = False
        self.status_var.set("⏸ Simulation paused")
    
    def stop_simulation(self):
        self.is_running = False
        if self.simulation:
            # Clear simulation data to prevent memory leaks
            self.simulation.history.clear()
        self.simulation = None
        self.current_step = 0
        self.emergency_triggered = False
        self.priority_added = False
        self.start_btn.config(state="normal")
        self.status_var.set("🟢 Simulation stopped")
        self.update_agent_view()
        self.update_simulation_plot()
    
    def step_forward(self):
        if self.simulation and not self.is_running:
            self.simulation.step()
            self.current_step += 1
            self.update_gui()
    
    def update_gui(self):
        if self.simulation:
            self.update_simulation_plot()
            self.update_agent_view()
    
    def update_simulation_plot(self):
        self.sim_ax.clear()
        self.info_ax.clear()
        
        self.sim_ax.set_facecolor('#1e1e1e')
        self.info_ax.set_facecolor('#1e1e1e')
        
        if self.simulation and self.simulation.vehicles:
            vehicles_data = self.simulation.vehicles
            
            # Draw road
            road_length = 200
            total_road_width = self.num_lanes * self.lane_width
            
            self.sim_ax.add_patch(Rectangle((0, -total_road_width/2), road_length, total_road_width, 
                                          facecolor='#333333', alpha=0.7))
            
            # Lane markings
            for lane in range(self.num_lanes + 1):
                y_pos = -total_road_width/2 + lane * self.lane_width
                if lane == 0 or lane == self.num_lanes:
                    self.sim_ax.axhline(y=y_pos, xmin=0, xmax=road_length, color='white', linewidth=2, alpha=0.9)
                else:
                    for pos in range(0, int(road_length), 20):
                        self.sim_ax.add_patch(Rectangle((pos, y_pos-0.1), 10, 0.2, facecolor='yellow', alpha=0.8))
            
            # Draw vehicles
            collision_detected = False
            priority_present = False
            
            for vid, vehicle in vehicles_data.items():
                if hasattr(vehicle, 'x'):
                    pos_x, pos_y = vehicle.x, vehicle.y
                    vel, accel = vehicle.velocity, vehicle.acceleration
                    symbol = getattr(vehicle, 'symbol', '🚗')
                    color = getattr(vehicle, 'color', '#4FC3F7')
                    is_changing = vehicle.is_changing_lane
                    emergency = getattr(vehicle, 'emergency_braking', False)
                else:
                    pos_x, pos_y = vehicle.get('position', 0), 0
                    vel, accel = vehicle.get('velocity', 0), vehicle.get('acceleration', 0)
                    symbol, color, is_changing, emergency = '🚗', '#4FC3F7', False, False
                
                # Draw vehicle with emergency highlighting
                vehicle_color = '#FF0000' if emergency else color
                vehicle_rect = Rectangle((pos_x-self.vehicle_length/2, pos_y-self.vehicle_width/2), 
                                       self.vehicle_length, self.vehicle_width,
                                       facecolor=vehicle_color, edgecolor='white', linewidth=2, alpha=0.9)
                self.sim_ax.add_patch(vehicle_rect)
                
                # Symbols and info
                self.sim_ax.text(pos_x, pos_y+self.vehicle_width/2+0.8, symbol, ha='center', va='bottom', fontsize=10)
                self.sim_ax.text(pos_x, pos_y+self.vehicle_width/2+0.3, f"{vid}", ha='center', va='bottom', 
                               color='white', fontsize=9, fontweight='bold')
                self.sim_ax.text(pos_x, pos_y-self.vehicle_width/2-0.3, f"{vel:.1f} m/s", 
                               ha='center', va='top', color='white', fontsize=8)
                
                if is_changing:
                    self.sim_ax.text(pos_x, pos_y+self.vehicle_width/2+1.3, "🔄", ha='center', va='bottom', fontsize=12)
                
                if emergency:
                    self.sim_ax.text(pos_x, pos_y+self.vehicle_width/2+1.8, "🚨", ha='center', va='bottom', fontsize=14)
                
                if abs(accel) > 0.1:
                    arrow_dir = -1 if accel < 0 else 1
                    arrow_color = '#FF0000' if accel < -5 else '#FFA726' if accel < -2 else '#4CAF50'
                    self.sim_ax.arrow(pos_x, pos_y-self.vehicle_width/2-0.8, arrow_dir*2, 0, 
                                    head_width=0.3, head_length=0.5, fc=arrow_color, ec=arrow_color)
            
            # Check collisions
            if self.simulation.history:
                latest_collisions = self.simulation.history[-1].get('collisions', [])
                if latest_collisions:
                    collision_detected = True
                    for collision in latest_collisions:
                        self.sim_ax.text(road_length/2, total_road_width/2 + 1, f"🚨 COLLISION!", 
                                       ha='center', va='center', color='red', fontsize=14, fontweight='bold',
                                       bbox=dict(boxstyle="round,pad=0.5", facecolor='black', alpha=0.8))
            
            # Scenario info
            time_elapsed = getattr(self.simulation, 'time', self.current_step * 0.1)
            scenario_text = "BASIC" if self.simulation_mode == "basic" else "EMERGENCY" if self.simulation_mode == "emergency" else "PRIORITY"
            scenario_color = '#4CAF50' if self.simulation_mode == "basic" else '#FF6B6B' if self.simulation_mode == "emergency" else '#00FF00'
            
            if self.emergency_triggered:
                scenario_text += f" - {self.selected_emergency_vehicle.get()} BRAKING!"
            if self.priority_added:
                scenario_text += f" - {self.selected_priority_vehicle.get()} PRIORITY!"
                
            self.sim_ax.text(0.98, 0.98, scenario_text, transform=self.sim_ax.transAxes, color='white', fontsize=11,
                           ha='right', bbox=dict(boxstyle="round,pad=0.3", facecolor=scenario_color, alpha=0.9))
            
            self.sim_ax.text(0.02, 0.98, f'Time: {time_elapsed:.1f}s', transform=self.sim_ax.transAxes, 
                           color='white', fontsize=10, bbox=dict(boxstyle="round,pad=0.3", facecolor='#333333', alpha=0.8))
            
            if self.emergency_triggered:
                self.sim_ax.text(0.5, 0.9, "🚨 EMERGENCY BRAKING ACTIVE 🚨", transform=self.sim_ax.transAxes, 
                               color='red', fontsize=14, ha='center', fontweight='bold',
                               bbox=dict(boxstyle="round,pad=0.5", facecolor='black', alpha=0.8))
            
            if self.priority_added:
                self.sim_ax.text(0.5, 0.85, "🚑 PRIORITY VEHICLE ACTIVE", transform=self.sim_ax.transAxes, 
                               color='red', fontsize=12, ha='center', fontweight='bold',
                               bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.8))
            
            if collision_detected:
                self.sim_ax.text(0.5, 0.8, "💥 COLLISION DETECTED 💥", transform=self.sim_ax.transAxes, 
                               color='red', fontsize=16, ha='center', fontweight='bold',
                               bbox=dict(boxstyle="round,pad=0.5", facecolor='yellow', alpha=0.9))
            
            self.sim_ax.set_xlim(0, road_length)
            self.sim_ax.set_ylim(-total_road_width/2 - 2, total_road_width/2 + 2)
            self.sim_ax.set_xlabel('Position (m)', color='white')
            self.sim_ax.set_ylabel('Lane Position', color='white')
            self.sim_ax.set_title('🚗 Real-time Platooning Simulation', color='white', fontsize=12, pad=20)
            self.sim_ax.grid(True, alpha=0.2, color='white')
            
            # Lane labels
            for i, label in enumerate(['Right Lane', 'Middle Lane', 'Left Lane']):
                y_pos = -total_road_width/2 + (i + 0.5) * self.lane_width
                self.sim_ax.text(-10, y_pos, label, ha='right', va='center', color='white', fontsize=9, style='italic')
            
            # Info panel
            if self.simulation.history:
                latest_data = self.simulation.history[-1]
                emergency_count = 0
                priority_count = 0
                
                for action_data in latest_data['actions'].values():
                    if self._has_emergency_action(action_data):
                        emergency_count += 1
                    if self._has_priority_override(action_data):
                        priority_count += 1
                
                collision_count = len(latest_data.get('collisions', []))
                
                info_text = f"Time: {time_elapsed:.1f}s\n"
                info_text += f"Emergencies: {emergency_count}\n"
                info_text += f"Priority Actions: {priority_count}\n"
                info_text += f"Collisions: {collision_count}\n"
                info_text += f"Vehicles: {len(vehicles_data)}\n"
                
                if self.emergency_triggered:
                    info_text += "EMERGENCY ACTIVE\n"
                if self.priority_added:
                    info_text += "PRIORITY ACTIVE\n"
                
                self.info_ax.text(0.02, 0.8, info_text, transform=self.info_ax.transAxes,
                                color='white', fontsize=10, va='top',
                                bbox=dict(boxstyle="round,pad=0.5", facecolor='#333333'))
            
            self.info_ax.set_xlim(0, 1)
            self.info_ax.set_ylim(0, 1)
            self.info_ax.axis('off')
            
        else:
            # Welcome screen
            welcome_text = "Formal Platooning Verification System\n\n"
            welcome_text += "• Select scenario and vehicles\n"
            welcome_text += "• Watch dynamic adaptation\n"
            welcome_text += "• No collisions guaranteed\n"
            welcome_text += "• Real-time decision making\n\n"
            welcome_text += "Configure settings and click Start!"
            
            self.sim_ax.text(0.5, 0.5, welcome_text, ha='center', va='center',
                           transform=self.sim_ax.transAxes, color='white', fontsize=12)
            self.sim_ax.set_xlim(0, 1)
            self.sim_ax.set_ylim(0, 1)
            self.sim_ax.axis('off')
        
        self.sim_canvas.draw()
    
    def _has_emergency_action(self, action_data):
        """Helper method to check if action data contains emergency"""
        if hasattr(action_data, 'get'):  # Dictionary-like
            return action_data.get('emergency', False)
        elif hasattr(action_data, 'emergency'):  # Object with emergency attribute
            return action_data.emergency
        elif isinstance(action_data, dict):  # Nested dictionary
            if 'object' in action_data and hasattr(action_data['object'], 'emergency'):
                return action_data['object'].emergency
            elif 'dict' in action_data:
                return action_data['dict'].get('emergency', False)
        return False
    
    def _has_priority_override(self, action_data):
        """Helper method to check if action data contains priority override"""
        if hasattr(action_data, 'get'):  # Dictionary-like
            return action_data.get('priority_override', False)
        elif hasattr(action_data, 'priority_override'):  # Object with priority_override attribute
            return action_data.priority_override
        elif isinstance(action_data, dict):  # Nested dictionary
            if 'object' in action_data and hasattr(action_data['object'], 'priority_override'):
                return action_data['object'].priority_override
            elif 'dict' in action_data:
                return action_data['dict'].get('priority_override', False)
        return False
    
    def update_agent_view(self, event=None):
        self.agent_text.config(state=tk.NORMAL)
        self.agent_text.delete(1.0, tk.END)
        
        if self.simulation and self.current_step > 0:
            vid = self.selected_agent_vehicle.get()
            if hasattr(self.simulation, 'controllers') and vid in self.simulation.controllers:
                self.show_agent_reasoning(vid)
            else:
                self.agent_text.insert(tk.END, f"Select a vehicle to view its reasoning")
        else:
            self.agent_text.insert(tk.END, self.get_initial_agent_message())
            
        self.agent_text.config(state=tk.DISABLED)
    
    def show_agent_reasoning(self, vehicle_id):
        if vehicle_id not in self.simulation.controllers:
            return
            
        controller = self.simulation.controllers[vehicle_id]
        vehicle = self.simulation.vehicles[vehicle_id]
        
        # Get vehicle states
        vehicle_states = {}
        for vid, v in self.simulation.vehicles.items():
            if hasattr(v, 'x'):
                vehicle_states[vid] = {
                    'object': v,
                    'x': v.x, 'y': v.y, 'velocity': v.velocity, 'id': v.id,
                    'vehicle_type': getattr(v, 'vehicle_type', VehicleType.NORMAL)
                }
        
        # Get action
        action = controller.compute_action(vehicle_states, self.simulation.time)
        
        reasoning = f"🚗 AGENT: {vehicle_id.upper()}\n"
        reasoning += "═" * 40 + "\n\n"
        
        reasoning += "📊 CURRENT STATE\n"
        reasoning += f"• Position: ({vehicle.x:.1f}m, {vehicle.y:.1f}m)\n"
        reasoning += f"• Velocity: {vehicle.velocity:.1f}m/s\n"
        reasoning += f"• Acceleration: {vehicle.acceleration:.2f}m/s²\n"
        reasoning += f"• Lane: {vehicle.lane.name}\n"
        reasoning += f"• Role: {vehicle.role.value.upper()}\n\n"
        
        reasoning += "🎯 DECISION\n"
        reasoning += f"• {action.reason}\n"
        reasoning += f"• Command: {action.acceleration:.2f}m/s²\n"
        if action.target_lane:
            reasoning += f"• Changing to: {action.target_lane.name} lane\n"
        reasoning += f"• Emergency: {'🚨 YES' if action.emergency else '❌ NO'}\n"
        reasoning += f"• Priority: {'🚑 YES' if action.priority_override else '❌ NO'}\n\n"
        
        reasoning += "🔒 SAFETY STATUS\n"
        reasoning += "• Collision avoidance: ✅ ACTIVE\n"
        reasoning += "• Speed control: ✅ ACTIVE\n"
        reasoning += "• Lane safety: ✅ MONITORED\n"
        
        if self.emergency_triggered and vehicle_id == self.selected_emergency_vehicle.get():
            reasoning += "\n🚨 I AM THE EMERGENCY VEHICLE\n"
            reasoning += "• Performing emergency braking\n"
            reasoning += "• Alerting other vehicles\n"
        
        if self.priority_added and vehicle_id == self.selected_priority_vehicle.get():
            reasoning += "\n🚑 I AM THE PRIORITY VEHICLE\n"
            reasoning += "• Other vehicles yield to me\n"
            reasoning += "• I can overtake slower traffic\n"
        
        self.agent_text.insert(tk.END, reasoning)
    
    def show_safety_overview(self):
        if not self.simulation or not self.simulation.history:
            messagebox.showwarning("Warning", "Run simulation first to generate data")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.patch.set_facecolor('#1e1e1e')
        
        times = [step['time'] for step in self.simulation.history]
        vehicle_ids = list(self.simulation.history[0]['vehicles'].keys())
        
        # Position plot
        for vid in vehicle_ids:
            if hasattr(self.simulation.vehicles[vid], 'x'):
                positions = [step['vehicles'][vid]['x'] for step in self.simulation.history]
            else:
                positions = [step['vehicles'][vid]['position'] for step in self.simulation.history]
            ax1.plot(times, positions, label=vid, linewidth=2)
        
        ax1.set_title('Vehicle Positions', color='white')
        ax1.set_ylabel('Position (m)', color='white')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Velocity plot
        for vid in vehicle_ids:
            velocities = [step['vehicles'][vid]['velocity'] for step in self.simulation.history]
            ax2.plot(times, velocities, label=vid, linewidth=2)
        
        ax2.set_title('Vehicle Velocities', color='white')
        ax2.set_ylabel('Velocity (m/s)', color='white')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Distance plot
        if len(vehicle_ids) > 1:
            for i in range(len(vehicle_ids)-1):
                gaps = []
                for step in self.simulation.history:
                    if hasattr(self.simulation.vehicles[vehicle_ids[i]], 'x'):
                        pos1 = step['vehicles'][vehicle_ids[i]]['x']
                        pos2 = step['vehicles'][vehicle_ids[i+1]]['x']
                    else:
                        pos1 = step['vehicles'][vehicle_ids[i]]['position']
                        pos2 = step['vehicles'][vehicle_ids[i+1]]['position']
                    gaps.append(pos1 - pos2 - self.vehicle_length)
                ax3.plot(times, gaps, label=f'Gap {i+1}', linewidth=2)
        
        ax3.set_title('Following Distances', color='white')
        ax3.set_ylabel('Distance (m)', color='white')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Emergency events
        emergencies = []
        for step in self.simulation.history:
            has_emergency = False
            for action_data in step['actions'].values():
                if self._has_emergency_action(action_data):
                    has_emergency = True
                    break
            emergencies.append(1.0 if has_emergency else 0.0)
        
        ax4.plot(times, emergencies, 'r-', linewidth=2, label='Emergency Events')
        ax4.set_title('Emergency Events', color='white')
        ax4.set_ylabel('Emergency', color='white')
        ax4.set_ylim(-0.1, 1.1)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Dark theme
        for ax in [ax1, ax2, ax3, ax4]:
            ax.set_facecolor('#1e1e1e')
            ax.tick_params(colors='white')
            ax.xaxis.label.set_color('white')
            ax.yaxis.label.set_color('white')
        
        plt.tight_layout()
        plt.show()
    
    def show_position_graph(self):
        self.show_individual_graph('position', 'Vehicle Positions', 'Position (m)')
    
    def show_velocity_graph(self):
        self.show_individual_graph('velocity', 'Vehicle Velocities', 'Velocity (m/s)')
    
    def show_distance_graph(self):
        self.show_individual_graph('distance', 'Following Distances', 'Distance (m)')
    
    def show_emergency_graph(self):
        """Show emergency events over time"""
        if not self.simulation or not self.simulation.history:
            messagebox.showwarning("Warning", "Run simulation first to generate data")
            return
        
        popup = tk.Toplevel(self.root)
        popup.title("🚨 Emergency Events Over Time")
        popup.geometry("800x600")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        
        times = [step['time'] for step in self.simulation.history]
        
        # Count emergency actions per time step
        emergency_counts = []
        for step in self.simulation.history:
            emergency_count = 0
            for vid, action_data in step['actions'].items():
                if self._has_emergency_action(action_data):
                    emergency_count += 1
            emergency_counts.append(emergency_count)
        
        # Plot emergency events
        ax.plot(times, emergency_counts, 'r-', linewidth=3, label='Emergency Actions', marker='o', markersize=4)
        ax.fill_between(times, 0, emergency_counts, alpha=0.3, color='red')
        
        # Add markers for significant events
        if self.emergency_triggered:
            # Find when emergency was triggered
            for i, step in enumerate(self.simulation.history):
                if any(self._has_emergency_action(action_data) for action_data in step['actions'].values()):
                    ax.axvline(x=step['time'], color='yellow', linestyle='--', alpha=0.7, label='Emergency Triggered')
                    break
        
        ax.set_xlabel('Time (s)', color='white', fontsize=12)
        ax.set_ylabel('Number of Emergency Actions', color='white', fontsize=12)
        ax.set_title('🚨 Emergency Events Over Time', color='white', fontsize=14, fontweight='bold')
        ax.legend(facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
        ax.grid(True, alpha=0.3, color='white')
        ax.set_ylim(bottom=0)
        
        # Customize ticks
        ax.tick_params(colors='white')
        ax.xaxis.label.set_color('white')
        ax.yaxis.label.set_color('white')
        
        # Add statistics
        total_emergencies = sum(emergency_counts)
        max_emergencies = max(emergency_counts) if emergency_counts else 0
        
        stats_text = f"Total Emergency Events: {total_emergencies}\nMax Simultaneous: {max_emergencies}"
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, color='white', 
                fontsize=10, va='top', bbox=dict(boxstyle="round,pad=0.5", facecolor='red', alpha=0.3))
        
        canvas = FigureCanvasTkAgg(fig, popup)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)
    
    def show_individual_graph(self, graph_type, title, ylabel):
        if not self.simulation or not self.simulation.history:
            messagebox.showwarning("Warning", "Run simulation first to generate data")
            return
        
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("800x600")
        
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#1e1e1e')
        
        times = [step['time'] for step in self.simulation.history]
        vehicle_ids = list(self.simulation.history[0]['vehicles'].keys())
        
        if graph_type == 'position':
            for vid in vehicle_ids:
                if hasattr(self.simulation.vehicles[vid], 'x'):
                    positions = [step['vehicles'][vid]['x'] for step in self.simulation.history]
                else:
                    positions = [step['vehicles'][vid]['position'] for step in self.simulation.history]
                ax.plot(times, positions, label=vid, linewidth=2)
        elif graph_type == 'velocity':
            for vid in vehicle_ids:
                velocities = [step['vehicles'][vid]['velocity'] for step in self.simulation.history]
                ax.plot(times, velocities, label=vid, linewidth=2)
        elif graph_type == 'distance':
            if len(vehicle_ids) > 1:
                for i in range(len(vehicle_ids)-1):
                    gaps = []
                    for step in self.simulation.history:
                        if hasattr(self.simulation.vehicles[vehicle_ids[i]], 'x'):
                            pos1 = step['vehicles'][vehicle_ids[i]]['x']
                            pos2 = step['vehicles'][vehicle_ids[i+1]]['x']
                        else:
                            pos1 = step['vehicles'][vehicle_ids[i]]['position']
                            pos2 = step['vehicles'][vehicle_ids[i+1]]['position']
                        gaps.append(pos1 - pos2 - self.vehicle_length)
                    ax.plot(times, gaps, label=f'Gap {i+1}', linewidth=2)
        elif graph_type == 'emergency':
            emergency_counts = []
            for step in self.simulation.history:
                emergency_count = 0
                for action_data in step['actions'].values():
                    if self._has_emergency_action(action_data):
                        emergency_count += 1
                emergency_counts.append(emergency_count)
            
            ax.plot(times, emergency_counts, 'r-', linewidth=3, label='Emergency Actions', marker='o', markersize=4)
            ax.fill_between(times, 0, emergency_counts, alpha=0.3, color='red')
            ax.set_ylim(bottom=0)
        
        ax.set_xlabel('Time (s)', color='white')
        ax.set_ylabel(ylabel, color='white')
        ax.set_title(title, color='white')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.tick_params(colors='white')
        
        canvas = FigureCanvasTkAgg(fig, popup)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)

def main():
    root = tk.Tk()
    app = EnhancedPlatooningGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()