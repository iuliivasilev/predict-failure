import os
import subprocess
import time
import pandas as pd

from base.collector_base import AbstractDataCollector


class CpuCollectorMacOS(AbstractDataCollector):
    def __init__(self, config=None):
        self.update_config(config or {})

    def update_config(self, config):
        self.interval = config.get("interval", 1)  # сек между замерами

    def find_objects(self):
        """На macOS объекты = логические CPU"""
        try:
            cores = int(subprocess.check_output(["sysctl", "-n", "hw.ncpu"]).decode().strip())
            return [f"cpu{i}" for i in range(cores)]
        except Exception:
            return []

    def _get_loadavg(self):
        """Load average за 1, 5, 15 минут"""
        return os.getloadavg()

    def _get_cpu_usage(self):
        """
        Используем `ps -A -o %cpu` для замера загрузки CPU (в процентах).
        Это грубая оценка, но без сторонних библиотек иначе сложно.
        """
        try:
            output = subprocess.check_output(["ps", "-A", "-o", "%cpu"]).decode().strip().split("\n")[1:]
            cpu_usages = [float(x) for x in output if x.strip()]
            return sum(cpu_usages) / os.cpu_count()
        except Exception:
            return None

    def _get_cpu_freq(self):
        """Частота CPU в ГГц (nominal frequency)"""
        try:
            freq_hz = int(subprocess.check_output(["sysctl", "-n", "hw.cpufrequency"]).decode().strip())
            return freq_hz / 1e9  # ГГц
        except Exception:
            return None

    def _get_uptime(self):
        try:
            uptime_sec = float(subprocess.check_output(["sysctl", "-n", "kern.boottime"]).decode().split("sec")[0].split("=")[1])
            now = time.time()
            return now - uptime_sec
        except Exception:
            return None

    def collect(self, objects=None) -> pd.DataFrame:
        """Собрать метрики CPU"""
        timestamp = time.time()

        load1, load5, load15 = self._get_loadavg()
        usage = self._get_cpu_usage()
        freq = self._get_cpu_freq()
        uptime = self._get_uptime()

        data = {
            "timestamp": [timestamp],
            "cpu_usage_percent": [usage],
            "cpu_frequency_ghz": [freq],
            "load_1m": [load1],
            "load_5m": [load5],
            "load_15m": [load15],
            "uptime_sec": [uptime],
            "cores": [len(self.find_objects())],
        }

        return pd.DataFrame(data)
