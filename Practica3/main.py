from pysnmp.hlapi import *
import rrdtool
from time import *
import json
import os


class Agente:

    def __init__(self,comunidad:str,host:str):
        self.Comunidad=comunidad
        self.Host=host
        self.Nombre_sistema=self.consultaSNMP("1.3.6.1.2.1.1.1.0")
        self.Num_interfaces=self.consultaSNMP("1.3.6.1.2.1.2.1.0")
        self.Tiempo_Activo=self.consultaSNMP("1.3.6.1.2.1.1.3.0")

        self.InMemorySize=None
        self.hrSystemInitialLoadDevice=None
        self.hrSystemInitialLoadParameters=None
        # Creando carpeta para almacenar la base de datos generadas
        self.path=self.Host+"/"
        self.strBaseRRD=self.path+"Base.rrd"
        self.strBaseXML=self.path+"Base.xml"
        try:
            os.mkdir(self.Host)
        except:
            pass

    

    def update(self,duracion=60,time_step=5):
        filas=duracion/time_step
        self.createRRD(time_step,filas) # creando base de datos 

        inicio=time()
        fin= inicio + duracion# un minuto
        
        while True:
            print(self.consultas())
            inicio=time()
            if not inicio < fin:
                break
        print(rrdtool.lastupdate(self.strBaseRRD))
        

    # def reporte(self):
    #     ultima_lectura=int(rrdtool.last(self.Host+"/"+"miUDP.rrd"))
    #     print(ultima_lectura)
    #     tiempo_final=ultima_lectura
    #     tiempo_inicial=tiempo_final-600

    #     dicc=rrdtool.fetch(self.Host+'/miUDP.rrd',"-s,"+str(tiempo_inicial),"LAST")
    #     Filas=60
    #     datos=dicc[2][Filas-1]
    #     print(dicc)


    def consultas(self)->bool:
        # str_mib="1.3.6.1.2.1"
        # host-resources-mib= str_mib+".25"

        # InMemorySize:1.3.6.1.2.1.25.2.2
        self.InMemorySize = self.consultaSNMP("1.3.6.1.2.1.7.1.0")
        # hrSystemInitialLoadDevice:1.3.6.1.2.1.25.1.3
        self.hrSystemInitialLoadDevice= self.consultaSNMP("1.3.6.1.2.1.7.2.0")
        # hrSystemInitialLoadParameters:1.3.6.1.2.1.25.1.4
        self.hrSystemInitialLoadParameters = self.consultaSNMP("1.3.6.1.2.1.7.3.0")

        # hrStorageTable:1.3.6.1.2.1.25.2.3
        self.hrStorageTable = self.consultaSNMP("1.3.6.1.2.1.25.3.3.1.2.196608")
        # hrProcessorTable:1.3.6.1.2.1.25.3.3


        rrdtool.update(self.strBaseRRD,"N:" + self.InMemorySize + ":"
                                            + self.hrSystemInitialLoadDevice + ":" 
                                            + self.hrSystemInitialLoadParameters + ":" 
                                            + self.hrStorageTable)
                                            
        rrdtool.dump(self.strBaseRRD ,self.strBaseXML)

        return True

    def consultaSNMP(self,oid:str):
        errorIndication, errorStatus, errorIndex, varBinds = next(
            # hace la solicitud getsnmp
            getCmd(SnmpEngine(),
                CommunityData(self.Comunidad),
                UdpTransportTarget((self.Host, 161)), # udp
                ContextData(),
                ObjectType(ObjectIdentity(oid))))

        # tratamiento de errores
        if errorIndication:
            print(errorIndication)
        elif errorStatus:
            print('%s at %s' % (errorStatus.prettyPrint(),errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
        else:
            for varBind in varBinds:
                varB=(' = '.join([x.prettyPrint() for x in varBind]))
                # print(varB)
                resultado= varB.split()[2] # se agarra la ultima parte de la consulta
        return resultado

    def createRRD(self,tiempo_step:int,numero_filas:int):
        # creamos la bae de datos
        ret = rrdtool.create(self.strBaseRRD,
        # Tiempo en segs y fecha del sistema al momento de iniciar el almacenamiento
                            "--start",'N',
        # Duracion del step en segundos,
        # cada cuantos segundos tomara los datos del buffer y aplicar la funcion que nosotros queremos
                            "--step",str(tiempo_step),
        # Data Source
        #DS:
            # Nombre de la variable: 
                    # Tipo de dato de la variable: 
                            # segundos que deben de pasar para que el dato sea invalido(siempre igual que el del step): 
                                    # Limite inferior: 
                                            # Limite superior
                            "DS:var1:GAUGE:"+str(tiempo_step)+":0:100",
        # Lo que se va almacenart en cada fila
        #RRA: 
            # Funcion que se le aplicara a los datos contenidos en el buffer (de cada step): 
                    # la mitad de muestras se validan: cada 1 step : 
                            # numero de filas en la base de datos
                            "RRA:AVERAGE:0:1:"+str(numero_filas)) 

        #en caso de haber un error lo sabremos
        if ret:
            print (rrdtool.error())

    def __eq__(self, agente):
        return self.Host==agente.Host

    def __str__(self)->str:
        s1="\n|=============="+self.Host+"================|"
        s2="\nComunidad:",self.Comunidad
        s3="\nHost:",self.Host
        s4="\nNombre del sistema:",self.Nombre_sistema
        s5="\nNumero de interfaces de red:",self.Num_interfaces
        s6="\nTiempo desde el ultimo reinicio:"+self.Tiempo_Activo+"Segs"
        s7="\n"+self.InMemorySize
        s8="\n"+self.hrSystemInitialLoadDevice
        s9="\n"+self.hrSystemInitialLoadParameters
        s10="\n|==========================================|\n"

        return s1+s2+s3+s4+s5+s6+s7+s8+s9+s10