# -*- coding: utf-8 -*-
"""
Created on Wed Nov 30 22:00:48 2016

@author: lechuza
"""
import psycopg2

#we export all the tables of the flights database to csv files, then import each of them into a Cassandra schema
conn = psycopg2.connect(database="flights", user="postgres", password="persyy",host='/var/run/postgresql/')

cur=conn.cursor()

cur.execute("Select table_name from information_schema.tables where table_schema='public';")

for table in cur:
    print(table)

tupy=cur.fetchall() #elements are tuples

#copy each of the tables to a csv on my local
for elem in tupy:
    #insert into this loop a cur.execute() that takes this python element as an argument... additionally, will be writing these tables to file via cur.copy_to()...
    base='/home/lechuza/Documents/CUNY/data_class/project4/'
    file=base+elem[0]+'.csv'
    f=open(file,'w')
    cur.copy_to(f,elem[0],sep=",")
                

#retrieve all metadata from information_schema on each of the tables to aid in the table creation within Cassandra
dicy={}
for elem in tupy:
    #compile the select statement
    base="select table_name,column_name,data_type from information_schema.columns where table_schema='public' and table_name = '%s';" %(elem[0])
    cur.execute(base)
    dicy[elem[0]]=cur.fetchall()

#close up... finished with postgres
cur.close()
conn.close()

#open connection to Cassandra
from cassandra.cluster import Cluster
from cassandra import policies

cluster = Cluster(contact_points=['127.0.0.1'],
                  load_balancing_policy=policies.TokenAwarePolicy(policies.DCAwareRoundRobinPolicy(local_dc='datacenter1')),
                  default_retry_policy=policies.RetryPolicy()) 

session=cluster.connect()
#in order to create the tables prior to importing the data from the csv, I need to map the column data types as defined by postgres to those defined in Cassandra

#look through the dictionary of table information and create an array from only the datatype portions of the dictionary
mylist=[]
for k,v in dicy.items():
    #each value of the k,v is an array of tuples... 
    for elem in v:
        #index the third element of the tuple
        mylist.append(elem[2])
print(mylist[0:5])
uniques=list(set(mylist))

#sort the list for the sake of reliability when writing the associations of Cassandra data types
uniques.sort()
print(uniques)

#we have four elements in this list of unique postgres datatypes, we map them in a dictionary... this dictionary will be referenced to build the 'create table' syntax within Cassandra
cas_dtypes={}
cas_dtypes[uniques[0]]='text'
cas_dtypes[uniques[1]]='text'
cas_dtypes[uniques[2]]='double'
cas_dtypes[uniques[3]]='int'

#create keyspace, aka schema
session.execute("create keyspace IF NOT EXISTS flights with replication = {'class':'SimpleStrategy','replication_factor':1}")

session.execute('use flights')
#goal: create one dictionary per table having key-value pairs = column_name:datatype... will use this list of columns names for the COPY FROM statement, but need to ensure that columns are in the same order as the csv
colnames={}
for k,v in dicy.items():
    lis=[]
    for tables in v:
        lis.append(tables[1])
    colnames[k]=lis
    
for k,v in dicy.items():
    dic={}
    for elem in v: #elem = ea. column of table
        dic[elem[1]]=cas_dtypes[elem[2]]
    #after filling the dictionary, create a list that we later unlist to build the string
    table_list=[]    
    for key,val in dic.items():
        table_list.append(key+' '+val)
    columns=', '.join(table_list)
    #introduce string formatting
    statement="create table IF NOT EXISTS flights.%(tablename)s(uid uuid,%(cols)s,PRIMARY KEY(uid))" %{'tablename':k,'cols':columns}
    print(statement)
    session.execute(statement)

    
    
#ensure that all tables have been created within 'flights' keyspace (what Cassandra calls schemas)
ty=session.execute("select table_name from system_schema.tables where keyspace_name='flights'")
for elem in ty:
    print(elem)
    
#mine my local directory in search of all files ending in .csv - the name of the file will be the same as the table in Cassandra

import glob, os
import uuid
import pandas as pd
import numpy as np

base='/home/lechuza/Documents/CUNY/data_class/project4/'
s=','
dic_full_files={}
#create a data container for each of the csv, and create the appropriate 'INSERT' statement associated with that table and the column names, but don't execute the 'INSERT' yet
for file in os.listdir(base):
    if file.endswith(".csv"):
        #'file' = a string
        full=base+file #csv
        newf=file.replace('.csv','') #name of table - only -
        
        flat=s.join(colnames[newf])
        df=pd.read_csv(full,header=None) #dic of pd.df
        quest='?,'*(len(colnames[newf])+1)
        quest=quest[:-1]
        statement="INSERT INTO %(table_name)s (uid, %(lists)s) VALUES(%(quest)s)" % {'table_name':newf,'lists':flat,'quest':quest}
        lis=[]
#prepare the statement once
        lis.append(statement)
        lis.append(df)
        dic_full_files[newf]=lis

#dataframe apply function: this 'apply' function is applied to each row of the dataframe: it prepares a new container for the data in the row then executes the 'INSERT' statement that writes it to the appropriate table in the keyspace
def rowInsert(g,prep_st):
    uid=uuid.uuid4()
    #gf=[x for x in g.iloc[1,:].values] #row data
    gf=[x for x in g] #row data
    gf.insert(0,uid) #content
    #print(gf)
    session.execute(prep_st,gf) #prepare 'prep_st' only once

#this final loop iterates through the dictionary created above that stores the appropriate 'INSERT' statement as well as the raw data of each table. Lastly, it calls the above defined function. Notice that the insert statement is first prepared, then later executed. Prepared statements are prepared only once and executed many times.
for k,v in dic_full_files.items():
    prep_stat=session.prepare(v[0]) #1st element is prep. statement
    df=v[1]
    df.apply(rowInsert,args=(prep_stat,),axis=1)