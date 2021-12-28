import json
import os
import time
import datetime
import boto3
import csv
import pandas as pd
import threading

import requests

from spotifyclient import SpotifyClient

# environment variables
S3_BUCKET = os.environ.get("S3_BUCKET")
S3_BUCKET_DATA_FOLDER = os.environ.get("S3_BUCKET_DATA_FOLDER")
S3_BUCKET_CONFIG_KEY = os.environ.get("S3_BUCKET_CONFIG_KEY")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE")
CLIENT_ID = os.environ.get("CLIENT_ID")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET")
BASE_URL = os.environ.get("BASE_URL")
AUTH_URL = os.environ.get("AUTH_URL")

# connections
s3_client = boto3.client("s3")
dynamodb = boto3.client("dynamodb")
spotify_client = SpotifyClient(client_id=CLIENT_ID,
                            client_secret=CLIENT_SECRET,
                            base_url=BASE_URL,
                            auth_url=AUTH_URL)
                            
# functions
def write_dict_to_s3(s3_client, bucket_name, file_name, data):
    response = s3_client.put_object(
            Bucket=bucket_name, 
            Key=file_name,
            Body=data)
    return response["ResponseMetadata"]["HTTPStatusCode"]
    
def write_artist_to_dynamodb(artist, table_name):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    item = {
            "artist_name":{"S":artist["artist_name"]},
            "date":{"S":today},
            "artist_id":{"S": artist["artist_id"]},
            "top_tracks":{"S": str(artist["top_tracks"])},
            "top_tracks_main_info":{"S": artist["top_tracks_main_info"]}
    }
    response = dynamodb.put_item(
        TableName=table_name, 
        Item=item
    )
    return response["ResponseMetadata"]["HTTPStatusCode"]

def get_artist_from_dynamodb(artist_name, date=None):
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    response = dynamodb.get_item(
        TableName="spotify_artists",
        Key={
            "artist_name": {"S": artist_name},
            "date": {"S": date}
        }
    )
    return response["Item"]["artist_id"]

def tracks_main_info(tracks: dict):
    tracks = pd.json_normalize(tracks['tracks'])
    main_info = tracks[["id","name","popularity"]].to_json(orient="records")
    return main_info
    
def process_artist(artist, spotify_client, s3_client, s3_bucket, dynamodb_table):
    # get top track info
    top_tracks = spotify_client.get_top_tracks(artist["artist_id"])
    artist["top_tracks"] = top_tracks

    # reduce to main info
    top_tracks_main_info = tracks_main_info(top_tracks)
    artist["top_tracks_main_info"] = top_tracks_main_info
    
    # write to S3
    top_tracks_json = json.dumps(obj=top_tracks, 
                        indent=2, 
                        separators=(",", ":"))
                        
    ts = datetime.datetime.now().strftime("%Y-%m-%d")
    file_name = S3_BUCKET_DATA_FOLDER + "top_tracks_" + artist["artist_name"].replace(" ","_") + "_" + ts + ".json"
    
    write_dict_to_s3(s3_client=s3_client,
        bucket_name=s3_bucket,
        file_name=file_name,
        data=top_tracks_json)
    print(f"Wrote s3://{s3_bucket}/{file_name}")
    
    # write to DynamoDB
    write_artist_to_dynamodb(artist, dynamodb_table)
    print(f"Wrote {artist['artist_name']} to DynamoDB ({dynamodb_table})")

def lambda_handler(event, context):
    
    # read artists config file
    artist_config = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_BUCKET_CONFIG_KEY)
    df_artist_config = pd.read_csv(filepath_or_buffer=artist_config["Body"], 
                            sep=';',
                            header=0)
    print(df_artist_config)

    # use local config instead of S3
    #artist_config_path = os.path.join(os.path.dirname(__file__),"config/artists.csv")
    #df_artist_config = pd.read_csv(filepath_or_buffer=artist_config_path, 
    #                        sep=';',
    #                        header=0)

    # find Spotify ID per artist
    df_artist_config["artist_id"] = df_artist_config.apply(lambda artist: 
        spotify_client.get_artist_id_from_search(artist["artist_name"]),
        axis=1)
    print(df_artist_config)
    
    # process each artist concurrently in separate thread
    threads = []
    for index, artist in df_artist_config.iterrows():
        th = threading.Thread(target=process_artist, args=(artist,spotify_client,s3_client,S3_BUCKET,DYNAMODB_TABLE))
        threads.append(th)
        th.start()
        print(F"Started thread {index+1}/{len(df_artist_config)} for {artist['artist_name']}")
    
    # ensure all threads finished running
    for th in threads:
        th.join()
    
    # sequential processing instead of threads
    #for index, artist in df_artist_config.iterrows():
    #    print(F"Will process {artist['artist_name']} (Spotify ID: {artist['artist_id']})")
    #    process_artist(artist, spotify_client, s3_client)