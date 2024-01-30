# GTool

GTool es una herramienta de búsqueda para Google y DuckDuckGo, que permite personalizar tus consultas y filtrar los resultados según tus necesidades.

## Configuración DuckDuckGo
DuckDuckGo es un navegador que se centra en la privacidad, por ello, no usa cookies y funciona
directamente sin configurar nada.  

**NOTA**: DDG tiene desactivado el filtrado por rango de fechas (--range), no funciona

## Configuración Google

Para poder hacer uso de la herramienta es necesario exportar dos variables de entorno que contienen dos cookies obligatorias de Google:

-  COOKIE_AEC: Garantizar que las solicitudes dentro de una sesión de navegación son realizadas por el usuario y no por otros sitios - 6 meses
-  COOKIE_SCOS: Se utiliza para almacenar el estado de un usuario con respecto a sus elecciones de cookies - 13 meses

```bash
COOKIE_AEC="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
COOKIE_SCOS="SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"
```
Mediante el uso del argumento `--rotate` se podrán crear distintos enviroments (.env) y almacenarlos en la carpeta `./profiles` (en la ruta actual del usuario), de este modo la herramienta cogerá en cada ejecución un enviroment aleatorio y con ello un set de cookies diferente, reduciendo las probabilidades de captcha. 

![imagen](https://github.com/XAI-disinfodemics/gtool/assets/35236167/fba4b984-53b9-42f0-9a29-63617612b2a6)

### ¿Cómo obtener las cookies?

Para obtener ambas cookies basta con ir al navegador y realizar una búsqueda sobre Google, analizar el tráfico (inspeccionar elemento > Network > petición ?search...) y extraer de ahí las cookies. 

Una forma más cómoda es la siguiente:
1. Descargar la extensión de Chrome `Cookie-editor` (https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm).
2. Habilitar en incognito
3. Realizar una búsqueda en Google y **rechazar cookies**
4. Abrir la extensión y copiar la información de la cookie **AEC** y **SCOS**
5. Repetir los pasos 2-4 para cada .env que se quiera añadir en la carpeta `./profiles`

<img src="https://github.com/XAI-disinfodemics/gtool/assets/35236167/bba88353-0ffd-4536-a8d4-756b72ae188b" width="50%" height="50%">

## Uso

La línea de comando general para usar GTool es:

```bash
usage: run.py [-h] [-L LEVEL] [-p] [-mp PAGES] [-v] -q QUERY -f FILE {DuckDuckGo,Google} ...

```

## Argumentos

### Argumentos Opcionales

-   `-h, --help` : Muestra el mensaje de ayuda y termina.

#### Argumentos Generales Opcionales

-   `-L LEVEL, --loglevel LEVEL` : Define el nivel de log (por defecto: WARNING). Ejemplos: \["INFO", "DEBUG", "WARNING", "ERROR"\].
    
-   `-p, --proxies` : Permite el uso de proxy. Se requiere la variable de entorno "PROXY\_URL".
    

-   `-v, --verbose` : Si se establece, devuelve un JSON con más información (como la página y la posición de la URL).

-   `-mp PAGES, --max_pages PAGES` : El número máximo de páginas de resultados de búsqueda a recorrer. El valor predeterminado es 3.

### Argumentos obligatorios

-   `-q QUERY, --query QUERY` : Consulta a buscar.
    
-   `-f FILE, --filename FILE` : Nombre del archivo de resultados donde se almacenarán todos los resultados.
    
### DuckDuckGo - Argumentos opcionales de filtrado

-   `--time {h,d,w,m,y}` : Especifica el filtro de tiempo. Las opciones son "h" para la última hora, "d" para el último día, "w" para la última semana, "m" para el último mes, "y" para el último año.

-   `--range RANGE` : Especifica el filtro de rango de fechas en el formato 'DD/MM/YYYY - DD/MM/YYYY'. Puedes ignorar el inicio y el final usando el comodín '#' (For example: '# - DD/MM/YYYY' or 'DD/MM/YYYY - #')(default: None)

-    `--lang {au-en,es-es,wt-wt,ar-es,at-de,be-fr,be-nl,br-pt,bg-bg,ca-en,ca-fr,ct-ca,cl-es,cn-zh,co-es,hr-hr,cz-cs,dk-da,ee-et,fi-fi,fr-fr,de-de,gr-el,hk-tzh,hu-hu,is-is,in-en,id-en,ie-en,il-en,it-it,jp-jp,kr-kr,lv-lv,lt-lt,my-en,mx-es,nl-nl,nz-en,no-no,pk-en,pe-es,ph-en,pl-pl,pt-pt,ro-ro,ru-ru,xa-ar,sg-en,sk-sk,sl-sl,za-en,es-ca,se-sv,ch-de,ch-fr,tw-tzh,th-en,tr-tr,us-en,us-es,ua-uk,uk-en,vn-en}` : Forzar a DuckDuckgo a devolver resultados sólo en un idioma específico.
  
### Google - Argumentos opcionales de filtrado

-   `-r, --rotate` : Si se establece, seleccionará aleatoriamente un archivo `.env*` del directorio `./profiles` (en la ruta del usuario). En este directorio, el usuario puede añadir múltiples archivos `.env` (con las variables de entorno AEC/SCOS/PROXY_URL) en diferentes configuraciones.
  
-   `--time {h,d,w,m,y}` : Especifica el filtro de tiempo. Las opciones son "h" para la última hora, "d" para el último día, "w" para la última semana, "m" para el último mes, "y" para el último año.

-   `--range RANGE` : Especifica el filtro de rango de fechas en el formato 'DD/MM/YYYY - DD/MM/YYYY'. Puedes ignorar el inicio y el final usando el comodín '#' (For example: '# - DD/MM/YYYY' or 'DD/MM/YYYY - #')(default: None)
    
-   `--sort` : Si se establece, ordena los resultados por fecha, mostrando los resultados más recientes primero.

-    `--lang {af,ar,hy,be,bg,ca,zh-CN,zh-TW,hr,cs,da,nl,en,eo,et,tl,fi,fr,de,el,iw,hi,hu,is,id,it,ja,ko,lv,lt,no,fa,pl,pt,ro,ru,sr,sk,sl,es,sw,sv,th,tr,uk,vi}` : Forzar a Google a devolver resultados sólo en un idioma específico (Sólo acepta algunos códigos del RFC 5646). No funciona bien, las primeras páginas (1-2) siempre contiene sitios en el idioma de su ubicación.
