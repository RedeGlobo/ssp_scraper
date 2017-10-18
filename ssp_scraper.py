# coding: utf-8
#!/usr/bin/env python

__author__ = "Rodrigo Esteves e Priscilla Lusie"
__version__ = "1.0"

import logging
import os
import re
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException



class SSP_Scraper:
    """ 
        Classe para download dos arquivos relativos a diversos crimes presentes 
        na página da Secretaria de Segurança Pública de SP (SSP).
        Usa o selenium para selecionar o crime e o período desejado na página do SSP,
        permitindo que o download seja feito ao clicar no botão exportar.
    """
    url = 'http://www.ssp.sp.gov.br/transparenciassp/'
    crime_xpath = '//a[@class="btnNat dynWidth block" or @class="btnNat2 dynWidth block"]'
    year_xpath = '//ul[@class="nav nav-tabs anoNav"]//a[@class="block"]'
    month_xpath = '//ul[@class="nav nav-pills mesNav"]//a[@class="block"]'
    suspiciousDeath_xpath = '//div[@class="col-lg-3 col-md-3 col-sm-3 col-xs-3 nopadd centered"]'+\
                            '//a[@class="btnItem dynWidth block" or @class="btnItem2 dynWidth block"]'

    def __init__(self, download_dir, timeout=900, log=None):
        self.download_dir = download_dir
        self.timeout = timeout
        self.log = log

        self._driver = self.__get_chrome_driver(self.download_dir, self.timeout)
        self._wait = WebDriverWait(self._driver, self.timeout)
        self._driver.get(self.url)

    def __del__(self):
        """ Finaliza o driver utilizado para navegação Web
        """
        self._driver.close()

    @staticmethod
    def __get_chrome_driver(download_dir, timeout):
        """ Inicializa o driver do chrome para a navegação Web na página do SSP de SP.
            Args:
                download_dir (str): diretório para download dos arquivos
                timeout (int): tempo em segundos para que espere a resposta de uma execução do javascript presente na página web
            Returns:
                Uma instância do driver do chrome
        """
        chromeOptions = webdriver.ChromeOptions()
        prefs = {'download.default_directory' : download_dir, 
                 'profile.default_content_setting_values.automatic_downloads': 1}
        chromeOptions.add_experimental_option("prefs",prefs)
        #chromeOptions.add_argument("--dns-prefetch-disable")
        #chromeOptions.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=chromeOptions)
        driver.set_script_timeout(timeout)
        driver.set_page_load_timeout(timeout)
        driver.implicitly_wait(timeout)
        return driver

    def __get_crime_elements(self):
        """ Extrai os botões válidos de crimes a serem explorados. 
            Note:
                A página deve ter sido carregada previamente.
            Returns:
                Vetor de crimes cujos dados estão disponíveis para download
        """
        crimes = []
        itens = self._driver.find_elements_by_xpath(self.crime_xpath)
        for i in itens:
            id = i.get_attribute('id')
            if id.find('cphBody_btnTaxaHomicidio') != -1:
                continue
            crimes.append(id)
        return crimes

    def __get_available_periods(self):
        """ Captura os anos e meses disponíveis para o crime selecionado.
        Note:
            Deve ser chamado após o botão relativo ao crime desejado ter sido clicado.
        """
        years = self._driver.find_elements_by_xpath(self.year_xpath)
        months = self._driver.find_elements_by_xpath(self.month_xpath)

        yearsRef = []
        for y in years:
             yearsRef.append(y.get_attribute('id'))
        
        monthsRef = []
        for m in months:
             monthsRef.append(m.get_attribute('id'))
        return yearsRef, monthsRef

    @staticmethod
    def __get_year_from_str(y):
        """ A partir de uma string, extrai o valor numérico relativo ao ano se existir.
            Returns:
                O ano com 4 dígitos ou a própria string se não conseguir encontrar o ano.
        """
        ano = re.search('(\d+)', y)
        if ano:
            ano = ano.group(1)
            if len(ano) == 3:
                ano = '2'+ano
            elif len(ano) == 2:
                ano = '20'+ano
            elif len(ano) == 1:
                ano = '200'+ano
            ano = int(ano)
        else:
            ano = y
        return ano

    def __get_files_from_crime(self, crime_name):
        """ Faz download de todos os arquivos disponíveis para um crime.
            Os arquivos estão disponíveis por mês (mês/ano)
            Note:
                o botão relativo ao crime deve ter sido clicado previamente.
            Args:
                crime_name (str): nome do crime
        """
        years, months = self.__get_available_periods()

        for y in years:
            ano = self.__get_year_from_str(y)
            buttonElement = self._wait.until(EC.visibility_of_element_located((By.ID, y)))
            self._driver.execute_script('arguments[0].click()', buttonElement)

            for m in months[::-1]:
                mes = re.search('(\d+)', m)
                mes = int(mes.group(1)) if mes else m

                processed = self.check_downloaded_file(crime_name, ano, mes)
                if processed:
                    if self.log:
                        self.log.debug('Arquivo já existe: base={} ano={} mes={}'.format(crime_name, ano, mes))
                    #return
                    continue

                buttonElement = self._wait.until(EC.visibility_of_element_located((By.ID, m)))
                self._driver.execute_script('arguments[0].click()', buttonElement)

               # on the IML element of the crime buttons list, the "exportar" has a different id
                if crime_name == 'IML':
                    exportar_id = "cphBody_ExportarIMLButton"
                else:
                    exportar_id = "cphBody_ExportarBOLink"

                try:
                    exportButtonElement = self._driver.find_element_by_id(exportar_id)
                    buttonRef = exportButtonElement.get_attribute('onclick')

                    if self.log:
                        self.log.debug('Salvando base={} ano={} mes={}'.format(crime_name, ano, mes))
                    #self._driver.execute_async_script(buttonRef)
                    self._driver.execute_script(buttonRef)
                except:
                    e = sys.exc_info()
                    if self.log:
                        self.log.error(e)

    def check_downloaded_file(self, crime_name, ano, mes):
        """  Recebe o nome do crime e o período relativo ao arquivo para que seja conferido se o download 
         do arquivo já foi feito ou não.
         Args:
            crime_name (str): nome do crime relativo ao arquivo
            ano (int): ano referente ao arquivo
            mes (int): mês referente ao arquivo
         Returns:
             True se o arquivo já foi processado anteriormente, caso contrário, False.
        """
        return False

    def process_crimes(self):
        """ Processa cada um dos crimes obtidos em get_crime_elements.
            Para cada crime encontrado:
                * seleciona o botão do crime na página Web
                * faz download dos arquivos disponíveis, selecionando o período desejado do arquivo
                  e chamando o javascript presente no botão 'EXPORTAR' presente na página.
        """
        if self.log:
            self.log.debug('A buscar dados')
        crime_elements = self.__get_crime_elements()
        
        if self.log:
            self.log.debug('Encontradas {} ocorrências'.format(len(crime_elements)))
        for crime in crime_elements[::-1]:
            crime_name = re.search('btn(\w+)', crime)
            if crime_name:
                crime_name = crime_name.group(1)
            else:
                crime_name = crime
            crime_name = crime_name.replace('Homicicio', 'Homicidio')

            buttonElement = self._wait.until(EC.visibility_of_element_located((By.ID, crime)))
            self._driver.execute_script('arguments[0].click()', buttonElement)

            if crime_name == 'MorteSuspeita':
                # "Morte suspeita" needs an special treatment, 
                suspiciousDeath = self._driver.find_elements_by_xpath(self.suspiciousDeath_xpath)
                suspiciousDeaths = []
                for s in suspiciousDeath:
                    sType_text = s.get_attribute("text")
                    sType = s.get_attribute("id")
                    suspiciousDeaths.append((sType_text, sType))

                for s in suspiciousDeaths:
                    if self.log:
                        self.log.debug('\n################################\nProcessando ' + crime_name + 
                                       ' - ' +s[0] + '\n################################\n')

                    buttonElement = self._wait.until(EC.visibility_of_element_located((By.ID, s[1])))
                    self._driver.execute_script('arguments[0].click()', buttonElement)

                    self.__get_files_from_crime(crime_name + ' ' + s[0])
            else:
                if self.log:
                    self.log.debug('\n################################\nProcessando ' + 
                                   crime_name + '\n################################\n')

                self.__get_files_from_crime(crime_name)

