"""Constants for the Litter-Robot integration."""
DOMAIN = "litterrobot"

CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_EVENTS = "notify_events"
CONF_NOTIFY_CRITICAL = "notify_critical"
CONF_NOTIFY_WARNING = "notify_warning"

EVENT_TYPES = [
    "clean_cycle_complete",
    "cat_sensor_interrupted",
    "waste_drawer_full",
    "pet_visit",
    "robot_online",
    "robot_offline",
    "drawer_removed",
    "bonnet_removed",
    "pinch_detected",
    "motor_fault",
]

DEFAULT_NOTIFY_EVENTS = list(EVENT_TYPES)

# Critical — hardware safety, bypass DND with loud sound
DEFAULT_CRITICAL_EVENTS = [
    "waste_drawer_full",
    "pinch_detected",
    "motor_fault",
]

# Warning — prevents cycling, time-sensitive (breaks Focus modes)
DEFAULT_WARNING_EVENTS = [
    "cat_sensor_interrupted",
    "robot_offline",
    "drawer_removed",
    "bonnet_removed",
]
