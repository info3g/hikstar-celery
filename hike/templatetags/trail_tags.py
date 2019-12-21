import datetime

from django import template

register = template.Library()


@register.filter
def get_distance(total_length: float) -> float:
    if not total_length:
        return 0.0
    value = float(total_length) / 1000.0
    return f"{value:.2f}"


@register.filter
def duration_to_hours(duration: int) -> str:
    if duration is None:
        return "unknown"
    tdelta = datetime.timedelta(minutes=duration)
    mm, ss = divmod(tdelta.seconds, 60)
    hh, mm = divmod(mm, 60)

    time_str = f"{hh}h{mm}"
    if tdelta.days:
        return f"{tdelta.days}d {time_str}"
    return time_str
