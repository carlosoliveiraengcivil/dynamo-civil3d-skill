# Referência Completa: AutoCAD & Civil 3D .NET API no Dynamo (CPython3)

Este guia contém os padrões de código, namespaces e métodos da API `.NET` do AutoCAD e do Autodesk Civil 3D para uso dentro de nós Python (`CPython3` / `pythonnet`) no Dynamo.

---

## 1. Boilerplate Padrão de Importação (`CPython3`)

Todo nó Python no Dynamo para Civil 3D que interage com o banco de dados DWG deve iniciar com este cabeçalho seguro:

```python
import sys
import math
import traceback
import clr

# 1. Assemblies do AutoCAD .NET API
clr.AddReference('acmgd')
clr.AddReference('acdbmgd')
clr.AddReference('accoremgd')

# 2. Assemblies do Civil 3D .NET API
clr.AddReference('AecBaseMgd')
clr.AddReference('AecPropDataMgd')
clr.AddReference('AeccDbMgd')

# 3. Assemblies do Dynamo e Nós Civil 3D
clr.AddReference('ProtoGeometry')
clr.AddReference('AutoCADNodes')
clr.AddReference('Civil3DNodes')

# Imports AutoCAD (usando alias AcGeom para evitar colisão com DesignScript)
from Autodesk.AutoCAD.Runtime import *
from Autodesk.AutoCAD.ApplicationServices import *
from Autodesk.AutoCAD.EditorInput import *
from Autodesk.AutoCAD.DatabaseServices import *
import Autodesk.AutoCAD.Geometry as AcGeom

# Imports Civil 3D
from Autodesk.Civil.ApplicationServices import *
from Autodesk.Civil.DatabaseServices import *
from Autodesk.Civil.DatabaseServices.Styles import *
from Autodesk.Civil.Settings import *

# Imports Property Sets (BIM / IFC)
from Autodesk.Aec.PropertyData import *
from Autodesk.Aec.PropertyData.DatabaseServices import *

# Imports Dynamo Geometry (com alias DynGeom)
import Autodesk.DesignScript.Geometry as DynGeom
import Autodesk.AutoCAD.DynamoNodes as AcDynNodes
import Autodesk.Civil.DynamoNodes as CivDynNodes
```

---

## 2. Gerenciamento de Documento, Transações e Unwrapping

### Padrão de Transação Segura (`LockDocument` + `StartTransaction`)
No Civil 3D (especialmente quando acionado via Dynamo Player ou janelas modais), bloqueie sempre o documento (`adoc.LockDocument()`) antes de iniciar uma transação de escrita:

```python
adoc = Application.DocumentManager.MdiActiveDocument
ed = adoc.Editor
db = adoc.Database
civdoc = CivilApplication.ActiveDocument

with adoc.LockDocument():
    with db.TransactionManager.StartTransaction() as tr:
        # Operações aqui...
        tr.Commit()
```

### Função Universal para Extrair `ObjectId` de Entradas do Dynamo
Os objetos conectados a `IN[0]`, `IN[1]`, etc. podem ser objetos encapsulados do Dynamo (`AcDynNodes.Object`), `ObjectId` nativos ou `Handle` (string). Use sempre este extrator recursivo:

```python
def to_object_id(obj, db=None):
    """Converte qualquer objeto Dynamo, Handle ou ObjectId em um Autodesk.AutoCAD.DatabaseServices.ObjectId."""
    if obj is None:
        return ObjectId.Null
    if isinstance(obj, ObjectId):
        return obj
    # Wrapper do Dynamo (AutoCADNodes / Civil3DNodes)
    if hasattr(obj, "InternalObjectId"):
        return obj.InternalObjectId
    if hasattr(obj, "InternalDBObject"):
        return obj.InternalDBObject.ObjectId
    # Handle em formato hexadecimal (string)
    if isinstance(obj, str) and db is not None:
        try:
            h = Handle(int(obj, 16))
            return db.GetObjectId(False, h, 0)
        except Exception:
            return ObjectId.Null
    return ObjectId.Null

def unwrap_list(data):
    """Garante que o input seja tratado como lista plana."""
    if data is None:
        return []
    if isinstance(data, (list, tuple)):
        res = []
        for item in data:
            res.extend(unwrap_list(item))
        return res
    return [data]
```

---

## 3. Operações por Disciplina na API do Civil 3D

### 3.1. Superfícies (`TinSurface` e `TinVolumeSurface`)

```python
# Obter todas as superfícies do documento ou abrir por nome
surface_ids = civdoc.GetSurfaceIds()
target_surf = None
for sid in surface_ids:
    surf = tr.GetObject(sid, OpenMode.ForRead)
    if isinstance(surf, TinSurface) and surf.Name == "TN_PRIMITIVO":
        target_surf = surf
        break

# Consultar cota (Z) em coordenada (X, Y)
# Atenção: lança PointNotOnSurfaceException se (X, Y) estiver fora da borda da TIN!
try:
    z = target_surf.FindElevationAtXY(x, y)
except Exception:
    z = None  # Ponto fora da superfície

# Extrair malha de triângulos da superfície TIN (para IA / Pathfinding A* / Declividades)
triangles = target_surf.GetTriangles(False) # False = ignora triângulos invisíveis/ocultos
for tri in triangles:
    v1 = tri.Vertex1.Location # AcGeom.Point3d
    v2 = tri.Vertex2.Location
    v3 = tri.Vertex3.Location

# Criar Superfície de Volume (Corte / Aterro)
style_id = civdoc.Styles.SurfaceStyles[0]
vol_surf_id = TinVolumeSurface.Create("VOL_TERRAPLENAGEM", base_surf_id, comp_surf_id, style_id)
vol_surf = tr.GetObject(vol_surf_id, OpenMode.ForRead)
props = vol_surf.GetVolumeProperties()
cut_vol = props.UnadjustedCutVolume      # m³
fill_vol = props.UnadjustedFillVolume    # m³
net_vol = props.UnadjustedNetVolume      # m³
```

### 3.2. Alinhamentos Horizontais (`Alignment`)

```python
align_ids = civdoc.GetAlignmentIds()
align = tr.GetObject(align_ids[0], OpenMode.ForRead)

# Estaca inicial e final
sta_start = align.StartingStation
sta_end = align.EndingStation
length = align.Length

# Converter (Estaca, Offset) -> (X, Y)
x_out = clr.Reference[float](0.0)
y_out = clr.Reference[float](0.0)
align.PointLocation(station, offset, x_out, y_out)
pt_xy = (float(x_out.Value), float(y_out.Value))

# Converter (X, Y) -> (Estaca, Offset)
sta_out = clr.Reference[float](0.0)
off_out = clr.Reference[float](0.0)
align.StationOffset(x, y, sta_out, off_out)
sta, off = float(sta_out.Value), float(off_out.Value)

# Inspecionar entidades horizontais (Tangentes, Curvas Circulares, Espirais)
for ent in align.Entities:
    ent_type = ent.EntityType # Line, Arc, SpiralCurveSpiral, etc.
    if hasattr(ent, "Radius"):
        r = ent.Radius
```

### 3.3. Perfis Longitudinais / Greides (`Profile` & `ProfilePVI`)

```python
# Obter perfis de um alinhamento
profile_ids = align.GetProfileIds()
profile = tr.GetObject(profile_ids[0], OpenMode.ForWrite)

# Consultar cota do perfil em uma estaca
elev = profile.ElevationAt(station)
grade = profile.GradeAt(station) # Declividade em decimal (ex: 0.045 = 4.5%)

# Ler e manipular PVIs (Pontos de Inflexão Vertical)
for pvi in profile.PVIs:
    sta_pvi = pvi.Station
    elev_pvi = pvi.Elevation
    grade_in = pvi.GradeIn
    grade_out = pvi.GradeOut

# Criar um novo Perfil de Projeto (Layout Profile) e adicionar PVIs + Parábolas
layer_id = align.LayerId
prof_style_id = civdoc.Styles.ProfileStyles[0]
label_set_id = civdoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0]
new_prof_id = Profile.CreateByLayout("GREIDE_OTIMIZADO_IA", align.ObjectId, layer_id, prof_style_id, label_set_id)
new_prof = tr.GetObject(new_prof_id, OpenMode.ForWrite)

# Adicionar PVIs extremos e intermediários
pvi1 = new_prof.PVIs.AddPVI(sta_start, z_start)
pvi2 = new_prof.PVIs.AddPVI(sta_mid, z_mid)
pvi3 = new_prof.PVIs.AddPVI(sta_end, z_end)

# Adicionar parábola simétrica de concordância vertical no PVI central com comprimento L
new_prof.Entities.AddFreeSymmetricParabolaByLength(pvi2.Station, pvi2.Elevation, curve_length)
```

### 3.4. Corredores (`Corridor`, `Baseline`, `BaselineRegion`)

```python
corr_ids = civdoc.CorridorCollection
for cid in corr_ids:
    corr = tr.GetObject(cid, OpenMode.ForWrite)
    for bl in corr.Baselines:
        for reg in bl.BaselineRegions:
            # Ajustar frequência de seções
            reg.AppliedAssemblySetting.FrequencyAlongTangents = 10.0
            reg.AppliedAssemblySetting.FrequencyAlongCurves = 5.0
            # Configurar Targets de superfície
            targets = reg.GetTargets()
            for t in targets:
                if t.TargetType == SubassemblyLogicalNameType.Surface:
                    t.TargetIds.Clear()
                    t.TargetIds.Add(target_surf.ObjectId)
            reg.SetTargets(targets)
    # Reconstruir corredor após alterações
    corr.Rebuild()
```

### 3.5. Redes de Drenagem e Esgoto (`Network`, `Pipe`, `Structure`)

```python
net_ids = civdoc.GetPipeNetworkIds()
net = tr.GetObject(net_ids[0], OpenMode.ForRead)

# Iterar e modificar Tubos (Pipes)
for pid in net.GetPipeIds():
    pipe = tr.GetObject(pid, OpenMode.ForWrite)
    name = pipe.Name
    inner_diam = pipe.InnerDiameterOrWidth  # metros
    outer_diam = pipe.OuterDiameterOrWidth
    slope = pipe.Slope                      # m/m
    length_3d = pipe.Length3DCenterToCenter
    min_cover = pipe.MinimumCover           # Cobrimento mínimo (se RefSurface definida)
    
    # Alterar cotas de montante e jusante (StartPoint / EndPoint no eixo ou geratriz)
    sp = pipe.StartPoint
    ep = pipe.EndPoint
    pipe.StartPoint = AcGeom.Point3d(sp.X, sp.Y, new_z_start)
    pipe.EndPoint = AcGeom.Point3d(ep.X, ep.Y, new_z_end)

# Iterar e modificar Poços de Visita / Caixas (Structures)
for stid in net.GetStructureIds():
    st = tr.GetObject(stid, OpenMode.ForWrite)
    st.ControlSumpBy = StructureControlSumpType.ByDepth
    st.SumpDepth = 0.0
    # Ajustar à superfície de referência
    if target_surf is not None:
        st.RefSurfaceId = target_surf.ObjectId
        st.UseSurfaceAdjustmentValue = True
        st.SurfaceAdjustmentValue = 0.0
```

### 3.6. Property Sets BIM / IFC (`AecPropDataMgd`)

```python
# Ler ou escrever dados em um Property Set anexado a um objeto Civil 3D / AutoCAD
def set_property_set_value(tr, obj_id, prop_set_name, prop_name, value):
    prop_sets = PropertyDataServices.GetPropertySets(obj_id)
    for ps_id in prop_sets:
        ps = tr.GetObject(ps_id, OpenMode.ForWrite)
        if ps.PropertySetDefinitionName == prop_set_name:
            prop_id = ps.PropertyNameToId(prop_name)
            ps.SetAt(prop_id, value)
            return True
    return False
```

### 3.7. Seleção Interativa Direta no Editor do AutoCAD (DXF Filter)

Quando o usuário deseja selecionar entidades diretamente na tela ao rodar o grafo:

```python
def select_entities_by_dxf(ed, prompt_msg, dxf_types_csv):
    """
    Exemplo de dxf_types_csv:
    - 'AECC_ALIGNMENT'
    - 'AECC_TIN_SURFACE'
    - 'AECC_PIPE,AECC_STRUCTURE'
    - 'LWPOLYLINE,POLYLINE'
    """
    pso = PromptSelectionOptions()
    pso.MessageForAdding = f"\n{prompt_msg}: "
    tv = [TypedValue(int(DxfCode.Start), dxf_types_csv)]
    sf = SelectionFilter(tv)
    res = ed.GetSelection(pso, sf)
    if res.Status == PromptStatus.OK:
        return list(res.Value.GetObjectIds())
    return []
```
