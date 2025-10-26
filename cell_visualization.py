#!/usr/bin/env python3
"""
LEF Pin Shape Visualizer with Pin Selection

CHANGES ADDED:
- Pin selection section in left panel (below layer controls)
- Checkboxes to select/deselect individual pins
- "Select All Pins" / "Deselect All Pins" buttons
- Combined filtering: shows only selected pins on selected layers
- Unselected pins are hidden completely
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
        self.layer_stipples = {}
        self.pin_vars = {}  # NEW: Track pin selection states
        self.pins_data = []
        self.cell_size = None
        self.cell_origin = None

        # Visualization parameters
        self.canvas_width = 800
        self.canvas_height = 700
        self.margin = 50

        # Available stipple patterns for random assignment
        self.available_stipples = ['gray12', 'gray25', 'gray50', 'gray75']

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

        # Left panel - Layer and Pin controls
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # === LAYER CONTROLS SECTION ===
        layer_panel = ttk.LabelFrame(left_panel, text="Layer Controls", padding="10")
        layer_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 5))

        # Scrollable layer list
        layer_canvas = tk.Canvas(layer_panel, width=250, height=300)
        layer_scrollbar = ttk.Scrollbar(layer_panel, orient="vertical",
                                       command=layer_canvas.yview)
        self.layer_frame = ttk.Frame(layer_canvas)

        layer_canvas.configure(yscrollcommand=layer_scrollbar.set)
        layer_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        layer_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        layer_canvas_window = layer_canvas.create_window((0, 0),
                                                         window=self.layer_frame,
                                                         anchor='nw')

        def configure_layer_scroll_region(event):
            layer_canvas.configure(scrollregion=layer_canvas.bbox("all"))

        self.layer_frame.bind("<Configure>", configure_layer_scroll_region)

        # Buttons for layer control
        layer_button_frame = ttk.Frame(layer_panel)
        layer_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(layer_button_frame, text="Select All",
                  command=self.select_all_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(layer_button_frame, text="Deselect All",
                  command=self.deselect_all_layers).pack(side=tk.LEFT, padx=2)
        ttk.Button(layer_button_frame, text="Pin Info",
                  command=self.show_pin_info_dialog).pack(side=tk.LEFT, padx=2)

        # === NEW: PIN SELECTION SECTION ===
        pin_panel = ttk.LabelFrame(left_panel, text="Pin Selection", padding="10")
        pin_panel.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Scrollable pin list
        pin_canvas = tk.Canvas(pin_panel, width=250, height=300)
        pin_scrollbar = ttk.Scrollbar(pin_panel, orient="vertical",
                                     command=pin_canvas.yview)
        self.pin_frame = ttk.Frame(pin_canvas)

        pin_canvas.configure(yscrollcommand=pin_scrollbar.set)
        pin_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        pin_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        pin_canvas_window = pin_canvas.create_window((0, 0),
                                                     window=self.pin_frame,
                                                     anchor='nw')

        def configure_pin_scroll_region(event):
            pin_canvas.configure(scrollregion=pin_canvas.bbox("all"))

        self.pin_frame.bind("<Configure>", configure_pin_scroll_region)

        # Buttons for pin control
        pin_button_frame = ttk.Frame(pin_panel)
        pin_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        ttk.Button(pin_button_frame, text="Select All Pins",
                  command=self.select_all_pins).pack(side=tk.LEFT, padx=2)
        ttk.Button(pin_button_frame, text="Deselect All Pins",
                  command=self.deselect_all_pins).pack(side=tk.LEFT, padx=2)

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

        # Extract cell size and origin
        self.extract_cell_info()

        # Extract pin data
        self.extract_pin_data()

        # Update layer controls
        self.update_layer_controls()

        # NEW: Update pin controls
        self.update_pin_controls()

        # Draw the cell
        self.draw_cell()

        origin_text = f" (Origin: {self.cell_origin})" if self.cell_origin else ""
        self.status_label.config(text=f"Displaying cell: {cell_name}{origin_text}")

    def extract_cell_info(self):
        """Extract cell size and origin from SIZE and ORIGIN attributes"""
        self.cell_size = None
        self.cell_origin = None

        if 'attributes' not in self.current_cell:
            return

        # Extract SIZE
        if 'size' in self.current_cell['attributes']:
            size_info = self.current_cell['attributes']['size']
            if isinstance(size_info, dict) and 'width' in size_info and 'height' in size_info:
                self.cell_size = (size_info['width'], size_info['height'])

        # Extract ORIGIN from content_lines
        if 'content_lines' in self.current_cell:
            for line in self.current_cell['content_lines']:
                if line.startswith('ORIGIN '):
                    coords = self.extract_coordinates(line)
                    if coords and len(coords) >= 2:
                        self.cell_origin = (coords[0], coords[1])

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

        # Assign random colors and stipple patterns to layers
        for layer in sorted(layers):
            if layer not in self.layer_colors:
                self.layer_colors[layer] = self.random_color()

            # Assign random stipple pattern if not already assigned
            if layer not in self.layer_stipples:
                self.layer_stipples[layer] = random.choice(self.available_stipples)

        # Create checkboxes
        for layer in sorted(layers):
            var = tk.BooleanVar(value=True)
            self.layer_vars[layer] = var

            frame = ttk.Frame(self.layer_frame)
            frame.pack(fill=tk.X, pady=2)

            cb = ttk.Checkbutton(frame, text=f"{layer} ({self.layer_stipples[layer]})",
                                variable=var,
                                command=self.draw_cell)
            cb.pack(side=tk.LEFT)

            # Color indicator with stipple pattern
            color_canvas = tk.Canvas(frame, width=30, height=15,
                                    highlightthickness=1, highlightbackground='black')
            color_canvas.pack(side=tk.RIGHT, padx=5)
            color_canvas.create_rectangle(0, 0, 30, 15,
                                         fill=self.layer_colors[layer],
                                         stipple=self.layer_stipples[layer],
                                         outline='black')

    # NEW: Update pin controls
    def update_pin_controls(self):
        """Update pin checkboxes based on current cell"""
        # Clear existing checkboxes
        for widget in self.pin_frame.winfo_children():
            widget.destroy()

        self.pin_vars.clear()

        if not self.pins_data:
            ttk.Label(self.pin_frame, text="No pins found").pack()
            return

        # Create checkboxes for each pin (default: all selected)
        for pin_data in self.pins_data:
            pin_name = pin_data['name']
            var = tk.BooleanVar(value=True)  # Default: show all pins
            self.pin_vars[pin_name] = var

            frame = ttk.Frame(self.pin_frame)
            frame.pack(fill=tk.X, pady=2)

            cb = ttk.Checkbutton(frame, text=pin_name,
                                variable=var,
                                command=self.draw_cell)
            cb.pack(side=tk.LEFT)

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

    # NEW: Pin selection methods
    def select_all_pins(self):
        """Select all pin checkboxes"""
        for var in self.pin_vars.values():
            var.set(True)
        self.draw_cell()

    def deselect_all_pins(self):
        """Deselect all pin checkboxes"""
        for var in self.pin_vars.values():
            var.set(False)
        self.draw_cell()

    def get_pin_shape_info(self, pin_name=None):
        """Get pin shape information for the current cell"""
        if not self.pins_data:
            return None

        if pin_name:
            for pin_data in self.pins_data:
                if pin_data['name'] == pin_name:
                    return pin_data
            return None
        else:
            return self.pins_data

    def get_all_pin_names(self):
        """Get list of all pin names in current cell"""
        return [pin['name'] for pin in self.pins_data]

    def get_pin_layers(self, pin_name):
        """Get all layers used by a specific pin"""
        pin_data = self.get_pin_shape_info(pin_name)
        if not pin_data:
            return []

        layers = set()
        for shape in pin_data['shapes']:
            layers.add(shape['layer'])
        return sorted(list(layers))

    def get_pin_bounding_box(self, pin_name):
        """Get bounding box for a specific pin"""
        pin_data = self.get_pin_shape_info(pin_name)
        if not pin_data or not pin_data['shapes']:
            return None

        all_coords = []
        for shape in pin_data['shapes']:
            all_coords.extend(shape['coords'])

        x_coords = [all_coords[i] for i in range(0, len(all_coords), 2)]
        y_coords = [all_coords[i] for i in range(1, len(all_coords), 2)]

        return (min(x_coords), min(y_coords), max(x_coords), max(y_coords))

    def print_pin_info(self, pin_name=None):
        """Print detailed pin shape information to console"""
        if pin_name:
            pin_data = self.get_pin_shape_info(pin_name)
            if not pin_data:
                print(f"Pin '{pin_name}' not found")
                return
            pins_to_print = [pin_data]
        else:
            pins_to_print = self.pins_data

        for pin in pins_to_print:
            print(f"\n{'='*60}")
            print(f"PIN: {pin['name']}")
            print(f"{'='*60}")
            print(f"Number of shapes: {len(pin['shapes'])}")

            for i, shape in enumerate(pin['shapes'], 1):
                print(f"\n  Shape {i}:")
                print(f"    Type: {shape['type']}")
                print(f"    Layer: {shape['layer']}")
                print(f"    Coordinates: {shape['coords']}")

                if shape['type'] == 'RECT' and len(shape['coords']) >= 4:
                    x1, y1, x2, y2 = shape['coords'][:4]
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    print(f"    Width: {width:.2f}, Height: {height:.2f}")
                    print(f"    Area: {width * height:.2f}")

            bbox = self.get_pin_bounding_box(pin['name'])
            if bbox:
                min_x, min_y, max_x, max_y = bbox
                print(f"\n  Bounding Box:")
                print(f"    ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})")
                print(f"    Total span: {max_x - min_x:.2f} x {max_y - min_y:.2f}")

    def export_pin_shapes_to_dict(self):
        """Export all pin shape information to a Python dictionary"""
        if not self.current_cell:
            return None

        export_data = {
            'cell_name': self.current_cell.get('name', 'Unknown'),
            'cell_size': self.cell_size,
            'cell_origin': self.cell_origin,
            'pins': {}
        }

        for pin_data in self.pins_data:
            pin_name = pin_data['name']
            export_data['pins'][pin_name] = {
                'shapes': pin_data['shapes'],
                'layers': self.get_pin_layers(pin_name),
                'bounding_box': self.get_pin_bounding_box(pin_name)
            }

        return export_data

    def show_pin_info_dialog(self):
        """Show a dialog with pin information"""
        if not self.pins_data:
            messagebox.showinfo("No Data", "No pin data available. Please load a cell first.")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Pin Shape Information")
        dialog.geometry("700x500")

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        selection_frame = ttk.Frame(main_frame)
        selection_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(selection_frame, text="Select Pin:").pack(side=tk.LEFT, padx=5)
        pin_var = tk.StringVar()
        pin_names = self.get_all_pin_names()
        pin_combo = ttk.Combobox(selection_frame, textvariable=pin_var,
                                 values=pin_names, state='readonly', width=20)
        pin_combo.pack(side=tk.LEFT, padx=5)
        if pin_names:
            pin_combo.current(0)

        ttk.Button(selection_frame, text="Show All Pins",
                  command=lambda: self.update_pin_text(text_widget, None)).pack(side=tk.LEFT, padx=5)

        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget = tk.Text(text_frame, wrap=tk.WORD,
                             yscrollcommand=scrollbar.set,
                             font=('Courier', 9))
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)

        def update_info():
            selected_pin = pin_var.get()
            self.update_pin_text(text_widget, selected_pin)

        ttk.Button(selection_frame, text="Show Selected Pin",
                  command=update_info).pack(side=tk.LEFT, padx=5)

        ttk.Button(selection_frame, text="Export to Console",
                  command=lambda: self.print_pin_info(pin_var.get() if pin_var.get() else None)).pack(side=tk.LEFT, padx=5)

        update_info()

    def update_pin_text(self, text_widget, pin_name):
        """Update text widget with pin information"""
        text_widget.delete(1.0, tk.END)

        if pin_name:
            pin_data = self.get_pin_shape_info(pin_name)
            if not pin_data:
                text_widget.insert(tk.END, f"Pin '{pin_name}' not found")
                return
            pins_to_show = [pin_data]
        else:
            pins_to_show = self.pins_data

        for pin in pins_to_show:
            text_widget.insert(tk.END, f"{'='*60}\n")
            text_widget.insert(tk.END, f"PIN: {pin['name']}\n")
            text_widget.insert(tk.END, f"{'='*60}\n")
            text_widget.insert(tk.END, f"Number of shapes: {len(pin['shapes'])}\n")
            text_widget.insert(tk.END, f"Layers used: {', '.join(self.get_pin_layers(pin['name']))}\n")

            for i, shape in enumerate(pin['shapes'], 1):
                text_widget.insert(tk.END, f"\n  Shape {i}:\n")
                text_widget.insert(tk.END, f"    Type: {shape['type']}\n")
                text_widget.insert(tk.END, f"    Layer: {shape['layer']}\n")
                text_widget.insert(tk.END, f"    Coordinates: {shape['coords']}\n")

                if shape['type'] == 'RECT' and len(shape['coords']) >= 4:
                    x1, y1, x2, y2 = shape['coords'][:4]
                    width = abs(x2 - x1)
                    height = abs(y2 - y1)
                    text_widget.insert(tk.END, f"    Width: {width:.2f}, Height: {height:.2f}\n")
                    text_widget.insert(tk.END, f"    Area: {width * height:.2f}\n")

            bbox = self.get_pin_bounding_box(pin['name'])
            if bbox:
                min_x, min_y, max_x, max_y = bbox
                text_widget.insert(tk.END, f"\n  Bounding Box:\n")
                text_widget.insert(tk.END, f"    ({min_x:.2f}, {min_y:.2f}) to ({max_x:.2f}, {max_y:.2f})\n")
                text_widget.insert(tk.END, f"    Total span: {max_x - min_x:.2f} x {max_y - min_y:.2f}\n")

            text_widget.insert(tk.END, "\n\n")

    def draw_cell(self):
        """Draw the current cell on canvas - MODIFIED to filter by pin selection"""
        self.canvas.delete('all')

        if not self.pins_data:
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                                   text="No pin shapes to display",
                                   font=('Arial', 14))
            return

        # Calculate bounding box (only from visible elements)
        all_coords = []
        for pin_data in self.pins_data:
            pin_name = pin_data['name']

            # NEW: Check if pin is selected
            if pin_name in self.pin_vars and not self.pin_vars[pin_name].get():
                continue  # Skip unselected pins

            for shape in pin_data['shapes']:
                layer = shape['layer']
                if layer in self.layer_vars and self.layer_vars[layer].get():
                    all_coords.extend(shape['coords'])

        # Include cell boundary in bounding box if available
        if self.cell_size:
            width, height = self.cell_size
            if self.cell_origin:
                origin_x, origin_y = self.cell_origin
                all_coords.extend([
                    -origin_x, -origin_y,
                    width - origin_x, height - origin_y
                ])
            else:
                all_coords.extend([0, 0, width, height])

        if not all_coords:
            self.canvas.create_text(self.canvas_width // 2, self.canvas_height // 2,
                                   text="No visible layers or pins",
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

        # Draw cell boundary first (if available)
        if self.cell_size:
            self.draw_cell_boundary()

        # Draw pins - MODIFIED to check pin selection
        for pin_data in self.pins_data:
            pin_name = pin_data['name']

            # NEW: Skip if pin is not selected
            if pin_name in self.pin_vars and not self.pin_vars[pin_name].get():
                continue

            for shape in pin_data['shapes']:
                layer = shape['layer']

                # Skip if layer is disabled
                if layer not in self.layer_vars or not self.layer_vars[layer].get():
                    continue

                color = self.layer_colors.get(layer, '#888888')
                stipple = self.layer_stipples.get(layer, 'gray25')

                shape_center_x = None
                shape_center_y = None

                if shape['type'] == 'RECT':
                    x1, y1, x2, y2 = shape['coords']
                    canvas_coords = self.to_canvas_coords([x1, y1, x2, y2])
                    self.canvas.create_rectangle(*canvas_coords,
                                                fill=color,
                                                stipple=stipple,
                                                outline='black',
                                                width=1)
                    shape_center_x = (canvas_coords[0] + canvas_coords[2]) / 2
                    shape_center_y = (canvas_coords[1] + canvas_coords[3]) / 2

                elif shape['type'] == 'POLYGON':
                    canvas_coords = self.to_canvas_coords(shape['coords'])
                    self.canvas.create_polygon(*canvas_coords,
                                              fill=color,
                                              stipple=stipple,
                                              outline='black',
                                              width=1)
                    x_sum = sum(canvas_coords[i] for i in range(0, len(canvas_coords), 2))
                    y_sum = sum(canvas_coords[i] for i in range(1, len(canvas_coords), 2))
                    num_points = len(canvas_coords) // 2
                    shape_center_x = x_sum / num_points
                    shape_center_y = y_sum / num_points

                elif shape['type'] == 'PATH':
                    canvas_coords = self.to_canvas_coords(shape['coords'])
                    self.canvas.create_line(*canvas_coords,
                                           fill=color,
                                           width=3)
                    shape_center_x = (canvas_coords[0] + canvas_coords[-2]) / 2
                    shape_center_y = (canvas_coords[1] + canvas_coords[-1]) / 2

                # Draw pin name at shape's center
                if shape_center_x is not None and shape_center_y is not None:
                    text_bbox = self.canvas.create_text(shape_center_x, shape_center_y,
                                           text=pin_name, font=('Arial', 8, 'bold'),
                                           fill='blue')
                    bbox = self.canvas.bbox(text_bbox)
                    if bbox:
                        self.canvas.create_rectangle(bbox[0]-2, bbox[1]-1, bbox[2]+2, bbox[3]+1,
                                                     fill='white', outline='')
                        self.canvas.create_text(shape_center_x, shape_center_y,
                                               text=pin_name, font=('Arial', 8, 'bold'),
                                               fill='blue')

    def draw_cell_boundary(self):
        """Draw the cell boundary rectangle with dimensions"""
        if not self.cell_size:
            return

        width, height = self.cell_size

        if self.cell_origin:
            origin_x, origin_y = self.cell_origin
            x_min = -origin_x
            y_min = -origin_y
            x_max = width - origin_x
            y_max = height - origin_y
        else:
            x_min = 0
            y_min = 0
            x_max = width
            y_max = height

        boundary_coords = self.to_canvas_coords([x_min, y_min, x_max, y_max])
        x1, y1, x2, y2 = boundary_coords

        self.canvas.create_rectangle(x1, y1, x2, y2,
                                     outline='red',
                                     width=2,
                                     dash=(10, 5))

        # Width dimension
        mid_x = (x1 + x2) / 2
        self.canvas.create_line(x1, y2 + 15, x2, y2 + 15,
                               fill='red', width=1, arrow=tk.BOTH)
        self.canvas.create_text(mid_x, y2 + 25,
                               text=f"W: {width:.2f}",
                               font=('Arial', 10, 'bold'),
                               fill='red')

        # Height dimension
        mid_y = (y1 + y2) / 2
        self.canvas.create_line(x2 + 15, y1, x2 + 15, y2,
                               fill='red', width=1, arrow=tk.BOTH)
        self.canvas.create_text(x2 + 40, mid_y,
                               text=f"H: {height:.2f}",
                               font=('Arial', 10, 'bold'),
                               fill='red',
                               angle=270)

        # Corner labels
        self.canvas.create_text(x1 - 30, y1 - 10,
                               text=f"({x_min:.1f},{y_min:.1f})",
                               font=('Arial', 8),
                               fill='red')
        self.canvas.create_text(x2 + 30, y2 + 10,
                               text=f"({x_max:.1f},{y_max:.1f})",
                               font=('Arial', 8),
                               fill='red')

        # Origin marker
        if self.cell_origin and (self.cell_origin[0] != 0 or self.cell_origin[1] != 0):
            origin_canvas = self.to_canvas_coords([0, 0])
            ox, oy = origin_canvas[0], origin_canvas[1]

            self.canvas.create_line(ox - 10, oy, ox + 10, oy,
                                   fill='blue', width=2)
            self.canvas.create_line(ox, oy - 10, ox, oy + 10,
                                   fill='blue', width=2)
            self.canvas.create_text(ox + 15, oy - 15,
                                   text="ORIGIN (0,0)",
                                   font=('Arial', 9, 'bold'),
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


if __name__ == "__main__":
    # Run GUI
    main()

    # Uncomment below to run programmatic example instead:
    # example_programmatic_access()

