# DEF (Design Exchange Format) Introduction

## Overview

The Design Exchange Format (DEF) is a standard file format used in electronic design automation (EDA) for representing the physical layout and connectivity of integrated circuits. This document provides an introduction to each section of a DEF file based on the `complete.5.8.def` example.

## File Structure

A DEF file consists of multiple sections that define different aspects of a chip design. Each section serves a specific purpose in describing the physical implementation of the circuit.

## Sections Overview

### 1. Header Information

```def
VERSION 5.8 ;
NAMESCASESENSITIVE ON ;
DIVIDERCHAR "/" ;
BUSBITCHARS "[]" ;
DESIGN design ;
TECHNOLOGY technology ;
UNITS DISTANCE MICRONS 1000 ;
```

**Purpose**: Defines basic file format information and design metadata.

- `VERSION`: Specifies the DEF format version
- `NAMESCASESENSITIVE`: Controls case sensitivity for names
- `DIVIDERCHAR`: Character used for hierarchical name separation
- `BUSBITCHARS`: Characters used for bus bit notation
- `DESIGN`: Name of the design
- `TECHNOLOGY`: Technology library reference
- `UNITS`: Defines the unit system (database units per micron)

### 2. PROPERTYDEFINITIONS Section

**Purpose**: Defines custom properties that can be attached to various design objects.

Properties can be defined for:
- `DESIGN`: Design-level properties
- `REGION`: Region properties
- `GROUP`: Group properties
- `COMPONENT`: Component/cell properties
- `NET`: Net properties
- `SPECIALNET`: Special net properties
- `ROW`: Row properties
- `COMPONENTPIN`: Component pin properties
- `NONDEFAULTRULE`: Non-default rule properties

Each property has a type (`STRING`, `INTEGER`, `REAL`) and optional range constraints.

### 3. DIEAREA Section

```def
DIEAREA ( -190000 -120000 ) ( -190000 350000 ) ( 190000 350000 )
        ( 190000 190000 ) ( 190360 190000 ) ( 190360 -120000 ) ;
```

**Purpose**: Defines the boundary of the die area as a polygon with coordinate points.

### 4. ROW Section

**Purpose**: Defines placement rows where standard cells can be placed.

Key attributes:
- Row name and type (`CORE`, `ARRAYSITE`)
- Origin coordinates and orientation
- Repetition pattern (`DO numX BY numY STEP stepX stepY`)
- Optional properties

### 5. TRACKS Section

**Purpose**: Defines routing tracks for different metal layers.

```def
TRACKS Y 52 DO 857 STEP 104 MASK 1 ;
TRACKS X 52 DO 1720 STEP 104 MASK 2 LAYER M2 ;
```

- Direction (`X` or `Y`)
- Starting position
- Number of tracks and spacing
- Optional mask and layer information

### 6. GCELLGRID Section

**Purpose**: Defines the global routing grid used by the router.

```def
GCELLGRID X 0 DO 100 STEP 600 ;
GCELLGRID Y 10 DO 120 STEP 400 ;
```

### 7. VIAS Section

**Purpose**: Defines via structures used for inter-layer connections.

Via definitions include:
- Via name
- Pattern name (optional)
- Layer rectangles and polygons
- Mask information
- Via rules and parameters

Types of via definitions:
- Explicit geometry (`RECT`, `POLYGON`)
- Rule-based (`VIARULE`, `CUTSIZE`, `ENCLOSURE`)

### 8. STYLES Section

**Purpose**: Defines polygon styles for routing shapes.

```def
STYLES 10 ;
- STYLE 0 ( 30 10 ) ( 10 30 ) ( -10 30 ) ( -30 10 ) ( -30 -10 ) ( -10 -30 ) ( 10 -30 ) ( 30 -10 ) ;
```

Each style defines a polygon shape by its vertices.

### 9. NONDEFAULTRULES Section

**Purpose**: Defines non-default routing rules that override standard design rules.

Features:
- Layer-specific width and spacing rules
- Via definitions
- Wire extension rules
- Minimum cut requirements
- Properties

### 10. REGIONS Section

**Purpose**: Defines logical regions within the design.

```def
REGIONS 2 ;
- region1 ( -500 -500 ) ( 300 100 ) ( 500 500 ) ( 1000 1000 )
  + TYPE FENCE
```

Region types:
- `FENCE`: Hard boundary
- `GUIDE`: Soft guidance

### 11. COMPONENTS Section

**Purpose**: Defines all component instances (cells) in the design.

Key information per component:
- Component name and master cell reference
- Placement status (`PLACED`, `FIXED`, `COVER`, `UNPLACED`)
- Location and orientation
- Special attributes (`SOURCE`, `WEIGHT`, `REGION`)
- Properties

Placement orientations: `N`, `S`, `E`, `W`, `FN`, `FS`, `FE`, `FW`

### 12. PINS Section

**Purpose**: Defines the design's external pins/ports.

Pin definitions include:
- Pin name and connected net
- Direction (`INPUT`, `OUTPUT`, `INOUT`, `FEEDTHRU`)
- Usage (`SIGNAL`, `POWER`, `GROUND`, `CLOCK`, `ANALOG`, `SCAN`, `RESET`)
- Physical geometry (layers, shapes)
- Placement information
- Antenna information

### 13. PINPROPERTIES Section

**Purpose**: Assigns properties to specific pins (either design pins or component pins).

### 14. BLOCKAGES Section

**Purpose**: Defines areas where routing or placement is restricted.

Types of blockages:
- `LAYER`: Routing blockages on specific layers
- `PLACEMENT`: Placement blockages

Blockage modifiers:
- `SLOTS`: Allows slots but blocks routing
- `FILLS`: Allows fills but blocks routing
- `PUSHDOWN`: Applies to lower levels of hierarchy
- `COMPONENT`: Component-specific blockages

### 15. SPECIALNETS Section

**Purpose**: Defines special nets (typically power and ground networks).

Features:
- Net connectivity
- Routing geometry with shapes
- Shield nets
- Voltage and current specifications
- Advanced routing options

Routing shapes include: `RING`, `STRIPE`, `FOLLOWPIN`, `IOWIRE`, `COREWIRE`, `BLOCKWIRE`, `FILLWIRE`, `PADRING`, `BLOCKRING`, `BLOCKAGEWIRE`

### 16. NETS Section

**Purpose**: Defines regular signal nets and their routing.

Net information includes:
- Connectivity (components and pins)
- Routing geometry
- Virtual pins
- Subnets
- Non-default rules
- Shield nets
- Properties

### 17. SCANCHAINS Section

**Purpose**: Defines scan chains for design-for-test (DFT).

Scan chain elements:
- Start and stop points
- Ordered and floating components
- Common scan pins
- Partition information

### 18. GROUPS Section

**Purpose**: Defines logical groups of components.

Group attributes:
- Component list
- Soft constraints (area limits)
- Region assignments
- Properties

### 19. SLOTS Section

**Purpose**: Defines slot patterns in metal layers (for manufacturing or design rules).

### 20. FILLS Section

**Purpose**: Defines fill patterns to meet metal density requirements.

Fill types:
- Layer fills (metal shapes)
- Via fills
- Mask and OPC (Optical Proximity Correction) information

### 21. BEGINEXT/ENDEXT Section

**Purpose**: Allows tool-specific extensions to the DEF format.

```def
BEGINEXT "tag"
- CREATOR "Cadence" ;
- OTTER furry
  + PROPERTY arrg later ;
ENDEXT
```

## Coordinate System

- All coordinates are in database units
- The coordinate system is typically Cartesian (X-Y)
- The origin (0,0) is usually at the lower-left corner
- Units are defined in the header (e.g., 1000 database units = 1 micron)

## Common Patterns

### Orientation Codes
- `N`: North (0°)
- `S`: South (180°)
- `E`: East (90°)
- `W`: West (270°)
- `FN`: Flipped North (mirrored about X-axis)
- `FS`: Flipped South (mirrored about X-axis, then rotated 180°)
- `FE`: Flipped East (mirrored about X-axis, then rotated 90°)
- `FW`: Flipped West (mirrored about X-axis, then rotated 270°)

### Mask Information
- `MASK`: Specifies mask number for multi-patterning lithography
- Used in layers, vias, and routing

### Hierarchical Names
- Use divider character for hierarchy (default "/")
- Support for array notation with brackets "[]"
- Escape sequences for special characters

## Usage in EDA Flow

DEF files are used throughout the physical design flow:
1. **Floorplanning**: DIEAREA, ROWS, REGIONS
2. **Placement**: COMPONENTS with placement information
3. **Clock Tree Synthesis**: SPECIALNETS for clock networks
4. **Routing**: NETS, SPECIALNETS with routing geometry
5. **Physical Verification**: BLOCKAGES, antenna information
6. **Manufacturing**: FILLS, SLOTS for DRC compliance

This format enables seamless data exchange between different EDA tools while maintaining design integrity and completeness. 