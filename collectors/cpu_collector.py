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

    def update_config(self, config):
        self.interval = config.get("interval", 1)  # сек между замерами

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
        """Использование CPU в процентах через ps"""
        try:
            output = subprocess.check_output(["ps", "-A", "-o", "%cpu"]).decode().strip().split("\n")[1:]
            cpu_usages = [float(x) for x in output if x.strip()]
            return sum(cpu_usages) / len(self.find_objects())
        except Exception:
            return None

    def _get_cpu_freq(self):
        """Средняя частота CPU в ГГц"""
        try:
            # Получаем частоту из /proc/cpuinfo
            with open('/proc/cpuinfo', 'r') as f:
                lines = f.readlines()
            
            frequencies = []
            for line in lines:
                if 'cpu MHz' in line.lower():
                    freq_mhz = float(line.split(':')[1].strip())
                    frequencies.append(freq_mhz)
            
            if frequencies:
                avg_freq_ghz = sum(frequencies) / len(frequencies) / 1000
                return avg_freq_ghz
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
        
### Draft massive Collector

# class CpuCollectorLinux:
#     def __init__(self, config=None):
#         self.update_config(config or {})

#     def update_config(self, config):
#         self.interval = config.get("interval", 1)  # сек между замерами

#     def find_objects(self) -> List[str]:
#         """На Linux объекты = логические CPU"""
#         try:
#             # Получаем количество логических процессоров
#             with open('/proc/cpuinfo', 'r') as f:
#                 cores = [line for line in f.readlines() if line.startswith('processor')]
#             return [f"cpu{i}" for i in range(len(cores))]
#         except Exception:
#             return []

#     def _get_loadavg(self) -> tuple:
#         """Load average за 1, 5, 15 минут"""
#         try:
#             with open('/proc/loadavg', 'r') as f:
#                 load_data = f.read().split()
#             return float(load_data[0]), float(load_data[1]), float(load_data[2])
#         except Exception:
#             return 0.0, 0.0, 0.0

#     def _get_cpu_usage(self) -> Dict[str, Any]:
#         """
#         Получаем подробную статистику использования CPU из /proc/stat
#         Возвращает общее использование и по отдельным CPU
#         """
#         try:
#             with open('/proc/stat', 'r') as f:
#                 lines = f.readlines()
            
#             cpu_data = {}
            
#             for line in lines:
#                 if line.startswith('cpu'):
#                     parts = line.split()
#                     cpu_name = parts[0]
                    
#                     # Время в разных состояниях (user, nice, system, idle, iowait, irq, softirq, steal, guest, guest_nice)
#                     times = list(map(int, parts[1:11]))
                    
#                     # Общее время
#                     total_time = sum(times)
                    
#                     # Время простоя (idle + iowait)
#                     idle_time = times[3] + times[4]
                    
#                     # Активное время
#                     active_time = total_time - idle_time
                    
#                     cpu_data[cpu_name] = {
#                         'total': total_time,
#                         'active': active_time,
#                         'idle': idle_time,
#                         'times': times
#                     }
            
#             return cpu_data
#         except Exception:
#             return {}

#     def _get_cpu_freq(self) -> Dict[str, Any]:
#         """Частоты CPU - текущая, минимальная, максимальная"""
#         try:
#             freq_data = {}
#             cpu_objects = self.find_objects()
            
#             for cpu in cpu_objects:
#                 cpu_num = cpu.replace('cpu', '')
#                 try:
#                     # Текущая частота
#                     with open(f'/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_cur_freq', 'r') as f:
#                         current_freq = int(f.read().strip()) / 1000000  # КГц в ГГц
                    
#                     # Минимальная частота
#                     with open(f'/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_min_freq', 'r') as f:
#                         min_freq = int(f.read().strip()) / 1000000
                    
#                     # Максимальная частота
#                     with open(f'/sys/devices/system/cpu/cpu{cpu_num}/cpufreq/scaling_max_freq', 'r') as f:
#                         max_freq = int(f.read().strip()) / 1000000
                    
#                     freq_data[cpu] = {
#                         'current_ghz': current_freq,
#                         'min_ghz': min_freq,
#                         'max_ghz': max_freq
#                     }
#                 except FileNotFoundError:
#                     continue
            
#             # Средние значения по всем CPU
#             if freq_data:
#                 avg_current = sum([freq_data[cpu]['current_ghz'] for cpu in freq_data]) / len(freq_data)
#                 avg_min = sum([freq_data[cpu]['min_ghz'] for cpu in freq_data]) / len(freq_data)
#                 avg_max = sum([freq_data[cpu]['max_ghz'] for cpu in freq_data]) / len(freq_data)
                
#                 freq_data['average'] = {
#                     'current_ghz': avg_current,
#                     'min_ghz': avg_min,
#                     'max_ghz': avg_max
#                 }
            
#             return freq_data
#         except Exception:
#             return {}

#     def _get_cpu_info(self) -> Dict[str, Any]:
#         """Информация о процессоре"""
#         try:
#             info = {}
#             with open('/proc/cpuinfo', 'r') as f:
#                 lines = f.readlines()
            
#             # Берем данные первого процессора (обычно одинаковые для всех)
#             cpu0_info = {}
#             for line in lines:
#                 if line.strip() == '':
#                     break  # Конец первого блока
#                 if ':' in line:
#                     key, value = line.split(':', 1)
#                     cpu0_info[key.strip()] = value.strip()
            
#             info['model'] = cpu0_info.get('model name', 'Unknown')
#             info['vendor'] = cpu0_info.get('vendor_id', 'Unknown')
#             info['physical_cores'] = self._get_physical_cores()
#             info['siblings'] = int(cpu0_info.get('siblings', 1))
#             info['cpu_family'] = cpu0_info.get('cpu family', 'Unknown')
#             info['cache_size'] = cpu0_info.get('cache size', 'Unknown')
            
#             return info
#         except Exception:
#             return {}

#     def _get_physical_cores(self) -> int:
#         """Количество физических ядер"""
#         try:
#             # Считаем уникальные physical id
#             physical_ids = set()
#             core_ids = set()
            
#             with open('/proc/cpuinfo', 'r') as f:
#                 current_physical = None
#                 current_core = None
                
#                 for line in f:
#                     if line.startswith('physical id'):
#                         current_physical = line.split(':')[1].strip()
#                     elif line.startswith('core id'):
#                         current_core = line.split(':')[1].strip()
#                     elif line.strip() == '':
#                         if current_physical is not None and current_core is not None:
#                             physical_ids.add(current_physical)
#                             core_ids.add((current_physical, current_core))
#                         current_physical = None
#                         current_core = None
            
#             return len(core_ids)
#         except Exception:
#             return len(self.find_objects())

#     def _get_uptime(self) -> float:
#         """Время работы системы"""
#         try:
#             with open('/proc/uptime', 'r') as f:
#                 uptime_seconds = float(f.read().split()[0])
#             return uptime_seconds
#         except Exception:
#             return None

#     def _get_cpu_temperature(self) -> Dict[str, float]:
#         """Температура CPU"""
#         try:
#             temp_data = {}
            
#             # Проверяем доступные датчики температуры
#             thermal_zones = []
#             for zone in os.listdir('/sys/class/thermal'):
#                 if zone.startswith('thermal_zone'):
#                     thermal_zones.append(zone)
            
#             for zone in thermal_zones:
#                 try:
#                     with open(f'/sys/class/thermal/{zone}/type', 'r') as f:
#                         sensor_type = f.read().strip()
                    
#                     with open(f'/sys/class/thermal/{zone}/temp', 'r') as f:
#                         temp = int(f.read().strip()) / 1000.0  # миллиградусы в градусы
                    
#                     temp_data[sensor_type] = temp
#                 except FileNotFoundError:
#                     continue
            
#             return temp_data
#         except Exception:
#             return {}

#     def _get_interrupts(self) -> int:
#         """Общее количество прерываний"""
#         try:
#             with open('/proc/interrupts', 'r') as f:
#                 lines = f.readlines()
            
#             total_interrupts = 0
#             for line in lines[1:]:  # Пропускаем заголовок
#                 if line.strip():
#                     # Суммируем прерывания для первого CPU (обычно достаточно для общей картины)
#                     parts = line.split()
#                     if len(parts) > 1:
#                         total_interrupts += int(parts[1])
            
#             return total_interrupts
#         except Exception:
#             return 0

#     def collect(self, objects=None) -> pd.DataFrame:
#         """Собрать метрики CPU"""
#         timestamp = time.time()

#         # Получаем все метрики
#         load1, load5, load15 = self._get_loadavg()
#         cpu_usage = self._get_cpu_usage()
#         cpu_freq = self._get_cpu_freq()
#         uptime = self._get_uptime()
#         cpu_info = self._get_cpu_info()
#         cpu_temp = self._get_cpu_temperature()
#         total_interrupts = self._get_interrupts()

#         # Подготавливаем данные
#         data = {
#             "timestamp": [timestamp],
#             "load_1m": [load1],
#             "load_5m": [load5],
#             "load_15m": [load15],
#             "uptime_sec": [uptime],
#             "logical_cores": [len(self.find_objects())],
#             "physical_cores": [cpu_info.get('physical_cores', 0)],
#             "cpu_model": [cpu_info.get('model', 'Unknown')],
#             "total_interrupts": [total_interrupts],
#         }

#         # Добавляем использование CPU
#         if 'cpu' in cpu_usage:  # Общее использование
#             cpu_total = cpu_usage['cpu']
#             if 'prev_cpu_total' in self.__dict__:
#                 # Расчет использования в процентах
#                 total_diff = cpu_total['total'] - self.prev_cpu_total['total']
#                 active_diff = cpu_total['active'] - self.prev_cpu_total['active']
#                 if total_diff > 0:
#                     usage_percent = (active_diff / total_diff) * 100
#                 else:
#                     usage_percent = 0
#             else:
#                 usage_percent = 0
            
#             data["cpu_usage_percent"] = [usage_percent]
#             self.prev_cpu_total = cpu_total

#         # Добавляем частоты
#         if 'average' in cpu_freq:
#             data["cpu_freq_current_ghz"] = [cpu_freq['average']['current_ghz']]
#             data["cpu_freq_min_ghz"] = [cpu_freq['average']['min_ghz']]
#             data["cpu_freq_max_ghz"] = [cpu_freq['average']['max_ghz']]

#         # Добавляем температуру (берем максимальную)
#         if cpu_temp:
#             max_temp = max(cpu_temp.values()) if cpu_temp else 0
#             data["cpu_temp_celsius"] = [max_temp]

#         return pd.DataFrame(data)