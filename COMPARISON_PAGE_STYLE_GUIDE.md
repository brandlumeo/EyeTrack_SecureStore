# Comparison Page - Visual Style Guide

## Component Library

---

## 1. Product Header Card

### Purpose
Display product information in a card format with image, name, price, and action buttons.

### Desktop Version (140px image)
```
┌────────────────────────────┐
│                            │
│    [Product Image]         │  max-width: 140px
│     4:3 aspect ratio       │
│                            │
├────────────────────────────┤
│    Product Name (Bold)     │  1.05rem, Sora font
│    ₹45,000                 │  1.45rem, accent color
│                            │
│  [Best Price] [Top Stock]  │  Optional badges
│                            │
├────────────────────────────┤
│ [View] [Remove]            │  Full-width buttons
└────────────────────────────┘
```

### Mobile Version (90px image)
```
┌──────────────────┐
│  [Product Img]   │  max-width: 90px
├──────────────────┤
│  Product Name    │  0.8rem
│  ₹45,000         │  1rem
│ [View][Remove]   │  Stacked horizontally
└──────────────────┘
```

### CSS Classes
```css
.compare-product-header
.compare-product-image
.compare-product-image-placeholder
.compare-product-name
.compare-product-price
.compare-product-actions
```

### States
```
Default:
  Border: 1px solid rgba(255,255,255,0.1)
  Background: linear-gradient(135deg, rgba(10,44,79,0.35), rgba(7,23,41,0.4))
  Transform: translateY(0)

Hover:
  Border: 1px solid rgba(0,169,218,0.3)
  Background: linear-gradient(135deg, rgba(10,44,79,0.5), rgba(7,23,41,0.55))
  Transform: translateY(-2px)
  Box-shadow: 0 8px 20px rgba(0,0,0,0.3)
  Transition: 220ms var(--easing-premium)
```

---

## 2. Stock Status Badge

### Green Badge (In Stock)
```
┌─────────────────┐
│ ✓ In Stock      │
└─────────────────┘

Background: rgba(71, 230, 138, 0.14)
Border: 1px solid rgba(71, 230, 138, 0.5)
Text: #8ff2b7
Padding: 0.45rem 0.75rem
Border-radius: 0.65rem
Font-size: 0.8rem
Font-weight: 600
Text-transform: uppercase
Letter-spacing: 0.04em
```

### Orange Badge (Low Stock)
```
┌─────────────────┐
│ ⚠ 3 Left        │
└─────────────────┘

Background: rgba(245, 158, 11, 0.14)
Border: 1px solid rgba(245, 158, 11, 0.5)
Text: #ffc869
(Same padding, border-radius, etc.)
```

### Red Badge (Out of Stock)
```
┌──────────────────────────┐
│ ✕ Out of Stock           │
└──────────────────────────┘

Background: rgba(215, 38, 61, 0.14)
Border: 1px solid rgba(215, 38, 61, 0.5)
Text: #ffc4cc
(Same padding, border-radius, etc.)
```

### Hover Effect
```
Default: 
  Background: rgba(X, Y, Z, 0.14)
  
Hover:
  Background: rgba(X, Y, Z, 0.22)
  Border: rgba(X, Y, Z, 0.7)
  Box-shadow: 0 4px 12px rgba(X, Y, Z, 0.2)
  Transition: 180ms var(--easing-premium)
```

---

## 3. Action Buttons

### View Product Button (Cyan)
```
┌────────────────┐
│ 👁 View        │
└────────────────┘

Default:
  Background: rgba(0, 169, 218, 0.14)
  Border: 1px solid rgba(0, 169, 218, 0.4)
  Text: #7adfff
  Font-size: 0.85rem
  Padding: 0.55rem 0.75rem
  Border-radius: 0.65rem
  
Hover:
  Background: rgba(0, 169, 218, 0.24)
  Border: rgba(0, 169, 218, 0.65)
  Box-shadow: 0 4px 12px rgba(0, 169, 218, 0.25)
  Transform: translateY(-1px)
  Transition: 180ms var(--easing-premium)
  
Active/Pressed:
  Transform: translateY(0)
  Box-shadow: 0 2px 8px rgba(0, 169, 218, 0.15)
```

### Remove Button (Red)
```
┌────────────────┐
│ 🗑 Remove      │
└────────────────┘

Default:
  Background: rgba(215, 38, 61, 0.14)
  Border: 1px solid rgba(215, 38, 61, 0.4)
  Text: #ffc4cc
  (Same padding, border-radius, font-size)
  
Hover:
  Background: rgba(215, 38, 61, 0.24)
  Border: rgba(215, 38, 61, 0.65)
  Box-shadow: 0 4px 12px rgba(215, 38, 61, 0.25)
  Transform: translateY(-1px)
  
Active/Pressed:
  Transform: translateY(0)
  Box-shadow: 0 2px 8px rgba(215, 38, 61, 0.15)
```

### Button Container
```
.compare-product-actions
  Display: grid
  Gap: 0.5rem
  Width: 100%
  
Mobile: display: flex (for side-by-side)
```

---

## 4. Check/Cross Icons

### Check (Green, Yes)
```
┌──────────────┐
│ ✓ (check)    │
└──────────────┘

Background: rgba(71, 230, 138, 0.14)
Border: 1px solid rgba(71, 230, 138, 0.5)
Text: #8ff2b7
Padding: 0.4rem 0.65rem
Border-radius: 0.6rem
Font-weight: 600
Font-size: 0.85rem
Display: inline-flex
Align-items: center
Gap: 0.3rem

Icon: <i class="bi bi-check-lg"></i>
Icon-size: 1rem
```

### Cross (Red, No)
```
┌──────────────┐
│ ✕ (cross)    │
└──────────────┘

Background: rgba(215, 38, 61, 0.14)
Border: 1px solid rgba(215, 38, 61, 0.5)
Text: #ffc4cc
(Same padding, styling as Check)

Icon: <i class="bi bi-x-lg"></i>
Icon-size: 1rem
```

---

## 5. Best Value Highlight

### Highlight Effect
```
Regular Cell:
  Background: transparent
  Border: 1px solid rgba(255,255,255,0.08)
  Padding: 1rem
  
Best Value Cell (.compare-best):
  Background: rgba(255, 183, 0, 0.13)
  Box-shadow: inset 0 0 0 1px rgba(255, 183, 0, 0.35)
  Font-weight: 700
  (Same padding)
  
Color: Gold (#f5b700) theme
```

### Visual Comparison
```
Price Row (showing best):

┌──────────┬─────────────┬──────────┐
│ Attr     │ ₹45,000 ✓   │ ₹50,000  │
│          │ (best)      │          │
│          │ gold bg     │ normal   │
└──────────┴─────────────┴──────────┘
             ^ highlighted cell with gold background
```

---

## 6. Table Structure

### Header Row
```
┌────────────┬──────────┬──────────┬──────────┬──────────┐
│ Attribute  │ Product 1│ Product 2│ Product 3│ Product 4│
│            │          │          │          │          │
│ Sticky     │          Sticky Background                │
│ Left       │         (gradient)                         │
└────────────┴──────────┴──────────┴──────────┴──────────┘

Background: linear-gradient(90deg, rgba(7,44,74,0.45), rgba(10,30,50,0.35))
Border-bottom: 1px solid rgba(255,255,255,0.12)
Position: sticky / top: 0
Z-index: 10
Text: uppercase, 0.05em letter-spacing
```

### Data Rows
```
Regular Row (even):
  Background: rgba(255,255,255,0.02)
  Border-bottom: 1px solid rgba(255,255,255,0.08)
  Padding: 1rem
  
Regular Row (odd):
  Background: rgba(255,255,255,0.02)  (same as even)
  
Hover (any row):
  Background: rgba(255,255,255,0.04) (odd)
  Background: rgba(255,255,255,0.06) (even)
  Transition: 220ms var(--easing-premium)
```

### Attribute Column (Sticky Left)
```
Position: sticky
Left: 0
Z-index: 9
Min-width: 160px (desktop)
Min-width: 120px (tablet)
Min-width: 0 (mobile)

Background: inherit from row
Font-weight: 600
Color: #ddf3ff
Text-align: left
```

---

## 7. Empty State

### Empty State Display
```
        ┌─────────────────────────┐
        │                         │
        │      [Large Icon]       │
        │         📊              │ 3.5rem, muted color
        │                         │
        │  No items selected for  │
        │  comparison             │
        │                         │
        │  Add products from the  │
        │  store to start         │
        │  comparing.             │
        │                         │
        │  [Browse Products]      │  CTA button
        │                         │
        └─────────────────────────┘

Background: linear-gradient(135deg, rgba(10,44,79,0.2), rgba(7,23,41,0.25))
Border: 1px dashed rgba(255,255,255,0.15)
Border-radius: 0.85rem
Padding: 3rem 2rem (vertical/horizontal)

Icon Color: rgba(159, 183, 207, 0.3)
Title: #ddf3ff
Description: #9fb7cf
CTA Button: .btn-premium-cta
```

---

## 8. Color Palette Reference

### Primary Colors
```
Primary Dark:     #041427  (--bg-1)
Secondary Dark:   #0a2c4f  (--bg-2)
Card Background:  rgba(7, 23, 41, 0.72)
Text Primary:     #edf6ff
Text Muted:       #9fb7cf
```

### Accent Colors
```
Gold:             #f5b700 (--accent)
Warm:             #ff8b00 (--accent-warm)
Cyan:             #00a9da (--accent-2)
```

### Status Colors
```
Success/Green:    #8ff2b7 (rgba(71, 230, 138, ...))
Warning/Orange:   #ffc869 (rgba(245, 158, 11, ...))
Error/Red:        #ffc4cc (rgba(215, 38, 61, ...))
```

### Transparency Levels
```
.01 = 1% opacity     → Very subtle backgrounds
.04 = 4% opacity     → Hover states
.06 = 6% opacity     → Alternate rows, strong hover
.08-0.12 = 8-12%     → Borders, separators
.14 = 14% opacity    → Badge backgrounds
.24 = 24% opacity    → Button hover backgrounds
.35-0.4 = 35-40%     → Element borders
```

---

## 9. Typography Scale

### Font Family
```
Primary: "Sora" sans-serif (headings)
Secondary: "Manrope" sans-serif (body)
Fallback: "Segoe UI Symbol", sans-serif
```

### Font Sizes
```
Product Name:      1.05rem (desktop), 0.8rem (mobile)
Product Price:     1.45rem (desktop), 1rem (mobile)
Attribute Label:   0.95rem (desktop), 0.75rem (mobile)
Table Data:        0.9rem (desktop), 0.75rem (mobile)
Headers:           0.95rem, uppercase
Badges:            0.8rem, uppercase, 0.04em letter-spacing
```

### Font Weights
```
Light:             400
Regular:           500
Medium:            600
Bold:              700
Extra Bold:        800
```

---

## 10. Spacing System

### Base Unit: 0.25rem (4px)

```
0.25rem = XS gap
0.5rem  = Small gap between items
0.75rem = Medium padding
1rem    = Standard padding/spacing
1.25rem = Large padding
1.35rem = Card padding
1.5rem  = Large spacing
2rem    = Extra large
3rem    = Jumbo spacing
```

### Common Spacing
```
Button Padding:        0.55rem 0.75rem
Badge Padding:         0.45rem 0.75rem
Card Padding:          1.35rem (desktop), 1rem (tablet), 0.8rem (mobile)
Cell Padding:          1rem (desktop), 0.8rem (tablet), 0.65rem (mobile)
Row Gap:               1.5rem (mobile cards)
Button Gap:            0.5rem
Icon Gap:              0.3rem
```

---

## 11. Border Styles

### Table Borders
```
Header Border:         1px solid rgba(255,255,255,0.12)
Row Border:            1px solid rgba(255,255,255,0.08)
Cell Border:           none (borders on rows only)
Card Border:           1px solid rgba(255,255,255,0.1)
Hover Border:          1px solid rgba(0,169,218,0.3)
Dashed (empty):        1px dashed rgba(255,255,255,0.15)
```

### Border Radius
```
Small:    0.6rem - 0.65rem (buttons, badges)
Medium:   0.85rem (cards, container)
Large:    1rem (main sections)
```

---

## 12. Shadow & Glow Effects

### Box Shadows
```
Soft Shadow:       0 4px 12px rgba(0,0,0,0.2)
Strong Shadow:     0 8px 20px rgba(0,0,0,0.3)
Button Glow:       0 4px 12px rgba(X,Y,Z,0.25) (colored)
Inset Highlight:   inset 0 0 0 1px rgba(255,183,0,0.35)
```

### Transitions
```
Fast:    180ms (buttons)
Medium:  220ms (borders, backgrounds)
Smooth:  240ms (complex animations)

Easing:  cubic-bezier(0.22, 1, 0.36, 1) (premium easing)
         ease (fallback)
         ease-in-out (smooth scroll)
```

---

## 13. Hover States Progression

### Button Hover Pattern
```
Default:
  Opacity: 1
  Transform: translateY(0)
  Box-shadow: none
  
Hover (User Interaction):
  Opacity: 1
  Transform: translateY(-1px)
  Box-shadow: 0 4px 12px rgba(X,Y,Z,0.25)
  Transition: 180ms
  
Active (Click):
  Transform: translateY(0)
  Box-shadow: 0 2px 8px rgba(X,Y,Z,0.15)
```

### Card Hover Pattern
```
Default:
  Border: rgba(255,255,255,0.1)
  Background: linear-gradient(normal)
  Transform: translateY(0)
  
Hover:
  Border: rgba(0,169,218,0.3)
  Background: linear-gradient(darker)
  Transform: translateY(-2px)
  Box-shadow: 0 8px 20px rgba(0,0,0,0.3)
  Transition: 220ms
```

---

## 14. Responsive Design Tokens

### Desktop (1200px+)
```
Card Width:        140px image
Font Size:         1.05rem (product name)
Padding:           1.35rem (cards)
Button Height:     auto
```

### Tablet (992px-1200px)
```
Card Width:        120px image
Font Size:         0.95rem
Padding:           1rem
Button Height:     auto
```

### Mobile L (768px-992px)
```
Card Width:        100px image
Font Size:         0.85rem
Padding:           0.9rem
Button Height:     40px+
```

### Mobile S (<768px)
```
Card Width:        90px image
Font Size:         0.8rem
Padding:           0.8rem
Button Height:     44px+ (touch)
Layout:            Card-based (full width)
Button Layout:     Stacked vertical or horizontal flex
```

---

## Color Combinations

### Recommended Color Pairs

| Usage | Background | Border | Text | Hover BG |
|-------|-----------|--------|------|----------|
| In Stock | rgba(71,230,138,0.14) | rgba(71,230,138,0.5) | #8ff2b7 | rgba(71,230,138,0.22) |
| Low Stock | rgba(245,158,11,0.14) | rgba(245,158,11,0.5) | #ffc869 | rgba(245,158,11,0.22) |
| Out Stock | rgba(215,38,61,0.14) | rgba(215,38,61,0.5) | #ffc4cc | rgba(215,38,61,0.22) |
| View Btn | rgba(0,169,218,0.14) | rgba(0,169,218,0.4) | #7adfff | rgba(0,169,218,0.24) |
| Remove Btn | rgba(215,38,61,0.14) | rgba(215,38,61,0.4) | #ffc4cc | rgba(215,38,61,0.24) |
| Best Highlight | rgba(255,183,0,0.13) | rgba(255,183,0,0.35) | inherit | same |
| Table Header | rgba(7,44,74,0.45) | rgba(255,255,255,0.12) | #ddf3ff | same |

---

## Animation & Interaction Guidelines

### Duration Guidelines
```
Instant:    0ms (immediate feedback)
Fast:       180ms (buttons, quick actions)
Medium:     220ms (hover states)
Slow:       240ms+ (complex sequences)
```

### Transform Patterns
```
Lift Effect:       translateY(-1px to -2px)
Scale Effect:      scale(1.0 to 1.02)
Rotate Effect:     rotate(slight angle)
Fade Effect:       opacity: 0 to 1
Slide Effect:      translateX/Y
```

### Avoid
- ❌ Excessive animations
- ❌ Overly bright colors
- ❌ Disorienting transitions
- ❌ Auto-playing videos/gifs
- ❌ Color-only status indicators

---

## Export & Print Styles

### Print Conversion
```
Screen:  Dark theme with colors
Print:   White theme, optimized for paper

Changes:
- Background: #fff (white)
- Text: #111 (black)
- Borders: #cfcfcf (gray)
- Headers: #f5f5f5 (light gray)
- Shadows: none
- Buttons: hidden
- Badges: borders only (with #999 borders)
```

---

## Accessibility Requirements

### Color Contrast
```
✓ Text on background: 4.5:1+ ratio
✓ Large text: 3:1+ ratio
✓ Icons: match text contrast
✗ Color only indicator: needs text/symbol
```

### Touch Targets
```
✓ Minimum: 44px × 44px
✓ Buttons: at least 40px height
✓ Spacing: 8px+ between interactive elements
✓ Labels: visible and descriptive
```

---

## Component Checklist

- [x] Product header cards
- [x] Stock status badges
- [x] Action buttons
- [x] Check/cross indicators
- [x] Best value highlighting
- [x] Table structure
- [x] Empty state
- [x] Responsive layouts
- [x] Hover animations
- [x] Print styles
- [x] Dark/light modes
- [x] Accessibility features

---

**This style guide ensures consistent, professional design across all comparison page components.**
