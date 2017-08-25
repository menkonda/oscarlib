import cx_Oracle
import inspect

class Object(object):
    pass


class IgrClientException(Exception):
    def __init__(self, message):
        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        super().__init__('method : ' + calframe[1][3] + ' : ' + message)


class IgrClient(cx_Oracle.Connection):
    def __init__(self, connection_string):
        super().__init__(connection_string)

    def get_last_msg_rcv(self):
        sql = 'select * from (select * from s_sri_sas_rin_in order by dat_evt_sri desc) where rownum = 1 '

        cursor = self.cursor()
        cursor.execute(sql)

        if not cursor:
            raise IgrClientException(
                "Status should be started, aborted, aborted in init, aborted in final, completed or ready for start")

        return cursor
