# CAS Popup Examples

This page demonstrates the `cas-popup` directive, which creates a button that opens a GeoGebra CAS (Computer Algebra System) window in a popup dialog.

## Basic Usage

Default 350x500 CAS window:

```{cas-popup}
```

## Custom Size

A larger 600x700 window:

```{cas-popup} 600 700
```

## Custom Button Text and Title

Custom button text and dialog title:

```{cas-popup} 400 600 "Open Calculator" "My CAS Window"
```

## Norwegian Text

Using Norwegian text for button and title:

```{cas-popup} 500 650 "Åpne kalkulator" "Matematisk kalkulator"
```

## Sidebar Layout

Float the button to the right side of the page:

```{cas-popup} 350 500 "CAS" "Calculator"
:layout: sidebar
```

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.

The sidebar CAS button should float to the right of this text. This demonstrates how you can integrate the CAS calculator seamlessly into your content without disrupting the flow.

## Multiple CAS Windows

You can have multiple CAS windows on the same page:

```{cas-popup} 400 500 "CAS Window 1" "Calculator 1"
```

```{cas-popup} 400 500 "CAS Window 2" "Calculator 2"
```

## Features

The CAS popup directive includes:

- **Resizable and draggable** dialog window
- **Scroll-locking** when interacting with GeoGebra (prevents page scrolling)
- **Theme-aware** styling (adapts to light/dark mode)
- **Touch support** for mobile devices
- **Customizable** size, text, and layout
- **Norwegian language** support in GeoGebra interface

## Technical Details

The directive:
- Uses jQuery UI for dialog functionality
- Loads GeoGebra's CAS perspective
- Handles window resizing gracefully
- Prevents background scrolling during interaction
- Supports multiple instances on the same page
