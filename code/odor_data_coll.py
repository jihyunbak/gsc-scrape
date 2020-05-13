# odor_data_coll.py
# 2019-2020 Ji Hyun Bak

from bs4 import BeautifulSoup
import csv

from .utils_webscraper import simple_get
from . import utils

TARGET_URL = None

class OdorDataCollector:
    ''' code for web-scraping from the GSC website '''
    
    def __init__(self, target_url=TARGET_URL, list_num=None, out_dir='', file_prefix='', talkative=True):
        # input
        if target_url is None:
            raise ValueError('target_url is required.')
        if list_num is None:
            raise ValueError('list_num is required.')
        self.target_url = target_url
        self.num = list_num # database list number
        
        # output
        self.out_dir = out_dir
        utils.make_dir(self.out_dir)
        self.file_prefix = file_prefix
    
        self.talkative = talkative
    
    def get_odor_info_from_list(self, list_only=False, test_run=False):
        """
        retrieve odor information from all molecules in each list 
        """
        # get the list of URLs
        # (always set full_list to False when using it to retrieve individual entries)
        all_mol_address = self.get_list_db(full_list=False, use_existing_file=True)
        if list_only:
            return
            
        if self.talkative:
            print('running through all {} molecules in the list ...'.format(len(all_mol_address)))
        
        # create output directory
        listdir = self.out_dir + 'list%d/' % self.num
        utils.make_dir(listdir)

        # loop over list
        for idx in range(0,len(all_mol_address)):
            # retrieve odor information from the specified entry 
            toc = self.get_odor_info_single_mol(all_mol_address, idx, listdir)
            if test_run:
                if self.talkative:
                    print('stopped by test_run option')
                break # for developing
            # wait for a while before making the next request (not to overload server)
            utils.wait(toc*5)

    def get_list_db(self, use_existing_file=True, full_list=False):
        """
        retrieves product list from the GSC website
        creates a csv file
        """
        file_postfix = '_full' if full_list else ''
        csvfilename = self._make_dbfilename(file_postfix=file_postfix)
        
        if utils.isfile(csvfilename) and use_existing_file:
            if self.talkative:
                print('file already exists: ' + csvfilename)
            return utils.read_csv(csvfilename)
        
        # retrieve list from website
        all_mol_address, header = self._retrieve_mol_list(additional_info=full_list)
        if all_mol_address is None:
            return None # could not find website
        
        # write to a csv file
        self._write_list_to_csv(csvfilename, all_mol_address, header=header)
        if self.talkative:
            print('file saved to: ' + csvfilename)
        
        return all_mol_address
        
    def _make_dbfilename(self, file_postfix=''):
        return (self.out_dir + self.file_prefix + 'list%d' + file_postfix + '.csv') % self.num

    def get_odor_info_single_mol(self, all_mol_address, idx, listdir):
        """
        retrieve odor-related information for a single molecule.
        """
        # retrieve page from one molecule
        mol_name = all_mol_address[idx][0]
        if self.talkative:
            print(mol_name)
        mol_url = all_mol_address[idx][1]
        mol_code = utils.search_string_between(mol_url, self.target_url + 'data/', '.html')
        
        # set up output file name
        outfilename = listdir + 'list%d_mol%d_%s.txt' % (self.num, idx, mol_code)
        if utils.isfile(outfilename):
            print('list file already exists:' + outfilename)
            return 0

        # get website content
        _, tic = utils.timer()
        mol_html = simple_get(mol_url)
        toc, _ = utils.timer(tic)
        if self.talkative:
            print('time for webpage retrieval: ' + str(toc))
        
        # parse and find section heading "Organoleptic properties"
        mol_soup = BeautifulSoup(mol_html, 'html.parser')
        for sec in mol_soup.find_all(attrs={"class": "sectionclass"}):
            if(sec.text[0:6]=='Organo'):
                break
        tab_organo = sec.find_next_sibling('table') # we want the following table
        
        # write to file
        self._write_odor_info_to_file(outfilename, tab_organo, mol_name, mol_code)
        
        return toc

    def _retrieve_mol_list(self, additional_info=True):
        ''' written for a specific target website format '''
        
        # locate target webpage url
        url_list = self.target_url + 'allproc-%d.html' % self.num
        
        # retrieve webpage content
        raw_html = simple_get(url_list) 
        if raw_html is None:
            # website not found
            return None, None
        
        # parse html content
        soup = BeautifulSoup(raw_html, 'html.parser') 
        if self.talkative:
            print(soup.title.text) # check content
        
        if additional_info:
            # retrieve more information (4/17/2019)
            cnt = -1 # so that first data row counts as 0
            mylist = []
            for row in soup.table.find_all('tr'): # the tr's
                myrow1 = self._read_row_html(row)
                if myrow1: # if not empty
                    myrow2 = [self.num, cnt] + myrow1
                    mylist.append(myrow2)
                    cnt = cnt + 1 # increment after writing!
            all_mol_address = mylist[1:-1] # skip first (header) & last rows (disclaimer)
            header = ['ListIdx','MolIdx','CAS','Prefix','Name','URL','MoreInfo']
            return all_mol_address, header
        
        # extract link and molecule name only (early version)
        all_mol_address = [];
        for link in soup.table.find_all('a'):
            click_action = link.get('onclick')
            mol_name = link.text
            mol_url = utils.search_string_between(click_action, "openMainWindow\(\'", "\'\);")
            all_mol_address.append([mol_name, mol_url])
        header = ["MoleculeName", "MolURL"]
        return all_mol_address, header

    def _read_row_html(self, row):
        '''
        retreives all information from each row in list html
        '''
        myrow = []
        for dat in row.find_all('td'):
            mycol = []
            if not dat.find_all('a'): # CAS number
                myprefix = []
            else:
                myprefix = ['']
            more_text = []
            for item in dat.children:
                # print(item)
                if type(item) is type(dat): # if a tag
                    if item.name=='a':
                        link = item
                        click_action = link.get('onclick')
                        mol_name = link.text
                        mol_url = utils.search_string_between(click_action, "openMainWindow\(\'", "\'\);")
                        mycol.append(mol_name)
                        mycol.append(mol_url)
                    elif item.name=='div':
                        myprefix = [item.text]
                else:
                    sn = item
                    sn_clean = sn.replace('\r', '').replace('\n', '') # remove newlines
                    more_text.append(sn_clean)
            mycol.append('; '.join(more_text)) # make a single string
            myrow = myrow + myprefix + mycol # concatenate
        return myrow

    def _write_list_to_csv(self, csvfilename, content_list, header=None, quoting=csv.QUOTE_NONNUMERIC):
        # write in a csv file
        with open(csvfilename, 'w', newline='') as f:
            writer = csv.writer(f, quoting=quoting)
            if header is not None:
                writer.writerow(header)
            writer.writerows(content_list)

    def _write_odor_info_to_file(self, outfilename, tab_organo, mol_name, mol_code):
        # -- header
        ft = open(outfilename,'w')
        ft.write(mol_name + '\n')
        ft.write(mol_code + '\n')
        ft.write('\n')
        
        # -- odor information
        for mytd in tab_organo.find_all('td'): #, class_=['qinfr2','radw5']):
            if(mytd.text[0:4]=='Odor'):
                if(mytd.attrs.get('class')==['demstrafrm']):
                    break # other-source block starts
                ft.write('====================\n')
                row = mytd.contents
                for item in row:
                    if type(item) is type(mytd):
                        ft.write(item.get_text(strip=True, separator='\n'))
                        ft.write('\n')
                    else:
                        ft.write(item + '\n')
            if mytd.find_all('a'):
                for odortag in mytd.find_all('a'):
                    taglink = odortag.attrs.get('href')
                    result = utils.search_string_between(taglink, self.target_url + 'odor/', '.html', extract_pattern=False)
                    if result is None:
                        pass # not an odor tag
                    else:
                        ft.write('>> ' + result.group(1) + '\n')
        
        ft.close()
        if self.talkative:
            print('Saved to: ' + outfilename)
