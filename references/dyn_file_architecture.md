# Arquitetura de Arquivos `.dyn` (JSON) & Compatibilidade com Dynamo Player

Desde o Dynamo 2.0+ (incluindo o Dynamo para Civil 3D 2022, 2023, 2024, 2025 e 2026+), todo arquivo `.dyn` é um documento **JSON estruturado**. Compreender sua estrutura exata permite gerar ferramentas completas programaticamente sem precisar montar nós manualmente.

---

## 1. Estrutura Raiz de um Arquivo `.dyn`

```json
{
  "Uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "IsCustomNode": false,
  "Description": "Ferramenta de Engenharia Civil 3D gerada por IA",
  "Name": "Nome_Da_Ferramenta",
  "ElementResolver": {
    "ResolutionMap": {}
  },
  "Inputs": [],
  "Outputs": [],
  "Nodes": [],
  "Connectors": [],
  "Dependencies": [],
  "NodeLibraryDependencies": [],
  "Thumbnail": "",
  "GraphDocumentationURL": null,
  "ExtensionWorkspaceData": [
    {
      "ExtensionGuid": "28992e1d-abb9-417f-8b1b-05e053bee670",
      "Name": "Properties",
      "Version": "2.16",
      "Data": {}
    }
  ],
  "Author": "Dynamo Civil 3D AI Specialist",
  "Linting": {
    "activeLinter": "None",
    "activeLinterId": "7b75fb44-43fd-4631-a878-29f4d5d8399a",
    "warningCount": 0,
    "errorCount": 0
  },
  "Bindings": [],
  "View": {
    "Dynamo": {
      "ScaleFactor": 1.0,
      "HasRunWithoutCrash": true,
      "IsVisibleInDynamoLibrary": true,
      "Version": "2.19.3.6394",
      "RunType": "Manual",
      "RunPeriod": "1000"
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
      "UpZ": 0.0
    },
    "ConnectorPins": [],
    "NodeViews": [],
    "Annotations": [],
    "X": 0.0,
    "Y": 0.0,
    "Zoom": 0.85
  }
}
```

> [!IMPORTANT]
> **Modo de Execução (`RunType`)**: Sempre defina `"RunType": "Manual"` em ferramentas de engenharia que modificam o banco de dados do Civil 3D ou executam algoritmos pesados de IA, evitando execuções acidentais ao abrir o arquivo.

---

## 2. Tipos de Nós (`ConcreteType`) Essenciais

### 2.1. Nó Python (`PythonNodeModels.PythonNode`)
O coração de qualquer ferramenta avançada para Civil 3D:

```json
{
  "ConcreteType": "PythonNodeModels.PythonNode, PythonNodeModels",
  "NodeType": "PythonScriptNode",
  "Code": "# Código CPython3 aqui...",
  "Engine": "CPython3",
  "EngineName": "CPython3",
  "VariableInputPorts": true,
  "Id": "a1b2c3d4e5f64789a1b2c3d4e5f60001",
  "Inputs": [
    {
      "Id": "a1b2c3d4e5f64789a1b2c3d4e5f60011",
      "Name": "IN[0]",
      "Description": "Input #0",
      "UsingDefaultValue": false,
      "Level": 2,
      "UseLevels": false,
      "KeepListStructure": false
    }
  ],
  "Outputs": [
    {
      "Id": "a1b2c3d4e5f64789a1b2c3d4e5f60021",
      "Name": "OUT",
      "Description": "Resultado da execução do script Python",
      "UsingDefaultValue": false,
      "Level": 2,
      "UseLevels": false,
      "KeepListStructure": false
    }
  ],
  "Replication": "Disabled",
  "Description": "Executa um script CPython3 com acesso à API .NET do Civil 3D."
}
```

### 2.2. Nós de Entrada Nativa para o **Dynamo Player**

Para que o engenheiro possa ajustar parâmetros diretamente no **Dynamo Player** do Civil 3D sem abrir o grafo:
1. O nó deve ser um nó de Input (`StringInput`, `DoubleInput`, `BoolSelector`, `Filename`, `Directory`).
2. O seu respectivo `NodeView` (em `View.NodeViews`) deve ter `"IsSetAsInput": true` e `"Name": "Título amigável do parâmetro"`.
3. O array raiz `"Inputs"` do `.dyn` deve conter o descritor do Input correspondente.

#### String Input (`CoreNodeModels.Input.StringInput`)
```json
{
  "ConcreteType": "CoreNodeModels.Input.StringInput, CoreNodeModels",
  "NodeType": "StringInputNode",
  "InputValue": "TN_PRIMITIVO",
  "Id": "node_id_32_hex",
  "Inputs": [],
  "Outputs": [
    {
      "Id": "port_id_32_hex",
      "Name": "",
      "Description": "String",
      "UsingDefaultValue": false,
      "Level": 2,
      "UseLevels": false,
      "KeepListStructure": false
    }
  ],
  "Replication": "Disabled",
  "Description": "Cria uma cadeia de caracteres."
}
```

#### Number Input (`CoreNodeModels.Input.DoubleInput`)
```json
{
  "ConcreteType": "CoreNodeModels.Input.DoubleInput, CoreNodeModels",
  "NodeType": "NumberInputNode",
  "NumberType": "Double",
  "InputValue": 1.5,
  "Id": "node_id_32_hex",
  "Inputs": [],
  "Outputs": [
    {
      "Id": "port_id_32_hex",
      "Name": "",
      "Description": "Double",
      "UsingDefaultValue": false,
      "Level": 2,
      "UseLevels": false,
      "KeepListStructure": false
    }
  ],
  "Replication": "Disabled",
  "Description": "Cria um número."
}
```

#### Boolean Input (`CoreNodeModels.Input.BoolSelector`)
```json
{
  "ConcreteType": "CoreNodeModels.Input.BoolSelector, CoreNodeModels",
  "NodeType": "BooleanInputNode",
  "InputValue": true,
  "Id": "node_id_32_hex",
  "Inputs": [],
  "Outputs": [
    {
      "Id": "port_id_32_hex",
      "Name": "",
      "Description": "Boolean",
      "UsingDefaultValue": false,
      "Level": 2,
      "UseLevels": false,
      "KeepListStructure": false
    }
  ],
  "Replication": "Disabled",
  "Description": "Seleção entre verdadeiro e falso."
}
```

### 2.3. Nó de Saída / Watch para o **Dynamo Player** (`CoreNodeModels.Watch`)
Para exibir relatórios executivos, métricas de otimização de IA ou status no **Dynamo Player**:
1. Conecte a saída do nó Python (ou de um CodeBlock de extração) a um nó `CoreNodeModels.Watch, CoreNodeModels`.
2. No `NodeView` desse Watch, defina `"IsSetAsOutput": true` e `"Name": "Relatório Executivo / Resultado"`.
3. Registre também no array raiz `"Outputs"`.

---

## 3. Conectores (`Connectors`), `NodeViews` e `Annotations`

### 3.1. Conectores (`Connectors`)
Cada conector liga a porta de saída (`Start` = `Output[i].Id`) de um nó à porta de entrada (`End` = `Input[j].Id`) de outro nó:
```json
{
  "Start": "output_port_id_32_hex",
  "End": "input_port_id_32_hex",
  "Id": "connector_id_32_hex",
  "IsHidden": "False"
}
```

### 3.2. Posicionamento Visual (`View.NodeViews`)
Todo nó em `"Nodes"` **deve** ter um item correspondente em `"View.NodeViews"` com `"Id"` idêntico ao `"Id"` do nó:
```json
{
  "Id": "node_id_32_hex",
  "Name": "01. Parâmetro: Superfície Alvo",
  "IsSetAsInput": true,
  "IsSetAsOutput": false,
  "Excluded": false,
  "ShowGeometry": true,
  "X": 100.0,
  "Y": 150.0
}
```

### 3.3. Padrão de Cores para Grupos (`View.Annotations`)
Sempre agrupe visualmente os nós em colunas lógicas usando `Annotations`:
- **Azul (`#FF48B5E0`)**: *01. Parâmetros de Entrada (Dynamo Player)* — Coluna $X \approx 100$
- **Roxo (`#FF8C62E8`)**: *02. Motor de IA & Otimização / Processamento .NET* — Coluna $X \approx 650$
- **Verde (`#FF27AE60`)**: *03. Relatórios Executivos & Auditoria BIM (Outputs)* — Coluna $X \approx 1200$
