"""Interface Manager

This module implements comprehensive UI/UX features for the recruitment system.
It follows SOTA practices including:
1. Adaptive and contextual design
2. Accessibility and inclusivity
3. Modern interaction patterns
4. Real-time feedback
5. Personalized experiences
6. Error boundaries
7. State management
8. Performance optimization
9. Analytics tracking

The design is inspired by patterns in the OpenManus-main repository."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ThemeMode(Enum):
    """UI theme modes."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"
    HIGH_CONTRAST = "high_contrast"

class DeviceType(Enum):
    """Device types for responsive design."""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"

@dataclass
class UIConfig:
    """UI configuration."""
    theme_mode: ThemeMode = ThemeMode.SYSTEM
    animation_enabled: bool = True
    font_size: int = 16
    high_contrast: bool = False
    reduced_motion: bool = False
    screen_reader: bool = False
    keyboard_navigation: bool = True
    auto_complete: bool = True
    tooltip_delay: float = 0.5
    error_boundary_enabled: bool = True
    analytics_enabled: bool = True
    performance_monitoring: bool = True
    state_persistence: bool = True

@dataclass
class LayoutConfig:
    """Layout configuration."""
    sidebar_width: int = 250
    header_height: int = 64
    footer_height: int = 48
    content_max_width: int = 1200
    grid_columns: int = 12
    spacing_unit: int = 8

@dataclass
class AnalyticsEvent:
    """Analytics event data."""
    event_type: str
    component_id: str
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)

class ErrorBoundary:
    """Error boundary for component error handling."""
    
    def __init__(self, fallback: Optional[Callable] = None):
        """Initialize error boundary.
        
        Args:
            fallback: Optional fallback render function
        """
        self.has_error = False
        self.error: Optional[Exception] = None
        self.error_info: Dict[str, Any] = {}
        self.fallback = fallback
        
    def catch(self, error: Exception, error_info: Dict[str, Any]):
        """Catch and handle error.
        
        Args:
            error: Caught exception
            error_info: Error context information
        """
        self.has_error = True
        self.error = error
        self.error_info = error_info
        logger.error(f"Error boundary caught: {error}", exc_info=True)
        
    def reset(self):
        """Reset error boundary state."""
        self.has_error = False
        self.error = None
        self.error_info = {}

class StateManager:
    """Manages component state and persistence."""
    
    def __init__(self):
        """Initialize state manager."""
        self.state: Dict[str, Any] = {}
        self.listeners: Dict[str, List[Callable]] = {}
        
    def get_state(self, key: str) -> Any:
        """Get state value.
        
        Args:
            key: State key
            
        Returns:
            State value if found, None otherwise
        """
        return self.state.get(key)
        
    def set_state(self, key: str, value: Any):
        """Set state value.
        
        Args:
            key: State key
            value: New state value
        """
        self.state[key] = value
        self._notify_listeners(key)
        
    def add_listener(self, key: str, listener: Callable):
        """Add state change listener.
        
        Args:
            key: State key
            listener: Listener callback
        """
        if key not in self.listeners:
            self.listeners[key] = []
        self.listeners[key].append(listener)
        
    def remove_listener(self, key: str, listener: Callable):
        """Remove state change listener.
        
        Args:
            key: State key
            listener: Listener callback
        """
        if key in self.listeners:
            self.listeners[key].remove(listener)
            
    def _notify_listeners(self, key: str):
        """Notify state change listeners.
        
        Args:
            key: Changed state key
        """
        if key in self.listeners:
            value = self.state[key]
            for listener in self.listeners[key]:
                listener(value)

class PerformanceMonitor:
    """Monitors component rendering and interaction performance."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics: Dict[str, List[float]] = {
            "render_time": [],
            "interaction_time": [],
            "load_time": []
        }
        
    def start_measure(self, metric_type: str) -> float:
        """Start performance measurement.
        
        Args:
            metric_type: Type of metric to measure
            
        Returns:
            Start timestamp
        """
        return time.time()
        
    def end_measure(self, metric_type: str, start_time: float):
        """End performance measurement.
        
        Args:
            metric_type: Type of metric measured
            start_time: Measurement start timestamp
        """
        duration = time.time() - start_time
        self.metrics[metric_type].append(duration)
        
        # Log if performance threshold exceeded
        threshold = self._get_threshold(metric_type)
        if duration > threshold:
            logger.warning(
                f"Performance threshold exceeded for {metric_type}: "
                f"{duration:.2f}s > {threshold:.2f}s"
            )
            
    def get_average(self, metric_type: str) -> float:
        """Get average metric value.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Average value
        """
        values = self.metrics[metric_type]
        return sum(values) / len(values) if values else 0
        
    def _get_threshold(self, metric_type: str) -> float:
        """Get performance threshold for metric.
        
        Args:
            metric_type: Type of metric
            
        Returns:
            Threshold value in seconds
        """
        thresholds = {
            "render_time": 0.1,  # 100ms
            "interaction_time": 0.05,  # 50ms
            "load_time": 0.5  # 500ms
        }
        return thresholds.get(metric_type, float("inf"))

class AnalyticsTracker:
    """Tracks UI analytics events."""
    
    def __init__(self):
        """Initialize analytics tracker."""
        self.events: List[AnalyticsEvent] = []
        
    def track_event(
        self,
        event_type: str,
        component_id: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Track analytics event.
        
        Args:
            event_type: Type of event
            component_id: ID of component
            data: Optional event data
        """
        event = AnalyticsEvent(
            event_type=event_type,
            component_id=component_id,
            data=data or {}
        )
        self.events.append(event)
        
    def get_events(
        self,
        event_type: Optional[str] = None,
        component_id: Optional[str] = None
    ) -> List[AnalyticsEvent]:
        """Get tracked events.
        
        Args:
            event_type: Optional event type filter
            component_id: Optional component ID filter
            
        Returns:
            Filtered events
        """
        events = self.events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
            
        if component_id:
            events = [e for e in events if e.component_id == component_id]
            
        return events

class Component(ABC):
    """Base class for UI components."""
    
    def __init__(self, id: str, visible: bool = True):
        """Initialize component.
        
        Args:
            id: Component identifier
            visible: Initial visibility
        """
        self.id = id
        self.visible = visible
        self.children: List[Component] = []
        self.parent: Optional[Component] = None
        self.styles: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[callable]] = {}
        self.error_boundary = ErrorBoundary()
        self.state = StateManager()
        self.performance = PerformanceMonitor()
        
    def render(self) -> Dict[str, Any]:
        """Render component with error boundary.
        
        Returns:
            Component render data
        """
        try:
            start_time = self.performance.start_measure("render_time")
            result = self._render()
            self.performance.end_measure("render_time", start_time)
            return result
        except Exception as e:
            self.error_boundary.catch(e, {
                "component": self.id,
                "timestamp": time.time()
            })
            if self.error_boundary.fallback:
                return self.error_boundary.fallback()
            return {
                "id": self.id,
                "type": "error",
                "error": str(e)
            }
            
    @abstractmethod
    def _render(self) -> Dict[str, Any]:
        """Internal render implementation.
        
        Returns:
            Component render data
        """
        pass
        
    def add_child(self, child: 'Component'):
        """Add child component.
        
        Args:
            child: Child component
        """
        child.parent = self
        self.children.append(child)
        
    def remove_child(self, child: 'Component'):
        """Remove child component.
        
        Args:
            child: Child component
        """
        if child in self.children:
            child.parent = None
            self.children.remove(child)
            
    def add_event_handler(self, event: str, handler: callable):
        """Add event handler.
        
        Args:
            event: Event type
            handler: Event handler function
        """
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
        
    def trigger_event(self, event: str, data: Any = None):
        """Trigger component event.
        
        Args:
            event: Event type
            data: Optional event data
        """
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            handler(data)

class Page(Component):
    """Page component."""
    
    def __init__(
        self,
        id: str,
        title: str,
        layout: Optional[str] = None
    ):
        """Initialize page.
        
        Args:
            id: Page identifier
            title: Page title
            layout: Optional layout template
        """
        super().__init__(id)
        self.title = title
        self.layout = layout or "default"
        self.meta: Dict[str, str] = {}
        
    def render(self) -> Dict[str, Any]:
        """Render page.
        
        Returns:
            Page render data
        """
        return {
            "id": self.id,
            "type": "page",
            "title": self.title,
            "layout": self.layout,
            "meta": self.meta,
            "children": [child.render() for child in self.children]
        }

class Form(Component):
    """Form component."""
    
    def __init__(
        self,
        id: str,
        fields: List[Dict[str, Any]],
        submit_handler: callable
    ):
        """Initialize form.
        
        Args:
            id: Form identifier
            fields: Form field definitions
            submit_handler: Form submission handler
        """
        super().__init__(id)
        self.fields = fields
        self.values: Dict[str, Any] = {}
        self.errors: Dict[str, str] = {}
        self.submitted = False
        self.add_event_handler("submit", submit_handler)
        
    def render(self) -> Dict[str, Any]:
        """Render form.
        
        Returns:
            Form render data
        """
        return {
            "id": self.id,
            "type": "form",
            "fields": self.fields,
            "values": self.values,
            "errors": self.errors,
            "submitted": self.submitted
        }
        
    def validate(self) -> bool:
        """Validate form values.
        
        Returns:
            True if valid, False otherwise
        """
        self.errors = {}
        valid = True
        
        for field in self.fields:
            field_id = field["id"]
            value = self.values.get(field_id)
            
            # Required field
            if field.get("required", False) and not value:
                self.errors[field_id] = "This field is required"
                valid = False
                continue
                
            # Field type validation
            if value:
                field_type = field.get("type", "text")
                if not self._validate_field_type(value, field_type):
                    self.errors[field_id] = f"Invalid {field_type} value"
                    valid = False
                    
            # Custom validation
            validator = field.get("validator")
            if validator and value:
                error = validator(value)
                if error:
                    self.errors[field_id] = error
                    valid = False
                    
        return valid
        
    def _validate_field_type(self, value: Any, field_type: str) -> bool:
        """Validate field value type.
        
        Args:
            value: Field value
            field_type: Field type
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if field_type == "number":
                float(value)
            elif field_type == "email":
                # Basic email validation
                if "@" not in value or "." not in value:
                    return False
            elif field_type == "date":
                datetime.strptime(value, "%Y-%m-%d")
            # Add more type validations as needed
        except:
            return False
            
        return True
        
    def submit(self):
        """Submit form."""
        if self.validate():
            self.submitted = True
            self.trigger_event("submit", self.values)
        else:
            self.trigger_event("validation_error", self.errors)

class DataTable(Component):
    """Data table component."""
    
    def __init__(
        self,
        id: str,
        columns: List[Dict[str, Any]],
        data: List[Dict[str, Any]],
        page_size: int = 10
    ):
        """Initialize data table.
        
        Args:
            id: Table identifier
            columns: Column definitions
            data: Table data
            page_size: Rows per page
        """
        super().__init__(id)
        self.columns = columns
        self.data = data
        self.page_size = page_size
        self.current_page = 1
        self.sort_column = None
        self.sort_direction = "asc"
        self.filtered_data = data
        
    def render(self) -> Dict[str, Any]:
        """Render data table.
        
        Returns:
            Table render data
        """
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_data = self.filtered_data[start:end]
        
        return {
            "id": self.id,
            "type": "data_table",
            "columns": self.columns,
            "data": page_data,
            "total_rows": len(self.filtered_data),
            "page_size": self.page_size,
            "current_page": self.current_page,
            "sort_column": self.sort_column,
            "sort_direction": self.sort_direction
        }
        
    def sort(self, column: str, direction: str = "asc"):
        """Sort table data.
        
        Args:
            column: Column to sort by
            direction: Sort direction ("asc" or "desc")
        """
        self.sort_column = column
        self.sort_direction = direction
        
        reverse = direction == "desc"
        self.filtered_data.sort(
            key=lambda row: row.get(column, ""),
            reverse=reverse
        )
        
    def filter(self, filters: Dict[str, Any]):
        """Filter table data.
        
        Args:
            filters: Column filters
        """
        self.filtered_data = self.data.copy()
        
        for column, value in filters.items():
            if value:
                self.filtered_data = [
                    row for row in self.filtered_data
                    if str(value).lower() in str(row.get(column, "")).lower()
                ]
                
        self.current_page = 1
        
    def set_page(self, page: int):
        """Set current page.
        
        Args:
            page: Page number
        """
        total_pages = (len(self.filtered_data) + self.page_size - 1) // self.page_size
        self.current_page = max(1, min(page, total_pages))

class Chart(Component):
    """Chart component."""
    
    def __init__(
        self,
        id: str,
        type: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ):
        """Initialize chart.
        
        Args:
            id: Chart identifier
            type: Chart type
            data: Chart data
            options: Optional chart options
        """
        super().__init__(id)
        self.type = type
        self.data = data
        self.options = options or {}
        
    def render(self) -> Dict[str, Any]:
        """Render chart.
        
        Returns:
            Chart render data
        """
        return {
            "id": self.id,
            "type": "chart",
            "chart_type": self.type,
            "data": self.data,
            "options": self.options
        }
        
    def update_data(self, data: Dict[str, Any]):
        """Update chart data.
        
        Args:
            data: New chart data
        """
        self.data = data
        self.trigger_event("data_update", data)

class InterfaceManager:
    def __init__(
        self,
        ui_config: Optional[UIConfig] = None,
        layout_config: Optional[LayoutConfig] = None
    ):
        """Initialize interface manager.
        
        Args:
            ui_config: Optional UI configuration
            layout_config: Optional layout configuration
        """
        self.ui_config = ui_config or UIConfig()
        self.layout_config = layout_config or LayoutConfig()
        
        self.pages: Dict[str, Page] = {}
        self.current_page: Optional[Page] = None
        self.navigation_history: List[str] = []
        self.device_type = DeviceType.DESKTOP
        self.components: Dict[str, Component] = {}
        
        # New features
        self.state = StateManager()
        self.performance = PerformanceMonitor()
        self.analytics = AnalyticsTracker()
        
    def create_page(
        self,
        id: str,
        title: str,
        layout: Optional[str] = None
    ) -> Page:
        """Create new page.
        
        Args:
            id: Page identifier
            title: Page title
            layout: Optional layout template
            
        Returns:
            Created page
        """
        page = Page(id, title, layout)
        self.pages[id] = page
        self.components[id] = page
        return page
        
    def navigate(self, page_id: str):
        """Navigate to page.
        
        Args:
            page_id: Page identifier
        """
        if page_id in self.pages:
            if self.current_page:
                self.navigation_history.append(self.current_page.id)
            self.current_page = self.pages[page_id]
            
    def back(self) -> bool:
        """Navigate back in history.
        
        Returns:
            True if navigation successful, False otherwise
        """
        if self.navigation_history:
            previous_page = self.navigation_history.pop()
            self.current_page = self.pages[previous_page]
            return True
        return False
        
    def create_form(
        self,
        id: str,
        fields: List[Dict[str, Any]],
        submit_handler: callable
    ) -> Form:
        """Create form component.
        
        Args:
            id: Form identifier
            fields: Form field definitions
            submit_handler: Form submission handler
            
        Returns:
            Created form
        """
        form = Form(id, fields, submit_handler)
        self.components[id] = form
        return form
        
    def create_table(
        self,
        id: str,
        columns: List[Dict[str, Any]],
        data: List[Dict[str, Any]],
        page_size: int = 10
    ) -> DataTable:
        """Create data table component.
        
        Args:
            id: Table identifier
            columns: Column definitions
            data: Table data
            page_size: Rows per page
            
        Returns:
            Created table
        """
        table = DataTable(id, columns, data, page_size)
        self.components[id] = table
        return table
        
    def create_chart(
        self,
        id: str,
        type: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Chart:
        """Create chart component.
        
        Args:
            id: Chart identifier
            type: Chart type
            data: Chart data
            options: Optional chart options
            
        Returns:
            Created chart
        """
        chart = Chart(id, type, data, options)
        self.components[id] = chart
        return chart
        
    def get_component(self, id: str) -> Optional[Component]:
        """Get component by ID.
        
        Args:
            id: Component identifier
            
        Returns:
            Component if found, None otherwise
        """
        return self.components.get(id)
        
    def remove_component(self, id: str):
        """Remove component.
        
        Args:
            id: Component identifier
        """
        if id in self.components:
            component = self.components[id]
            
            # Remove from parent
            if component.parent:
                component.parent.remove_child(component)
                
            # Remove children
            for child in component.children:
                self.remove_component(child.id)
                
            del self.components[id]
            
    def update_theme(self, mode: ThemeMode):
        """Update UI theme mode.
        
        Args:
            mode: New theme mode
        """
        self.ui_config.theme_mode = mode
        
    def set_device_type(self, device_type: DeviceType):
        """Set device type for responsive design.
        
        Args:
            device_type: Device type
        """
        self.device_type = device_type
        
    def track_event(
        self,
        event_type: str,
        component_id: str,
        data: Optional[Dict[str, Any]] = None
    ):
        """Track UI analytics event.
        
        Args:
            event_type: Type of event
            component_id: ID of component
            data: Optional event data
        """
        if self.ui_config.analytics_enabled:
            self.analytics.track_event(event_type, component_id, data)
            
    def measure_performance(
        self,
        metric_type: str,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Measure operation performance.
        
        Args:
            metric_type: Type of metric
            operation: Operation to measure
            *args: Operation arguments
            **kwargs: Operation keyword arguments
            
        Returns:
            Operation result
        """
        if self.ui_config.performance_monitoring:
            start_time = self.performance.start_measure(metric_type)
            result = operation(*args, **kwargs)
            self.performance.end_measure(metric_type, start_time)
            return result
        return operation(*args, **kwargs)
        
    def render(self) -> Dict[str, Any]:
        """Render current interface state.
        
        Returns:
            Interface render data
        """
        if not self.current_page:
            return {}
            
        return {
            "config": {
                "ui": self.__dict__[self.ui_config],
                "layout": self.__dict__[self.layout_config]
            },
            "device_type": self.device_type.value,
            "page": self.current_page.render()
        }