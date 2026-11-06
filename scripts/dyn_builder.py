#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dyn_builder.py — Construtor Programático de Grafos Dynamo (.dyn) para Autodesk Civil 3D.

Permite gerar arquivos .dyn 100% compatíveis com o Dynamo 2.13–3.x (Civil 3D 2022–2026+)
e prontos para o Dynamo Player, com posicionamento automático de nós, grupos coloridos
(Annotations), entradas de usuário e nós CPython3.
"""

import json
import os
import uuid
import argparse
from typing import List, Dict, Any, Optional


def new_hex_id() -> str:
    """Gera um ID hexadecimal de 32 caracteres sem hífens (padrão interno de nós/portas do Dynamo)."""
    return uuid.uuid4().hex


def new_guid_str() -> str:
    """Gera um UUID padrão com hífens."""
    return str(uuid.uuid4())


class DynamoGraphBuilder:
    """Construtor estruturado de arquivos .dyn para Civil 3D e Dynamo Player."""

    COLOR_INPUT_BLUE = "#FF48B5E0"
    COLOR_AI_PURPLE = "#FF8C62E8"
    COLOR_C3D_ORANGE = "#FFF2994A"
    COLOR_OUTPUT_GREEN = "#FF27AE60"

    def __init__(self, name: str, description: str = "", author: str = "Dynamo Civil 3D AI Specialist"):
        self.uuid = new_guid_str()
        self.name = name
        self.description = description or f"Ferramenta Dynamo para Civil 3D: {name}"
        self.author = author

        self.inputs: List[Dict[str, Any]] = []
        self.outputs: List[Dict[str, Any]] = []
        self.nodes: List[Dict[str, Any]] = []
        self.connectors: List[Dict[str, Any]] = []
        self.node_views: List[Dict[str, Any]] = []
        self.annotations: List[Dict[str, Any]] = []

        self._auto_y_by_col: Dict[int, float] = {}

    def _next_y(self, x: float, step: float = 165.0, start_y: float = 120.0) -> float:
        col_key = int(round(x / 100.0))
        curr = self._auto_y_by_col.get(col_key, start_y)
        self._auto_y_by_col[col_key] = curr + step
        return curr

    def add_string_input(
        self,
        name: str,
        default_value: str = "",
        description: str = "Parâmetro de texto",
        x: float = 100.0,
        y: Optional[float] = None,
        is_player_input: bool = True,
    ) -> str:
        node_id = new_hex_id()
        port_id = new_hex_id()
        y_pos = y if y is not None else self._next_y(x)

        node = {
            "ConcreteType": "CoreNodeModels.Input.StringInput, CoreNodeModels",
            "NodeType": "StringInputNode",
            "InputValue": str(default_value),
            "Id": node_id,
            "Inputs": [],
            "Outputs": [
                {
                    "Id": port_id,
                    "Name": "",
                    "Description": "String",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Replication": "Disabled",
            "Description": description,
        }
        self.nodes.append(node)

        self.node_views.append(
            {
                "Id": node_id,
                "Name": name,
                "IsSetAsInput": bool(is_player_input),
                "IsSetAsOutput": False,
                "Excluded": False,
                "ShowGeometry": True,
                "X": float(x),
                "Y": float(y_pos),
            }
        )

        if is_player_input:
            self.inputs.append(
                {
                    "Id": node_id,
                    "Name": name,
                    "Type": "string",
                    "Type2": "string",
                    "Value": str(default_value),
                    "Description": description,
                    "SelectedIndex": 0,
                }
            )
        return node_id

    def add_number_input(
        self,
        name: str,
        default_value: float = 0.0,
        description: str = "Parâmetro numérico",
        x: float = 100.0,
        y: Optional[float] = None,
        is_player_input: bool = True,
    ) -> str:
        node_id = new_hex_id()
        port_id = new_hex_id()
        y_pos = y if y is not None else self._next_y(x)

        node = {
            "ConcreteType": "CoreNodeModels.Input.DoubleInput, CoreNodeModels",
            "NodeType": "NumberInputNode",
            "NumberType": "Double",
            "InputValue": float(default_value),
            "Id": node_id,
            "Inputs": [],
            "Outputs": [
                {
                    "Id": port_id,
                    "Name": "",
                    "Description": "Double",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Replication": "Disabled",
            "Description": description,
        }
        self.nodes.append(node)

        self.node_views.append(
            {
                "Id": node_id,
                "Name": name,
                "IsSetAsInput": bool(is_player_input),
                "IsSetAsOutput": False,
                "Excluded": False,
                "ShowGeometry": True,
                "X": float(x),
                "Y": float(y_pos),
            }
        )

        if is_player_input:
            self.inputs.append(
                {
                    "Id": node_id,
                    "Name": name,
                    "Type": "number",
                    "Type2": "number",
                    "Value": str(default_value),
                    "Description": description,
                    "SelectedIndex": 0,
                }
            )
        return node_id

    def add_bool_input(
        self,
        name: str,
        default_value: bool = True,
        description: str = "Opção booleana (Sim/Não)",
        x: float = 100.0,
        y: Optional[float] = None,
        is_player_input: bool = True,
    ) -> str:
        node_id = new_hex_id()
        port_id = new_hex_id()
        y_pos = y if y is not None else self._next_y(x)

        node = {
            "ConcreteType": "CoreNodeModels.Input.BoolSelector, CoreNodeModels",
            "NodeType": "BooleanInputNode",
            "InputValue": bool(default_value),
            "Id": node_id,
            "Inputs": [],
            "Outputs": [
                {
                    "Id": port_id,
                    "Name": "",
                    "Description": "Boolean",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Replication": "Disabled",
            "Description": description,
        }
        self.nodes.append(node)

        self.node_views.append(
            {
                "Id": node_id,
                "Name": name,
                "IsSetAsInput": bool(is_player_input),
                "IsSetAsOutput": False,
                "Excluded": False,
                "ShowGeometry": True,
                "X": float(x),
                "Y": float(y_pos),
            }
        )

        if is_player_input:
            self.inputs.append(
                {
                    "Id": node_id,
                    "Name": name,
                    "Type": "boolean",
                    "Type2": "boolean",
                    "Value": "true" if default_value else "false",
                    "Description": description,
                    "SelectedIndex": 0,
                }
            )
        return node_id

    def add_python_node(
        self,
        name: str,
        code: str,
        num_inputs: int = 1,
        description: str = "Motor CPython3 — Civil 3D .NET API & IA",
        x: float = 680.0,
        y: Optional[float] = None,
    ) -> str:
        node_id = new_hex_id()
        y_pos = y if y is not None else self._next_y(x, step=260.0, start_y=200.0)

        in_ports = []
        for i in range(max(1, num_inputs)):
            in_ports.append(
                {
                    "Id": new_hex_id(),
                    "Name": f"IN[{i}]",
                    "Description": f"Input #{i}",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            )

        out_port_id = new_hex_id()
        node = {
            "ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
            "NodeType": "PythonScriptNode",
            "Code": code,
            "Engine": "CPython3",
            "EngineName": "CPython3",
            "VariableInputPorts": True,
            "Id": node_id,
            "Inputs": in_ports,
            "Outputs": [
                {
                    "Id": out_port_id,
                    "Name": "OUT",
                    "Description": "Resultado da execução do script Python",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Replication": "Disabled",
            "Description": description,
        }
        self.nodes.append(node)

        self.node_views.append(
            {
                "Id": node_id,
                "Name": name,
                "IsSetAsInput": False,
                "IsSetAsOutput": False,
                "Excluded": False,
                "ShowGeometry": True,
                "X": float(x),
                "Y": float(y_pos),
            }
        )
        return node_id

    def add_watch_output(
        self,
        name: str,
        description: str = "Saída de dados e relatório para o Dynamo Player",
        x: float = 1220.0,
        y: Optional[float] = None,
        is_player_output: bool = True,
    ) -> str:
        node_id = new_hex_id()
        in_port_id = new_hex_id()
        out_port_id = new_hex_id()
        y_pos = y if y is not None else self._next_y(x, step=220.0, start_y=200.0)

        node = {
            "ConcreteType": "CoreNodeModels.Watch, CoreNodeModels",
            "NodeType": "ExtensionNode",
            "Id": node_id,
            "Inputs": [
                {
                    "Id": in_port_id,
                    "Name": "",
                    "Description": "Nó para inspecionar saída",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Outputs": [
                {
                    "Id": out_port_id,
                    "Name": "",
                    "Description": "Saída visualizada",
                    "UsingDefaultValue": False,
                    "Level": 2,
                    "UseLevels": False,
                    "KeepListStructure": False,
                }
            ],
            "Replication": "Disabled",
            "Description": description,
        }
        self.nodes.append(node)

        self.node_views.append(
            {
                "Id": node_id,
                "Name": name,
                "IsSetAsInput": False,
                "IsSetAsOutput": bool(is_player_output),
                "Excluded": False,
                "ShowGeometry": True,
                "X": float(x),
                "Y": float(y_pos),
            }
        )

        if is_player_output:
            self.outputs.append(
                {
                    "Id": node_id,
                    "Name": name,
                    "Type": "unknown",
                    "InitialValue": "",
                    "Description": description,
                }
            )
        return node_id

    def _find_node(self, node_id: str) -> Dict[str, Any]:
        for n in self.nodes:
            if n["Id"] == node_id:
                return n
        raise ValueError(f"Nó com ID '{node_id}' não encontrado.")

    def connect(
        self,
        from_node_id: str,
        to_node_id: str,
        from_port_index: int = 0,
        to_port_index: int = 0,
    ) -> str:
        src_node = self._find_node(from_node_id)
        dst_node = self._find_node(to_node_id)

        start_port_id = src_node["Outputs"][from_port_index]["Id"]
        end_port_id = dst_node["Inputs"][to_port_index]["Id"]
        conn_id = new_hex_id()

        self.connectors.append(
            {
                "Start": start_port_id,
                "End": end_port_id,
                "Id": conn_id,
                "IsHidden": "False",
            }
        )
        return conn_id

    def add_group(
        self,
        title: str,
        node_ids: List[str],
        description: str = "",
        color: str = "#FF48B5E0",
    ) -> str:
        group_id = new_hex_id()
        xs = []
        ys = []
        for nv in self.node_views:
            if nv["Id"] in node_ids:
                xs.append(nv["X"])
                ys.append(nv["Y"])

        left = (min(xs) - 25.0) if xs else 80.0
        top = (min(ys) - 70.0) if ys else 80.0
        width = (max(xs) - min(xs) + 320.0) if xs else 340.0
        height = (max(ys) - min(ys) + 220.0) if ys else 300.0

        self.annotations.append(
            {
                "Id": group_id,
                "Title": title,
                "DescriptionText": description,
                "IsExpanded": True,
                "WidthAdjustment": 0.0,
                "HeightAdjustment": 0.0,
                "Nodes": list(node_ids),
                "HasNestedGroups": False,
                "Left": left,
                "Top": top,
                "Width": width,
                "Height": height,
                "FontSize": 30.0,
                "GroupStyleId": "00000000-0000-0000-0000-000000000000",
                "InitialTop": top + 50.0,
                "InitialHeight": height,
                "TextblockHeight": 50.0,
                "Background": color,
            }
        )
        return group_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "Uuid": self.uuid,
            "IsCustomNode": False,
            "Description": self.description,
            "Name": self.name,
            "ElementResolver": {"ResolutionMap": {}},
            "Inputs": self.inputs,
            "Outputs": self.outputs,
            "Nodes": self.nodes,
            "Connectors": self.connectors,
            "Dependencies": [],
            "NodeLibraryDependencies": [],
            "Thumbnail": "",
            "GraphDocumentationURL": None,
            "ExtensionWorkspaceData": [
                {
                    "ExtensionGuid": "28992e1d-abb9-417f-8b1b-05e053bee670",
                    "Name": "Properties",
                    "Version": "2.19",
                    "Data": {},
                }
            ],
            "Author": self.author,
            "Linting": {
                "activeLinter": "None",
                "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a",
                "warningCount": 0,
                "errorCount": 0,
            },
            "Bindings": [],
            "View": {
                "Dynamo": {
                    "ScaleFactor": 1.0,
                    "HasRunWithoutCrash": True,
                    "IsVisibleInDynamoLibrary": True,
                    "Version": "2.19.3.6394",
                    "RunType": "Manual",
                    "RunPeriod": "1000",
                },
                "Camera": {
                    "Name": "_Background Preview",
                    "EyeX": -17.0,
                    "EyeY": 24.0,
                    "EyeZ": 50.0,
                    "LookX": 12.0,
                    "LookY": -13.0,
                    "LookZ": -58.0,
                    "UpX": 0.0,
                    "UpY": 1.0,
                    "UpZ": 0.0,
                },
                "ConnectorPins": [],
                "NodeViews": self.node_views,
                "Annotations": self.annotations,
                "X": 50.0,
                "Y": 50.0,
                "Zoom": 0.80,
            },
        }

    def save(self, filepath: str) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return os.path.abspath(filepath)


def main():
    parser = argparse.ArgumentParser(description="Construtor de arquivos .dyn para Civil 3D a partir de um script Python (.py)")
    parser.add_argument("--name", required=True, help="Nome da ferramenta Dynamo")
    parser.add_argument("--python-file", required=True, help="Caminho para o arquivo .py que irá no nó principal CPython3")
    parser.add_argument("--output", required=True, help="Caminho de saída do arquivo .dyn")
    parser.add_argument("--description", default="", help="Descrição da ferramenta")
    args = parser.parse_args()

    with open(args.python_file, "r", encoding="utf-8") as pf:
        py_code = pf.read()

    builder = DynamoGraphBuilder(name=args.name, description=args.description)
    in_run = builder.add_bool_input("01. Executar Ferramenta (Sim/Não)", True, "Ativa a execução no Civil 3D")
    py_node = builder.add_python_node(f"Motor IA & Civil 3D: {args.name}", py_code, num_inputs=1)
    out_watch = builder.add_watch_output("Relatório Executivo (Dynamo Player)")

    builder.connect(in_run, py_node, 0, 0)
    builder.connect(py_node, out_watch, 0, 0)

    builder.add_group("01. Entrada (Dynamo Player)", [in_run], color=DynamoGraphBuilder.COLOR_INPUT_BLUE)
    builder.add_group("02. Motor CPython3 (.NET + IA)", [py_node], color=DynamoGraphBuilder.COLOR_AI_PURPLE)
    builder.add_group("03. Saída Executiva", [out_watch], color=DynamoGraphBuilder.COLOR_OUTPUT_GREEN)

    saved = builder.save(args.output)
    print(f"[OK] Arquivo .dyn gerado com sucesso em: {saved}")


if __name__ == "__main__":
    main()
