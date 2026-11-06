# -*- coding: utf-8 -*-
"""
TEMPLATE OFICIAL: Nó CPython3 para Autodesk Civil 3D (.NET API + IA + Dynamo Player)
Compatível com Civil 3D 2022, 2023, 2024, 2025 e 2026+
"""

import sys
import math
import json
import traceback
import clr

# 1. Carregamento de Assemblies .NET do AutoCAD e Civil 3D
clr.AddReference("acmgd")
clr.AddReference("acdbmgd")
clr.AddReference("accoremgd")
clr.AddReference("AecBaseMgd")
clr.AddReference("AecPropDataMgd")
clr.AddReference("AeccDbMgd")
clr.AddReference("ProtoGeometry")
clr.AddReference("AutoCADNodes")
clr.AddReference("Civil3DNodes")

from Autodesk.AutoCAD.Runtime import *
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.EditorInput import *
from Autodesk.AutoCAD.DatabaseServices import *
import Autodesk.AutoCAD.Geometry as AcGeom

from Autodesk.Civil.ApplicationServices import *
from Autodesk.Civil.DatabaseServices import *
from Autodesk.Civil.DatabaseServices.Styles import *

import Autodesk.DesignScript.Geometry as DynGeom


# ==============================================================================
# UTILITÁRIOS DE ENGENHARIA E UNWRAPPING
# ==============================================================================

def to_object_id(obj, db=None):
    """Extrai o ObjectId nativo a partir de um objeto Dynamo, Handle ou ObjectId."""
    if obj is None:
        return ObjectId.Null
    if isinstance(obj, ObjectId):
        return obj
    if hasattr(obj, "InternalObjectId"):
        return obj.InternalObjectId
    if hasattr(obj, "InternalDBObject"):
        return obj.InternalDBObject.ObjectId
    if isinstance(obj, str) and db is not None:
        try:
            return db.GetObjectId(False, Handle(int(obj, 16)), 0)
        except Exception:
            return ObjectId.Null
    return ObjectId.Null


def find_surface_by_name(tr, civdoc, name_filter=""):
    """Busca uma TinSurface pelo nome (ou retorna a primeira disponível se vazio)."""
    surf_ids = civdoc.GetSurfaceIds()
    first_tin = None
    for sid in surf_ids:
        surf = tr.GetObject(sid, OpenMode.ForRead)
        if isinstance(surf, TinSurface):
            if first_tin is None:
                first_tin = surf
            if name_filter and surf.Name.strip().lower() == name_filter.strip().lower():
                return surf
    return first_tin


def find_alignment_by_name(tr, civdoc, name_filter=""):
    """Busca um Alignment pelo nome (ou retorna o primeiro disponível se vazio)."""
    alg_ids = civdoc.GetAlignmentIds()
    first_alg = None
    for aid in alg_ids:
        alg = tr.GetObject(aid, OpenMode.ForRead)
        if isinstance(alg, Alignment):
            if first_alg is None:
                first_alg = alg
            if name_filter and alg.Name.strip().lower() == name_filter.strip().lower():
                return alg
    return first_alg


# ==============================================================================
# EXECUÇÃO PRINCIPAL DO NÓ DYNAMO
# ==============================================================================

def run_civil3d_tool():
    # Leitura segura de entradas do Dynamo (IN[0], IN[1], ...)
    run_flag = bool(IN[0]) if len(IN) > 0 and IN[0] is not None else True
    target_surface_name = str(IN[1]) if len(IN) > 1 and IN[1] is not None else ""

    if not run_flag:
        return {"status": "AGUARDANDO", "mensagem": "Defina 'Executar = True' no Dynamo Player."}

    adoc = Application.DocumentManager.MdiActiveDocument
    if adoc is None:
        return {"status": "ERRO", "mensagem": "Nenhum documento DWG ativo no Civil 3D."}

    db = adoc.Database
    ed = adoc.Editor
    civdoc = CivilApplication.ActiveDocument

    report = {
        "status": "SUCESSO",
        "documento": adoc.Name,
        "superficie_utilizada": None,
        "total_alinhamentos": 0,
        "total_redes_drenagem": 0,
        "log": [],
    }

    try:
        with adoc.LockDocument():
            with db.TransactionManager.StartTransaction() as tr:
                surf = find_surface_by_name(tr, civdoc, target_surface_name)
                if surf is not None:
                    report["superficie_utilizada"] = surf.Name
                    props = surf.GetGeneralProperties()
                    report["log"].append(
                        f"Superfície '{surf.Name}' carregada (Cota Mín: {props.MinimumElevation:.2f}m, Máx: {props.MaximumElevation:.2f}m)."
                    )
                else:
                    report["log"].append("Nenhuma TinSurface encontrada no DWG.")

                report["total_alinhamentos"] = civdoc.GetAlignmentIds().Count
                report["total_redes_drenagem"] = civdoc.GetPipeNetworkIds().Count

                tr.Commit()
    except Exception as ex:
        report["status"] = "ERRO"
        report["erro_detalhado"] = str(ex)
        report["traceback"] = traceback.format_exc()

    return report


OUT = run_civil3d_tool()
