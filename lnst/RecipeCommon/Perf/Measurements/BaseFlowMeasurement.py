import signal
from lnst.RecipeCommon.Perf.Measurements.MeasurementError import MeasurementError
from lnst.RecipeCommon.Perf.Measurements.BaseMeasurement import BaseMeasurement
from lnst.RecipeCommon.Perf.Results import SequentialPerfResult

class Flow(object):
    def __init__(self,
                 type,
                 generator, generator_bind,
                 receiver, receiver_bind,
                 msg_size, duration, parallel_streams):
        self._type = type

        self._generator = generator
        self._generator_bind = generator_bind
        self._receiver = receiver
        self._receiver_bind = receiver_bind

        self._msg_size = msg_size
        self._duration = duration
        self._parallel_streams = parallel_streams

    @property
    def type(self):
        return self._type

    @property
    def generator(self):
        return self._generator

    @property
    def generator_bind(self):
        return self._generator_bind

    @property
    def receiver(self):
        return self._receiver

    @property
    def receiver_bind(self):
        return self._receiver_bind

    @property
    def msg_size(self):
        return self._msg_size

    @property
    def duration(self):
        return self._duration

    @property
    def parallel_streams(self):
        return self._parallel_streams

class FlowMeasurementResults(object):
    def __init__(self, flow):
        self._flow = flow
        self._generator_results = None
        self._generator_cpu_stats = None
        self._receiver_results = None
        self._receiver_cpu_stats = None

    @property
    def flow(self):
        return self._flow

    @property
    def generator_results(self):
        return self._generator_results

    @generator_results.setter
    def generator_results(self, value):
        self._generator_results = value

    @property
    def generator_cpu_stats(self):
        return self._generator_cpu_stats

    @generator_cpu_stats.setter
    def generator_cpu_stats(self, value):
        self._generator_cpu_stats = value

    @property
    def receiver_results(self):
        return self._receiver_results

    @receiver_results.setter
    def receiver_results(self, value):
        self._receiver_results = value

    @property
    def receiver_cpu_stats(self):
        return self._receiver_cpu_stats

    @receiver_cpu_stats.setter
    def receiver_cpu_stats(self, value):
        self._receiver_cpu_stats = value

class AggregatedFlowMeasurementResults(FlowMeasurementResults):
    def __init__(self, flow):
        self._flow = flow
        self._generator_results = SequentialPerfResult()
        self._generator_cpu_stats = SequentialPerfResult()
        self._receiver_results = SequentialPerfResult()
        self._receiver_cpu_stats = SequentialPerfResult()
        self._individual_results = []

    @property
    def individual_results(self):
        return self._individual_results

    def add_results(self, results):
        if results is None:
            return
        elif isinstance(results, AggregatedFlowMeasurementResults):
            self.individual_results.extend(results.individual_results)
            self.generator_results.extend(results.generator_results)
            self.generator_cpu_stats.extend(results.generator_cpu_stats)
            self.receiver_results.extend(results.receiver_results)
            self.receiver_cpu_stats.extend(results.receiver_cpu_stats)
        elif isinstance(results, FlowMeasurementResults):
            self.individual_results.append(results)
            self.generator_results.append(results.generator_results)
            self.generator_cpu_stats.append(results.generator_cpu_stats)
            self.receiver_results.append(results.receiver_results)
            self.receiver_cpu_stats.append(results.receiver_cpu_stats)
        else:
            raise MeasurementError("Adding incorrect results.")

class BaseFlowMeasurement(BaseMeasurement):
    @classmethod
    def report_results(cls, recipe, results):
        for flow_results in results:
            cls._report_flow_results(recipe, flow_results)

    @classmethod
    def evaluate_results(cls, recipe, results):
        #TODO split off into a separate evaluator class
        for flow_results in results:
            if flow_results.generator_results.average > 0:
                recipe.add_result(True, "Generator reported non-zero throughput")
            else:
                recipe.add_result(False, "Generator reported zero throughput")

            if flow_results.receiver_results.average > 0:
                recipe.add_result(True, "Receiver reported non-zero throughput")
            else:
                recipe.add_result(False, "Receiver reported zero throughput")

    @classmethod
    def _report_flow_results(cls, recipe, flow_results):
        generator = flow_results.generator_results
        generator_cpu = flow_results.generator_cpu_stats
        receiver = flow_results.receiver_results
        receiver_cpu = flow_results.receiver_cpu_stats

        desc = []
        desc.append("Generator measured throughput: {tput:.2f} +-{deviation:.2f}({percentage:.2f}%) {unit} per second."
                .format(tput=generator.average,
                        deviation=generator.std_deviation,
                        percentage=(generator.std_deviation/generator.average) * 100,
                        unit=generator.unit))
        desc.append("Generator process CPU data: {cpu:.2f} +-{cpu_deviation:.2f} {cpu_unit} per second."
                .format(cpu=generator_cpu.average,
                        cpu_deviation=generator_cpu.std_deviation,
                        cpu_unit=generator_cpu.unit))
        desc.append("Receiver measured throughput: {tput:.2f} +-{deviation:.2f}({percentage:.2}%) {unit} per second."
                .format(tput=receiver.average,
                        deviation=receiver.std_deviation,
                        percentage=(receiver.std_deviation/receiver.average) * 100,
                        unit=receiver.unit))
        desc.append("Receiver process CPU data: {cpu:.2f} +-{cpu_deviation:.2f} {cpu_unit} per second."
                .format(cpu=receiver_cpu.average,
                        cpu_deviation=receiver_cpu.std_deviation,
                        cpu_unit=receiver_cpu.unit))

        #TODO add flow description
        recipe.add_result(True, "\n".join(desc), data = dict(
                    generator_flow_data=generator,
                    generator_cpu_data=generator_cpu,
                    receiver_flow_data=receiver,
                    receiver_cpu_data=receiver_cpu))

    @classmethod
    def aggregate_results(cls, old, new):
        aggregated = []
        if old is None:
            old = [None] * len(new)
        for old_flow, new_flow in zip(old, new):
            aggregated.append(cls._aggregate_flows(old_flow, new_flow))
        return aggregated

    @classmethod
    def _aggregate_flows(cls, old_flow, new_flow):
        if old_flow is not None and old_flow.flow is not new_flow.flow:
            raise MeasurementError("Aggregating incompatible Flows")

        new_result = AggregatedFlowMeasurementResults(new_flow.flow)

        new_result.add_results(old_flow)
        new_result.add_results(new_flow)
        return new_result
