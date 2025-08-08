# PokeQueue Function

Una Azure Function que procesa solicitudes de reportes de Pokémon de forma asíncrona utilizando colas de Azure Storage y la PokéAPI.

## 🏗️ Arquitectura del Sistema PokeQueue

Este repositorio es parte de un ecosistema completo de microservicios para el procesamiento de reportes de Pokémon. El sistema completo está compuesto por los siguientes componentes:

### 🔗 Repositorios Relacionados

| Componente | Repositorio | Descripción |
|------------|-------------|-------------|
| **Frontend** | [PokeQueue UI](https://github.com/REliezer/pokequeue-ui) | Interfaz de usuario web para solicitar y gestionar reportes de Pokémon |
| **API REST** | [PokeQueue API](https://github.com/REliezer/pokequeueAPI) | API principal que gestiona solicitudes de reportes y coordinación del sistema |
| **Azure Functions** | [PokeQueue Functions](https://github.com/REliezer/pokequeue-function) | Este repositorio - Procesamiento asíncrono de reportes |
| **Base de Datos** | [PokeQueue SQL Scripts](https://github.com/REliezer/pokequeue-sql) | Scripts SQL para la configuración y mantenimiento de la base de datos |
| **Infraestructura** | [PokeQueue Terraform](https://github.com/REliezer/pokequeue-terrafom) | Configuración de infraestructura como código (IaC) |

### 🔄 Flujo de Datos del Sistema Completo

1. **PokeQueue UI** → Usuario solicita reporte desde la interfaz web
2. **PokeQueue UI** → Envía solicitud a **PokeQueue API**
3. **PokeQueue API** → Valida la solicitud y la guarda en la base de datos
4. **PokeQueue API** → Envía mensaje a la cola de Azure Storage
5. **PokeQueue Function** *(este repo)* → Procesa el mensaje de la cola
6. **PokeQueue Function** → Consulta PokéAPI y genera el reporte CSV
7. **PokeQueue Function** → Almacena el CSV en Azure Blob Storage
8. **PokeQueue Function** → Notifica el estado a **PokeQueue API**
9. **PokeQueue UI** → Consulta el estado y permite descargar el reporte terminado

### 🏗️ Diagrama de Arquitectura

```
   ┌─────────────────┐
   │   PokeQueue UI  │
   │ (Frontend Web)  │
   └─────────┼───────┘
             │
             ▼ HTTP/REST
  ┌─────────────────┐    ┌─────────────────┐
  │  PokeQueue API  │────│   Azure SQL DB  │
  │   (REST API)    │    │  (Persistencia) │
  └─────────┼───────┘    └─────────────────┘
            │
            ▼ Queue Message
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │  Azure Storage  │────│ PokeQueue Func  │────│   Azure Blob    │
   │     Queue       │    │ (Procesamiento) │    │    Storage      │
   └─────────────────┘    └─────────┼───────┘    └─────────────────┘
                                    │
                                    ▼ HTTP API Call
                           ┌─────────────────┐
                           │    PokéAPI      │
                           │ (Datos Pokémon) │
                           └─────────────────┘
```

## 📋 Descripción

Esta función serverless se activa mediante mensajes en una cola de Azure Storage y genera reportes en formato CSV con información detallada de Pokémon basada en su tipo. Los reportes generados se almacenan en Azure Blob Storage y se notifica el estado de la solicitud a través de una API externa.

## 🚀 Funcionalidades

- **Procesamiento asíncrono**: Utiliza Azure Storage Queue para el procesamiento de solicitudes
- **Integración con PokéAPI**: Obtiene información completa de Pokémon por tipo
- **Generación de reportes CSV**: Crea archivos CSV con estadísticas detalladas de Pokémon
- **Almacenamiento en la nube**: Guarda los reportes en Azure Blob Storage
- **Muestreo configurable**: Permite especificar el tamaño de muestra para los reportes
- **Gestión de estados**: Actualiza el estado de las solicitudes (inprogress, completed, failed)
- **Logging robusto**: Sistema de logging detallado para monitoreo y debugging

## 📊 Datos incluidos en los reportes

Cada reporte CSV incluye la siguiente información para cada Pokémon:

- **Información básica**: nombre, altura, peso, sprite
- **Características**: tipos, generación, habilidades
- **Estadísticas de combate**:
  - HP (puntos de vida)
  - Attack (ataque)
  - Defense (defensa)  
  - Special Attack (ataque especial)
  - Special Defense (defensa especial)
  - Speed (velocidad)

## 🛠️ Tecnologías utilizadas

- **Python 3.x**
- **Azure Functions** - Plataforma serverless
- **Azure Storage Queue** - Cola de mensajes
- **Azure Blob Storage** - Almacenamiento de archivos
- **PokéAPI** - API externa de datos de Pokémon
- **Pandas** - Procesamiento y generación de CSV
- **Requests** - Cliente HTTP para API calls

## 📦 Dependencias

```txt
azure-functions
requests
python-dotenv
pandas
azure-storage-blob==12.26.0
```

## ⚙️ Configuración

### Variables de entorno requeridas

Crea un archivo `.env` o configura las siguientes variables de entorno:

```env
DOMAIN=https://tu-api-domain.com
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
BLOB_CONTAINER_NAME=nombre-del-contenedor
STORAGE_ACCOUNT_NAME=nombre-de-la-cuenta-de-storage
QueueAzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=...
```

### Configuración de Azure

1. **Storage Account**: Crear una cuenta de Azure Storage
2. **Blob Container**: Crear un contenedor para almacenar los reportes CSV
3. **Storage Queue**: Crear una cola llamada `requests`
4. **Function App**: Desplegar la función en Azure Functions

## 🔄 Flujo de trabajo

1. **Trigger**: La función se activa cuando llega un mensaje a la cola `requests`
2. **Parsing**: Extrae el ID de solicitud y tamaño de muestra del mensaje
3. **Estado**: Actualiza el estado de la solicitud a "inprogress"
4. **Consulta API**: Obtiene información de la solicitud desde la API externa
5. **Obtención de datos**: Consulta la PokéAPI para obtener Pokémon del tipo especificado
6. **Procesamiento**: Recopila información detallada de cada Pokémon
7. **Generación CSV**: Crea el archivo CSV con los datos obtenidos
8. **Almacenamiento**: Sube el archivo CSV a Azure Blob Storage
9. **Finalización**: Actualiza el estado a "completed" con la URL del archivo

## 📝 Formato del mensaje de cola

```json
{
    "id": 123,
    "sample_size": 50
}
```

- `id` (requerido): Identificador único de la solicitud
- `sample_size` (opcional): Número de Pokémon a incluir en la muestra

## 🚀 Instalación Completa del Sistema PokeQueue

Para desplegar el sistema completo, necesitas configurar todos los componentes en el siguiente orden:

### 1. Infraestructura (Terraform)
```bash
# Clonar el repositorio de infraestructura
git clone https://github.com/REliezer/pokequeue-terrafom.git
cd pokequeue-terrafom

# Configurar variables de Terraform
terraform init
terraform plan
terraform apply
```

### 2. Base de Datos (SQL Scripts)
```bash
# Clonar el repositorio de base de datos
git clone https://github.com/REliezer/pokequeue-sql.git
cd pokequeue-sql

# Ejecutar scripts SQL en Azure SQL Database
# (Revisar el README del repositorio SQL para instrucciones específicas)
```

### 3. API REST
```bash
# Clonar y desplegar la API
git clone https://github.com/REliezer/pokequeueAPI.git
cd pokequeueAPI

# Seguir las instrucciones del README de la API
```

### 4. Azure Functions (Este Repositorio)
```bash
# Clonar este repositorio
git clone https://github.com/REliezer/pokequeue-function.git
cd pokequeue-function

# Seguir las instrucciones de despliegue a continuación
```

### 5. Frontend UI
```bash
# Clonar y desplegar el frontend
git clone https://github.com/REliezer/pokequeue-ui.git
cd pokequeue-ui

# Seguir las instrucciones del README del UI para configuración y despliegue
```

## 🚀 Despliegue de Azure Functions

### Prerrequisitos

- Azure CLI instalado y configurado
- Python 3.x
- Azure Functions Core Tools
- Infraestructura Azure ya desplegada (ver sección anterior)

### Pasos de despliegue

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/REliezer/pokequeue-function.git
   cd pokequeue-function
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus valores
   ```

5. **Desplegar a Azure**
   ```bash
   func azure functionapp publish <nombre-de-tu-function-app>
   ```

## 🔧 Desarrollo local

### Configuración del entorno local

1. **Instalar Azure Functions Core Tools**
   ```bash
   npm install -g azure-functions-core-tools@4 --unsafe-perm true
   ```

2. **Crear archivo de configuración local**
   ```bash
   func init --python
   ```

3. **Configurar `local.settings.json`**
   ```json
   {
     "IsEncrypted": false,
     "Values": {
       "AzureWebJobsStorage": "tu-connection-string",
       "FUNCTIONS_WORKER_RUNTIME": "python",
       "DOMAIN": "https://tu-api-domain.com",
       "AZURE_STORAGE_CONNECTION_STRING": "tu-connection-string",
       "BLOB_CONTAINER_NAME": "tu-contenedor",
       "STORAGE_ACCOUNT_NAME": "tu-storage-account",
       "QueueAzureWebJobsStorage": "tu-connection-string"
     }
   }
   ```

4. **Ejecutar localmente**
   ```bash
   func start
   ```

## 🧪 Testing

Para probar la función localmente:

1. **Enviar mensaje a la cola**
   ```python
   from azure.storage.queue import QueueClient
   import json
   
   queue_client = QueueClient.from_connection_string(
       conn_str="tu-connection-string",
       queue_name="requests"
   )
   
   message = {
       "id": 1,
       "sample_size": 10
   }
   
   queue_client.send_message(json.dumps(message))
   ```

2. **Verificar logs** en la consola de Azure Functions

## 📊 Monitoreo

La función incluye logging detallado que puedes monitorear a través de:

- **Application Insights** (configurado en `host.json`)
- **Azure Functions Logs**
- **Console output** durante desarrollo local

## 🛡️ Manejo de errores

La función incluye manejo robusto de errores:

- **Timeout de requests**: 60-120 segundos para API calls
- **Reintentos automáticos**: Azure Functions maneja reintentos de mensajes fallidos
- **Estados de fallo**: Marca solicitudes como "failed" en caso de error
- **Logging de errores**: Registra todos los errores para debugging

## 🔒 Seguridad

- **Variables de entorno**: Credenciales almacenadas de forma segura
- **Connection strings**: No expuestas en el código
- **HTTPS**: Todas las comunicaciones utilizan HTTPS

## 📈 Escalabilidad

- **Serverless**: Escala automáticamente basado en la carga de la cola
- **Procesamiento paralelo**: Puede procesar múltiples solicitudes simultáneamente
- **Límites configurables**: Azure Functions maneja los límites de concurrencia

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto es parte de un trabajo académico para Sistemas Expertos II PAC 2025.

## 📝 Ejemplo de Uso Completo

## 📌 Notas Adicionales

- **Tipos de Pokémon soportados**: Todos los tipos disponibles en PokéAPI
- **Límite de muestra**: Hasta el total de Pokémon disponibles por tipo
- **Tiempo de procesamiento**: Varía según el tamaño de muestra (aprox. 2-3 seg por Pokémon)
- **Formato de salida**: CSV con encoding UTF-8
- **Retención de archivos**: Los CSVs permanecen disponibles según la configuración de Azure Blob Storage

---

⚡ **PokeQueue Function** - Procesamiento eficiente de datos Pokémon en la nube
