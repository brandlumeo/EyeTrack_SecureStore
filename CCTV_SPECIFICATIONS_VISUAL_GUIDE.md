# CCTV Specifications Admin Interface - Visual Guide

## Django Admin Panel Layout

### Product Edit Page Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ Change Product                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ▼ 📦 Basic Information                                          │
│  ├─ Category *         [CCTV Cameras         ▼]                │
│  ├─ Name *             [Hikvision 8MP Camera     ]               │
│  ├─ Slug *             [hikvision-8mp-camera    ]               │
│  ├─ Description *      [                        ]               │
│  │                     [    (Multi-line text)    ]               │
│  │                     [                        ]               │
│  ├─ Image              [Choose File] [No file chosen]           │
│  └─ Is Available       [✓] Checked              │
│                                                                   │
│ ▼ 💰 Inventory & Pricing                                        │
│  ├─ Price *            [45000.00                ]               │
│  └─ Stock              [10                      ]               │
│                                                                   │
│ ► 📷 CCTV Specifications (Click to Expand)                      │
│  │                                                               │
│  │ [EXPANDED VIEW - CLICK ARROW TO COLLAPSE]                   │
│  │                                                               │
│  │ ├─ Camera Type        [Bullet            ▼]                │
│  │ ├─ Resolution         [8MP                   ]               │
│  │ ├─ Night Vision Range [30m                   ]               │
│  │ ├─ Field of View      [90°                   ]               │
│  │ ├─ Lens               [3.6mm                 ]               │
│  │ ├─ Frame Rate         [30fps                 ]               │
│  │ ├─ Weatherproof       [IP67                  ]               │
│  │ ├─ Connectivity       [Wired             ▼]                │
│  │ ├─ Power Source       [PoE               ▼]                │
│  │ ├─ Storage Support    [NVR, microSD         ]               │
│  │ ├─ Audio Support      [✓] Yes                │
│  │ ├─ AI Detection       [✓] Yes                │
│  │ └─ Warranty           [2 years               ]               │
│                                                                   │
│                                                    [Save]  [...]  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fieldset Hierarchy

```
PRODUCT ADMIN FORM
│
├─ 📦 Basic Information (EXPANDED)
│  ├─ Category
│  ├─ Name
│  ├─ Slug
│  ├─ Description
│  ├─ Image
│  └─ Is Available
│
├─ 💰 Inventory & Pricing (EXPANDED)
│  ├─ Price
│  └─ Stock
│
└─ 📷 CCTV Specifications (COLLAPSIBLE - starts collapsed)
   ├─ Camera Type (dropdown)
   ├─ Resolution (text)
   ├─ Night Vision Range (text)
   ├─ Field of View (text)
   ├─ Lens (text)
   ├─ Frame Rate (text)
   ├─ Weatherproof (text)
   ├─ Connectivity (dropdown)
   ├─ Power Source (dropdown)
   ├─ Storage Support (text)
   ├─ Audio Support (checkbox)
   ├─ AI Detection (checkbox)
   └─ Warranty (text)
```

---

## Field Type Visualization

### Choice Fields (Dropdowns)

#### Camera Type
```
┌─────────────────────────────────────┐
│ Camera Type                          │
├─────────────────────────────────────┤
│  Bullet          ▼                   │
├─────────────────────────────────────┤
│ • Bullet                             │
│ • Dome                               │
│ • Turret                             │
│ • PTZ                                │
│ • Wireless / WiFi                    │
│ • Fisheye                            │
│ • Indoor Cube                        │
└─────────────────────────────────────┘
```

#### Connectivity
```
┌─────────────────────────────────────┐
│ Connectivity                         │
├─────────────────────────────────────┤
│  Wired           ▼                   │
├─────────────────────────────────────┤
│ • Wired                              │
│ • Wi-Fi                              │
│ • Hybrid                             │
└─────────────────────────────────────┘
```

#### Power Source
```
┌─────────────────────────────────────┐
│ Power Source                         │
├─────────────────────────────────────┤
│  PoE             ▼                   │
├─────────────────────────────────────┤
│ • PoE                                │
│ • DC 12V                             │
│ • Battery                            │
│ • Solar                              │
└─────────────────────────────────────┘
```

### Text Fields

```
┌─────────────────────────────────────┐
│ Resolution                          │
├─────────────────────────────────────┤
│ [8MP                                ]│
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Night Vision Range                  │
├─────────────────────────────────────┤
│ [30m                                ]│
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Field of View                       │
├─────────────────────────────────────┤
│ [90°                                ]│
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ Lens                                │
├─────────────────────────────────────┤
│ [3.6mm                              ]│
└─────────────────────────────────────┘
```

### Boolean Fields (Checkboxes)

```
┌─────────────────────────────────────┐
│ Audio Support                       │
├─────────────────────────────────────┤
│ [✓] Audio Support                   │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ AI Detection                        │
├─────────────────────────────────────┤
│ [✓] AI Detection                    │
└─────────────────────────────────────┘
```

---

## Product List View

```
┌────────────────────────────────────────────────────────────────────┐
│ Select  Name                  Category        Price  Stock  Active  │
├────────────────────────────────────────────────────────────────────┤
│  □      Hikvision 8MP         CCTV Cameras    45000  10    ✓       │
│  □      CP Plus 5MP            CCTV Cameras    35000  5     ✓       │
│  □      Dahua 4MP              CCTV Cameras    28000  8     ✓       │
│  □      Uniview Turret          CCTV Cameras    52000  3     ✓       │
│  □      Uniview PTZ             CCTV Cameras    75000  2     ✓       │
│  □      Hikvision Fisheye       CCTV Cameras    65000  4     ✓       │
│                                                                      │
│  [+ Add Product]                                    [Search]        │
└────────────────────────────────────────────────────────────────────┘
```

---

## Complete Product Example

### Camera: Hikvision 8MP Bullet

```
┌──────────────────────────────────────────────────────────┐
│                  PRODUCT FORM                             │
├──────────────────────────────────────────────────────────┤
│                                                            │
│ 📦 BASIC INFORMATION                                      │
│ ├─ Category:        [CCTV Cameras              ▼]        │
│ ├─ Name:            [Hikvision 8MP Bullet Camera]        │
│ ├─ Slug:            [hikvision-8mp-bullet-camera]        │
│ ├─ Description:     [Enterprise-grade infrared    ]      │
│ │                   [dome camera with AI detection]      │
│ ├─ Image:           [Choose File] [thumbnail.jpg]        │
│ └─ Is Available:    [✓]                                   │
│                                                            │
│ 💰 INVENTORY & PRICING                                    │
│ ├─ Price:           [45000.00                   ]        │
│ └─ Stock:           [10                         ]        │
│                                                            │
│ 📷 CCTV SPECIFICATIONS  ► (Click to expand)              │
│  ▼ EXPANDED:                                              │
│  ├─ Camera Type:          [Bullet            ▼]          │
│  ├─ Resolution:           [8MP                 ]          │
│  ├─ Night Vision Range:   [30m                 ]          │
│  ├─ Field of View:        [90°                 ]          │
│  ├─ Lens:                 [3.6mm               ]          │
│  ├─ Frame Rate:           [30fps               ]          │
│  ├─ Weatherproof:         [IP67                ]          │
│  ├─ Connectivity:         [Wired            ▼]          │
│  ├─ Power Source:         [PoE               ▼]          │
│  ├─ Storage Support:      [NVR, microSD       ]          │
│  ├─ Audio Support:        [✓]                            │
│  ├─ AI Detection:         [✓]                            │
│  └─ Warranty:             [2 years             ]          │
│                                                            │
│                          [Save]  [Save and Continue]     │
│                                                            │
└──────────────────────────────────────────────────────────┘
```

---

## Data Entry Workflow

```
START
  │
  ├─► Go to Admin Panel
  │
  ├─► Navigate to Store → Products
  │
  ├─► Click "Add Product" or Edit Existing
  │
  ├─► Fill Basic Information (Required)
  │    ├─ Category: CCTV Cameras
  │    ├─ Name: Product Name
  │    ├─ Description: Features/details
  │    └─ Price & Stock
  │
  ├─► (OPTIONAL) Click CCTV Specifications to Expand
  │    ├─ Camera Type: Select from dropdown
  │    ├─ Resolution: Type (e.g., "8MP")
  │    ├─ Night Vision: Type (e.g., "30m")
  │    ├─ Field of View: Type (e.g., "90°")
  │    ├─ Lens: Type (e.g., "3.6mm")
  │    ├─ Frame Rate: Type (e.g., "30fps")
  │    ├─ Weatherproof: Type (e.g., "IP67")
  │    ├─ Connectivity: Select from dropdown
  │    ├─ Power Source: Select from dropdown
  │    ├─ Storage Support: Type (e.g., "NVR, microSD")
  │    ├─ Audio Support: Check if yes
  │    ├─ AI Detection: Check if yes
  │    └─ Warranty: Type (e.g., "2 years")
  │
  ├─► Click "Save"
  │
  └─► Product Created with Specifications
       │
       ├─► Shows on Product List
       ├─► Accessible via API endpoint
       └─► Displays on Compare Page
```

---

## Admin Interface Features

### Collapsible Section

**Collapsed (Default)**:
```
► 📷 CCTV Specifications  (13 fields)
```

Click arrow to expand all 13 fields at once.

**Expanded**:
```
▼ 📷 CCTV Specifications
 ├─ Camera Type
 ├─ Resolution
 ├─ Night Vision Range
 ├─ Field of View
 ├─ Lens
 ├─ Frame Rate
 ├─ Weatherproof
 ├─ Connectivity
 ├─ Power Source
 ├─ Storage Support
 ├─ Audio Support
 ├─ AI Detection
 └─ Warranty
```

Click arrow again to collapse.

### Help Text (Hover/Focus)

```
Camera Type
? Type of CCTV camera

Resolution
? Resolution (e.g., 4K, 2MP, 5MP)

Night Vision Range
? Night vision range in meters (e.g., 30m)

And so on for all fields...
```

---

## Compare Page Data Display

Once products have specifications in the admin, they appear on the compare page:

```
┌───────────────────────────────────────────────────────────────┐
│ Comparison Matrix                                              │
├──────────────────┬──────────────┬──────────────┬──────────────┤
│ Attribute        │ Product 1    │ Product 2    │ Product 3    │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Product          │ [Image]      │ [Image]      │ [Image]      │
│                  │ Hikvision    │ CP Plus      │ Dahua        │
│                  │ ₹45,000      │ ₹35,000      │ ₹28,000      │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Camera Type      │ Bullet       │ Dome         │ Turret       │
│ Resolution       │ 8MP ⭐       │ 5MP          │ 4MP          │
│ Night Vision     │ 30m ⭐       │ 20m          │ 25m          │
│ Field of View    │ 90°          │ 120° ⭐      │ 85°          │
│ Lens             │ 3.6mm        │ 2.8-12mm ⭐  │ 3.6mm        │
│ Frame Rate       │ 30fps ⭐     │ 25fps        │ 25fps        │
│ Weatherproof     │ IP67 ⭐      │ IP65         │ IP66         │
│ Connectivity     │ Wired        │ Wi-Fi        │ Wired        │
│ Power Source     │ PoE          │ Battery      │ PoE          │
│ Storage          │ NVR, µSD ⭐  │ Cloud        │ NVR          │
│ Audio Support    │ Yes ⭐       │ No           │ Yes ⭐       │
│ AI Detection     │ Yes ⭐       │ No           │ Yes ⭐       │
│ Warranty         │ 2 years      │ 1 year       │ 2 years      │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ Price            │ ₹45,000      │ ₹35,000 ⭐   │ ₹28,000 ⭐   │
│ Stock            │ 10 ⭐        │ 5            │ 8            │
└───────────────────────────────────────────────────────────────┘

⭐ = Best value for this attribute
```

---

## Summary

✅ **Admin Panel**: Clean, organized CCTV Specifications section  
✅ **Data Entry**: Simple form fields with dropdowns for choices  
✅ **Collapsible**: Minimizes clutter while keeping fields accessible  
✅ **Compare Page**: Automatically displays all specifications  
✅ **Visual Feedback**: Best values highlighted with badges  

---

**Visual Guide Version**: 1.0  
**Date**: March 10, 2026

