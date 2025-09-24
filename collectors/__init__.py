from .cpu_collector import CpuCollectorMacOS

DICT_COLLECTORS = {
    "Darwin": {
        "cpu": CpuCollectorMacOS
        },
    "Windows": {
        },
    "Linux": {
        }
}