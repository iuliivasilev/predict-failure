import os
import subprocess
import time
import pandas as pd
from typing import List, Dict, Any

from base.collector_base import AbstractDataCollector


class AbstractCPUDataCollector(AbstractDataCollector):
    """Базовый класс для всех CPU сборщиков"""
    def __init__(self, config=None):
        self.update_config(config or {})
        self._prev_cpu_times = None  # Для расчета точного использования CPU

    def update_config(self, config):
        self.interval = config.get("interval", 1)  # сек между замерами

    def collect(self, objects=None) -> pd.DataFrame:
        """Собрать метрики CPU"""
        timestamp = time.time()

        load1, load5, load15 = self._get_loadavg()
        usage = self._get_cpu_usage()
        freq = self._get_cpu_freq()
        uptime = self._get_uptime()
        processes = self._get_process_count()
        cpu_temp = self._get_cpu_temperature()
        context_switches = self._get_context_switches()

        data = {
            "timestamp": [timestamp],
            "cpu_usage_percent": [usage],
            "cpu_frequency_ghz": [freq],
            "load_1m": [load1],
            "load_5m": [load5],
            "load_15m": [load15],
            "uptime_sec": [uptime],
            "cores": [len(self.find_objects())],
            "processes_total": [processes],
            "cpu_temperature_c": [cpu_temp],
            "context_switches": [context_switches],
        }
        print("Собранные данные:", data)
        return pd.DataFrame(data)


class CpuCollectorMacOS(AbstractCPUDataCollector):
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
        """Более точное использование CPU через sysctl"""
        try:
            # Получаем статистику использования CPU
            cmd = ["sysctl", "-n", "kern.cp_time"]
            output = subprocess.check_output(cmd).decode().strip()
            cpu_times = list(map(int, output.split()))
            
            # user, nice, system, idle, (other times vary by system)
            total_time = sum(cpu_times)
            idle_time = cpu_times[3]  # idle time
            
            if self._prev_cpu_times is not None:
                prev_total, prev_idle = self._prev_cpu_times
                total_diff = total_time - prev_total
                idle_diff = idle_time - prev_idle
                
                if total_diff > 0:
                    usage_percent = 100.0 * (total_diff - idle_diff) / total_diff
                else:
                    usage_percent = 0.0
            else:
                usage_percent = 0.0
            
            self._prev_cpu_times = (total_time, idle_time)
            return usage_percent
            
        except Exception:
            # Fallback на ps метод
            try:
                output = subprocess.check_output(["ps", "-A", "-o", "%cpu"]).decode().strip().split("\n")[1:]
                cpu_usages = [float(x) for x in output if x.strip()]
                return sum(cpu_usages) / os.cpu_count()
            except Exception:
                return None

    def _get_cpu_freq(self):
        """Частота CPU в ГГц (номинальная и текущая)"""
        try:
            # Пробуем получить текущую частоту
            cmd = ["sysctl", "-n", "hw.cpufrequency"]
            freq_hz = int(subprocess.check_output(cmd).decode().strip())
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

    def _get_process_count(self):
        """Количество запущенных процессов"""
        try:
            output = subprocess.check_output(["ps", "-A"]).decode().strip().split("\n")
            return len(output) - 1  # Минус заголовок
        except Exception:
            return None

    def _get_cpu_temperature(self):
        """Температура CPU"""
        try:
            # Попробуем получить температуру через powermetrics
            cmd = ["sudo", "powermetrics", "--samplers", "cpu_power", "-n", "1", "-i", "100"]
            output = subprocess.check_output(cmd, timeout=2).decode()
            for line in output.split('\n'):
                if 'CPU die temperature' in line:
                    temp_str = line.split(':')[1].strip().split(' ')[0]
                    return float(temp_str)
        except Exception:
            pass
        return None

    def _get_context_switches(self):
        """Количество переключений контекста"""
        try:
            output = subprocess.check_output(["vm_stat"]).decode()
            for line in output.split('\n'):
                if 'CPU context switches' in line:
                    return int(line.split(':')[1].strip())
        except Exception:
            pass
        return None


class CpuCollectorLinux(AbstractCPUDataCollector):
    def find_objects(self):
        """На Linux объекты = логические CPU"""
        try:
            cores = int(subprocess.check_output(["nproc"]).decode().strip())
            return [f"cpu{i}" for i in range(cores)]
        except Exception:
            return []

    def _get_loadavg(self):
        """Load average за 1, 5, 15 минут"""
        try:
            with open('/proc/loadavg', 'r') as f:
                load_data = f.read().split()
            return float(load_data[0]), float(load_data[1]), float(load_data[2])
        except Exception:
            return 0.0, 0.0, 0.0

    def _get_cpu_usage(self):
        """Точное использование CPU через /proc/stat"""
        try:
            with open('/proc/stat', 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith('cpu '):  # Общая статистика CPU
                    parts = line.split()
                    user = int(parts[1])
                    nice = int(parts[2])
                    system = int(parts[3])
                    idle = int(parts[4])
                    iowait = int(parts[5])
                    
                    total_time = user + nice + system + idle + iowait
                    non_idle_time = user + nice + system
                    
                    if self._prev_cpu_times is not None:
                        prev_total, prev_non_idle = self._prev_cpu_times
                        total_diff = total_time - prev_total
                        non_idle_diff = non_idle_time - prev_non_idle
                        
                        if total_diff > 0:
                            usage_percent = 100.0 * non_idle_diff / total_diff
                        else:
                            usage_percent = 0.0
                    else:
                        usage_percent = 0.0
                    
                    self._prev_cpu_times = (total_time, non_idle_time)
                    return usage_percent
                    
        except Exception:
            # Fallback на ps метод
            try:
                output = subprocess.check_output(["ps", "-A", "-o", "%cpu"]).decode().strip().split("\n")[1:]
                cpu_usages = [float(x) for x in output if x.strip()]
                return sum(cpu_usages) / len(self.find_objects())
            except Exception:
                return None
        return None

    def _get_cpu_freq(self):
        """Средняя частота CPU в ГГц"""
        try:
            # Пробуем получить текущую частоту из /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
            
            frequencies = []
            for line in lines:
                if 'cpu mhz' in line.lower():
                    freq_mhz = float(line.split(':')[1].strip())
                    frequencies.append(freq_mhz)
            
            if frequencies:
                avg_freq_ghz = sum(frequencies) / len(frequencies) / 1000
                return avg_freq_ghz
            
            # Альтернативный метод
            try:
                output = subprocess.check_output(["lscpu"]).decode()
                for line in output.split('\n'):
                    if 'CPU MHz:' in line:
                        freq_mhz = float(line.split(':')[1].strip())
                        return freq_mhz / 1000
            except:
                pass
                
            return None
        except Exception:
            return None

    def _get_uptime(self):
        """Время работы системы"""
        try:
            with open('/proc/uptime', 'r') as f:
                uptime_seconds = float(f.read().split()[0])
            return uptime_seconds
        except Exception:
            return None

    def _get_process_count(self):
        """Количество запущенных процессов"""
        try:
            output = subprocess.check_output(["ps", "-A"]).decode().strip().split("\n")
            return len(output) - 1  # Минус заголовок
        except Exception:
            return None

    def _get_cpu_temperature(self):
        """Температура CPU"""
        try:
            # Пробуем разные возможные пути к датчикам температуры
            thermal_paths = [
                '/sys/class/thermal/thermal_zone0/temp',
                '/sys/class/hwmon/hwmon0/temp1_input',
                '/sys/class/hwmon/hwmon1/temp1_input',
            ]
            
            for path in thermal_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        temp = int(f.read().strip())
                        return temp / 1000.0  # Преобразуем в градусы Цельсия
        except Exception:
            pass
        return None

    def _get_context_switches(self):
        """Количество переключений контекста"""
        try:
            with open('/proc/stat', 'r') as f:
                for line in f:
                    if line.startswith('ctxt '):
                        return int(line.split()[1])
        except Exception:
            pass
        return None