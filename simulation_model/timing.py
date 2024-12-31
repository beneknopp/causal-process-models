from enum import Enum


class TimingType(Enum):
    FIXED = "FIXED",
    EXPONENTIAL = "EXPONENTIAL"


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

    def get_call_SML(self):
        if self.function_name is None:
            raise AttributeError("Anonymous method cannot be called explicitly.")
        return self.function_name + "(" + ",".join(self.args) + ")"

    def get_all_SML(self):
        raise NotImplementedError()

    def sample(self):
        raise NotImplementedError()


class FixedTimingFunction(TimingFunction):

    def __init__(self, fixed_time: TimeInterval, function_name=None):
        super().__init__([], TimingType.FIXED, function_name)
        self.fixed_time = fixed_time

    def get_all_SML(self):
        call_sml = self.get_call_SML()
        body_sml = self.__get_body_SML()
        all_sml = "{0}={1}".format(
            call_sml,
            body_sml
        )
        return all_sml

    def __get_body_SML(self):
        return "ModelTime.fromInt({0})".format(str(self.fixed_time.get_seconds()))

    def sample(self):
        return self.fixed_time.get_seconds()


class ActivityTiming:

    def __init__(self,
                 activity_name: str,
                 execution_delay: TimingFunction):
        self.activity_name = activity_name
        self.execution_delay = execution_delay


class WeekdayDensity:

    def __init__(self, monday_d: float, tuesday_d: float, wednesday_d: float,
                 thursday_d: float, friday_d: float, saturday_d: float, sunday_d: float):
        self.monday_d = monday_d
        self.tuesday_d = tuesday_d
        self.wednesday_d = wednesday_d
        self.thursday_d = thursday_d
        self.friday_d = friday_d
        self.saturday_d = saturday_d
        self.sunday_d = sunday_d

    @classmethod
    def StandardDensity(cls):
        """
        Standard workweek labor densities. People work during the week and not on the weekend.

        :return: A WeekdayDensity object
        """
        return cls(1, 1, 1, 1, 0.8, 0, 0)


class HourDensity:

    def __init__(self,
                 h0: float, h1: float, h2: float, h3: float, h4: float,
                 h5: float, h6: float, h7: float, h8: float, h9: float,
                 h10: float, h11: float, h12: float, h13: float, h14: float,
                 h15: float, h16: float, h17: float, h18: float, h19: float,
                 h20: float, h21: float, h22: float, h23: float):
        self.h0 = h0
        self.h1 = h1
        self.h2 = h2
        self.h3 = h3
        self.h4 = h4
        self.h5 = h5
        self.h6 = h6
        self.h7 = h7
        self.h8 = h8
        self.h9 = h9
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

    @classmethod
    def StandardDensity(cls):
        """
        Standard workday labor densities. People work during the day and not at night.

        :return: A HourDensity object
        """
        return cls(0, 0, 0, 0, 0, 0, 0, 0.5, 0.5, 1, 1, 1,
                   0.5, 1, 1, 1, 1, 0.5, 0.5, 0, 0, 0, 0, 0)


class TimeDensity:

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

