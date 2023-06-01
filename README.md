# GTool

GTool es una herramienta de búsqueda en Google, que permite personalizar tus consultas y filtrar los resultados según tus necesidades.

## Uso

La línea de comando general para usar GTool es:

```bash
gtool [-h] [-L LEVEL] [-p] -q QUERY -f FILE [--time {h,d,w,m,y}] [--sort] [-mp PAGES]
```

## Argumentos

### Argumentos Opcionales

-   `-h, --help` : Muestra el mensaje de ayuda y termina.

#### Argumentos Generales Opcionales

-   `-L LEVEL, --loglevel LEVEL` : Define el nivel de log (por defecto: WARNING). Ejemplos: \["INFO", "DEBUG", "WARNING", "ERROR"\].
    
-   `-p, --proxies` : Permite el uso de proxy. Se requiere la variable de entorno "PROXY\_URL".
    
- `-r, --rotate` : Si se establece, seleccionará aleatoriamente un archivo `.env*` del directorio `./profiles` (en la ruta del usuario). En este directorio, el usuario puede añadir múltiples archivos `.env` (con las variables de entorno AEC/SCOS/PROXY_URL) en diferentes configuraciones.


### Argumentos obligatorios

-   `-q QUERY, --query QUERY` : Consulta a buscar.
    
-   `-f FILE, --filename FILE` : Nombre del archivo de resultados donde se almacenarán todos los resultados.
    

### Argumentos opcionales de filtrado

-   `--time {h,d,w,m,y}` : Especifica el filtro de tiempo. Las opciones son "h" para la última hora, "d" para el último día, "w" para la última semana, "m" para el último mes, "y" para el último año.
    
-   `--sort` : Si se establece, ordena los resultados por fecha, mostrando los resultados más recientes primero.
    
-   `-mp PAGES, --max_pages PAGES` : El número máximo de páginas de resultados de búsqueda para rastrear. El valor predeterminado es 3.