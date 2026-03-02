import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.benchmark_utils import collect_environment_info, get_cpu_model, get_total_ram_gb


def test_cpu_model_not_empty():
    model = get_cpu_model()
    assert isinstance(model, str)
    assert model != ''


def test_ram_positive():
    ram = get_total_ram_gb()
    assert isinstance(ram, float)
    assert ram > 0


def test_collect_env_defaults():
    info = collect_environment_info()
    assert 'cpu_model' in info
    assert 'ram_gb' in info
    assert info['cache_state'] == 'cold'
    assert info['io_medium'] == 'unspecified'


def test_collect_env_custom():
    info = collect_environment_info(io_medium='NVMe SSD', cache_state='warm')
    assert info['io_medium'] == 'NVMe SSD'
    assert info['cache_state'] == 'warm'
