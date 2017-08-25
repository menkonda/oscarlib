from oscarlib.rms import RmsClient, RmsArticle
import paramiko
import datetime
from oscarlib.utils import *
import pkg_resources

rms_connection_string  = "rms13/rms13@RETAIL_rms13"
weblogic_server = 'lnxql99v2030.qualif.fr.auchan.com'

########

client = RmsClient(rms_connection_string,weblogic_server,'oretail','oretail')
client.init_alloc(100021516,2017,datetime.datetime.now(),10)


client.validate_alloc()
client.calculate_alloc()





