# GeoGebra Popup Examples

This page demonstrates the GeoGebra popup directive for creating interactive GeoGebra applets in dialog windows.

## What is GeoGebra Popup?

The GeoGebra popup directive creates a button that opens a full GeoGebra Classic applet in a draggable, resizable dialog window. This allows users to interact with GeoGebra without leaving the page.

## Example 1: Basic Popup (Default Size)

Click the button below to open a GeoGebra window with default settings (700×500):

```{ggb-popup}
```

## Example 2: Custom Size

Open a larger GeoGebra window (900×700):

```{ggb-popup} 900 700 "Open Large Calculator" "GeoGebra Calculator"
```

## Example 3: Geometry Perspective

Open GeoGebra in Geometry mode:

```{ggb-popup} 800 600 "Open Geometry" "Geometry Window"
:perspective: G
```

## Example 4: Graphing Perspective

Open GeoGebra in Graphing mode:

```{ggb-popup} 850 650 "Open Graphing Calculator" "Graphing Calculator"
:perspective: GS
```

## Example 5: With Menu Bar

Open GeoGebra with the menu bar visible:

```{ggb-popup} 800 600 "Open with Menu" "GeoGebra with Menu"
:menubar: true
```

## Example 6: CAS Mode

Open GeoGebra in Computer Algebra System (CAS) mode:

```{ggb-popup} 900 700 "Open CAS" "CAS Calculator"
:perspective: CAS
:menubar: true
```

## Features

- 🖱️ **Draggable**: Move the window anywhere on the screen
- 📏 **Resizable**: Adjust the size by dragging the edges
- 🎯 **Centered**: Opens in the center of your screen
- 🔄 **Responsive**: Adjusts when you resize the window
- 🎨 **Styled**: Uses jQuery UI theming
- 🧮 **Full Featured**: Complete GeoGebra Classic applet

## Common Perspectives

- **AG** (default): Algebra & Graphics view
- **G**: Geometry view only
- **GS**: Graphing/Function Graphing view
- **CAS**: Computer Algebra System view
- **3D**: 3D Graphics view

## Technical Notes

- Requires jQuery and jQuery UI (automatically loaded)
- Requires GeoGebra API (automatically loaded)
- Uses responsive sizing to adapt to dialog resizing
- Dialog remains open until explicitly closed
