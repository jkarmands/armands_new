from urllib.request import urlopen
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from urllib.parse import parse_qs
import mysql.connector
import requests
import ftplib
import os
#Izveidojam savienojumu ar Datu Bāzi
cnx = mysql.connector.connect(user='kamlv_onlinestock', password='av160377mnt22',
                              host='server1.firsthost.lv',
                              database='kamlv_online_stock')
cursor = cnx.cursor()

#cursor.execute("delete from monte_products where productID>0") 
#cursor.execute("delete from monte_prices where pid>0") 
#exit()

#Izveidojam savienojumu ar FTP lai ielādētu bildes
ftp= ftplib.FTP('www.online-stock.lv')
ftp.login('onlinestock@online-stock.lv', 'av160377mnt22')

# Links kuru ķidāsim
html = urlopen("http://euroshops.lv/index.php?route=product/category&path=59_860825302&limit=50")

# Norādam ko mēs īsi meklējam pēc tegiem
bsObj = BeautifulSoup(html)
recordList = bsObj.findAll("div", {"class": "product-layout product-list col-xs-12"})

# Taisam sarakstu
for record in recordList:
     #Paņemam datus
     title = record.find("h4").get_text().strip()
     price = record.find("p", {"class": "price"}).get_text().strip()
     bilde = record.find('img').attrs['src']
     links = record.find('a').attrs['href']
    
     #Paķidājam linku lai dabūtu ārā kategoriju un preces ID ar perseri
     product_url = record.find('a').attrs['href']
     parsed = urlparse(product_url)

     #No linka izvelkam precesid
     qs = parse_qs(parsed.query)['product_id'][0]

     #No linka izvelkam kategoriju
     qc = parse_qs(parsed.query)['path'][0]     
     res = qc.partition('_')[2]

     #Dabjam bildes nosaukumu priekš DB
     b = bilde.partition('http://euroshops.lv/image/cache/catalog/')[2]
     

     #Pārbaudam vai prece ar šādu ID ir datu bāze
     cursor.execute("select * from monte_products where productID='{}'".format(qs))   
     row = cursor.fetchone()
     if row == None:
          #jA NAV PRECES AR ŠĀDU ID taisam jaunu preci
          cursor.execute("insert into monte_products (productID, categoryID, name_lv, picture1) VALUES ('{}','{}','{}','{}')".format(qs,res,title,b))

          #Liekam Cenu attiecīgajai precei jo db cnas ir citā tabulā
          cursor.execute("insert into monte_prices (pid, price, enabled, stock) VALUES ('{}','{}','1','10')".format(qs,price.split('€')[0]))
          
          #Lādējam bildi lielo un mazo (viņas gan ir vienādas)
          url = bilde
          r = requests.get(url, allow_redirects=True)
          open(b, 'wb').write(r.content)
          
          ftp.cwd('/pictures/thumb/')
          uploadfile= open(b, 'rb')
          ftp.storbinary('STOR ' + b, uploadfile)
          ftp.cwd('/pictures/big/')
          uploadfile= open(b, 'rb')
          ftp.storbinary('STOR ' + b, uploadfile)
          uploadfile.close()
          #izdzēšam lokālo bildi
          os.remove(b)
          print("Prece Ielādēta: " + title)    
     else:  
          #ja IR prece ar šādu ID katram gadījumam updatojam Cenu
          cursor.execute("update monte_prices set price='{}' where pid='{}'".format(price.split('€')[0], qs))  
          print("Cena atjaunota: " + title)
print ("Finito")