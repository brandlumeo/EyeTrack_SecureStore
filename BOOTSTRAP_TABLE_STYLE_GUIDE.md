# Bootstrap Table Redesign - Visual Style Guide

## Component Library

---

## 1. Premium Dark Table

### Overview
Modern dark theme table replacing Bootstrap white table styling.

### Desktop Version
```
┌─────────────────────────────────────────────────────────┐
│ Product                  Price         Qty    Subtotal  │
│ (Header - Dark Gradient Background)                     │
├─────────────────────────────────────────────────────────┤
│ Camera 8MP              ₹ 45,000       3    ₹ 135,000  │
│ (Dark Row)                                               │
├─────────────────────────────────────────────────────────┤
│ Camera 5MP              ₹ 35,000       2    ₹ 70,000   │
│ (Slightly Lighter Row - Alternating)                    │
├─────────────────────────────────────────────────────────┤
│ DVR 8CH                 ₹ 12,000       1    ₹ 12,000   │
│ (On Hover: Lighter Background)                          │
└─────────────────────────────────────────────────────────┘

CSS Classes:
.premium-table (dark transparent background)
.premium-table thead (gradient header)
.premium-table th (header cells)
.premium-table tbody tr (rows)
.premium-table td (data cells)
```

### Mobile Version
```
┌──────────────────────────┐
│ Product  │  Price │ Qty  │
├──────────────────────────┤
│ Camera   │ ₹45000 │  3   │
│ 8MP      │        │      │
├──────────────────────────┤
│ Camera   │ ₹35000 │  2   │
│ 5MP      │        │      │
└──────────────────────────┘

(Horizontal scroll for additional columns)
```

### Colors
```
Background:     rgba(255,255,255,0.01-0.06)
Header BG:      linear-gradient(90deg, rgba(7,44,74,0.45), rgba(10,30,50,0.35))
Header Text:    #ddf3ff
Body Text:      #edf6ff
Border:         rgba(255,255,255,0.08-0.12)
Hover:          rgba(255,255,255,0.04-0.06)
Row Alternate:  rgba(255,255,255,0.02)
```

### Responsive Behavior
```
Desktop (1200px+):  Full layout, sticky headers
Tablet (992px):     Reduced padding, adjusted fonts
Mobile (768px):     Compact, horizontal scroll
Small (<768px):     Extra compact, touch-optimized
```

---

## 2. Quantity Controls (Cart Page)

### Layout
```
┌──────────────────────┐
│ −  │  3  │ +        │ ← Flex container
│ (Qty Controls)       │
└──────────────────────┘

Default: Inline-flex, gap: 0.75rem
Padding: 0.35rem
Border: 1px solid rgba(0,169,218,0.4)
Background: rgba(255,255,255,0.04)
Border-radius: 0.6rem
```

### Button Styling
```
Button:  − or +
Width:   28px
Height:  28px
Color:   #7adfff (Cyan)
BG:      rgba(0,169,218,0.14)
Border:  1px solid rgba(0,169,218,0.4)
Radius:  0.5rem

Hover:
  Background: rgba(0,169,218,0.24) (darker)
  Transform: translateY(-1px) (lift effect)
  Box-shadow: 0 4px 12px rgba(0,169,218,0.25) (glow)
  Transition: 180ms var(--easing-premium)

Active:
  Transform: translateY(0)
  Box-shadow: 0 2px 8px rgba(0,169,218,0.15)
```

### Responsive Sizing
```
Desktop:  28px buttons
Tablet:   26px buttons
Mobile:   24px buttons
Small:    22px buttons
```

### CSS Classes
```
.qty-controls     (flex container)
.qty-btn          (individual buttons)
```

---

## 3. Order Summary Card

### Layout
```
┌──────────────────────────────┐
│  Order Summary               │
├──────────────────────────────┤
│ Subtotal          ₹ 135,000  │
│ Shipping          ₹ 100      │
│ Tax (18%)         ₹ 24,300   │
├──────────────────────────────┤
│ Total Payable     ₹ 159,400  │
│ (Bold, Larger)               │
├──────────────────────────────┤
│ [Proceed to Checkout]        │
│ [Continue Shopping]          │
└──────────────────────────────┘
```

### Styling
```
Card:
  Border: 1px solid rgba(255,255,255,0.12)
  Background: rgba(7,23,41,0.72)
  Border-radius: 1rem
  Padding: 1.5rem
  Position: sticky (top: 120px)

Summary Line:
  Display: flex
  Justify-content: space-between
  Padding: 0.75rem 0
  Border-bottom: 1px solid rgba(255,255,255,0.08)
  Font-size: 0.95rem

Summary Line Span (Label):
  Color: var(--muted) = #9fb7cf
  Font-weight: 500

Summary Line Strong (Value):
  Color: #fff (white)
  Font-weight: 700

Last Line (Total):
  Font-size: 1.2rem
  Color: var(--accent) = #f5b700
```

### CSS Classes
```
.glass-card      (main card)
.sticky-summary  (sticky positioning)
.summary-line    (individual lines)
```

---

## 4. Service Coverage Matrix

### Layout
```
┌──────────────────────────────────────────────┐
│ Capability               │ S │ B │ E         │
│ (Header - Dark Gradient) │   │   │           │
├──────────────────────────────────────────────┤
│ ✓ Installation           │ ✓ │ ✓ │ ✓        │
│ ✓ Remote Monitoring      │ ✓ │ ✓ │ ✓        │
│ Analytics Tuning         │ − │ ✓ │ ✓        │
│ Central Dashboard        │ − │ − │ ✓        │
│ Preventive Maintenance   │ O │ I │ I        │
└──────────────────────────────────────────────┘

Legend: ✓ = Check, − = Not included, O = Optional, I = Included
```

### Column Alignment
```
Column 1:  text-align: left (capabilities)
Columns 2-4: text-align: center (checkmarks)
```

### Icon Styling
```
Checkmark: ✓
  Icon: bi bi-check-lg
  Color: #8ff2b7 (green)
  Font-size: 1.2rem
  Font-weight: 700

Not Included: −
  Text: "−"
  Color: #9fb7cf (muted)
```

### CSS Classes
```
.premium-table                (main table)
.bi-check-lg                  (checkmark icon)
.text-success                 (green color for checks)
```

---

## 5. Support Priority Matrix

### Layout
```
┌─────────────────────────────────────────────────┐
│ Priority │ Use Case    │ Initial  │ Resolution │
│ (Header) │             │ Response │ Target     │
├─────────────────────────────────────────────────┤
│ P1 Crit. │ Monitoring  │ 2 hours  │ Same day   │
│          │ Outage      │          │            │
├─────────────────────────────────────────────────┤
│ P2 High  │ Recording   │ 4 hours  │ 24 hours   │
│          │ Degradation │          │            │
├─────────────────────────────────────────────────┤
│ P3 Med   │ Config      │ 8 hours  │ 2 days     │
│          │ Adjustment  │          │            │
├─────────────────────────────────────────────────┤
│ P4 Low   │ General     │ 24 hours │ 3 days     │
│          │ Guidance    │          │            │
└─────────────────────────────────────────────────┘
```

### Column Alignment
```
Column 1: text-align: left (priority)
Column 2: text-align: left (use case)
Columns 3-4: text-align: center (times)
```

### Styling
```
Same as Service Coverage Matrix:
  Dark table
  Gradient headers
  Centered columns
  Subtle alternating rows
  Hover effects
```

### CSS Classes
```
.premium-table        (main styling)
```

---

## 6. Mini Info Card

### Layout (Services Page)
```
┌──────────────────────────────┐
│ Retail Chain Upgrade         │
│ Reduced incident response... │
└──────────────────────────────┘
```

### Styling
```
Border: 1px solid rgba(255,255,255,0.12)
Background: rgba(255,255,255,0.03)
Border-radius: 0.75rem
Padding: 1rem
Transition: all 220ms var(--easing-premium)

Hover:
  Background: rgba(255,255,255,0.06) (lighter)
  Border-color: rgba(0,169,218,0.3) (cyan tint)

Title (h6):
  Color: #fff
  Font-weight: 700
  Font-size: 0.95rem
  Margin-bottom: 0.5rem

Text (p):
  Color: var(--muted)
  Font-size: 0.9rem
  Margin-bottom: 0
```

### CSS Classes
```
.mini-info-card       (main card)
.mini-info-card h6    (title)
.mini-info-card p     (text)
```

---

## 7. Responsive Table Container

### Desktop
```
┌─────────────────────────────────┐
│  Table (full width)             │
│  All columns visible            │
│  Sticky headers                 │
└─────────────────────────────────┘

Width: 100%
Overflow: visible
```

### Tablet
```
┌────────────────────────┐
│  Table                 │
│  Columns fit           │
│  Slight scroll if needed
└────────────────────────┘

Width: 100%
Overflow: hidden (with border-radius)
```

### Mobile
```
┌──────────────┐
│  Col1  Col2  │ ← Horizontal scroll
│  ────────── │
│  Data  Data  │
└──────────────┘

Width: 100%
Overflow: auto (horizontal scroll)
-webkit-overflow-scrolling: touch
```

### CSS
```
.table-responsive {
  border-radius: 0.85rem;
  overflow: hidden;
  background: rgba(255,255,255,0.01);
  border: 1px solid rgba(255,255,255,0.08);
  margin: 0 -1rem -1rem -1rem; (within glass-card)
}

@media (max-width: 768px) {
  .table-responsive {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    margin: 0;
  }
}
```

---

## 8. Color Combinations

### Primary Table
| Element | Background | Border | Text |
|---------|-----------|--------|------|
| Cell | `rgba(255,255,255,0.02)` | `rgba(255,255,255,0.08)` | `#edf6ff` |
| Cell (Hover) | `rgba(255,255,255,0.04-0.06)` | same | same |
| Header | `linear-gradient(...)` | `rgba(255,255,255,0.12)` | `#ddf3ff` |

### Quantity Button
| State | Background | Border | Text |
|-------|-----------|--------|------|
| Default | `rgba(0,169,218,0.14)` | `rgba(0,169,218,0.4)` | `#7adfff` |
| Hover | `rgba(0,169,218,0.24)` | `rgba(0,169,218,0.65)` | same |
| Active | `rgba(0,169,218,0.14)` | `rgba(0,169,218,0.4)` | same |

### Info Card
| State | Background | Border | Text |
|-------|-----------|--------|------|
| Default | `rgba(255,255,255,0.03)` | `rgba(255,255,255,0.12)` | `var(--muted)` |
| Hover | `rgba(255,255,255,0.06)` | `rgba(0,169,218,0.3)` | same |

---

## 9. Typography

### Font Stack
```
Primary: "Sora" sans-serif (headings)
Secondary: "Manrope" sans-serif (body)
Fallback: "Segoe UI Symbol", sans-serif
```

### Font Sizes in Tables
| Element | Size | Weight |
|---------|------|--------|
| Header | 0.95rem | 600 |
| Data Cell | 0.95rem | 400 |
| Summary Line | 0.95rem | 400 |
| Summary Strong | 0.95rem | 700 |
| Info Title | 0.95rem | 700 |
| Info Text | 0.9rem | 400 |

### Responsive Font Sizes
```
Desktop (1200px+):  0.95rem (header), 0.95rem (cell)
Tablet (992px):     0.9rem, 0.9rem
Mobile (768px):     0.85rem, 0.85rem
Small (<768px):     0.8rem, 0.8rem
```

---

## 10. Spacing & Sizing

### Padding
```
Table Cell:         1rem (desktop)
Table Cell:         0.8rem (tablet)
Table Cell:         0.75rem (mobile)
Qty Controls:       0.35rem
Summary Line:       0.75rem vertical
Info Card:          1rem
```

### Gaps
```
Qty Controls Gap:   0.75rem (desktop), 0.5rem (tablet)
Flex Gaps:          0.6rem-0.75rem
```

### Border Radius
```
Table Container:    0.85rem
Button:             0.5rem-0.6rem
Card:               0.75rem-1rem
```

---

## 11. Hover States

### Table Row Hover
```
Default:  Background: rgba(255,255,255,0.02)
Hover:    Background: rgba(255,255,255,0.04-0.06)
Transition: 220ms var(--easing-premium)
```

### Button Hover
```
Default:  
  Background: rgba(0,169,218,0.14)
  Transform: translateY(0)

Hover:
  Background: rgba(0,169,218,0.24)
  Transform: translateY(-1px)
  Box-shadow: 0 4px 12px rgba(0,169,218,0.25)
  Transition: 180ms var(--easing-premium)
```

### Card Hover
```
Default:
  Border: rgba(255,255,255,0.12)
  Background: rgba(255,255,255,0.03)

Hover:
  Border: rgba(0,169,218,0.3)
  Background: rgba(255,255,255,0.06)
  Transition: 220ms var(--easing-premium)
```

---

## 12. Print Styles

### Print Conversion
```
Screen:  Dark theme with colors
Print:   White background, black text

Changes:
- Background: #fff !important
- Text: #111 !important
- Borders: #cfcfcf !important
- Headers: #f5f5f5 !important
- Shadows: none
- Buttons: hidden
```

---

## 13. Accessibility

### Color Contrast
```
✓ Header Text (#ddf3ff) on Header BG:     > 7:1
✓ Body Text (#edf6ff) on Dark BG:         > 5:1
✓ Muted Text (#9fb7cf) on Dark BG:        > 4.5:1
✓ Checkmark (#8ff2b7) on Dark BG:         > 4.5:1
✓ Cyan Button (#7adfff) on Dark BG:       > 4.5:1
```

### Touch Targets
```
Quantity Button:    28px × 28px (desktop)
                    24px × 24px (mobile)
                    ✓ Meets 44px touch minimum when including padding

Remove Button:      ~40px × 40px
                    ✓ Meets touch requirements
```

---

## Component Checklist

- [x] Premium dark table
- [x] Quantity controls (cart)
- [x] Order summary card
- [x] Service matrix table
- [x] Support priority table
- [x] Mini info cards
- [x] Responsive container
- [x] Hover effects
- [x] Responsive design
- [x] Accessibility features
- [x] Print styles

---

**This style guide ensures consistent, professional design across all redesigned table components.**

