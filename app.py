#!/usr/bin/env python3

import aws_cdk.core as cdk

from spotify_data_cdk.data_stack import SpotifyDataCdkStack


app = cdk.App()
SpotifyDataCdkStack(app, "spotify-data-cdk")

app.synth()
