#!/usr/bin/env python3

import aws_cdk as cdk

from spotify_data_cdk.spotify_data_cdk_stack import SpotifyDataCdkStack


app = cdk.App()
SpotifyDataCdkStack(app, "spotify-data-cdk")

app.synth()
