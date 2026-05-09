"""Agent tools registration."""

from .ssh_tools import ssh_exec, ssh_batch_exec
from .ipmi_tools import ipmi_power, ipmi_bootdev, ipmi_reset_password, ipmi_sensor, ipmi_sel
from .monitor_tools import check_monitor, query_deploy_history, query_logs
from .knowledge_tools import query_knowledge_base, save_to_knowledge

ALL_TOOLS = [
    ssh_exec,
    ssh_batch_exec,
    ipmi_power,
    ipmi_bootdev,
    ipmi_reset_password,
    ipmi_sensor,
    ipmi_sel,
    check_monitor,
    query_deploy_history,
    query_logs,
    query_knowledge_base,
    save_to_knowledge,
]
