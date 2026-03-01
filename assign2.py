import tkinter as tk
from tkinter import messagebox, ttk
import random
import heapq
import time
import math

class PathfinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Dynamic Pathfinding Agent")
        
        # Default Settings
        self.rows = 20
        self.cols = 20
        self.cell_size = 25
        self.obstacle_density = 0.3
        self.running = False
        self.dynamic_mode = False
        
        # Colors
        self.COLOR_EMPTY = "white"
        self.COLOR_WALL = "#2c3e50"
        self.COLOR_START = "#27ae60"
        self.COLOR_GOAL = "#e74c3c"
        self.COLOR_FRONTIER = "#f1c40f" # Yellow
        self.COLOR_VISITED = "#3498db"  # Blue
        self.COLOR_PATH = "#2ecc71"     # Green
        self.COLOR_AGENT = "#8e44ad"    # Purple
        
        # State
        self.grid = []
        self.start_node = (1, 1)
        self.goal_node = (18, 18)
        self.agent_pos = self.start_node
        self.current_path = []
        self.walls = set()
        
        # Setup GUI
        self.setup_ui()
        self.init_grid()

    def setup_ui(self):
        control_panel = tk.Frame(self.root, pady=10)
        control_panel.pack(side=tk.TOP, fill=tk.X)

        # Grid Settings
        tk.Label(control_panel, text="Size:").pack(side=tk.LEFT, padx=5)
        self.size_entry = tk.Entry(control_panel, width=5)
        self.size_entry.insert(0, "20")
        self.size_entry.pack(side=tk.LEFT)
        
        tk.Button(control_panel, text="Update Grid", command=self.update_grid_size).pack(side=tk.LEFT, padx=5)
        tk.Button(control_panel, text="Randomize Map", command=self.randomize_map).pack(side=tk.LEFT, padx=5)

        # Algorithm Selection
        tk.Label(control_panel, text="Algo:").pack(side=tk.LEFT, padx=5)
        self.algo_var = tk.StringVar(value="A*")
        self.algo_menu = ttk.Combobox(control_panel, textvariable=self.algo_var, values=["A*", "Greedy BFS"], width=10)
        self.algo_menu.pack(side=tk.LEFT)

        # Heuristic Selection
        tk.Label(control_panel, text="Heuristic:").pack(side=tk.LEFT, padx=5)
        self.heur_var = tk.StringVar(value="Manhattan")
        self.heur_menu = ttk.Combobox(control_panel, textvariable=self.heur_var, values=["Manhattan", "Euclidean"], width=10)
        self.heur_menu.pack(side=tk.LEFT)

        # Controls
        self.dynamic_btn = tk.Button(control_panel, text="Dynamic: OFF", command=self.toggle_dynamic, bg="#ecf0f1")
        self.dynamic_btn.pack(side=tk.LEFT, padx=10)
        
        tk.Button(control_panel, text="START SEARCH", command=self.start_search, bg="#27ae60", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(control_panel, text="RESET", command=self.reset_agent).pack(side=tk.LEFT, padx=5)

        # Metrics
        self.metrics_frame = tk.Frame(self.root, pady=5, bg="#f8f9fa")
        self.metrics_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.nodes_label = tk.Label(self.metrics_frame, text="Nodes Visited: 0", bg="#f8f9fa")
        self.nodes_label.pack(side=tk.LEFT, padx=20)
        self.cost_label = tk.Label(self.metrics_frame, text="Path Cost: 0", bg="#f8f9fa")
        self.cost_label.pack(side=tk.LEFT, padx=20)
        self.time_label = tk.Label(self.metrics_frame, text="Time: 0ms", bg="#f8f9fa")
        self.time_label.pack(side=tk.LEFT, padx=20)

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.handle_click)
        self.canvas.bind("<B1-Motion>", self.handle_click)

    def init_grid(self):
        # Update canvas dimensions based on new rows/cols
        self.canvas.config(
            width=self.cols * self.cell_size,
            height=self.rows * self.cell_size
        )
        self.draw_grid()

    def update_grid_size(self):
        try:
            val = int(self.size_entry.get())
            if val < 5:
                messagebox.showwarning("Warning", "Size too small! Minimum is 5.")
                return
            
            self.rows = self.cols = val
            self.walls.clear()
            self.start_node = (1, 1)
            self.agent_pos = self.start_node
            self.goal_node = (val - 2, val - 2)
            
            self.init_grid()
            self.root.geometry("")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for grid size.")

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(self.rows):
            for c in range(self.cols):
                color = self.COLOR_EMPTY
                if (r, c) == self.start_node: color = self.COLOR_START
                elif (r, c) == self.goal_node: color = self.COLOR_GOAL
                elif (r, c) in self.walls: color = self.COLOR_WALL
                
                self.canvas.create_rectangle(
                    c*self.cell_size, r*self.cell_size,
                    (c+1)*self.cell_size, (r+1)*self.cell_size,
                    fill=color, outline="#dcdde1", tags=f"rect_{r}_{c}"
                )
        self.draw_agent()

    def draw_agent(self):
        r, c = self.agent_pos
        self.canvas.delete("agent")
        self.canvas.create_oval(
            c*self.cell_size+4, r*self.cell_size+4,
            (c+1)*self.cell_size-4, (r+1)*self.cell_size-4,
            fill=self.COLOR_AGENT, tags="agent"
        )

    def handle_click(self, event):
        c, r = event.x // self.cell_size, event.y // self.cell_size
        if 0 <= r < self.rows and 0 <= c < self.cols:
            node = (r, c)
            if node != self.start_node and node != self.goal_node:
                if node in self.walls: self.walls.remove(node)
                else: self.walls.add(node)
                self.draw_grid()

    def randomize_map(self):
        self.walls.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) != self.start_node and (r, c) != self.goal_node:
                    if random.random() < self.obstacle_density:
                        self.walls.add((r, c))
        self.draw_grid()

    def get_heuristic(self, a, b):
        (r1, c1), (r2, c2) = a, b
        if self.heur_var.get() == "Manhattan":
            return abs(r1 - r2) + abs(c1 - c2)
        else:
            return math.sqrt((r1 - r2)**2 + (c1 - c2)**2)

    def search(self, start):
        algo = self.algo_var.get()
        pq = []
        heapq.heappush(pq, (0, 0, start, []))
        visited = set()
        start_time = time.time()
        nodes_count = 0

        while pq:
            f, g, current, path = heapq.heappop(pq)
            if current in visited: continue
            visited.add(current)
            nodes_count += 1
            
            if current == self.goal_node:
                exec_time = (time.time() - start_time) * 1000
                return path + [current], nodes_count, g, exec_time

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dr, current[1] + dc)
                if 0 <= neighbor[0] < self.rows and 0 <= neighbor[1] < self.cols:
                    if neighbor not in self.walls and neighbor not in visited:
                        new_g = g + 1
                        h = self.get_heuristic(neighbor, self.goal_node)
                        priority = (new_g + h) if algo == "A*" else h
                        heapq.heappush(pq, (priority, new_g, neighbor, path + [current]))
                        
        return None, nodes_count, 0, 0

    def start_search(self):
        self.agent_pos = self.start_node
        self.current_path, nodes, cost, timer = self.search(self.agent_pos)
        
        if self.current_path:
            self.nodes_label.config(text=f"Nodes Visited: {nodes}")
            self.cost_label.config(text=f"Path Cost: {len(self.current_path)-1}")
            self.time_label.config(text=f"Time: {timer:.2f}ms")
            self.visualize_path()
            self.animate_agent()
        else:
            messagebox.showinfo("Fail", "No valid path found!")

    def draw_final_path(self):
        for r, c in self.current_path:
            if (r, c) != self.start_node and (r, c) != self.goal_node:
                self.canvas.itemconfig(f"rect_{r}_{c}", fill=self.COLOR_PATH)

    def visualize_path(self):
        for r, c in self.current_path:
            if (r, c) != self.start_node and (r, c) != self.goal_node:
                self.canvas.itemconfig(f"rect_{r}_{c}", fill=self.COLOR_PATH)

    def toggle_dynamic(self):
        self.dynamic_mode = not self.dynamic_mode
        self.dynamic_btn.config(text=f"Dynamic: {'ON' if self.dynamic_mode else 'OFF'}",
                                bg="#f39c12" if self.dynamic_mode else "#ecf0f1")

    def animate_agent(self):
        if not self.current_path: return
        
        self.agent_pos = self.current_path.pop(0)
        self.draw_agent()
        
        if self.agent_pos == self.goal_node:
            messagebox.showinfo("Success", "Goal Reached!")
            return

        if self.dynamic_mode:
            self.spawn_dynamic_obstacle()

        self.root.after(150, self.animate_agent)

    def spawn_dynamic_obstacle(self):
        if random.random() < 0.05:
            r, c = random.randint(0, self.rows-1), random.randint(0, self.cols-1)
            if (r, c) not in [self.agent_pos, self.goal_node, self.start_node]:
                self.walls.add((r, c))
                self.canvas.itemconfig(f"rect_{r}_{c}", fill=self.COLOR_WALL)
                
                if (r, c) in self.current_path:
                    print(f"Collision on path at ({r},{c})! Re-planning...")
                    new_path, nodes, cost, timer = self.search(self.agent_pos)
                    if new_path:
                        self.current_path = new_path[1:]
                        self.visualize_path()
                    else:
                        self.current_path = []
                        messagebox.showwarning("Blocked", "Path blocked by dynamic obstacle!")

    def reset_agent(self):
        self.agent_pos = self.start_node
        self.current_path = []
        self.draw_grid()

if __name__ == "__main__":
    root = tk.Tk()
    app = PathfinderApp(root)
    root.mainloop()