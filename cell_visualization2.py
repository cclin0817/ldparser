#!/usr/bin/env python3
#!/usr/bin/env python3
"""
LEF Cell Pin Shape Visualizer

This program reads a LEF file and visualizes the pin shapes of standard cells.
Features:
- Select which cell to display from a dropdown
- Toggle layer visibility with checkboxes
- Display pin names on the shapes
- Random colors for each layer
- Zoom and pan capabilities
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
import random
import colorsys
from typing import Dict, List, Tuple, Any

# Add the src directory to path for LEF parser import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from lef_parser import LEFParser
except ImportError:
    # If running from different directory, try alternative import
    sys.path.insert(0, 'src')
    from lef_parser import LEFParser


class LEFPinVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("LEF Cell Pin Visualizer")
        self.root.geometry("1200x800")

        # Data storage
        self.lef_data = None
        self.current_cell = None
        self.layers = {}  # {layer_name: color}
        self.layer_vars = {}  # {layer_name: tk.BooleanVar}
        self.canvas_items = {}  # {layer_name: [canvas_item_ids]}
        self.pin_labels = []  # List of pin label canvas items

        # View parameters
        self.scale = 50  # pixels per micron
        self.offset_x = 100
        self.offset_y = 100

        # Colors
        self.layer_colors = {}
        self.color_index = 0

        # Setup UI
        self.setup_ui()

        # Bind mouse events for pan and zoom
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas.bind("<Button-4>", self.on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mouse_wheel)  # Linux

        self.last_x = 0
        self.last_y = 0

    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Control panel (left side)
        control_frame = ttk.Frame(main_frame, padding="5")
        control_frame.grid(row=0, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

        # File selection
        ttk.Label(control_frame, text="LEF File:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)

        file_frame = ttk.Frame(control_frame)
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)

        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_path_var, width=30)
        file_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(file_frame, text="Load", command=self.load_lef_file).pack(side=tk.LEFT, padx=(5, 0))

        # Cell selection
        ttk.Label(control_frame, text="Select Cell:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))

        self.cell_var = tk.StringVar()
        self.cell_combo = ttk.Combobox(control_frame, textvariable=self.cell_var, state="readonly", width=28)
        self.cell_combo.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        self.cell_combo.bind("<<ComboboxSelected>>", self.on_cell_selected)

        # Layer control
        ttk.Label(control_frame, text="Layer Control:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))

        # Create a frame with scrollbar for layer checkboxes
        layer_container = ttk.Frame(control_frame)
        layer_container.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        control_frame.rowconfigure(5, weight=1)

        # Scrollbar for layers
        layer_scrollbar = ttk.Scrollbar(layer_container, orient=tk.VERTICAL)
        layer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas for layer checkboxes
        self.layer_canvas = tk.Canvas(layer_container, yscrollcommand=layer_scrollbar.set, width=200)
        self.layer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        layer_scrollbar.config(command=self.layer_canvas.yview)

        # Frame inside canvas for checkboxes
        self.layer_frame = ttk.Frame(self.layer_canvas)
        self.layer_canvas_window = self.layer_canvas.create_window((0, 0), window=self.layer_frame, anchor="nw")

        # Zoom controls
        ttk.Label(control_frame, text="View Controls:", font=("Arial", 10, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))

        zoom_frame = ttk.Frame(control_frame)
        zoom_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Button(zoom_frame, text="Zoom In", command=self.zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Zoom Out", command=self.zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Fit", command=self.fit_to_view).pack(side=tk.LEFT, padx=2)
        ttk.Button(zoom_frame, text="Reset", command=self.reset_view).pack(side=tk.LEFT, padx=2)

        # Show pin names checkbox
        self.show_pin_names_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text="Show Pin Names",
                        variable=self.show_pin_names_var,
                        command=self.toggle_pin_names).grid(row=8, column=0, sticky=tk.W, pady=5)

        # Info label
        self.info_label = ttk.Label(control_frame, text="No file loaded", foreground="gray")
        self.info_label.grid(row=9, column=0, sticky=tk.W, pady=(10, 5))

        # Canvas for drawing (right side)
        canvas_frame = ttk.Frame(main_frame, relief=tk.SUNKEN, borderwidth=1)
        canvas_frame.grid(row=0, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))

        self.canvas = tk.Canvas(canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))

        self.status_label = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X)

    def browse_file(self):
        """Open file dialog to select LEF file"""
        filename = filedialog.askopenfilename(
            title="Select LEF file",
            filetypes=[("LEF files", "*.lef"), ("All files", "*.*")]
        )
        if filename:
            self.file_path_var.set(filename)

    def load_lef_file(self):
        """Load and parse the LEF file"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a LEF file first")
            return

        if not os.path.exists(file_path):
            messagebox.showerror("Error", f"File not found: {file_path}")
            return

        try:
            self.status_label.config(text="Loading LEF file...")
            self.root.update()

            # Parse LEF file
            parser = LEFParser()
            self.lef_data = parser.parse_file(file_path)

            # Extract cell names
            cell_names = []
            for block_name in self.lef_data['blocks'].keys():
                if block_name.startswith('MACRO_'):
                    cell_name = block_name.replace('MACRO_', '')
                    cell_names.append(cell_name)

            if not cell_names:
                messagebox.showwarning("Warning", "No MACRO definitions found in LEF file")
                return

            # Update cell combo box
            self.cell_combo['values'] = sorted(cell_names)
            self.cell_combo.set(cell_names[0])

            self.info_label.config(text=f"Loaded: {os.path.basename(file_path)}")
            self.status_label.config(text=f"Loaded {len(cell_names)} cells")

            # Automatically display first cell
            self.on_cell_selected()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load LEF file:\n{str(e)}")
            self.status_label.config(text="Error loading file")

    def on_cell_selected(self, event=None):
        """Handle cell selection"""
        cell_name = self.cell_var.get()
        if not cell_name or not self.lef_data:
            return

        self.current_cell = cell_name
        self.extract_layers_from_cell(cell_name)
        self.update_layer_checkboxes()
        self.draw_cell()

    def extract_layers_from_cell(self, cell_name):
        """Extract all layers used in the cell's pins"""
        self.layers.clear()

        macro_key = f"MACRO_{cell_name}"
        if macro_key not in self.lef_data['blocks']:
            return

        macro_block = self.lef_data['blocks'][macro_key][0]

        if 'sub_blocks' not in macro_block:
            return

        if 'PIN' not in macro_block['sub_blocks']:
            return

        # Extract layers from all pins
        for pin_block in macro_block['sub_blocks']['PIN']:
            if 'sub_blocks' in pin_block and 'PORT' in pin_block['sub_blocks']:
                for port_block in pin_block['sub_blocks']['PORT']:
                    for line in port_block['content_lines']:
                        if line.strip().startswith('LAYER '):
                            layer_name = line.strip().split()[1].rstrip(' ;')
                            if layer_name not in self.layers:
                                self.layers[layer_name] = self.get_random_color()

    def get_random_color(self):
        """Generate a random distinct color"""
        # Use HSV color space for better distribution
        hue = (self.color_index * 0.618033988749895) % 1  # Golden ratio
        saturation = 0.7 + (self.color_index % 3) * 0.1
        value = 0.7 + (self.color_index % 2) * 0.2

        self.color_index += 1

        rgb = colorsys.hsv_to_rgb(hue, saturation, value)
        return '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0] * 255),
            int(rgb[1] * 255),
            int(rgb[2] * 255)
        )

    def update_layer_checkboxes(self):
        """Update the layer control checkboxes"""
        # Clear existing checkboxes
        for widget in self.layer_frame.winfo_children():
            widget.destroy()

        self.layer_vars.clear()

        # Create new checkboxes
        for i, (layer_name, color) in enumerate(sorted(self.layers.items())):
            var = tk.BooleanVar(value=True)
            self.layer_vars[layer_name] = var

            frame = ttk.Frame(self.layer_frame)
            frame.grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)

            # Color indicator
            color_label = tk.Label(frame, text="■", foreground=color, font=("Arial", 14))
            color_label.pack(side=tk.LEFT, padx=(0, 5))

            # Checkbox
            cb = ttk.Checkbutton(frame, text=layer_name, variable=var,
                                command=lambda l=layer_name: self.toggle_layer(l))
            cb.pack(side=tk.LEFT)

        # Update scroll region
        self.layer_frame.update_idletasks()
        self.layer_canvas.config(scrollregion=self.layer_canvas.bbox("all"))

    def toggle_layer(self, layer_name):
        """Toggle visibility of a layer"""
        if layer_name not in self.canvas_items:
            return

        visible = self.layer_vars[layer_name].get()
        state = 'normal' if visible else 'hidden'

        for item_id in self.canvas_items[layer_name]:
            self.canvas.itemconfig(item_id, state=state)

    def toggle_pin_names(self):
        """Toggle visibility of pin names"""
        visible = self.show_pin_names_var.get()
        state = 'normal' if visible else 'hidden'

        for item_id in self.pin_labels:
            self.canvas.itemconfig(item_id, state=state)

    def draw_cell(self):
        """Draw the selected cell's pin shapes"""
        # Clear canvas
        self.canvas.delete("all")
        self.canvas_items.clear()
        self.pin_labels.clear()

        if not self.current_cell or not self.lef_data:
            return

        macro_key = f"MACRO_{self.current_cell}"
        if macro_key not in self.lef_data['blocks']:
            return

        macro_block = self.lef_data['blocks'][macro_key][0]

        # Get cell size for reference
        cell_width = 0
        cell_height = 0
        if 'size' in macro_block['attributes']:
            size = macro_block['attributes']['size']
            cell_width = size.get('width', 0)
            cell_height = size.get('height', 0)

        # Draw cell boundary (light gray)
        if cell_width > 0 and cell_height > 0:
            x1, y1 = self.transform_coords(0, 0)
            x2, y2 = self.transform_coords(cell_width, cell_height)
            self.canvas.create_rectangle(x1, y1, x2, y2,
                                        outline="lightgray", width=2, dash=(5, 5))

        if 'sub_blocks' not in macro_block or 'PIN' not in macro_block['sub_blocks']:
            return

        # Draw each pin
        for pin_block in macro_block['sub_blocks']['PIN']:
            pin_name = pin_block['name']

            if 'sub_blocks' in pin_block and 'PORT' in pin_block['sub_blocks']:
                self.draw_pin(pin_name, pin_block['sub_blocks']['PORT'])

        self.status_label.config(text=f"Displaying cell: {self.current_cell}")

    def draw_pin(self, pin_name, port_blocks):
        """Draw a single pin with all its ports"""
        for port_block in port_blocks:
            current_layer = None

            # Parse port geometry
            for line in port_block['content_lines']:
                line = line.strip()

                if line.startswith('LAYER '):
                    current_layer = line.split()[1].rstrip(' ;')
                    if current_layer not in self.canvas_items:
                        self.canvas_items[current_layer] = []

                elif line.startswith('RECT ') and current_layer:
                    # Parse rectangle
                    coords = self.parse_rect(line)
                    if coords:
                        self.draw_rectangle(current_layer, coords, pin_name)

                elif line.startswith('POLYGON ') and current_layer:
                    # Parse polygon
                    coords = self.parse_polygon(line)
                    if coords:
                        self.draw_polygon(current_layer, coords, pin_name)

                elif line.startswith('PATH ') and current_layer:
                    # Parse path
                    coords = self.parse_path(line)
                    if coords:
                        self.draw_path(current_layer, coords, pin_name)

    def parse_rect(self, line):
        """Parse RECT line and return coordinates"""
        import re
        # Remove RECT keyword and any MASK information
        line = re.sub(r'RECT\s+', '', line)
        line = re.sub(r'MASK\s+\d+\s+', '', line)
        line = re.sub(r'ITERATE.*DO.*STEP.*', '', line)
        line = line.rstrip(' ;')

        # Extract numbers
        numbers = re.findall(r'-?[\d.]+', line)
        if len(numbers) >= 4:
            return [float(n) for n in numbers[:4]]
        return None

    def parse_polygon(self, line):
        """Parse POLYGON line and return coordinates"""
        import re
        # Remove POLYGON keyword and any MASK information
        line = re.sub(r'POLYGON\s+', '', line)
        line = re.sub(r'MASK\s+\d+\s+', '', line)
        line = re.sub(r'ITERATE.*DO.*STEP.*', '', line)
        line = line.rstrip(' ;')

        # Extract numbers
        numbers = re.findall(r'-?[\d.]+', line)
        if len(numbers) >= 6:  # At least 3 points for a polygon
            coords = []
            for i in range(0, len(numbers), 2):
                if i + 1 < len(numbers):
                    coords.append((float(numbers[i]), float(numbers[i+1])))
            return coords
        return None

    def parse_path(self, line):
        """Parse PATH line and return coordinates"""
        import re
        # Remove PATH keyword and any MASK/ITERATE information
        line = re.sub(r'PATH\s+', '', line)
        line = re.sub(r'MASK\s+\d+\s+', '', line)
        line = re.sub(r'ITERATE.*DO.*STEP.*', '', line)
        line = line.rstrip(' ;')

        # Extract numbers
        numbers = re.findall(r'-?[\d.]+', line)
        if len(numbers) >= 4:  # At least 2 points for a path
            return [float(n) for n in numbers[:4]]
        return None

    def draw_rectangle(self, layer_name, coords, pin_name):
        """Draw a rectangle on the canvas"""
        x1, y1, x2, y2 = coords
        x1, y1 = self.transform_coords(x1, y1)
        x2, y2 = self.transform_coords(x2, y2)

        color = self.layers.get(layer_name, "black")

        item_id = self.canvas.create_rectangle(x1, y1, x2, y2,
                                              outline=color, fill="", width=2)
        self.canvas_items[layer_name].append(item_id)

        # Add pin name label at center
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        label_id = self.canvas.create_text(cx, cy, text=pin_name,
                                          fill="black", font=("Arial", 8))
        self.pin_labels.append(label_id)

    def draw_polygon(self, layer_name, coords, pin_name):
        """Draw a polygon on the canvas"""
        points = []
        for x, y in coords:
            tx, ty = self.transform_coords(x, y)
            points.extend([tx, ty])

        if len(points) >= 6:  # At least 3 points
            color = self.layers.get(layer_name, "black")

            item_id = self.canvas.create_polygon(points,
                                                outline=color, fill="", width=2)
            self.canvas_items[layer_name].append(item_id)

            # Add pin name label at centroid
            cx = sum(points[::2]) / len(coords)
            cy = sum(points[1::2]) / len(coords)
            label_id = self.canvas.create_text(cx, cy, text=pin_name,
                                              fill="black", font=("Arial", 8))
            self.pin_labels.append(label_id)

    def draw_path(self, layer_name, coords, pin_name):
        """Draw a path (line) on the canvas"""
        x1, y1, x2, y2 = coords
        x1, y1 = self.transform_coords(x1, y1)
        x2, y2 = self.transform_coords(x2, y2)

        color = self.layers.get(layer_name, "black")

        item_id = self.canvas.create_line(x1, y1, x2, y2,
                                        fill=color, width=3)
        self.canvas_items[layer_name].append(item_id)

        # Add pin name label at center
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        label_id = self.canvas.create_text(cx, cy, text=pin_name,
                                          fill="black", font=("Arial", 8))
        self.pin_labels.append(label_id)

    def transform_coords(self, x, y):
        """Transform LEF coordinates to canvas coordinates"""
        # LEF uses bottom-left origin, canvas uses top-left
        # Also apply scaling and offset
        canvas_x = x * self.scale + self.offset_x
        canvas_y = self.canvas.winfo_height() - (y * self.scale) - self.offset_y
        return canvas_x, canvas_y

    def zoom_in(self):
        """Zoom in the view"""
        self.scale *= 1.2
        self.draw_cell()

    def zoom_out(self):
        """Zoom out the view"""
        self.scale /= 1.2
        self.draw_cell()

    def fit_to_view(self):
        """Fit the cell to the canvas view"""
        if not self.current_cell or not self.lef_data:
            return

        macro_key = f"MACRO_{self.current_cell}"
        if macro_key not in self.lef_data['blocks']:
            return

        macro_block = self.lef_data['blocks'][macro_key][0]

        # Get cell size
        if 'size' in macro_block['attributes']:
            size = macro_block['attributes']['size']
            cell_width = size.get('width', 100)
            cell_height = size.get('height', 100)

            # Calculate scale to fit
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width > 100 and canvas_height > 100:
                scale_x = (canvas_width - 200) / cell_width
                scale_y = (canvas_height - 200) / cell_height
                self.scale = min(scale_x, scale_y)

                # Center the cell
                self.offset_x = (canvas_width - cell_width * self.scale) / 2
                self.offset_y = (canvas_height - cell_height * self.scale) / 2

                self.draw_cell()

    def reset_view(self):
        """Reset view to default"""
        self.scale = 50
        self.offset_x = 100
        self.offset_y = 100
        self.draw_cell()

    def on_mouse_down(self, event):
        """Handle mouse down for panning"""
        self.last_x = event.x
        self.last_y = event.y

    def on_mouse_drag(self, event):
        """Handle mouse drag for panning"""
        dx = event.x - self.last_x
        dy = event.y - self.last_y

        self.offset_x += dx
        self.offset_y -= dy  # Inverted for y

        self.last_x = event.x
        self.last_y = event.y

        self.draw_cell()

    def on_mouse_wheel(self, event):
        """Handle mouse wheel for zooming"""
        # Get mouse position relative to canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Zoom
        if event.delta > 0 or event.num == 4:
            scale_factor = 1.1
        else:
            scale_factor = 0.9

        self.scale *= scale_factor

        # Adjust offset to zoom toward mouse position
        self.offset_x = x - (x - self.offset_x) * scale_factor
        self.offset_y = y - (y - self.offset_y) * scale_factor

        self.draw_cell()


def main():
    """Main function"""
    root = tk.Tk()
    app = LEFPinVisualizer(root)

    # If a LEF file is provided as command line argument, load it
    if len(sys.argv) > 1:
        lef_file = sys.argv[1]
        if os.path.exists(lef_file):
            app.file_path_var.set(lef_file)
            app.load_lef_file()

    root.mainloop()


if __name__ == "__main__":
    main()
