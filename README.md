Obtém dados do site http://www.ssp.sp.gov.br/transparenciassp/.

Os arquivos são disponibilizados mensalmente.

# Fluxo:
![alt text](img/SSPDiagram.jpg)

Segue um exemplo de como usar a classe:

```
import os
import sys

download_dir = os.path.join(os.getcwd(), 'Files')
log = logging.getLogger(__name__)
scraper = SSP_Scraper(download_dir=download_dir, log=log)
try:          
    scraper.process_crimes()
except:
    log.error(sys.exc_info())
```

# Dependência:
Baixar navegador google chrome em:
https://www.google.com/chrome/browser/desktop/index.html

Baixar driver do google chrome em:
https://sites.google.com/a/chromium.org/chromedriver/downloads
