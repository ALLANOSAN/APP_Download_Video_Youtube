from PySide6.QtWidgets import QWidget, QVBoxLayout, QFrame
from PySide6.QtCore import Property, QPropertyAnimation
from PySide6.QtGui import QPainter, QLinearGradient, QColor, QBrush

class SkeletonWidget(QWidget):
    """
    A widget that displays a shimmering skeleton screen effect.
    Usually used as an overlay during loading.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = -1.0
        self.animation = QPropertyAnimation(self, b"shimmer_offset")
        self.animation.setDuration(1500)
        self.animation.setStartValue(-1.0)
        self.animation.setEndValue(1.0)
        self.animation.setLoopCount(-1)  # Infinite

        # Color palette from styles.py
        self.bg_color = QColor("#1E293B")  # surface
        self.shimmer_color = QColor("#334155") # surface_light

    @Property(float)
    def shimmer_offset(self):
        return self._offset

    @shimmer_offset.setter
    def shimmer_offset(self, value):
        self._offset = value
        self.update()

    def start(self):
        self.animation.start()
        self.show()

    def stop(self):
        self.animation.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        painter.fillRect(self.rect(), self.bg_color)

        # Create shimmer gradient
        gradient = QLinearGradient()
        gradient.setStart(self.width() * self._offset, 0)
        gradient.setFinalStop(self.width() * (self._offset + 0.5), 0)

        gradient.setColorAt(0, self.bg_color)
        gradient.setColorAt(0.5, self.shimmer_color)
        gradient.setColorAt(1, self.bg_color)

        painter.fillRect(self.rect(), QBrush(gradient))

class SkeletonCard(QFrame):
    """A card-shaped skeleton for grid items."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 240)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border-radius: 12px;
                border: 1px solid #475569;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Thumbnail placeholder
        self.thumb = SkeletonWidget(self)
        self.thumb.setFixedHeight(120)
        layout.addWidget(self.thumb)

        # Title placeholder
        self.title = SkeletonWidget(self)
        self.title.setFixedHeight(20)
        layout.addWidget(self.title)

        # Subtitle placeholder
        self.sub = SkeletonWidget(self)
        self.sub.setFixedHeight(15)
        self.sub.setFixedWidth(100)
        layout.addWidget(self.sub)

    def start(self):
        self.thumb.start()
        self.title.start()
        self.sub.start()

    def stop(self):
        self.thumb.stop()
        self.title.stop()
        self.sub.stop()
