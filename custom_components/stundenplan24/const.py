"""Constants for the Stundenplan24 integration."""

DOMAIN = "stundenplan24"

# Config flow
CONF_SCHOOL_URL = "school_url"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_STUDENT_ID = "student_id"

# Default values
DEFAULT_SCAN_INTERVAL = 30  # minutes
DEFAULT_NAME = "Stundenplan24"

# Sensor types
SENSOR_TYPE_CURRENT_LESSON = "current_lesson"
SENSOR_TYPE_NEXT_LESSON = "next_lesson"
SENSOR_TYPE_DAY_SCHEDULE = "day_schedule"
SENSOR_TYPE_SUBSTITUTIONS_TODAY = "substitutions_today"
SENSOR_TYPE_SUBSTITUTIONS_TOMORROW = "substitutions_tomorrow"

# Attributes
ATTR_SUBJECT = "subject"
ATTR_TEACHER = "teacher"
ATTR_ROOM = "room"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_LESSON_TYPE = "lesson_type"
ATTR_SUBSTITUTIONS = "substitutions"
ATTR_SCHEDULE = "schedule"
