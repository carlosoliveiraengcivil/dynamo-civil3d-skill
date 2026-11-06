#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_dyn.py — Validador Estrutural, Sintático (AST) e de Dynamo Player para arquivos .dyn (Civil 3D).

Uso:
    python validate_dyn.py <caminho_do_arquivo.dyn>
"""

import ast
import json
import os
import sys
from typing import List, Tuple


def validate_dyn_file(filepath: str) -> Tuple[bool, List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if not os.path.exists(filepath):
        return False, [f"Arquivo não encontrado: {filepath}"], []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as ex:
        return False, [f"JSON inválido no arquivo .dyn: {ex}"], []

    required_keys = ["Uuid", "Name", "Nodes", "Connectors", "View"]
    for k in required_keys:
        if k not in data:
            errors.append(f"Chave obrigatória ausente na raiz do .dyn: '{k}'")

    if errors:
        return False, errors, warnings

    nodes = data.get("Nodes", [])
    connectors = data.get("Connectors", [])
    view = data.get("View", {})
    node_views = view.get("NodeViews", [])

    node_ids = set()
    output_port_ids = set()
    input_port_ids = set()
    python_nodes_count = 0

    for idx, node in enumerate(nodes):
        nid = node.get("Id")
        if not nid:
            errors.append(f"Nó #{idx} não possui 'Id'.")
            continue
        if nid in node_ids:
            errors.append(f"ID de nó duplicado detectado: '{nid}'")
        node_ids.add(nid)

        for inp in node.get("Inputs", []):
            pid = inp.get("Id")
            if pid:
                input_port_ids.add(pid)
        for outp in node.get("Outputs", []):
            pid = outp.get("Id")
            if pid:
                output_port_ids.add(pid)

        concrete = node.get("ConcreteType", "")
        if "PythonNode" in concrete:
            python_nodes_count += 1
            engine = node.get("Engine", "")
            if engine != "CPython3":
                warnings.append(f"Nó Python '{nid}' usa Engine='{engine}' em vez de 'CPython3'.")

            code = node.get("Code", "")
            if not code.strip():
                errors.append(f"Nó Python '{nid}' possui código vazio.")
            else:
                try:
                    ast.parse(code)
                except SyntaxError as sex:
                    errors.append(
                        f"Erro de sintaxe Python no nó '{nid}' (linha {sex.lineno}): {sex.msg}"
                    )
                if "OUT" not in code:
                    warnings.append(
                        f"Nó Python '{nid}' não parece atribuir a variável de saída 'OUT'."
                    )

    # Verificar NodeViews
    nv_ids = {nv.get("Id") for nv in node_views if nv.get("Id")}
    missing_views = node_ids - nv_ids
    if missing_views:
        errors.append(f"Nós sem posicionamento em View.NodeViews: {missing_views}")

    # Verificar Conectores
    for c_idx, conn in enumerate(connectors):
        start_id = conn.get("Start")
        end_id = conn.get("End")
        if start_id not in output_port_ids:
            errors.append(f"Conector #{c_idx} referencia porta de saída inexistente: '{start_id}'")
        if end_id not in input_port_ids:
            errors.append(f"Conector #{c_idx} referencia porta de entrada inexistente: '{end_id}'")

    # Verificar prontidão para Dynamo Player
    player_inputs = [nv for nv in node_views if nv.get("IsSetAsInput") is True]
    player_outputs = [nv for nv in node_views if nv.get("IsSetAsOutput") is True]
    if not player_inputs:
        warnings.append("Nenhum nó marcado com 'IsSetAsInput: true' para o Dynamo Player.")
    if not player_outputs:
        warnings.append("Nenhum nó marcado com 'IsSetAsOutput: true' para o Dynamo Player.")

    run_type = view.get("Dynamo", {}).get("RunType", "Manual")
    if run_type != "Manual":
        warnings.append(f"RunType está configurado como '{run_type}' (recomendado: 'Manual').")

    is_ok = len(errors) == 0
    return is_ok, errors, warnings


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if len(sys.argv) < 2:
        print("Uso: python validate_dyn.py <arquivo.dyn>")
        sys.exit(1)

    target = sys.argv[1]
    ok, errs, warns = validate_dyn_file(target)

    print("=" * 65)
    print(f"VALIDAÇÃO DE ARQUIVO DYNAMO (.dyn): {os.path.basename(target)}")
    print("=" * 65)
    if warns:
        print(f"\n[!] Avisos ({len(warns)}):")
        for w in warns:
            print(f"  - {w}")

    if errs:
        print(f"\n[ERRO] Falhas encontradas ({len(errs)}):")
        for e in errs:
            print(f"  - {e}")
        sys.exit(2)
    else:
        with open(target, "r", encoding="utf-8") as f:
            d = json.load(f)
        n_nodes = len(d.get("Nodes", []))
        n_conns = len(d.get("Connectors", []))
        n_groups = len(d.get("View", {}).get("Annotations", []))
        n_in = len(d.get("Inputs", []))
        n_out = len(d.get("Outputs", []))
        print(f"\n[SUCESSO] Arquivo .dyn 100% válido e pronto para o Civil 3D!")
        print(f"  • Nome da Ferramenta : {d.get('Name')}")
        print(f"  • Total de Nós       : {n_nodes}")
        print(f"  • Conectores         : {n_conns}")
        print(f"  • Grupos Visuais     : {n_groups}")
        print(f"  • Dynamo Player I/O  : {n_in} Input(s) | {n_out} Output(s)")
        print("=" * 65)
        sys.exit(0)


if __name__ == "__main__":
    main()
