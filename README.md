# Video Compress

Docker container to compress a video down to a level that Plex can handle

## Usage

Any video files in the /scan volume will be compressed.  Use `-c` to compress.
`-v` for verbose

```
docker build . -t video-compress
docker run -ti -v $PWD/sample:/scan --rm video-compress -c -v
```
