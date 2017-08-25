import cx_Oracle
import inspect
import paramiko
import dateutil.parser
import pkg_resources
import oscarlib.utils
import datetime

TEMPLATE_DIR=DATA_PATH = pkg_resources.resource_filename('oscarlib.rms','rms_templates')
STATUS_LABELS={'W':'Draft','C':'Closed','A':'Approved'}


class Object(object):
    pass


class RmsClientException(Exception):
    def __init__(self, message):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        super().__init__('method : ' + calframe[1][3] + ' : ' + message)


class RmsBddClient(cx_Oracle.Connection):
    def __init__(self, db_connection_string):
        self.db_connection_string =  db_connection_string
        super().__init__(db_connection_string)

    # self.rms_host = rms_host
    # self.rms_passwd = rms_passwd
    # self.igr_host = igr_host
    # self.igr_passwd = igr_passwd
    # self.rms_port = rms_port
    # self.igr_port = igr_port

    def set_job_status(self, job_name, status):
        status_list = ('started', 'aborted', 'aborted in init', 'aborted in process', 'aborted in final', 'completed',
                       'ready for start')
        if status not in status_list:
            raise RmsClientException(
                "Status should be started, aborted, aborted in init, aborted in final, completed or ready for start")

        sql = "UPDATE RESTART_PROGRAM_STATUS SET PROGRAM_STATUS = \'" + status + "\' WHERE PROGRAM_NAME = \'" + job_name + "\'"

        cursor = self.cursor()
        cursor.execute(sql)
        cursor.close()
        self.commit()

        return cursor

    def set_job_restart(self, job_name):
        return self.set_job_status(job_name, 'ready for start')

    def retopper_pdt(self, orin_code):
        pass

    def gen_order_rcpt(self, v_order_no):
        cursor = self.cursor()
        cursor.execute('select count(*) from ordhead where order_no = ' + str(v_order_no))
        for row in cursor:
            nb_cmd = row[0]

        if nb_cmd == 0:
            raise RmsClientException("Command is not in orhead")
        if nb_cmd != 1:
            raise RmsClientException("Duplicate command in database")

        cursor.callproc('RECEIVE_COMMAND', [v_order_no])
        cursor.close()

        return cursor

    def recv_order(self, order):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.load_system_host_keys()
        ssh_client.connect('128.239.236.195', 22, 'oretail', 'oretail')

    def sales_by_family_and_country(self, v_date):

        if type(v_date).__name__ == 'str':
            s_frmt_date = dateutil.parser.parse(v_date).strftime('%m%dùy')

        s_sql = """select sl.SALES_DATE, (case 
			when substr(item,1,2)= 11 then 'ENFANT'
			when substr(item,1,2)= 12 then 'HOMME'
			when substr(item,1,2)= 13 then 'BEBE'
			when substr(item,1,2)= 14 then 'FEMME'
			ELSE 'ERROR'
			end) as Rayon
			, substr(store_name,1,2), sum(sl.SALES_QTY) from au_storesales sl
			inner join store st on st.store=sl.store
			where sl.SALES_DATE > to_date('08/08/2016','dd/mm/yyyy')
			group by sl.sales_date, substr(item,1,2), substr(store_name,1,2)
			order by 1,2,3 desc"""

        cursor = self.cursor()
        cursor.execute(s_sql)

        return cursor

    def receive_last_days(self,nb_days):
        with open (TEMPLATE_DIR+'\\'+'temp.sql') as f:
            s_template = " ".join(f.readlines()).replace('\n',' ')

        s_sql  = oscarlib.utils.render_template(s_template,{'NB_DAYS':str(nb_days)})

        print(s_sql)

        cursor = self.cursor()
        cursor.execute(s_sql)
        return cursor

class RmsClient(RmsBddClient, paramiko.SSHClient):
    def __init__(self,db_connection_string,weblogic_server,weblogic_user,weblogic_password,weblogic_port=22):
        RmsBddClient.__init__(self,db_connection_string)
        paramiko.SSHClient.__init__(self)
        self.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.load_system_host_keys()
        self.weblogic_server = weblogic_server
        self.weblogic_user = weblogic_user
        self.weblogic_password = weblogic_password
        self.weblogic_port = weblogic_port


    def init_alloc(self,ref_code,store_id,delivery_date,quantity):
        alloc = RmsAllocation(self.db_connection_string, ref_code,store_id,delivery_date,quantity)
        alloc.initialize()
        return alloc

    def validate_alloc(self):
        paramiko.SSHClient.connect(self,self.weblogic_server, username=self.weblogic_user, password=self.weblogic_password, port=self.weblogic_port)
        stdin, stdout, stderr = self.exec_command('export ALC_EXEC_DIR=/product/WEBLOGIC/user_projects/domains/retail_domain/alloc13/calc;$ALC_EXEC_DIR/au_validate_alc_stg.sh')

        cursor = self.cursor()

    def calculate_alloc(self):
        self.connect(self.weblogic_server, username=self.weblogic_user, password=self.weblogic_password, port=self.weblogic_port)
        stdin, stdout, stderr =  self.exec_command('export ALC_EXEC_DIR=/product/WEBLOGIC/user_projects/domains/retail_domain/alloc13/calc;$ALC_EXEC_DIR/au_create_alc_stg.sh')
        print(stdout.readlines())
        print(stderr.readlines())

class RmsArticle:
    def __init__(self, orin, connection_string):
        self.connection_string = connection_string
        self.orin = str(orin)

        # self.get_attributes()

    def get_attributes(self):
        rms_client = RmsBddClient(self.connection_string)
        sql = 'select m.*, r.rsip, d.diff_desc from item_master m left join v_item_rsip r on m.item=r.item left join diff_ids d on d.diff_id =m.diff_1 where m.item='+self.orin
        cursor = rms_client.cursor()

        cursor.execute(sql)
        infos = cursor.fetchone()

        if not infos:
            raise RmsClientException("Article not found in database")

        self.item_type=infos[1]
        self.item_parent=infos[4]
        self.item_grandparent = infos[5]

        self.module=infos[18]
        self.sous_rayon=infos[19]
        self.famille = infos[20]

        self.status=STATUS_LABELS[infos[21]]
        self.description=infos[24]
        self.long_description = infos[25]

        if self.item_grandparent:
            self.type="EAN"
        elif self.item_parent:
            self.type="TCO"
        else:
            self.type="REF"

        self.is_package = True if str(self.orin).startswith('10') else False
        self.rsip = infos[-2]
        self.color = infos[-1]
        cursor.close()

        if self.is_package:
            cursor = rms_client.cursor()
            cursor.execute('select item from packitem where pack_no='+str(self.orin))
            self.package_orins =  [ elem[0] for  elem in cursor.fetchall()]
            self.package_content = [ RmsArticle(elem,self.connection_string) for  elem in self.package_orins]
            cursor.close()


class RmsAllocation(object):
    def __init__(self,connection_string,ref_code,store_id,delivery_date,quantity):
        self.ref_code = ref_code
        self.store_id = store_id
        self.delivery_date = delivery_date
        self.quantity = quantity
        self.connection_string = connection_string

        art = RmsArticle(ref_code,connection_string)
        art.get_attributes()

        if art.type != 'TCO' and not art.is_package:
            raise RmsClientException('Article cannot be allocated, it should be a TCO or Package')

    def initialize(self):
        rms_client = RmsBddClient(self.connection_string)
        cursor = rms_client.cursor()
        val = 0
        load_id = cursor.callfunc('init_alloc',val,[self.ref_code,self.store_id,self.delivery_date,self.quantity])
        self.load_id = load_id
        return load_id

    def validate(self,weblogic_server,username,password,port=22):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(weblogic_server, username=username, password=password, port=port)

        stdin, stdout, stderr, = ssh_client.exec_command('export ALC_EXEC_DIR=/product/WEBLOGIC/user_projects/domains/retail_domain/alloc13/calc;$ALC_EXEC_DIR/au_validate_alc_stg.sh')

    def calculate(self, weblogic_server, username, password, port=22):
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(weblogic_server, username=username, password=password, port=port)

        ssh_client.exec_command('export ALC_EXEC_DIR=/product/WEBLOGIC/user_projects/domains/retail_domain/alloc13/calc;$ALC_EXEC_DIR/au_create_alc_stg.sh')

    def get_stage_status(self):
        if not self.load_id:
            return None

        rms_client = RmsBddClient(self.connection_string)
        cursor = rms_client.cursor()

        cursor.execute('select status from au_alloc_stage where load_id=') + str(self.load_id)

        return cursor.fetchone()[0]



