from __future__ import annotations

from typing import Any, Optional


class VerilogInstance:
    def __init__(self, data: Any):
        self._data = data

    @property
    def instance_name(self) -> str:
        return self._data.instance_name

    @instance_name.setter
    def instance_name(self, value: str):
        self._data.instance_name = value

    @property
    def module_name(self) -> str:
        return self._data.module_name

    @module_name.setter
    def module_name(self, value: str):
        self._data.module_name = value

    @property
    def port_list(self) -> list[tuple[str, str]]:
        return list(self._data.port_list)

    @port_list.setter
    def port_list(self, value: list[tuple[str, str]]):
        self._data.port_list = value


class VerilogModule:
    def __init__(self, data_or_name: Any):
        if isinstance(data_or_name, str):
            self._data = None
            self.name = data_or_name
            self.ports: dict[str, dict[str, Any]] = {}
            self.inputs: dict[str, dict[str, Any]] = {}
            self.outputs: dict[str, dict[str, Any]] = {}
            self.wires: dict[str, dict[str, Any]] = {}
            self.instances: dict[str, dict[str, Any]] = {}
            return

        self._data = data_or_name
        self.name = data_or_name.name
        self.ports = {name: {"direction": None, "width": 1} for name in data_or_name.ports}
        self.inputs = {name: {"direction": "input", "width": 1} for name in data_or_name.inputs}
        self.outputs = {name: {"direction": "output", "width": 1} for name in data_or_name.outputs}
        self.wires = {name: {"width": 1} for name in data_or_name.wires}
        self.instances: dict[str, dict[str, Any]] = {}

        for instance in data_or_name.instances:
            self.add_instance(
                instance.instance_name,
                instance.module_name,
                list(instance.port_list),
            )

        for lhs, rhs in data_or_name.assignments:
            self.add_instance(
                f"__assign_{rhs}__to__{lhs}",
                "__assign__",
                [(lhs, rhs)],
            )

    @property
    def native_instances(self) -> list[VerilogInstance]:
        if self._data is None:
            return []
        return [VerilogInstance(instance) for instance in self._data.instances]

    @property
    def assignments(self) -> list[tuple[str, str]]:
        if self._data is None:
            return [
                instance["portlist"][0]
                for instance in self.instances.values()
                if instance["module"] == "__assign__"
            ]
        return list(self._data.assignments)

    def get_module_name(self) -> str:
        if self._data is None:
            return self.name
        return self._data.get_module_name()

    def get_all_ports(self) -> list[str]:
        return list(self.ports)

    def get_all_inputs(self) -> list[str]:
        return list(self.inputs)

    def get_all_outputs(self) -> list[str]:
        return list(self.outputs)

    def get_all_wires(self) -> list[str]:
        return list(self.wires)

    def get_all_instances(self) -> dict[str, dict[str, Any]]:
        return self.instances

    def get_all_assignments(self) -> list[tuple[str, str]]:
        return self.assignments

    def add_port(self, name: str, direction: Optional[str], width: int):
        if direction is None:
            self.ports[name] = {"direction": None, "width": width}
        elif direction == "input":
            self.inputs[name] = {"direction": "input", "width": width}
            self.ports.pop(name, None)
        elif direction == "output":
            self.outputs[name] = {"direction": "output", "width": width}
            self.ports.pop(name, None)

    def add_wire(self, name: str, width: int):
        self.wires[name] = {"width": width}

    def add_instance(self, name: str, module: str, portlist: list[tuple[str, str]]):
        self.instances[name] = {"module": module, "portlist": portlist}

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "total_ports": len(self.inputs) + len(self.outputs) + len(self.ports),
            "inputs": len(self.inputs),
            "outputs": len(self.outputs),
            "wires": len(self.wires),
            "instances": len(self.instances),
            "undefined_ports": len(self.ports),
        }

    def print_summary(self):
        print(f"\n=== Module: {self.name} ===")
        print(f"Inputs: {len(self.inputs)}")
        print(f"Outputs: {len(self.outputs)}")
        print(f"Wires: {len(self.wires)}")
        print(f"Instances: {len(self.instances)}")

        if self.ports:
            print(f"\nWarning: {len(self.ports)} ports are not defined as input or output:")
            for port_name, port_info in self.ports.items():
                print(f"  Port: {port_name}, width: {port_info['width']}")
