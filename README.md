# Backend - Treasury Research API

API REST construida con FastAPI para búsquedas de contenido de tesorería a nivel mundial.

## 🚀 Inicio Rápido

1. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno:**
   ```bash
   cp env.example.txt .env
   # Editar .env con tus credenciales
   ```

3. **Iniciar servidor:**
   ```bash
   python api.py
   # O
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Documentación API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 Endpoints

### POST /api/search
Inicia una nueva búsqueda de tesorería.

**Request Body:**
```json
{
  "query": "treasury management",
  "max_results": 100,
  "sources": ["pubmed", "arxiv"],
  "date_from": "2020-01-01",
  "date_to": "2024-12-31",
  "language": "en",
  "use_ai_enhancement": true
}
```

**Response:**
```json
{
  "search_id": "uuid-string",
  "status": "processing",
  "message": "Search started with ID: uuid-string"
}
```

### GET /api/search/{search_id}/status
Obtiene el estado de una búsqueda.

### GET /api/search/{search_id}/results
Obtiene los resultados de una búsqueda (con paginación).

### GET /api/searches
Lista las búsquedas recientes.

### DELETE /api/search/{search_id}
Elimina una búsqueda y sus resultados.

## 🔧 Configuración

### Variables de Entorno Requeridas

- `NCBI_API_KEY`: API key de NCBI para PubMed
- `NCBI_EMAIL`: Email para PubMed
- `GEMINI_API_KEY`: API key de Google Gemini (opcional, para IA)
- `FIREBASE_SERVICE_ACCOUNT_PATH`: Ruta al archivo JSON de Firebase
- `FIREBASE_SERVICE_ACCOUNT_JSON`: JSON de Firebase como string (alternativa)

## 📦 Módulos

- **api.py**: API principal FastAPI
- **scraper_treasury.py**: Scraper multi-fuente (PubMed, arXiv, etc.)
- **gemini_treasury_analyzer.py**: Analizador IA con Gemini
- **firebase_service.py**: Servicio para Firestore

## 🐛 Troubleshooting

Ver el README principal para solución de problemas comunes.
