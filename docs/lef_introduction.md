# LEF (Library Exchange Format) Introduction

## Overview

The Library Exchange Format (LEF) is a standard file format used in electronic design automation (EDA) for representing the physical and electrical characteristics of standard cell libraries and technology information. This document provides an introduction to each section of a LEF file based on the `complete.5.8.lef` example.

## File Structure

A LEF file consists of multiple sections that define different aspects of a technology library. Each section serves a specific purpose in describing the physical implementation rules, layer definitions, and cell abstractions needed for physical design.

## Sections Overview
### Section dividence for coding design
1. P -> END P blocks: [UNITS, PROPERTYDEFINITIONS, SPACING, IRDROP ]
2. P PN -> END PN blocks: [LAYER, VIA, VIARULE, NONDEFAULTRULE, SITE, MACRO, (MACRO-PIN), ]

### Section overview
1. Header Information - Version, naming conventions, global settings
2. UNITS Section - Unit definitions for electrical and physical parameters
3. LAYER Sections - Technology layer definitions with routing rules, spacing constraints, and antenna modeling
4. VIA/VIARULE Sections - Via definitions and parameterized via generation rules
5. NONDEFAULTRULE Sections - Special routing rules for wide nets, analog signals, etc.
6. SITE/ARRAY Sections - Placement site definitions and array templates
7. MACRO Sections - Cell abstractions with pins, timing, and physical information
8. Advanced Features - Multi-patterning, current density modeling, antenna rules


### 1. Header Information

```lef
VERSION 5.8 ;
NAMESCASESENSITIVE ON ;
FIXEDMASK ;
NOWIREEXTENSIONATPIN ON ;
BUSBITCHARS "<>" ;
DIVIDERCHAR ":" ;
USEMINSPACING OBS OFF ;
USEMINSPACING PIN ON ;
CLEARANCEMEASURE EUCLIDEAN ;
CLEARANCEMEASURE MAXXY ;
```

**Purpose**: Defines basic file format information and global settings.

- `VERSION`: Specifies the LEF format version
- `NAMESCASESENSITIVE`: Controls case sensitivity for names
- `FIXEDMASK`: Enables fixed mask assignment for multi-patterning
- `NOWIREEXTENSIONATPIN`: Controls wire extension at pins
- `BUSBITCHARS`: Characters used for bus bit notation ("<>")
- `DIVIDERCHAR`: Character used for hierarchical name separation (":")
- `USEMINSPACING`: Controls minimum spacing rules for different contexts
- `CLEARANCEMEASURE`: Defines how clearances are measured (EUCLIDEAN or MAXXY)

### 2. Defines Section

```lef
&defines &VDD/GND_site = "VDDGND" ;
&defines &VDD/GND_site = "VDDGND1" ;
```

**Purpose**: Defines preprocessor-like macros for use throughout the LEF file.

### 3. UNITS Section

```lef
UNITS
   TIME NANOSECONDS 100 ;
   CAPACITANCE PICOFARADS 10 ;
   RESISTANCE OHMS 10000 ;
   POWER MILLIWATTS 10000 ;
   CURRENT MILLIAMPS 10000 ;
   VOLTAGE VOLTS 1000 ;
   DATABASE MICRONS 20000 ;
   FREQUENCY MEGAHERTZ 10 ;
END UNITS
```

**Purpose**: Defines the unit system used throughout the LEF file.

- `DATABASE MICRONS`: Conversion factor from database units to microns
- Electrical units: TIME, CAPACITANCE, RESISTANCE, POWER, CURRENT, VOLTAGE
- `FREQUENCY`: For timing-related specifications

### 4. MANUFACTURINGGRID Section

```lef
MANUFACTURINGGRID 3.5 ;
```

**Purpose**: Defines the manufacturing grid resolution for the technology.

### 5. PROPERTYDEFINITIONS Section

**Purpose**: Defines custom properties that can be attached to various design objects.

Properties can be defined for:
- `LIBRARY`: Library-level properties
- `LAYER`: Layer properties  
- `VIA`: Via properties
- `VIARULE`: Via rule properties
- `NONDEFAULTRULE`: Non-default rule properties
- `MACRO`: Macro/cell properties
- `PIN`: Pin properties

Each property has a type (`STRING`, `INTEGER`, `REAL`) and optional range constraints.

### 6. LAYER Sections

**Purpose**: Defines the physical layers used in the technology.

#### Layer Types:
- `MASTERSLICE`: Base layers (e.g., POLYS, POLYS01)
- `CUT`: Via/contact layers (e.g., CUT01, CUT12, CA, V1, V2)
- `ROUTING`: Metal interconnect layers (e.g., RX, PC, M1, M2, M3, M4, M5, MT)
- `IMPLANT`: Implant layers
- `OVERLAP`: Overlap layers

#### Key Layer Attributes:

**Routing Layers:**
```lef
LAYER M1
   TYPE ROUTING ;
   DIRECTION HORIZONTAL ;
   PITCH 1.8 ;
   WIDTH 1 ;
   SPACING 0.9 ;
   RESISTANCE RPERSQ 0.103 ;
   CAPACITANCE CPERSQDIST 0.000156 ;
   ANTENNA... ;
END M1
```

- `DIRECTION`: Preferred routing direction (HORIZONTAL, VERTICAL, DIAG45, DIAG135)
- `PITCH`: Routing pitch/grid
- `WIDTH`: Default/minimum wire width
- `SPACING`: Minimum spacing rules
- `RESISTANCE`: Sheet resistance
- `CAPACITANCE`: Parasitic capacitance
- Antenna rules for DRC compliance

**Cut Layers:**
```lef
LAYER V1
   TYPE CUT ;
   SPACING 0.6 LAYER CA ;
END V1
```

- `SPACING`: Cut-to-cut spacing rules
- Layer-specific spacing constraints

#### Advanced Spacing Rules:
- `LENGTHTHRESHOLD`: Length-dependent spacing
- `RANGE`: Width-dependent spacing  
- `INFLUENCE`: Influence distance for spacing
- `PARALLELOVERLAP`: Parallel overlap constraints
- `ENDOFLINE`: End-of-line spacing rules
- `SPACINGTABLE`: Table-driven spacing rules

#### Antenna Rules:
Extensive antenna modeling for manufacturing compliance:
- `ANTENNAMODEL`: Different oxide models
- `ANTENNAAREARATIO`: Area ratios for antenna effects
- `ANTENNADIFFAREARATIO`: Diffusion area considerations
- `ANTENNACUMAREARATIO`: Cumulative area effects
- Gate area, side area, and metal length specifications

### 7. VIA Sections

**Purpose**: Defines standard via structures for inter-layer connections.

#### Via Types:

**Explicit Geometry Vias:**
```lef
VIA M1_M2 DEFAULT
   RESISTANCE 1.5 ;
   LAYER M1 ;
      RECT MASK 1 -0.6 -0.6 0.6 0.6 ;
   LAYER V1 ;
      RECT MASK 2 -0.45 -0.45 0.45 0.45 ;
   LAYER M2 ;
      RECT MASK 3 -0.45 -0.45 0.45 0.45 ;
END M1_M2
```

**Rule-Based Vias:**
```lef
VIA myBlockVia
   VIARULE DEFAULT ;
   CUTSIZE 0.1 0.1 ;
   LAYERS metal1 via12 metal2 ;
   CUTSPACING 0.1 0.1 ;
   ENCLOSURE 0.05 0.01 0.01 0.05 ;
   ROWCOL 1 2 ;
END myBlockVia
```

Key attributes:
- `RESISTANCE`: Electrical resistance per cut
- Layer geometry (RECT, POLYGON)
- `MASK`: Mask assignment for multi-patterning
- `FOREIGN`: Reference to external definitions
- `TOPOFSTACKONLY`: Stack limitations

### 8. VIARULE Sections

**Purpose**: Defines parameterized via generation rules.

```lef
VIARULE via12 GENERATE DEFAULT
   LAYER m1 ;
      ENCLOSURE 0.03 0.01 ;
   LAYER m2 ;
      ENCLOSURE 0.05 0.01 ;
   LAYER cut12 ;
      RECT -0.1 -0.1 0.1 0.1 ;
      SPACING 0.40 BY 0.40 ;
      RESISTANCE 20 ;
END via12
```

- `GENERATE`: Indicates parameterized via rule
- `ENCLOSURE`: Metal enclosure requirements
- `SPACING`: Cut-to-cut spacing
- `DIRECTION`: Preferred metal directions
- `WIDTH`: Metal width ranges
- `OVERHANG`/`METALOVERHANG`: Metal extension rules

### 9. NONDEFAULTRULE Sections

**Purpose**: Defines non-default routing rules for special nets.

```lef
NONDEFAULTRULE wide3x
   LAYER metal1
      WIDTH 3.0 ;
   END metal1
   MINCUTS cut12 2 ;
END wide3x
```

Features:
- Layer-specific width and spacing overrides
- `MINCUTS`: Minimum via cut requirements
- `HARDSPACING`: Strict spacing enforcement
- `USEVIA`/`USEVIARULE`: Specific via selections
- Custom resistance and capacitance values

### 10. Electrical Specifications

#### Noise and Timing:
```lef
UNIVERSALNOISEMARGIN 0.1 20 ;
EDGERATETHRESHOLD1 0.1 ;
EDGERATETHRESHOLD2 0.9 ;
NOISETABLE 1 ;
```

#### Current Density:
Advanced current density modeling:
- `ACCURRENTDENSITY`: AC current density tables
- `DCCURRENTDENSITY`: DC current density limits
- Frequency-dependent specifications
- Width and area-dependent tables

### 11. Global Spacing Rules

```lef
SPACING
   SAMENET CUT01 CA 1.5 ;
   SAMENET CA V1 1.5 STACK ;
   SAMENET M1 M1 3.5 STACK ;
END SPACING
```

**Purpose**: Defines global spacing rules between layers.

### 12. Technology Parameters

```lef
MINFEATURE 0.1 0.1 ;
DIELECTRIC 0.000345 ;
IRDROP 
   TABLE DRESHI 0.0001 -0.7 0.001 -0.8 ;
END IRDROP
```

- `MINFEATURE`: Minimum feature sizes
- `DIELECTRIC`: Dielectric constant
- `IRDROP`: IR drop characterization tables

### 13. SITE Sections

**Purpose**: Defines placement sites for different cell types.

```lef
SITE CORE
   CLASS CORE ;
   SIZE 0.700 BY 8.400 ;
END CORE
```

Site classes:
- `CORE`: Standard cells
- `PAD`: I/O pads  
- `CORNER`: Corner cells
- `AREAIO`: Area I/O

Special features:
- `ROWPATTERN`: Complex site patterns
- `SYMMETRY`: Allowed orientations (X, Y, R90)

### 14. ARRAY Sections

**Purpose**: Defines array-based placement templates.

```lef
ARRAY M7E4XXX
   SITE CORE -5021.450 -4998.000 N DO 14346 BY 595 STEP 0.700 16.800 ;
   CANPLACE COVER -7315.000 -7315.000 N DO 1 BY 1 STEP 0.000 0.000 ;
   CANNOTOCCUPY CORE -5021.450 -4989.600 FS DO 100 BY 595 STEP 0.700 16.800 ;
   TRACKS X -6148.800 DO 17569 STEP 0.700 LAYER RX ;
   FLOORPLAN 100% ... END 100% ;
   GCELLGRID X -6157.200 DO 1467 STEP 8.400 ;
END M7E4XXX
```

- `CANPLACE`: Allowed placement regions
- `CANNOTOCCUPY`: Blocked placement regions
- `TRACKS`: Routing track definitions
- `FLOORPLAN`: Hierarchical floorplan specifications
- `GCELLGRID`: Global routing grid

### 15. MACRO Sections

**Purpose**: Defines cell abstractions with pins, timing, and physical information.

#### Macro Classification:
```lef
MACRO INV
   CLASS CORE ;
   SOURCE BLOCK ;
   SIZE 67.2 BY 24 ;
   SYMMETRY X Y R90 ;
   SITE CORE1 ;
```

**Cell Classes:**
- `CORE`: Standard cells
- `PAD`: I/O cells
- `ENDCAP`: End cap cells
- `RING`: Ring structures
- `BLOCK`: Hard macros
- `COVER`: Cover cells
- `SPACER`: Spacer cells
- `ANTENNACELL`: Antenna diodes
- `WELLTAP`: Well tap cells

**Special Attributes:**
- `BLACKBOX`: No internal details
- `SOFT`: Soft macros
- `BUMP`: Bump structures

#### Pin Definitions:
```lef
PIN Z DIRECTION OUTPUT ;
   USE SIGNAL ;
   CAPACITANCE 0.1 ;
   RESISTANCE 0.2 ;
   POWER 0.1 ;
   PORT
      LAYER M2 ;
         PATH 30.8 9 42 9 ;
   END
END Z
```

**Pin Attributes:**
- `DIRECTION`: INPUT, OUTPUT, INOUT, FEEDTHRU
- `USE`: SIGNAL, POWER, GROUND, CLOCK, ANALOG, SCAN, RESET
- `SHAPE`: ABUTMENT, RING, FEEDTHRU
- Electrical characteristics (capacitance, resistance, power)
- Antenna information
- `MUSTJOIN`: Pin connection requirements

**Port Geometry:**
- `RECT`: Rectangular shapes
- `POLYGON`: Polygonal shapes  
- `PATH`: Path-based routing
- `VIA`: Via instances
- `MASK`: Mask assignments
- `ITERATE`: Repeated patterns

#### Timing Information:
```lef
TIMING
   FROMPIN A ;
   TOPIN Z ;
   RISE INTRINSIC .39 .41 1.2 .25 .29 1.8 .67 .87 2.2 ;
   FALL INTRINSIC .24 .29 1.3 .26 .31 1.7 .6 .8 2.1 ;
   UNATENESS INVERT ;
END TIMING
```

#### Blockages (OBS):
```lef
OBS
   LAYER M1 DESIGNRULEWIDTH 4.5 ;
      RECT 24.1 1.5 43.5 16.5 ;
      PATH 532.0 534 1999.2 534 ;
      VIA 470.4 475 VIABIGPOWER12 ;
END
```

- `DESIGNRULEWIDTH`: Minimum width for design rules
- `SPACING`: Layer-specific spacing
- `EXCEPTPGNET`: Exceptions for power/ground networks

#### Density Information:
```lef
DENSITY
   LAYER metal1 ;
      RECT 0 0 100 100 45.5 ;
   LAYER metal2 ;
      RECT 0 0 250 140 20.5 ;
END
```

**Purpose**: Metal density specifications for CMP (Chemical Mechanical Polishing) requirements.

### 16. Antenna Specifications

Global antenna rules:
```lef
ANTENNAINPUTGATEAREA 45 ;
ANTENNAINOUTDIFFAREA 65 ;
ANTENNAOUTPUTDIFFAREA 55 ;
```

### 17. Extension Sections

```lef
BEGINEXT "SIGNATURE"
   CREATOR "CADENCE"
   DATE "04/14/98"
ENDEXT
```

**Purpose**: Tool-specific extensions and metadata.

## Advanced Features

### Multi-Patterning Support
- `MASK`: Layer mask assignments
- `FIXEDMASK`: Fixed mask constraints
- Mask-aware spacing and design rules

### Current Density Modeling
- Frequency-dependent AC current density
- Width and area-dependent DC limits
- Peak, average, and RMS specifications

### Antenna Modeling
- Multiple oxide models (OXIDE1, OXIDE2, etc.)
- Area and perimeter effects
- Cumulative and differential calculations
- Gate and diffusion contributions

### Advanced Spacing Rules
- Length and width-dependent spacing
- End-of-line constraints
- Parallel overlap rules
- Same-net spacing specifications
- Influence-based spacing

## Coordinate System

- All coordinates are in database units
- The coordinate system is Cartesian (X-Y)
- Units are defined in the UNITS section
- Default origin at lower-left corner

## Common Patterns

### Orientation Codes
- `N`: North (0°)
- `S`: South (180°)
- `E`: East (90°)
- `W`: West (270°)
- `FN`: Flipped North
- `FS`: Flipped South
- `FE`: Flipped East
- `FW`: Flipped West

### Layer Directions
- `HORIZONTAL`: Horizontal preferred routing
- `VERTICAL`: Vertical preferred routing
- `DIAG45`: 45-degree diagonal
- `DIAG135`: 135-degree diagonal

### Site Symmetries
- `X`: Mirror about X-axis
- `Y`: Mirror about Y-axis
- `R90`: 90-degree rotation

## Usage in EDA Flow

LEF files are used throughout the physical design flow:

1. **Technology Setup**: LAYER definitions, spacing rules, via rules
2. **Library Characterization**: MACRO definitions with timing and power
3. **Floorplanning**: SITE and ARRAY definitions for placement
4. **Placement**: Cell abstractions and placement sites
5. **Routing**: Layer properties, spacing rules, via definitions
6. **Physical Verification**: Antenna rules, current density limits
7. **Manufacturing**: Multi-patterning rules, density requirements

The LEF format provides a complete technology and library description that enables seamless integration between different EDA tools while maintaining design rule compliance and electrical correctness. 