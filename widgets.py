# widgets.py
import json
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QScrollArea, QFrame, QStyledItemDelegate,
    QAbstractItemView, QStyle, QGraphicsDropShadowEffect,
    QDoubleSpinBox, QAbstractSpinBox, QTableWidget
)
from PySide6.QtGui import QColor, QPainter, QBrush, QPen, QFont, QRadialGradient, QDrag
# [修复] QObject, QEvent, Qt, Signal 必须从 QtCore 导入
from PySide6.QtCore import Qt, Signal, QPointF, QRectF, QObject, QEvent, QMimeData
from utils import ThemeManager, LanguageManager
from config import PRESET_TAGS, STATUS_COLORS


class TagRow(QWidget):
    removed = Signal(QWidget)
    def __init__(self, name, value="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignVCenter)
        
        self.lbl = QLabel(name)
        # [修复] 使用 accent 作为背景(浅色), btn_text 作为文字(深色)
        self.lbl.setStyleSheet(f"""
            background-color: {ThemeManager.current['accent']};
            color: {ThemeManager.current['btn_text']};
            border-radius: 8px;
            padding: 0 12px;
            font-weight: 600; 
            font-size: 14px;
            qproperty-alignment: 'AlignCenter';
        """)
        self.lbl.setFixedHeight(32) 
        
        self.inp = QLineEdit(value)
        try:
            placeholder = LanguageManager.t("concentration_placeholder")
        except:
            placeholder = "Conc."

        self.update_language()
        self.inp.setFixedHeight(40)
        
        self.btn = QPushButton("×")
        self.btn.setFixedSize(30, 30)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ThemeManager.current['text_sub']};
                border-radius: 15px;
                font-weight: bold; 
                font-size: 22px; 
                padding: 0px; 
                border: none;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {ThemeManager.current['bg_input']};
                color: #D93025;
            }}
        """)
        self.btn.clicked.connect(lambda: self.removed.emit(self))
        
        layout.addWidget(self.lbl)
        layout.addWidget(self.inp, 1)
        layout.addWidget(self.btn)

    def update_language(self):
        try:
            self.inp.setPlaceholderText(LanguageManager.t("concentration_placeholder"))
        except: pass
        
    def get_data(self):
        return {"name": self.lbl.text(), "val": self.inp.text()}

# 专门用于 TagEditor，防止滚轮像机关枪一样自动添加标签
class NonScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        # 彻底忽略滚轮事件，防止滚动页面时误加抗生素
        event.ignore()

class TagEditor(QWidget):
    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignVCenter)
        
        # [关键] 使用 NonScrollComboBox，防止滚轮误触
        self.combo = NonScrollComboBox() 
        self.combo.setEditable(True)
        self.combo.setFixedHeight(44)
        
        # 信号连接
        self.combo.currentIndexChanged.connect(self.on_add)
        self.combo.lineEdit().returnPressed.connect(self.on_manual)
        
        layout.addWidget(self.combo)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(120)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.container = QWidget()
        self.v_layout = QVBoxLayout(self.container)
        self.v_layout.setAlignment(Qt.AlignTop)
        self.v_layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout.setSpacing(10)
        
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)
        
        self.rows = []
        self.update_language()

    def update_language(self):
        current_idx = self.combo.currentIndex()
        self.combo.blockSignals(True)
        self.combo.clear()
        
        try:
            add_txt = LanguageManager.t("add_resistance")
        except:
            add_txt = "Add resistance..."
            
        self.combo.addItems([add_txt] + PRESET_TAGS)
        
        if current_idx >= 0: self.combo.setCurrentIndex(current_idx)
        else: self.combo.setCurrentIndex(0)
        self.combo.blockSignals(False)
        
        for row in self.rows: 
            row.update_language()
        
    def on_add(self, idx):
        if idx == 0: return
        text = self.combo.currentText()
        if text:
            self.add_tag(text)
            self.combo.setCurrentIndex(0)
        
    def on_manual(self):
        txt = self.combo.currentText().strip()
        try:
            default_txt = LanguageManager.t("add_resistance")
        except:
            default_txt = "Add resistance..."
            
        if txt and txt != default_txt:
            self.add_tag(txt)
            self.combo.setCurrentIndex(0)
            
    def add_tag(self, name, val=""):
        # 这里的 TagRow 必须在上面已经定义
        row = TagRow(name, val)
        row.removed.connect(self.remove_tag)
        self.v_layout.addWidget(row)
        self.rows.append(row)
        self.dataChanged.emit()
        
    def remove_tag(self, row):
        self.v_layout.removeWidget(row)
        row.deleteLater()
        if row in self.rows: self.rows.remove(row)
        self.dataChanged.emit()
        
    def set_data(self, json_str):
        self.blockSignals(True)
        for r in self.rows:
            self.v_layout.removeWidget(r)
            r.deleteLater()
        self.rows.clear()
        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                for x in data: 
                    row = TagRow(x['name'], x.get('val', ''))
                    row.removed.connect(self.remove_tag)
                    self.v_layout.addWidget(row)
                    self.rows.append(row)
        except: pass
        self.blockSignals(False)
        
    def get_json(self):
        return json.dumps([r.get_data() for r in self.rows], ensure_ascii=False)

class CryoVialDelegate(QStyledItemDelegate):
    def __init__(self, db):
        super().__init__()
        self.db = db

    # widgets.py -> CryoVialDelegate -> paint 方法

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        
        t = ThemeManager.current
        rect = option.rect
        data = index.data(Qt.UserRole)
        
        # === 1. 绘制背景 (状态色) ===
        cell_bg = Qt.transparent
        show_warning = False # 预警开关
        
        if data:
            status = data.get("status", "In Stock")
            is_discarded = "Discarded" in status or "报废" in status
            
            if "Removed" in status or "取出" in status:
                cell_bg = QColor(t['status_bg_removed'])
            elif is_discarded:
                cell_bg = QColor(t['status_bg_discarded'])
            elif QColor(t['status_bg_instock']).alpha() > 0:
                cell_bg = QColor(t['status_bg_instock'])

            # 预警判断：体积 < 30% 且不是报废
            vol = float(data.get('volume', 0))
            vol_max = float(data.get('vol_max', 0))
            if vol_max > 0 and (vol / vol_max) < 0.3 and not is_discarded:
                show_warning = True

        if cell_bg != Qt.transparent:
            painter.setPen(Qt.NoPen)
            painter.setBrush(cell_bg)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

        if not data:
            cx, cy = rect.center().x(), rect.center().y()
            radius = min(rect.width(), rect.height()) / 2 - 8
            painter.setPen(QPen(QColor(t['well_ring']), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            painter.restore()
            return

        # === 2. 计算几何 ===
        margin = 6
        draw_rect = QRectF(rect.left() + margin, rect.top() + margin, 
                           rect.width() - 2*margin, rect.height() - 2*margin)
        cx = draw_rect.center().x()
        cy = draw_rect.center().y()
        radius = min(draw_rect.width(), draw_rect.height()) / 2
        ring_width = 5.0 

        # === 3. 基础颜色 (轨道 & 进度) ===
        is_dark_theme = ("Dark" in t['bg_main']) or (t['bg_main'] == "#000000")
        if is_dark_theme:
            track_color = QColor(0, 0, 0, 20)
            progress_color = QColor(0, 0, 0, 255) 
        else:
            track_color = QColor(0, 0, 0, 20)
            progress_color = QColor(0, 0, 0, 255)

        # 绘制轨道
        painter.setPen(QPen(track_color, ring_width))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # === 4. 绘制进度条 ===
        vol = float(data.get('volume', 0))
        vol_max = float(data.get('vol_max', 0))
        
        if vol_max > 0:
            ratio = max(0.0, min(1.0, vol / vol_max))
            pen_progress = QPen(progress_color, ring_width)
            pen_progress.setCapStyle(Qt.RoundCap)
            painter.setPen(pen_progress)
            span_angle = int(-ratio * 360 * 16)
            arc_rect = QRectF(cx - radius, cy - radius, radius*2, radius*2)
            painter.drawArc(arc_rect, 90 * 16, span_angle)

        # === 5. 绘制中心类型圆点 ===
        stype = data.get("type", "Other")
        type_hex = self.db.cached_types.get(stype, "#8E8E93")
        circle_brush = QColor(type_hex)
        
        inner_radius = radius - (ring_width / 2) - 2
        if inner_radius < 1: inner_radius = 1
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(circle_brush)
        painter.drawEllipse(QPointF(cx, cy), inner_radius, inner_radius)

        # === 6. [修复] 绘制文字 (支持简写+特征双行显示) ===
        # 自动计算文字颜色 (深底白字，浅底黑字)
        is_dark_circle = circle_brush.lightness() < 160
        text_color = QColor("white") if is_dark_circle else QColor(t['text_main'])
        painter.setPen(text_color)
        
        short = data.get("short", "").strip()
        name = data.get("name", "").strip()
        feature = data.get("feature", "").strip()
        
        # 主文字：优先显示简写
        main_text = short if short else name
        if len(main_text) > 5: main_text = main_text[:4] + ".."
        
        text_rect = QRectF(cx - inner_radius, cy - inner_radius, inner_radius*2, inner_radius*2)
        
        if feature:
            # --- 双行模式 ---
            if len(feature) > 6: feature = feature[:5] + ".."
            
            # 上半部分：主文字 (加粗)
            f_main = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(f_main)
            r_top = QRectF(text_rect.left(), text_rect.top() + text_rect.height()*0.15, 
                           text_rect.width(), text_rect.height()*0.4)
            painter.drawText(r_top, Qt.AlignCenter | Qt.AlignBottom, main_text)
            
            # 下半部分：特征 (小字号)
            f_sub = QFont("Segoe UI", 7, QFont.Normal)
            painter.setFont(f_sub)
            
            # 特征颜色稍微淡一点
            sub_color = QColor(text_color)
            sub_color.setAlpha(200) 
            painter.setPen(sub_color)
            
            r_bottom = QRectF(text_rect.left(), text_rect.top() + text_rect.height()*0.55, 
                              text_rect.width(), text_rect.height()*0.3)
            painter.drawText(r_bottom, Qt.AlignCenter | Qt.AlignTop, feature)
            
        else:
            # --- 单行模式 ---
            f_main = QFont("Segoe UI", 10, QFont.Bold)
            painter.setFont(f_main)
            painter.drawText(text_rect, Qt.AlignCenter, main_text)

        # === 7. 绘制红色惊叹号图标 (Alert) ===
        if show_warning:
            warn_size = 14
            # 位置：圆环右上角
            wx = cx + radius * 0.7 - warn_size/2
            wy = cy - radius * 0.7 - warn_size/2
            warn_rect = QRectF(wx, wy, warn_size, warn_size)
            
            # 红底
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("#D93025"))
            painter.drawEllipse(warn_rect)
            
            # 白字
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(warn_rect, Qt.AlignCenter, "!")

        # === 8. 选中高亮 ===
        if option.state & QStyle.StateFlag.State_Selected:
            highlight_color = QColor("#FFFFFF") if is_dark_theme else QColor("#000000")
            pen = QPen(highlight_color, 3)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 12, 12)

        painter.restore()

class ModernToolTip(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 设为无边框窗口 + 总是置顶 + 不抢焦点
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10) # 留出阴影区域
        
        # 实际的卡片容器
        self.card = QFrame()
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(16, 12, 16, 12)
        self.card_layout.setSpacing(4)
        
        # 内容标签 (支持富文本)
        self.lbl_content = QLabel()
        self.lbl_content.setTextFormat(Qt.RichText)
        self.lbl_content.setWordWrap(False) # 让 HTML 表格决定宽度
        self.card_layout.addWidget(self.lbl_content)
        
        layout.addWidget(self.card)
        
        # 添加阴影特效
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(24)
        self.shadow.setOffset(0, 4)
        self.card.setGraphicsEffect(self.shadow)

    def show_tip(self, global_pos, html_content):
        t = ThemeManager.current
        
        # 动态设置样式 (确保深色模式适配)
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: {t['bg_panel']};
                border: 1px solid {t['border']};
                border-radius: 10px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        
        # 设置阴影颜色
        shadow_color = QColor(0, 0, 0, 80) if "Dark" in ThemeManager.current['bg_main'] else QColor(0, 0, 0, 30)
        self.shadow.setColor(shadow_color)
        
        self.lbl_content.setText(html_content)
        self.adjustSize()
        
        # 智能定位：防止超出屏幕右侧或底部
        screen = self.screen().availableGeometry()
        w, h = self.width(), self.height()
        x, y = global_pos.x() + 20, global_pos.y() + 20
        
        if x + w > screen.right():
            x = global_pos.x() - w - 10
        if y + h > screen.bottom():
            y = global_pos.y() - h - 10
            
        self.move(x, y)
        self.show()

    def hide_tip(self):
        self.hide()

# === [新增 1] 防误触滚轮过滤器 ===
class WheelFilter(QObject):
    """
    这是一个事件过滤器。
    作用：禁止 ComboBox/SpinBox/DateEdit 在没有获取焦点时响应鼠标滚轮。
    防止用户在滚动右侧详情页时，误触修改了数据。
    """
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            # 如果控件没有获得焦点，就拦截（吃掉）这个滚轮事件
            if not obj.hasFocus():
                event.ignore()
                return True # 返回 True 表示事件已被处理，不再向下传递
        return super().eventFilter(obj, event)


# === [新增 2] 现代步进器 (仿 iOS/胶囊风格) ===
from PySide6.QtWidgets import QDoubleSpinBox, QAbstractSpinBox

# widgets.py -> ModernNumberEdit 类 (替换整个类)

class ModernNumberEdit(QWidget):
    """
    自定义的数字输入框，布局为： [ - ]  数值  [ + ]
    完全替代原生的 QDoubleSpinBox 样式。
    """
    valueChanged = Signal(float) # 转发信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.btn_minus = QPushButton("－")
        self.btn_minus.setCursor(Qt.PointingHandCursor)
        self.btn_minus.setObjectName("step_btn") 
        self.btn_minus.setAutoRepeat(True) 
        self.btn_minus.setAutoRepeatDelay(500)
        self.btn_minus.setAutoRepeatInterval(100)
        
        # [修改] 使用 ModernDoubleSpinBox 替代原生 QDoubleSpinBox
        self.spin = ModernDoubleSpinBox() 
        self.spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
        self.spin.setAlignment(Qt.AlignCenter)
        self.spin.setFrame(False)
        self.spin.valueChanged.connect(self.valueChanged.emit)
        
        # [移除] 以前的 WheelFilter 逻辑可以删掉了，因为 ModernDoubleSpinBox 已经处理了
        # self._filter = WheelFilter(self)
        # self.spin.installEventFilter(self._filter)
        
        self.btn_plus = QPushButton("＋")
        self.btn_plus.setCursor(Qt.PointingHandCursor)
        self.btn_plus.setObjectName("step_btn")
        self.btn_plus.setAutoRepeat(True)
        
        self.btn_minus.clicked.connect(self.spin.stepDown)
        self.btn_plus.clicked.connect(self.spin.stepUp)
        
        layout.addWidget(self.btn_minus)
        layout.addWidget(self.spin, 1)
        layout.addWidget(self.btn_plus)
        
        self.update_style()

    def update_style(self):
        t = ThemeManager.current
        
        # [需求] 无论 Light/Dark，强制蓝底白字
        # 使用 iOS 风格的蓝色
        btn_color = "#007AFF" 
        text_color = "#FFFFFF"

        self.setStyleSheet(f"""
            /* [关键修复] 使用 ID 选择器 + !important 确保不被全局样式覆盖 */
            QPushButton#step_btn {{
                background-color: {btn_color};
                color: {text_color};
                border-radius: 16px;       /* 半径是宽度的一半 -> 圆形 */
                font-weight: bold;
                font-size: 18px;
                font-family: "Segoe UI", sans-serif;
                border: none;
                
                /* [关键] 强制锁定尺寸，防止被 padding 撑成椭圆 */
                min-width: 32px;
                max-width: 32px;
                min-height: 32px;
                max-height: 32px;
                padding: 0px; 
                margin: 0px;
            }}

            QPushButton#step_btn:hover {{
                background-color: #0062CC; /* 悬停深蓝 */
            }}
            
            QPushButton#step_btn:pressed {{
                background-color: #0051A8;
            }}
            
            /* 中间输入框 */
            QDoubleSpinBox {{
                background-color: transparent;
                color: {t['text_main']};
                font-size: 16px;
                font-weight: bold;
                padding: 0;
                border: none;
            }}
        """)

    def value(self): return self.spin.value()
    def setValue(self, v): self.spin.setValue(v)
    def setRange(self, min_v, max_v): self.spin.setRange(min_v, max_v)
    def setSuffix(self, s): self.spin.setSuffix(s)
    def setDecimals(self, d): self.spin.setDecimals(d)
    def blockSignals(self, b): return self.spin.blockSignals(b)

class ExcelGrid(QTableWidget):
    # 信号：源行, 源列, 目标行, 目标列
    drag_committed = Signal(int, int, int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # === 1. 基础设置 ===
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # [重要] 禁止双击编辑，防止还没保存就拖拽导致数据丢失
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # === 2. 开启拖放 ===
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        # 这里虽然设置 MoveAction，但在 dropEvent 里我们会改成 CopyAction
        self.setDefaultDropAction(Qt.MoveAction)
        
        # 记录拖拽源
        self._drag_row = -1
        self._drag_col = -1

    def mousePressEvent(self, event):
        """记录鼠标按下时的格子坐标（比 currentItem 更准）"""
        if event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                self._drag_row = item.row()
                self._drag_col = item.column()
            else:
                self._drag_row = -1
                self._drag_col = -1
        super().mousePressEvent(event)

    def startDrag(self, supportedActions):
        """开始拖拽"""
        if self._drag_row != -1 and self._drag_col != -1:
            super().startDrag(supportedActions)

    def dragEnterEvent(self, event):
        event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        """松手时触发"""
        target_item = self.itemAt(event.pos())
        if not target_item:
            return

        dst_r = target_item.row()
        dst_c = target_item.column()
        src_r = self._drag_row
        src_c = self._drag_col
        
        # === [核心修复] ===
        # 1. 如果源和目标是同一个格子（比如只是移动了一点点），直接忽略！
        if (src_r, src_c) == (dst_r, dst_c):
            event.ignore() # 忽略事件，什么都不发生
            return

        # 2. 如果是有效移动
        if src_r != -1 and src_c != -1:
            # 发出信号，让 main_window 去改数据库
            self.drag_committed.emit(src_r, src_c, dst_r, dst_c)

        # 3. [关键一步] 欺骗 Qt 说这是“复制”
        # 这样 QTableWidget 就不会自动清空源格子的内容了
        # 数据的移动/删除全权交给我们的数据库逻辑处理
        event.setDropAction(Qt.CopyAction)
        event.accept()

# === [新增 1] 防误触下拉框 ===
class ModernComboBox(QComboBox):
    def wheelEvent(self, event):
        """核心修复：只有获得焦点时才响应滚轮，否则传给父容器滚动页面"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

# === [新增 2] 防误触数字框 (用于 ModernNumberEdit 内部) ===
class ModernDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        """核心修复：只有获得焦点时才响应滚轮"""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()