from simulation_model.timing import ActivityTiming, TimingFunction, TimeDensity, ActivityTimingManager


class SimulationParameters:

    CASE_ID_PREFIX = "CASE"

    def __init__(self,
                 number_of_cases: int,
                 case_arrival_rate: TimingFunction,
                 case_arrival_density: TimeDensity,
                 service_time_density: TimeDensity,
                 activity_timings: list[ActivityTiming],
                 ):
        """
        Parameters of the simulation that is passed along with the Petri net and causal model
        for to make the Colored Petri net executable.

        :param number_of_cases: How many instances should be simulated in total.
        :param case_arrival_rate: How much time elapses between cases starting the process.
        :param case_arrival_density: At what times cases do arrive.
        :param service_time_density: At what times the process execution proceeds (working hours).
        :param activity_timings: How long executions of specific activities take.
        """
        self.number_of_cases = number_of_cases
        self.case_arrival_rate = case_arrival_rate
        self.case_arrival_density = case_arrival_density
        self.service_time_density = service_time_density
        self.__activity_names = [act_timing.activity_name for act_timing in activity_timings]
        self.activity_timings = activity_timings
        self.activity_timing_manager = ActivityTimingManager({
            act_timing.activity_name: act_timing for act_timing in activity_timings
        })

    def get_activity_names(self):
        return self.__activity_names

    def has_activity(self, activity_id):
        return self.activity_timing_manager.has_activity(activity_id)

    def get_activity_delay_call(self, act_name: str):
        return self.activity_timing_manager.get_activity_timing(act_name).execution_delay.get_call_SML()

    def get_case_arrival_delay_call(self):
        return self.case_arrival_rate.get_call_SML()
