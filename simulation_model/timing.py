from enum import Enum


class TimingType(Enum):
    FIXED = "FIXED",
    EXPONENTIAL = "EXPONENTIAL"


class ProcessTimeCategory(Enum):
    ARRIVAL = "ARRIVAL"
    SERVICE = "SERVICE"


class TimeUnit(Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"
    WEEKDAY = "weekday"


class TimeInterval:

    def __init__(self, seconds=0, minutes=0, hours=0, days=0, weeks=0):
        self.seconds = seconds
        self.minutes = minutes
        self.hours = hours
        self.days = days
        self.weeks = weeks
        if all(x == 0 for x in [seconds, minutes, hours, days, weeks]):
            raise RuntimeWarning("Instant TimeInterval initialized (duration is zero).")

    def get_seconds(self) -> int:
        time_total = self.seconds
        time_total += 60 * self.minutes
        time_total += 60 * 60 * self.hours
        time_total += 60 * 60 * 24 * self.days
        time_total += 60 * 60 * 24 * 7 * self.weeks
        return time_total


class TimingFunction:

    def __init__(self, args: list, timing_type: TimingType, function_name: str = None):
        self.function_name = function_name
        self.args = args
        self.timing_type = timing_type

    def get_all_SML(self):
        call_sml = self.get_call_SML()
        body_sml = self.get_body_SML()
        all_sml = "fun {0}={1}".format(
            call_sml,
            body_sml
        )
        return all_sml

    def get_call_SML(self):
        if self.function_name is None:
            raise AttributeError("Anonymous method cannot be called explicitly.")
        return self.function_name + "(" + ",".join(self.args) + ")"

    def get_function_name_SML(self):
        return self.function_name

    def sample(self):
        raise NotImplementedError()


class FixedTimingFunction(TimingFunction):

    def __init__(self, fixed_time: TimeInterval, function_name=None):
        super().__init__([], TimingType.FIXED, function_name)
        self.fixed_time = fixed_time

    def get_body_SML(self):
        return "({0})".format(str(float(self.fixed_time.get_seconds())))

    def sample(self):
        return self.fixed_time.get_seconds()


class ExponentialTimingFunction(TimingFunction):

    def __init__(self, average_value: TimeInterval, maximal_value: TimeInterval, function_name=None):
        super().__init__([], TimingType.EXPONENTIAL, function_name)
        self.average_value = average_value
        self.maximal_value = maximal_value

    def get_body_SML(self):
        return "let val x = exponential(1.0/{1}) in if x > {2} then {0}() else x end:real;".format(
            self.function_name,
            str(float(self.average_value.get_seconds())),
            str(float(self.maximal_value.get_seconds()))
        )

    def sample(self):
        raise NotImplementedError()


class ActivityTiming:

    def __init__(self,
                 activity_name: str,
                 execution_delay: TimingFunction):
        self.activity_name = activity_name
        self.execution_delay = execution_delay


class TimeDensity:

    def __init__(self):
        pass

    def get_as_dict(self):
        raise NotImplementedError()


class WeekdayDensity(TimeDensity):

    def __init__(self, monday_d: float, tuesday_d: float, wednesday_d: float, thursday_d: float, friday_d: float,
                 saturday_d: float, sunday_d: float):
        super().__init__()
        self.monday_d = monday_d
        self.tuesday_d = tuesday_d
        self.wednesday_d = wednesday_d
        self.thursday_d = thursday_d
        self.friday_d = friday_d
        self.saturday_d = saturday_d
        self.sunday_d = sunday_d

    def get_as_dict(self):
        return {
            "Mon": self.monday_d,
            "Tue": self.tuesday_d,
            "Wed": self.wednesday_d,
            "Thu": self.thursday_d,
            "Fri": self.friday_d,
            "Sat": self.saturday_d,
            "Sun": self.sunday_d,
        }

    @classmethod
    def StandardDensity(cls):
        """
        Standard workweek labor densities. People work during the week and not on the weekend.

        :return: A WeekdayDensity object
        """
        return cls(1, 1, 1, 1, 0.8, 0, 0)


class HourDensity(TimeDensity):

    def __init__(self, h00: float, h01: float, h02: float, h03: float, h04: float, h05: float, h06: float, h07: float,
                 h08: float, h09: float, h10: float, h11: float, h12: float, h13: float, h14: float, h15: float,
                 h16: float, h17: float, h18: float, h19: float, h20: float, h21: float, h22: float, h23: float):
        super().__init__()
        self.h00 = h00
        self.h01 = h01
        self.h02 = h02
        self.h03 = h03
        self.h04 = h04
        self.h05 = h05
        self.h06 = h06
        self.h07 = h07
        self.h08 = h08
        self.h09 = h09
        self.h10 = h10
        self.h11 = h11
        self.h12 = h12
        self.h13 = h13
        self.h14 = h14
        self.h15 = h15
        self.h16 = h16
        self.h17 = h17
        self.h18 = h18
        self.h19 = h19
        self.h20 = h20
        self.h21 = h21
        self.h22 = h22
        self.h23 = h23

    def get_as_dict(self):
        keys = ["0" + str(i) if i < 10 else str(i) for i in range(24)]
        return {
            k: getattr(self, f"h{k}", None)
            for k in keys
        }

    @classmethod
    def StandardDensity(cls):
        """
        Standard workday labor densities. People work during the day and not at night.

        :return: A HourDensity object
        """
        return cls(0, 0, 0, 0, 0, 0, 0, 0.5, 0.5, 1, 1, 1,
                   0.5, 1, 1, 1, 1, 0.5, 0.5, 0, 0, 0, 0, 0)


class TimeDensityCalendar:

    def __init__(self, weekday_density: WeekdayDensity, hour_density: HourDensity):
        self.weekday_density = weekday_density
        self.hour_density = hour_density

    @classmethod
    def StandardDensity(cls):
        """
        Standard labor densities, i.e., not at weekends and not at night,
        see the standard constructors of the weekday and hour densities.

        :return: A TimeDensity object
        """
        return cls(WeekdayDensity.StandardDensity(), HourDensity.StandardDensity())


class ActivityTimingManager:
    activity_timings: dict[str, ActivityTiming]

    def __init__(self, activity_timings=None):
        if activity_timings is None:
            activity_timings = dict()
        self.activity_timings = activity_timings

    def add_activity_timing(self, activity_id: str, activity_timing: ActivityTiming):
        self.activity_timings[activity_id] = activity_timing

    def get_activity_timing(self, activity_name: str):
        return self.activity_timings[activity_name]

    def has_activity(self, activity_name: str):
        return activity_name in self.activity_timings

