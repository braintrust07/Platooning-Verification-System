"""
Agent reasoning display panel
"""

import tkinter as tk
from tkinter import ttk

class AgentView:
    """Panel for displaying agent reasoning"""
    
    def __init__(self, parent):
        self.parent = parent
        self.setup_panel()
    
    def setup_panel(self):
        """Setup the agent reasoning panel"""
        self.frame = ttk.Frame(self.parent)
        
        # Agent selection
        selection_frame = ttk.Frame(self.frame)
        selection_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(selection_frame, text="Select Agent:").pack(side=tk.LEFT)
        self.agent_var = tk.StringVar(value="vehicle_0")
        self.agent_combo = ttk.Combobox(selection_frame, textvariable=self.agent_var, state="readonly")
        self.agent_combo['values'] = [f'vehicle_{i}' for i in range(8)]
        self.agent_combo.pack(side=tk.LEFT, padx=5)
        
        # Reasoning display
        self.reasoning_text = tk.Text(self.frame, height=15, width=50, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.reasoning_text.yview)
        self.reasoning_text.configure(yscrollcommand=scrollbar.set)
        self.reasoning_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial message
        self.show_welcome_message()
    
    def show_welcome_message(self):
        """Show welcome message in agent view"""
        self.reasoning_text.config(state=tk.NORMAL)
        self.reasoning_text.delete(1.0, tk.END)
        self.reasoning_text.insert(tk.END, """🤖 AGENT REASONING DISPLAY

Select a vehicle to see its decision-making process.

Each agent uses:
• Formal verification rules
• Mathematical safety guarantees
• Real-time sensor data
• Cooperative communication

Start simulation to see agents in action!""")
        self.reasoning_text.config(state=tk.DISABLED)
    
    def update_reasoning(self, agent_data):
        """Update agent reasoning display"""
        self.reasoning_text.config(state=tk.NORMAL)
        self.reasoning_text.delete(1.0, tk.END)
        
        if agent_data:
            self.reasoning_text.insert(tk.END, f"🚗 {agent_data['id'].upper()}\n")
            self.reasoning_text.insert(tk.END, "="*40 + "\n\n")
            self.reasoning_text.insert(tk.END, f"Position: {agent_data['position']:.1f}m\n")
            self.reasoning_text.insert(tk.END, f"Velocity: {agent_data['velocity']:.1f}m/s\n")
            self.reasoning_text.insert(tk.END, f"Role: {agent_data['role']}\n\n")
            self.reasoning_text.insert(tk.END, f"Decision: {agent_data['action_reason']}\n")
            self.reasoning_text.insert(tk.END, f"Emergency: {agent_data['emergency']}\n")
        else:
            self.show_welcome_message()
            
        self.reasoning_text.config(state=tk.DISABLED)
    
    def get_frame(self):
        """Get the panel frame"""
        return self.frame
    
    def get_selected_agent(self):
        """Get currently selected agent"""
        return self.agent_var.get()
    
    def set_agent_callback(self, callback):
        """Set callback for agent selection changes"""
        self.agent_combo.bind('<<ComboboxSelected>>', callback)