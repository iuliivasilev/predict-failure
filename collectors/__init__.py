from .cpu_collector import CpuCollectorMacOS, CpuCollectorLinux

DICT_COLLECTORS = {
    "Darwin": {
        "cpu": CpuCollectorMacOS
        },
    "Windows": {
        },
    "Linux": {
        "cpu": CpuCollectorLinux
        }
}