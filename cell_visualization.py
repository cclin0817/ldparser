#!/usr/bin/env python3
"""
LEF Pin Shape Visualizer

Visualizes standard cell pin shapes from LEF files with layer control.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import random
import re

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.lef_parser import LEFParser
except ImportError:
    print("Error: Cannot import LEFParser. Make sure src/lef_parser.py is available.")
    sys.exit(1)


class LEFVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("LEF Pin Shape Visualizer")
        self.root.geometry("1200x800")

        # Data storage
        self.lef_data = None
        self.current_cell = None
        self.layer_colors = {}
        self.layer_vars = {}
        self.pins_data = []

        # Visualization parameters
        self.canvas_width = 800
        self.canvas_height = 700
        self.margin = 50

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        """Create the main UI components"""
        # Top control panel
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # File selection
        ttk.Label(control_frame, text="LEF File:").pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(control_frame, text="No file loaded",
                                    relief=tk.SUNKEN, width=40)
        self.file_label.pack(side=tk.LEFT, padx=5)

        ttk.Button(control_frame, text="Load LEF",
                  command=self.load_lef_file).pack(side=tk.LEFT, padx=5)

        # Cell selection
        ttk.Label(control_frame, text="Cell:").pack(side=tk.LEFT, padx=5)
        self.cell_combo = ttk.Combobox(control_frame, width=25, state='readonly')
        self.cell_combo.pack(side=tk.LEFT, padx=5)
        self.cell_combo.bind('<<ComboboxSelected>>', self.on_cell_selected)

        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Layer controls
        left_panel = ttk.LabelFrame(content_frame, text="Layer Controls", padding="10")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Scrollable layer list
        layer_canvas = tk.Canvas(left_panel, width=250, height=600)
        layer_scrollbar = ttk.Scrollbar(left_panel, orient="vertical",
                                       command=layer_canvas.yview)
        self.layer_frame = ttk.Frame(layer_canvas)

        layer_canvas.configure(yscrollcommand=layer_scrollbar.set)
        layer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        layer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        layer_canvas_window = layer_canvas.create_window((0, 0),
                                                         window=self.layer_frame,
                                                         anchor='nw')

        def configure_scroll_region(event):
            layer_canvas.configure(scrollregion=layer_canvas.bbox("all"))

        self.layer_frame.bind("<Configure>", configure_scroll_region)

        # Buttons for layer control
        button_frame = ttk.Frame(left_panel)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Select All",
                  command=self.select_all_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Deselect All",
                  command=self.deselect_all_layers).pack(side=tk.LEFT, padx=2)

        # Right panel - Canvas for visualization
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(right_panel)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas = tk.Canvas(canvas_frame, bg='white',
                               xscrollcommand=h_scrollbar.set,
                               yscrollcommand=v_scrollbar.set,
                               scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        # Status bar
        self.status_label = ttk.Label(self.root, text="Ready",
                                      relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def load_lef_file(self):
        """Load and parse a LEF file"""
        filename = filedialog.askopenfilename(
            title="Select LEF File",
            filetypes=[("LEF files", "*.lef"), ("All files", "*.*")]
        )

        if not filename:
            return

        try:
            self.status_label.config(text=f"Loading {os.path.basename(filename)}...")
            self.root.update()

            # Parse LEF file
            parser = LEFParser()
            self.lef_data = parser.parse_file(filename)

            # Extract MACRO cells
            macro_cells = {}
            for block_name, block_list in self.lef_data['blocks'].items():
                if block_name.startswith('MACRO_'):
                    cell_name = block_name.replace('MACRO_', '')
                    macro_cells[cell_name] = block_list[0]

            if not macro_cells:
                messagebox.showwarning("No Cells", "No MACRO cells found in LEF file")
                self.status_label.config(text="Ready")
                return

            # Update UI
            self.file_label.config(text=os.path.basename(filename))
            self.cell_combo['values'] = sorted(macro_cells.keys())
            self.cell_combo.current(0)

            # Load first cell
            self.on_cell_selected(None)

            self.status_label.config(text=f"Loaded {len(macro_cells)} cells from {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load LEF file:\n{str(e)}")
            self.status_label.config(text="Error loading file")

    def on_cell_selected(self, event):
        """Handle cell selection from dropdown"""
        if not self.cell_combo.get():
            return

        cell_name = self.cell_combo.get()

        # Find the cell data
        block_name = f"MACRO_{cell_name}"
        if block_name not in self.lef_data['blocks']:
            return

        self.current_cell = self.lef_data['blocks'][block_name][0]

        # Extract pin data
        self.extract_pin_data()

        # Update layer controls
        self.update_layer_controls()

        # Draw the cell
        self.draw_cell()

        self.status_label.config(text=f"Displaying cell: {cell_name}")

    def extract_pin_data(self):
        """Extract pin geometry data from current cell"""
        self.pins_data = []

        if 'sub_blocks' not in self.current_cell:
            return

        if 'PIN' not in self.current_cell['sub_blocks']:
            return

        pins = self.current_cell['sub_blocks']['PIN']

        for pin in pins:
            pin_name = pin['name']
            pin_shapes = []

            # Check if pin has PORT sub-blocks
            if 'sub_blocks' in pin and 'PORT' in pin['sub_blocks']:
                ports = pin['sub_blocks']['PORT']

                for port in ports:
                    # Extract layer and shapes from content lines
                    shapes = self.parse_port_content(port['content_lines'])
                    pin_shapes.extend(shapes)

            if pin_shapes:
                self.pins_data.append({
                    'name': pin_name,
                    'shapes': pin_shapes
                })

    def parse_port_content(self, content_lines):
        """Parse PORT content to extract layer and geometry information"""
        shapes = []
        current_layer = None

        for line in content_lines:
            line = line.strip()
            if not line:
                continue

            # Check for LAYER statement
            if line.startswith('LAYER '):
                parts = line.split()
                if len(parts) >= 2:
                    current_layer = parts[1].rstrip(' ;')
                continue

            # Skip if no layer defined yet
            if not current_layer:
                continue

            # Parse RECT
            if line.startswith('RECT '):
                coords = self.extract_coordinates(line)
                if coords and len(coords) >= 4:
                    shapes.append({
                        'type': 'RECT',
                        'layer': current_layer,
                        'coords': coords[:4]
                    })

            # Parse POLYGON
            elif line.startswith('POLYGON '):
                coords = self.extract_coordinates(line)
                if coords and len(coords) >= 6:
                    shapes.append({
                        'type': 'POLYGON',
                        'layer': current_layer,
                        'coords': coords
                    })

            # Parse PATH
            elif line.startswith('PATH '):
                coords = self.extract_coordinates(line)
                if coords and len(coords) >= 4:
                    shapes.append({
                        'type': 'PATH',
                        'layer': current_layer,
                        'coords': coords
                    })

        return shapes

    def extract_coordinates(self, line):
        """Extract numeric coordinates from a line"""
        # Remove keywords and MASK information
        line = re.sub(r'RECT|POLYGON|PATH|MASK\s+\d+', '', line)

        # Find all numbers (including negative and decimals)
        numbers = re.findall(r'-?\d+\.?\d*', line)

        try:
            return [float(n) for n in numbers]
        except ValueError:
            return []

    def update_layer_controls(self):
        """Update layer checkboxes based on current cell"""
        # Clear existing checkboxes
        for widget in self.layer_frame.winfo_children():
            widget.destroy()

        self.layer_vars.clear()

        # Collect all unique layers from pins
        layers = set()
        for pin_data in self.pins_data:
            for shape in pin_data['shapes']:
                layers.add(shape['layer'])

        if not layers:
            ttk.Label(self.layer_frame, text="No layers found").pack()
            return

        # Assign random colors to layers
        for layer in sorted(layers):
            if layer not in self.layer_colors:
                self.layer_colors[layer] = self.random_color()

        # Create checkboxes
        for layer in sorted(layers):
            var = tk.BooleanVar(value=True)
            self.layer_vars[layer] = var

            frame = ttk.Frame(self.layer_frame)
            frame.pack(fill=tk.X, pady=2)

            cb = ttk.Checkbutton(frame, text=layer, variable=var,
                                command=self.draw_cell)
            cb.pack(side=tk.LEFT)

            # Color indicator
            color_label = tk.Label(frame, bg=self.layer_colors[layer],
                                  width=3, relief=tk.RAISED)
            color_label.pack(side=tk.RIGHT, padx=5)

    def random_color(self):
        """Generate a random color"""
        r = random.randint(50, 255)
        g = random.randint(50, 255)
        b = random.randint(50, 255)
        return f'#{r:02x}{g:02x}{b:02x}'

    def select_all_layers(self):
        """Select all layer checkboxes"""
        for var in self.layer_vars.values():
            var.set(True)
        self.draw_cell()

    def deselect_all_layers(self):
        """Deselect all layer checkboxes"""
        for var in self.layer_vars.values():
            var.set(False)
        self.draw_cell()

    def draw_cell(self):
        """Draw the current cell on canvas"""
        self.canvas.delete('all')

        if not self.pins_data:
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                                   text="No pin shapes to display",
                                   font=('Arial', 14))
            return

        # Calculate bounding box
        all_coords = []
        for pin_data in self.pins_data:
            for shape in pin_data['shapes']:
                layer = shape['layer']
                if layer in self.layer_vars and self.layer_vars[layer].get():
                    all_coords.extend(shape['coords'])

        if not all_coords:
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                                   text="No visible layers",
                                   font=('Arial', 14))
            return

        # Get bounds
        x_coords = [all_coords[i] for i in range(0, len(all_coords), 2)]
        y_coords = [all_coords[i] for i in range(1, len(all_coords), 2)]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # Calculate scale to fit canvas
        design_width = max_x - min_x
        design_height = max_y - min_y

        if design_width == 0 or design_height == 0:
            return

        available_width = self.canvas_width - 2 * self.margin
        available_height = self.canvas_height - 2 * self.margin

        scale_x = available_width / design_width
        scale_y = available_height / design_height
        self.scale = min(scale_x, scale_y)

        # Center the design
        self.offset_x = self.margin - min_x * self.scale
        self.offset_y = self.margin - min_y * self.scale

        # Draw pins
        for pin_data in self.pins_data:
            pin_name = pin_data['name']
            pin_center_x = 0
            pin_center_y = 0
            shape_count = 0

            for shape in pin_data['shapes']:
                layer = shape['layer']

                # Skip if layer is disabled
                if layer not in self.layer_vars or not self.layer_vars[layer].get():
                    continue

                color = self.layer_colors.get(layer, '#888888')

                if shape['type'] == 'RECT':
                    x1, y1, x2, y2 = shape['coords']
                    canvas_coords = self.to_canvas_coords([x1, y1, x2, y2])
                    self.canvas.create_rectangle(*canvas_coords,
                                                fill=color, outline='black', width=1)
                    pin_center_x += (canvas_coords[0] + canvas_coords[2]) / 2
                    pin_center_y += (canvas_coords[1] + canvas_coords[3]) / 2
                    shape_count += 1

                elif shape['type'] == 'POLYGON':
                    canvas_coords = self.to_canvas_coords(shape['coords'])
                    self.canvas.create_polygon(*canvas_coords,
                                              fill=color, outline='black', width=1)
                    # Calculate center
                    for i in range(0, len(canvas_coords), 2):
                        pin_center_x += canvas_coords[i]
                        pin_center_y += canvas_coords[i + 1]
                    shape_count += len(canvas_coords) // 2

                elif shape['type'] == 'PATH':
                    canvas_coords = self.to_canvas_coords(shape['coords'])
                    self.canvas.create_line(*canvas_coords,
                                           fill=color, width=3)
                    pin_center_x += (canvas_coords[0] + canvas_coords[-2]) / 2
                    pin_center_y += (canvas_coords[1] + canvas_coords[-1]) / 2
                    shape_count += 1

            # Draw pin name at center of shapes
            if shape_count > 0:
                pin_center_x /= shape_count
                pin_center_y /= shape_count
                self.canvas.create_text(pin_center_x, pin_center_y,
                                       text=pin_name, font=('Arial', 8, 'bold'),
                                       fill='blue')

    def to_canvas_coords(self, coords):
        """Convert design coordinates to canvas coordinates"""
        canvas_coords = []
        for i in range(0, len(coords), 2):
            x = coords[i] * self.scale + self.offset_x
            y = self.canvas_height - (coords[i + 1] * self.scale + self.offset_y)
            canvas_coords.extend([x, y])
        return canvas_coords


def main():
    root = tk.Tk()
    app = LEFVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
