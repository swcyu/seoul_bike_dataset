import findspark
findspark.init()

from pyspark import SparkConf, SparkContext 
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import *

import json
import time
import requests
import os

# spark_version = '3.2.2'
# os.environ['PYSPARK_SUBMIT_ARGS'] = '--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.2'

# Session 생성
spark = SparkSession.builder.appName('Stream_bikes').getOrCreate()

schemas = StructType([ \
    StructField("stationId",StringType(),True), \
    StructField("parkingBikeTotCnt",StringType(),True), \
    StructField("rackTotCnt",StringType(),True), \
    StructField("share",StringType(),True), \
    StructField("stationName",StringType(),True), \
    StructField("lat",StringType(),True), \
    StructField("lot",StringType(),True), \
])

# parkingBikeTotCnt: 거치된 자전거 수
# rackTotCnt : 거치대 수
# share : 거치율
# stationId : 대여소 id
# stationName : 이름
# lat,lot : 위도, 경도
# read stream - Dataframe, kafka와 커넥트
stream_kafka_df = spark.readStream.format("kafka")\
    .option("kafka.bootstrap.servers", "ubuntu:9091,ubuntu:9092,ubuntu:9093")\
    .option('subscribe','stream_bikes')\
    .option('startingOffsets','earliest')\
    .load()

select_stream_df = stream_kafka_df.selectExpr("CAST(value AS STRING) as json_data")\
    .select(split(col("json_data"),",").alias("streams"))\
    .select(explode(col("streams")))\
    .withColumn("json_data",from_json(col("col"),schemas))\
    .select("json_data.*")

load_stream_df=select_stream_df.drop("lat","lot","stationName")\
    .withColumnRenamed('parkingBikeTotCnt', 'count_parking_bikes')\
    .withColumnRenamed('rackTotCnt','count_racks')\
    .withColumnRenamed('share', 'per_share')\
    .withColumnRenamed('stationId', 'station_id')

# root
#  |-- station_id: string (nullable = true)
#  |-- count_parking_bikes: string (nullable = true)
#  |-- count_racks: string (nullable = true)
#  |-- per_share: string (nullable = true)

query = load_stream_df.writeStream\
    .format("console")\
    .outputMode("append")\
    .option("checkpointLocation",".checkpoint")\
    .start()

query.awaitTermination()


# ./spark/bin/spark-submit --master yarn --packages org.apache.kafka:kafka_2.12:3.2.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.2 /home/ubuntu/jaryogong_proj/jaryogong_prj/pyspark_streaming/pyspark_api_streaming.py