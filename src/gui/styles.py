"""
Centralized Design System for YouTube Music Pro.
Defines colors, typography, spacing, and modern QSS templates.
"""

# HSL-Based Palette (using QSS compatible hex or rgb equivalent)
# Primary: Deep Navy / Slate
# Accent: Teal / Emerald
COLORS = {
    "background": "#0F172A",      # Slate 900
    "surface": "#1E293B",         # Slate 800
    "surface_light": "#334155",   # Slate 700
    "border": "#475569",          # Slate 600
    "text_primary": "#F8FAFC",    # Slate 50
    "text_secondary": "#94A3B8",  # Slate 400
    "accent_primary": "#2DD4BF",  # Teal 400
    "accent_secondary": "#10B981", # Emerald 500
    "accent_hover": "#5EEAD4",    # Teal 300
    "error": "#F43F5E",           # Rose 500
    "success": "#22C55E",         # Green 500
}

# Typography Hierarchy (Major Third - 1.25)
# Base: 14px (standard desktop size)
TYPOGRAPHY = {
    "title_lg": "28px",    # ~2.0x
    "title_md": "22px",    # ~1.6x
    "body_lg": "18px",     # ~1.25x
    "body_md": "14px",     # Base
    "body_sm": "12px",     # Small
}

# Spacing & Targets
SIZES = {
    "touch_target": "48px",
    "button_height": "42px",
    "input_height": "44px",
    "radius_lg": "12px",
    "radius_md": "8px",
    "radius_sm": "4px",
}

# SHADOWS (using multiple layers for realism)
SHADOWS = {
    "glass": "rgba(0, 0, 0, 0.4)",
}

# QSS Templates
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {COLORS['background']};
}}

QWidget {{
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter italic', 'Roboto', sans-serif;
}}

QGroupBox {{
    font-weight: bold;
    border: 2px solid {COLORS['border']};
    border-radius: {SIZES['radius_lg']};
    margin-top: 20px;
    padding-top: 15px;
    background-color: {COLORS['surface']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 20px;
    padding: 0 8px;
    color: {COLORS['accent_primary']};
}}

QLineEdit, QComboBox {{
    padding: 10px 15px;
    border: 2px solid {COLORS['border']};
    border-radius: {SIZES['radius_md']};
    background-color: {COLORS['surface_light']};
    color: {COLORS['text_primary']};
    font-size: {TYPOGRAPHY['body_md']};
    min-height: 25px;
}}

QLineEdit:focus, QComboBox:focus {{
    border-color: {COLORS['accent_primary']};
}}

QPushButton {{
    padding: 10px 24px;
    border: none;
    border-radius: {SIZES['radius_md']};
    background-color: {COLORS['surface_light']};
    color: {COLORS['text_primary']};
    font-weight: bold;
    font-size: {TYPOGRAPHY['body_md']};
    min-height: 32px;
}}

QPushButton:hover {{
    background-color: {COLORS['border']};
}}

QPushButton:disabled {{
    background-color: {COLORS['surface']};
    color: {COLORS['text_secondary']};
}}

QPushButton#primaryButton {{
    background-color: {COLORS['accent_primary']};
    color: {COLORS['background']};
    font-size: {TYPOGRAPHY['body_lg']};
}}

QPushButton#primaryButton:hover {{
    background-color: {COLORS['accent_hover']};
}}

QProgressBar {{
    border: 1px solid {COLORS['border']};
    border-radius: {SIZES['radius_sm']};
    text-align: center;
    background-color: {COLORS['surface_light']};
}}

QProgressBar::chunk {{
    background-color: {COLORS['accent_primary']};
    border-radius: 2px;
}}

QScrollBar:vertical {{
    border: none;
    background: {COLORS['surface']};
    width: 10px;
    margin: 0px 0px 0px 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}

QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    gridline-color: {COLORS['border']};
    border-radius: {SIZES['radius_md']};
}}

QHeaderView::section {{
    background-color: {COLORS['surface_light']};
    padding: 10px;
    border: none;
    border-bottom: 2px solid {COLORS['accent_primary']};
    font-weight: bold;
}}
"""

MODAL_STYLE = MAIN_STYLE + f"""
QWidget {{
    background-color: {COLORS['background']};
}}
"""
